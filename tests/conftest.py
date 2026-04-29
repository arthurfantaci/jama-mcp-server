"""Shared pytest fixtures for the Jama MCP Server test suite."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from jama_client import JamaClient
from jama_client.auth import OAuthCredentials


@pytest.fixture
def jama_base_url() -> str:
    """Return the test base URL used by respx-mocked tests."""
    return "https://jama.example"


@pytest.fixture
def jama_token_url(jama_base_url: str) -> str:
    """Return the OAuth token endpoint URL used by respx-mocked tests."""
    return f"{jama_base_url}/rest/oauth/token"


@pytest.fixture
def jama_credentials(jama_base_url: str) -> OAuthCredentials:
    """Return a fresh ``OAuthCredentials`` instance for unit tests."""
    return OAuthCredentials(client_id="cid", client_secret="cs", base_url=jama_base_url)


@pytest.fixture
def jama_token_stub() -> dict[str, Any]:
    """Return a sample OAuth token endpoint response payload."""
    return {"access_token": "tok", "expires_in": 3600}


@pytest.fixture
def mock_jama_client() -> AsyncMock:
    """Return an ``AsyncMock`` configured to behave as a :class:`JamaClient`."""
    client = AsyncMock(spec=JamaClient)
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    return client
