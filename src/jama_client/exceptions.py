"""Exception hierarchy for the Jamacloud REST API client.

The :class:`JamaError` base class roots a typed hierarchy mapping Jamacloud
HTTP error semantics onto Python exceptions. The :mod:`jama_client.client`
transport layer raises these directly; the :mod:`jama_mcp_server` layer
catches expected absences (404) and re-raises everything else. See
``docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`` Section 6.
"""

from __future__ import annotations

from typing import Any


class JamaError(Exception):
    """Base class for every error raised by the Jama client."""


class JamaAuthError(JamaError):
    """The Jamacloud API rejected the request with HTTP 401."""


class JamaForbiddenError(JamaError):
    """The Jamacloud API rejected the request with HTTP 403."""


class JamaNotFoundError(JamaError):
    """The Jamacloud API responded with HTTP 404 for a resource lookup."""


class JamaRateLimitError(JamaError):
    """The Jamacloud API rate-limited the request with HTTP 429.

    Args:
        message: Human-readable description of the rate-limit response.
        retry_after: ``Retry-After`` header value in seconds, if provided.
    """

    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class JamaServerError(JamaError):
    """The Jamacloud API responded with an HTTP 5xx status."""


class JamaNetworkError(JamaError):
    """A transport-level failure occurred (connection, timeout, DNS, TLS)."""


class JamaValidationError(JamaError):
    """A Jamacloud response failed Pydantic validation.

    Args:
        message: Description of the validation mismatch.
        payload: The raw response payload that failed to validate, if available.
    """

    def __init__(self, message: str, *, payload: Any | None = None) -> None:
        super().__init__(message)
        self.payload = payload
