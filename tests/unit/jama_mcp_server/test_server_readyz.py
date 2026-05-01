"""Tests for the streamable-HTTP /readyz route handler."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from jama_client import JamaClient
from jama_mcp_server import server as server_module
from jama_mcp_server.server import _readyz


@pytest.fixture(autouse=True)
def _reset_state():
    """Ensure the module-level _state.jama_client starts and ends as None for each test."""
    server_module._state.jama_client = None
    yield
    server_module._state.jama_client = None


async def test_readyz_returns_503_when_client_is_none() -> None:
    """No client in _state (e.g., before lifespan startup) returns 503 not_ready."""
    request = MagicMock()  # _readyz does not read the request
    response = await _readyz(request)

    assert response.status_code == 503
    body = json.loads(response.body)
    assert body == {"status": "not_ready", "reason": "client_not_initialized"}


async def test_readyz_returns_200_when_token_is_fresh() -> None:
    """A populated client with a fresh token returns 200 ready."""
    client = MagicMock(spec=JamaClient)
    client.is_token_fresh.return_value = True
    server_module._state.jama_client = client

    response = await _readyz(MagicMock())

    assert response.status_code == 200
    body = json.loads(response.body)
    assert body == {"status": "ready"}
    client.is_token_fresh.assert_called_once()


async def test_readyz_returns_503_when_token_is_stale() -> None:
    """A populated client with a stale or absent token returns 503 not_ready."""
    client = MagicMock(spec=JamaClient)
    client.is_token_fresh.return_value = False
    server_module._state.jama_client = client

    response = await _readyz(MagicMock())

    assert response.status_code == 503
    body = json.loads(response.body)
    assert body == {"status": "not_ready", "reason": "token_unavailable"}
    client.is_token_fresh.assert_called_once()
