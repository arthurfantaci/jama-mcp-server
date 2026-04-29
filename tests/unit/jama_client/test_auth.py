"""Tests for jama_client OAuth helpers (credentials, token, cache)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from jama_client.auth import OAuthCredentials, Token, TokenCache


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
