"""Tests for the FastMCP lifespan and server construction."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

from jama_mcp_server import server as server_module
from jama_mcp_server.config import Settings
from jama_mcp_server.server import build_server, jama_lifespan

if TYPE_CHECKING:
    import pytest


class _FakeClient:
    """Stand-in for JamaClient supporting async-context-manager lifecycle."""

    def __init__(self) -> None:
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> _FakeClient:
        self.entered = True
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.exited = True

    async def warm_token_cache(self) -> None:
        """No-op warm for tests that don't care about cache warming."""


async def test_jama_lifespan_yields_client_and_cleans_up(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lifespan yields the client in context and calls __aexit__ on exit."""
    fake = _FakeClient()

    def _factory(_settings: object) -> _FakeClient:
        return fake

    settings = MagicMock(jama_base_url="https://jama.example", jama_oauth_client_id="cid")
    settings.jama_oauth_client_secret.get_secret_value = MagicMock(return_value="cs")

    server = MagicMock()
    async with jama_lifespan(server, settings=settings, client_factory=_factory) as ctx:
        assert ctx["jama_client"] is fake
        assert fake.entered
    assert fake.exited


def test_build_server_returns_fastmcp_instance() -> None:
    """build_server returns a FastMCP instance with the .tool decorator attribute."""
    settings = MagicMock(
        jama_base_url="https://jama.example",
        jama_oauth_client_id="cid",
        mcp_http_host="127.0.0.1",
        mcp_http_port=8765,
    )
    settings.jama_oauth_client_secret.get_secret_value = MagicMock(return_value="cs")
    server = build_server(settings=settings)
    assert server is not None
    assert hasattr(server, "tool")  # FastMCP exposes the @tool decorator


async def test_lifespan_warms_token_cache_and_populates_state(
    mock_jama_client: AsyncMock,
) -> None:
    """jama_lifespan calls warm_token_cache() and populates _state.jama_client during yield."""
    settings = Settings(
        jama_base_url="https://jama.example",
        jama_oauth_client_id="cid",
        jama_oauth_client_secret="cs",
    )

    def factory(_settings: Settings) -> AsyncMock:
        return mock_jama_client

    # Verify clean baseline.
    assert server_module._state.jama_client is None

    async with server_module.jama_lifespan(None, settings=settings, client_factory=factory) as ctx:
        # During yield: client is in lifespan_context AND in _state
        assert ctx["jama_client"] is mock_jama_client
        assert server_module._state.jama_client is mock_jama_client
        # Eager warm was called exactly once
        mock_jama_client.warm_token_cache.assert_awaited_once()

    # After yield: _state is cleared
    assert server_module._state.jama_client is None
