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


async def test_lifespan_warms_token_cache_and_yields_client(
    mock_jama_client: AsyncMock,
) -> None:
    """jama_lifespan calls warm_token_cache() and yields the client to lifespan_context."""
    settings = Settings(
        jama_base_url="https://jama.example",
        jama_oauth_client_id="cid",
        jama_oauth_client_secret="cs",
    )

    def factory(_settings: Settings) -> AsyncMock:
        return mock_jama_client

    async with server_module.jama_lifespan(None, settings=settings, client_factory=factory) as ctx:
        # During yield: client is in lifespan_context (per-MCP-session context)
        assert ctx["jama_client"] is mock_jama_client
        # Eager warm was called exactly once at session start
        mock_jama_client.warm_token_cache.assert_awaited_once()


async def test_run_http_with_warm_populates_and_clears_state(
    mock_jama_client: AsyncMock,
) -> None:
    """_run_http_with_warm warms cache, populates _state during serve, clears it on exit."""
    settings = Settings(
        jama_base_url="https://jama.example",
        jama_oauth_client_id="cid",
        jama_oauth_client_secret="cs",
    )

    def factory(_settings: Settings) -> AsyncMock:
        return mock_jama_client

    # Build a stub FastMCP whose run_streamable_http_async asserts the
    # invariants in-flight, so we observe _state DURING serve, not just
    # before/after.
    seen: dict[str, object] = {}

    async def fake_serve() -> None:
        seen["state_during_serve"] = server_module._state.jama_client
        seen["warm_calls_during_serve"] = mock_jama_client.warm_token_cache.await_count

    fake_server = MagicMock()
    fake_server.run_streamable_http_async = fake_serve

    # Verify clean baseline.
    assert server_module._state.jama_client is None

    await server_module._run_http_with_warm(fake_server, settings, client_factory=factory)

    # During serve: _state was populated, warm fired exactly once before serve.
    assert seen["state_during_serve"] is mock_jama_client
    assert seen["warm_calls_during_serve"] == 1
    # After serve: _state is cleared (try/finally cleanup).
    assert server_module._state.jama_client is None
