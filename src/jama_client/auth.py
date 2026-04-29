"""OAuth 2.0 client_credentials authentication for Jamacloud.

Exposes :class:`OAuthCredentials` (immutable configuration), :class:`Token`
(access token plus issuance metadata), :class:`TokenCache` (in-memory cache
with proactive refresh at or above 90 percent of TTL), and the
:func:`fetch_token` wire call against ``/rest/oauth/token``. See
``docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`` Section 6.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
from pydantic import BaseModel, ConfigDict, Field

from jama_client.exceptions import (
    JamaAuthError,
    JamaForbiddenError,
    JamaNetworkError,
    JamaServerError,
    JamaValidationError,
)

_REFRESH_FRACTION = 0.9


class OAuthCredentials(BaseModel):
    """Immutable OAuth 2.0 client_credentials configuration."""

    model_config = ConfigDict(frozen=True)

    client_id: str
    client_secret: str
    base_url: str


class Token(BaseModel):
    """An OAuth access token with issuance metadata."""

    model_config = ConfigDict(frozen=True)

    access_token: str
    expires_in: int
    issued_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    @property
    def expires_at(self) -> datetime:
        """Return the absolute expiry instant."""
        return self.issued_at + timedelta(seconds=self.expires_in)

    def is_stale(self, *, now: datetime) -> bool:
        """Return ``True`` once at or beyond 90 percent of the token's TTL."""
        elapsed = (now - self.issued_at).total_seconds()
        return elapsed >= _REFRESH_FRACTION * self.expires_in


class TokenCache:
    """Single-token in-memory cache with proactive refresh."""

    def __init__(self) -> None:
        self._token: Token | None = None

    def get(self, *, now: datetime) -> Token | None:
        """Return the cached token if present and not stale, else ``None``."""
        token = self._token
        if token is None or token.is_stale(now=now):
            return None
        return token

    def set(self, token: Token) -> None:
        """Replace the cached token."""
        self._token = token

    def clear(self) -> None:
        """Evict the cached token."""
        self._token = None


async def fetch_token(creds: OAuthCredentials, http: httpx.AsyncClient) -> Token:
    """Exchange OAuth client credentials for an access token.

    Args:
        creds: Immutable OAuth credentials including ``base_url``.
        http: Pre-constructed ``httpx.AsyncClient`` used to issue the request.

    Returns:
        A :class:`Token` representing the access token.

    Raises:
        JamaAuthError: The token endpoint returned 401.
        JamaForbiddenError: The token endpoint returned 403.
        JamaServerError: The token endpoint returned a 5xx status.
        JamaNetworkError: A transport-level error occurred.
        JamaValidationError: The response body did not include the expected fields.
    """
    url = f"{creds.base_url.rstrip('/')}/rest/oauth/token"
    try:
        response = await http.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(creds.client_id, creds.client_secret),
        )
    except httpx.HTTPError as exc:
        msg = f"OAuth token request failed at the transport layer: {exc!r}"
        raise JamaNetworkError(msg) from exc

    if response.status_code == 401:
        msg = "OAuth token endpoint rejected client credentials (HTTP 401)."
        raise JamaAuthError(msg)
    if response.status_code == 403:
        msg = "OAuth token endpoint forbade the request (HTTP 403)."
        raise JamaForbiddenError(msg)
    if 500 <= response.status_code < 600:
        msg = f"OAuth token endpoint returned HTTP {response.status_code}."
        raise JamaServerError(msg)
    if response.status_code != 200:
        msg = f"Unexpected status {response.status_code} from OAuth token endpoint."
        raise JamaAuthError(msg)

    try:
        payload = response.json()
        access_token = payload["access_token"]
        expires_in = int(payload["expires_in"])
    except (KeyError, ValueError, TypeError) as exc:
        msg = "OAuth token response missing required fields."
        raise JamaValidationError(msg, payload=response.text) from exc

    return Token(access_token=access_token, expires_in=expires_in)
