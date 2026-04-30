"""Tests for the streamable-HTTP /health route handler."""

from __future__ import annotations

from unittest.mock import MagicMock

from starlette.responses import JSONResponse

from jama_mcp_server.server import _health


async def test_health_returns_status_ok() -> None:
    """The _health handler returns 200 with the canonical liveness payload."""
    request = MagicMock()  # _health does not read the request
    response = await _health(request)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    assert response.body == b'{"status":"ok"}'
