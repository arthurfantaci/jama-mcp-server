"""Tests for jama_mcp_server.config.Settings."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from jama_mcp_server.config import Settings


def test_settings_loads_from_environment(monkeypatch):
    monkeypatch.setenv("JAMA_BASE_URL", "https://jama.example")
    monkeypatch.setenv("JAMA_OAUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("JAMA_OAUTH_CLIENT_SECRET", "cs")
    monkeypatch.setenv("MCP_TRANSPORT", "stdio")
    monkeypatch.setenv("MCP_HTTP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_HTTP_PORT", "8765")

    settings = Settings()

    assert settings.jama_base_url == "https://jama.example"
    assert settings.jama_oauth_client_id == "cid"
    assert settings.jama_oauth_client_secret.get_secret_value() == "cs"
    assert settings.mcp_transport == "stdio"
    assert settings.mcp_http_host == "127.0.0.1"
    assert settings.mcp_http_port == 8765


def test_settings_defaults_for_optional_fields(monkeypatch):
    monkeypatch.delenv("MCP_HTTP_HOST", raising=False)
    monkeypatch.delenv("MCP_HTTP_PORT", raising=False)
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.setenv("JAMA_BASE_URL", "https://jama.example")
    monkeypatch.setenv("JAMA_OAUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("JAMA_OAUTH_CLIENT_SECRET", "cs")

    settings = Settings()

    assert settings.mcp_transport == "stdio"
    assert settings.mcp_http_host == "127.0.0.1"
    assert settings.mcp_http_port == 8765


def test_settings_raises_when_required_missing(monkeypatch):
    for var in ("JAMA_BASE_URL", "JAMA_OAUTH_CLIENT_ID", "JAMA_OAUTH_CLIENT_SECRET"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_rejects_unknown_transport(monkeypatch):
    monkeypatch.setenv("JAMA_BASE_URL", "https://jama.example")
    monkeypatch.setenv("JAMA_OAUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("JAMA_OAUTH_CLIENT_SECRET", "cs")
    monkeypatch.setenv("MCP_TRANSPORT", "telepathy")
    with pytest.raises(ValidationError):
        Settings()
