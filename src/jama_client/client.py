"""Asynchronous HTTP client for the Jamacloud REST API.

The :class:`JamaClient` class is an async context manager wrapping
``httpx.AsyncClient``, owning the OAuth :class:`TokenCache`, performing
response envelope unwrapping (``meta`` / ``links`` / ``data``), and
mapping HTTP status codes to typed :mod:`jama_client.exceptions`. The
retry policy is the narrow one defined in Section 6 of the design spec.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, NoReturn, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from types import TracebackType

from jama_client.auth import OAuthCredentials, Token, TokenCache, fetch_token
from jama_client.exceptions import (
    JamaAuthError,
    JamaError,
    JamaForbiddenError,
    JamaNetworkError,
    JamaNotFoundError,
    JamaRateLimitError,
    JamaServerError,
    JamaValidationError,
)
from jama_client.models import Project, User

_M = TypeVar("_M", bound=BaseModel)

_DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_NETWORK_RETRY_LIMIT = 2
_NETWORK_RETRY_BASE_DELAY = 0.5


class JamaClient:
    """Async client wrapping a curated subset of the Jamacloud REST API."""

    def __init__(
        self,
        creds: OAuthCredentials,
        *,
        timeout: httpx.Timeout | None = None,
    ) -> None:
        """Initialize the client; the underlying HTTP transport opens on ``__aenter__``.

        Args:
            creds: Immutable OAuth credentials (including the ``base_url``).
            timeout: Optional ``httpx.Timeout`` override; defaults to a sensible value.
        """
        self._creds = creds
        self._timeout = timeout or _DEFAULT_TIMEOUT
        self._http: httpx.AsyncClient | None = None
        self._tokens = TokenCache()

    @property
    def is_open(self) -> bool:
        """Return ``True`` when the underlying HTTP client is open."""
        return self._http is not None

    async def __aenter__(self) -> JamaClient:
        """Open the underlying ``httpx.AsyncClient``."""
        self._http = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the underlying ``httpx.AsyncClient`` and clear the token cache."""
        if self._http is not None:
            await self._http.aclose()
            self._http = None
        self._tokens.clear()

    async def _ensure_token(self) -> Token:
        """Return a valid token, refreshing proactively at or above 90 percent of TTL."""
        now = datetime.now(tz=UTC)
        cached = self._tokens.get(now=now)
        if cached is not None:
            return cached
        if self._http is None:
            msg = "JamaClient must be used as an async context manager."
            raise RuntimeError(msg)
        token = await fetch_token(self._creds, self._http)
        self._tokens.set(token)
        return token

    async def get_current_user(self) -> User:
        """Return the user identified by the current OAuth credentials.

        Returns:
            A :class:`~jama_client.models.User` populated from the API response.

        Raises:
            JamaValidationError: When the response cannot be validated as a :class:`User`.
        """
        data = await self._request("GET", "/rest/latest/users/current")
        return self._validate(User, data)

    async def list_projects(self) -> list[Project]:
        """Return the first page of accessible Jama projects.

        Pagination metadata (``meta.pageInfo``) is discarded by the default
        envelope-unwrapping behaviour. Phase 2 may revisit pagination by
        passing ``return_envelope=True`` and surfacing ``pageInfo`` to
        callers; for Phase 1 the first page is sufficient for the
        traceability slice.
        """
        data = await self._request("GET", "/rest/latest/projects")
        return [self._validate(Project, item) for item in data]

    @staticmethod
    def _validate(model_cls: type[_M], payload: Any) -> _M:
        """Validate an API payload as ``model_cls``, translating failures to JamaValidationError.

        Args:
            model_cls: The Pydantic model class to validate against.
            payload: The raw API payload (typically a ``dict``).

        Returns:
            A validated instance of ``model_cls``.

        Raises:
            JamaValidationError: When the payload fails Pydantic validation.
        """
        try:
            return model_cls.model_validate(payload)
        except (ValidationError, TypeError, ValueError) as exc:
            msg = f"Failed to validate {model_cls.__name__} response."
            raise JamaValidationError(msg, payload=payload) from exc

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        return_envelope: bool = False,
    ) -> Any:
        """Issue an authenticated request against the Jamacloud API.

        Args:
            method: HTTP verb.
            path: Path under the configured ``base_url`` (must start with ``/``).
            params: Optional query parameters.
            return_envelope: When ``True`` returns the full ``{meta,links,data}`` envelope;
                otherwise returns just the unwrapped ``data`` field.

        Returns:
            Parsed JSON ``data`` field by default, or the full envelope when requested.

        Raises:
            JamaAuthError: The API returned HTTP 401.
            JamaForbiddenError: The API returned HTTP 403.
            JamaNotFoundError: The API returned HTTP 404.
            JamaRateLimitError: The API rate-limited the request and retry was exhausted.
            JamaServerError: The API returned a 5xx status and retry was exhausted.
            JamaNetworkError: A transport-level failure occurred after retries.
            JamaValidationError: The response body failed envelope validation.
            RuntimeError: When invoked outside the async context manager.
        """
        if self._http is None:
            msg = "JamaClient must be used as an async context manager."
            raise RuntimeError(msg)

        url = f"{self._creds.base_url.rstrip('/')}{path}"

        rate_retried = False
        server_retried = False
        network_attempt = 0

        while True:
            token = await self._ensure_token()
            headers = {"Authorization": f"Bearer {token.access_token}"}
            try:
                response = await self._http.request(method, url, params=params, headers=headers)
            except httpx.HTTPError as exc:
                if network_attempt < _NETWORK_RETRY_LIMIT:
                    network_attempt += 1
                    await asyncio.sleep(_NETWORK_RETRY_BASE_DELAY * (2 ** (network_attempt - 1)))
                    continue
                msg = f"Network failure contacting Jamacloud: {exc!r}"
                raise JamaNetworkError(msg) from exc

            status = response.status_code

            if status == 200:
                return self._parse_envelope(response, return_envelope=return_envelope)

            if status == 429:
                if not rate_retried:
                    rate_retried = True
                    retry_after = self._parse_retry_after(response)
                    await asyncio.sleep(retry_after)
                    continue
                msg = "Jamacloud rate limit exceeded after retry."
                raise JamaRateLimitError(msg, retry_after=self._parse_retry_after(response))

            if 500 <= status < 600:
                if not server_retried:
                    server_retried = True
                    continue
                msg = f"Jamacloud returned HTTP {status}."
                raise JamaServerError(msg)

            self._raise_for_status(status)

    @staticmethod
    def _parse_envelope(response: httpx.Response, *, return_envelope: bool) -> Any:
        """Parse and unwrap a Jamacloud response envelope.

        Args:
            response: The raw ``httpx.Response`` to parse.
            return_envelope: When ``True`` return the full payload dict; otherwise
                return only the ``data`` field.

        Returns:
            The unwrapped ``data`` value or the full envelope dict.

        Raises:
            JamaValidationError: When the body is not valid JSON or lacks a ``data`` key.
        """
        try:
            payload = response.json()
        except ValueError as exc:
            msg = "Jamacloud response was not valid JSON."
            raise JamaValidationError(msg, payload=response.text) from exc
        if not isinstance(payload, dict) or "data" not in payload:
            msg = "Jamacloud response missing expected meta/links/data envelope."
            raise JamaValidationError(msg, payload=payload)
        return payload if return_envelope else payload["data"]

    @staticmethod
    def _parse_retry_after(response: httpx.Response) -> int:
        """Extract the ``Retry-After`` header value in seconds.

        Args:
            response: The ``httpx.Response`` carrying the header.

        Returns:
            Integer seconds to wait; defaults to 1 if the header is absent or invalid.
        """
        raw = response.headers.get("Retry-After", "1")
        try:
            return max(0, int(raw))
        except ValueError:
            return 1

    @staticmethod
    def _raise_for_status(status: int) -> NoReturn:
        """Raise a typed exception for a non-success, non-retried HTTP status code.

        Args:
            status: The HTTP status code to map.

        Raises:
            JamaAuthError: For HTTP 401.
            JamaForbiddenError: For HTTP 403.
            JamaNotFoundError: For HTTP 404.
            JamaValidationError: For any other unexpected status code.
        """
        mapping: dict[int, type[JamaError]] = {
            401: JamaAuthError,
            403: JamaForbiddenError,
            404: JamaNotFoundError,
        }
        exc_cls = mapping.get(status)
        if exc_cls is not None:
            raise exc_cls(f"Jamacloud returned HTTP {status}.")
        msg = f"Jamacloud returned unexpected HTTP {status}."
        raise JamaValidationError(msg)
