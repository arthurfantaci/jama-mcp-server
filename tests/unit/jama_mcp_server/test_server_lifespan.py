"""Tests for the FastMCP lifespan and server construction."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

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
