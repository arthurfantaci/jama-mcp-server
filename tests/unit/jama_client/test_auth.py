"""Tests for jama_client OAuth helpers (credentials, token, cache)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
import respx

from jama_client.auth import OAuthCredentials, Token, TokenCache, fetch_token
from jama_client.exceptions import (
    JamaAuthError,
    JamaForbiddenError,
    JamaNetworkError,
    JamaServerError,
    JamaValidationError,
)


def _now() -> datetime:
    return datetime(2026, 4, 29, 12, 0, 0, tzinfo=UTC)


def test_oauth_credentials_immutable():
    creds = OAuthCredentials(client_id="cid", client_secret="cs", base_url="https://j.example")
    with pytest.raises(Exception):  # pydantic ValidationError or FrozenInstanceError
        creds.client_id = "other"  # type: ignore[misc]


def test_token_expiry_calculation():
    issued = _now()
    token = Token(access_token="t", expires_in=3600, issued_at=issued)
    assert token.expires_at == issued + timedelta(seconds=3600)


def test_token_cache_returns_none_when_empty():
    cache = TokenCache()
    assert cache.get(now=_now()) is None


def test_token_cache_returns_token_when_fresh():
    cache = TokenCache()
    token = Token(access_token="fresh", expires_in=3600, issued_at=_now())
    cache.set(token)
    assert cache.get(now=_now() + timedelta(seconds=60)) is token


def test_token_cache_returns_none_at_or_above_ninety_percent_ttl():
    cache = TokenCache()
    issued = _now()
    cache.set(Token(access_token="aging", expires_in=3600, issued_at=issued))
    # 90% of 3600 = 3240 seconds.
    assert cache.get(now=issued + timedelta(seconds=3239)) is not None
    assert cache.get(now=issued + timedelta(seconds=3240)) is None
    assert cache.get(now=issued + timedelta(seconds=3241)) is None


def test_token_cache_clear_evicts_token():
    cache = TokenCache()
    cache.set(Token(access_token="t", expires_in=3600, issued_at=_now()))
    cache.clear()
    assert cache.get(now=_now()) is None


_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "jama_responses"
_BASE_URL = "https://jama.example"


def _creds() -> OAuthCredentials:
    return OAuthCredentials(client_id="cid", client_secret="cs", base_url=_BASE_URL)


@respx.mock
async def test_fetch_token_success_returns_token():
    payload = json.loads((_FIXTURES / "oauth_token.json").read_text())
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(return_value=httpx.Response(200, json=payload))
    async with httpx.AsyncClient() as client:
        token = await fetch_token(_creds(), client)
    assert token.access_token == payload["access_token"]
    assert token.expires_in == payload["expires_in"]


@respx.mock
async def test_fetch_token_uses_basic_auth_and_form_body():
    route = respx.post(f"{_BASE_URL}/rest/oauth/token").mock(
        return_value=httpx.Response(200, json={"access_token": "x", "expires_in": 60}),
    )
    async with httpx.AsyncClient() as client:
        await fetch_token(_creds(), client)
    request = route.calls.last.request
    assert request.headers["authorization"].startswith("Basic ")
    assert request.headers["content-type"].startswith("application/x-www-form-urlencoded")
    assert b"grant_type=client_credentials" in request.content


@respx.mock
async def test_fetch_token_raises_auth_error_on_401():
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(return_value=httpx.Response(401))
    async with httpx.AsyncClient() as client:
        with pytest.raises(JamaAuthError):
            await fetch_token(_creds(), client)


@respx.mock
async def test_fetch_token_raises_forbidden_error_on_403():
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(return_value=httpx.Response(403))
    async with httpx.AsyncClient() as client:
        with pytest.raises(JamaForbiddenError):
            await fetch_token(_creds(), client)


@respx.mock
async def test_fetch_token_raises_server_error_on_503():
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(return_value=httpx.Response(503))
    async with httpx.AsyncClient() as client:
        with pytest.raises(JamaServerError):
            await fetch_token(_creds(), client)


@respx.mock
async def test_fetch_token_raises_network_error_on_transport_failure():
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(side_effect=httpx.ConnectError("boom"))
    async with httpx.AsyncClient() as client:
        with pytest.raises(JamaNetworkError):
            await fetch_token(_creds(), client)


@respx.mock
async def test_fetch_token_raises_validation_error_on_missing_fields():
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(
        return_value=httpx.Response(200, json={"unexpected": "shape"}),
    )
    async with httpx.AsyncClient() as client:
        with pytest.raises(JamaValidationError):
            await fetch_token(_creds(), client)


@respx.mock
async def test_fetch_token_raises_auth_error_on_unexpected_status():
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(return_value=httpx.Response(302))
    async with httpx.AsyncClient() as client:
        with pytest.raises(JamaAuthError):
            await fetch_token(_creds(), client)
