"""Tests for JamaClient transport: lifecycle, _request envelope, retry policy."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx

from jama_client.client import JamaClient
from jama_client.exceptions import (
    JamaAuthError,
    JamaForbiddenError,
    JamaNetworkError,
    JamaNotFoundError,
    JamaRateLimitError,
    JamaServerError,
    JamaValidationError,
)


@respx.mock
async def test_client_is_async_context_manager_and_closes_http(
    jama_credentials,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    async with JamaClient(jama_credentials) as client:
        assert client.is_open
    assert not client.is_open


@respx.mock
async def test_request_unwraps_envelope_and_returns_data(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/ping").mock(
        return_value=httpx.Response(200, json={"meta": {}, "links": {}, "data": {"ok": True}}),
    )
    async with JamaClient(jama_credentials) as client:
        result = await client._request("GET", "/rest/latest/ping")
    assert result == {"ok": True}


@respx.mock
async def test_request_returns_envelope_when_caller_requests_it(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    payload = {"meta": {"pageInfo": {"totalResults": 1}}, "links": {}, "data": []}
    respx.get(f"{jama_base_url}/rest/latest/ping").mock(
        return_value=httpx.Response(200, json=payload),
    )
    async with JamaClient(jama_credentials) as client:
        envelope = await client._request("GET", "/rest/latest/ping", return_envelope=True)
    assert envelope == payload


@respx.mock
async def test_request_injects_bearer_token(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.get(f"{jama_base_url}/rest/latest/ping").mock(
        return_value=httpx.Response(200, json={"meta": {}, "links": {}, "data": {}}),
    )
    async with JamaClient(jama_credentials) as client:
        await client._request("GET", "/rest/latest/ping")
    assert route.calls.last.request.headers["authorization"] == "Bearer tok"


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, JamaAuthError),
        (403, JamaForbiddenError),
        (404, JamaNotFoundError),
        (500, JamaServerError),
    ],
)
@respx.mock
async def test_request_maps_status_codes_to_typed_exceptions(
    status,
    expected,
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/ping").mock(return_value=httpx.Response(status))
    async with JamaClient(jama_credentials) as client:
        with pytest.raises(expected):
            await client._request("GET", "/rest/latest/ping")


@respx.mock
async def test_request_rate_limit_retries_once_with_retry_after(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.get(f"{jama_base_url}/rest/latest/ping").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"meta": {}, "links": {}, "data": {"ok": True}}),
        ],
    )
    with patch("jama_client.client.asyncio.sleep") as mock_sleep:
        async with JamaClient(jama_credentials) as client:
            result = await client._request("GET", "/rest/latest/ping")
    assert result == {"ok": True}
    assert route.call_count == 2
    assert mock_sleep.await_count == 1


@respx.mock
async def test_request_rate_limit_raises_after_second_failure(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/ping").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "0"}),
    )
    async with JamaClient(jama_credentials) as client:
        with pytest.raises(JamaRateLimitError):
            await client._request("GET", "/rest/latest/ping")


@respx.mock
async def test_request_server_error_retries_once(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.get(f"{jama_base_url}/rest/latest/ping").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json={"meta": {}, "links": {}, "data": {"ok": True}}),
        ],
    )
    async with JamaClient(jama_credentials) as client:
        result = await client._request("GET", "/rest/latest/ping")
    assert result == {"ok": True}
    assert route.call_count == 2


@respx.mock
async def test_request_network_error_retries_with_backoff_then_raises(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.get(f"{jama_base_url}/rest/latest/ping").mock(
        side_effect=httpx.ConnectError("boom"),
    )
    with patch("jama_client.client.asyncio.sleep") as mock_sleep:
        async with JamaClient(jama_credentials) as client:
            with pytest.raises(JamaNetworkError):
                await client._request("GET", "/rest/latest/ping")
    assert route.call_count == 3  # initial + 2 retries per _NETWORK_RETRY_LIMIT
    assert mock_sleep.await_count == 2


@respx.mock
async def test_request_raises_validation_error_on_missing_envelope(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/ping").mock(
        return_value=httpx.Response(200, text="not-json"),
    )
    async with JamaClient(jama_credentials) as client:
        with pytest.raises(JamaValidationError):
            await client._request("GET", "/rest/latest/ping")


async def test_client_request_outside_context_raises_runtime_error(jama_credentials):
    client = JamaClient(jama_credentials)
    with pytest.raises(RuntimeError):
        await client._request("GET", "/rest/latest/ping")


@pytest.mark.parametrize(
    ("retry_after_value", "expected"),
    [
        ("5", 5),
        ("0", 0),
        ("-3", 0),
        ("not-a-number", 1),
        (None, 1),
    ],
)
def test_parse_retry_after_handles_various_inputs(retry_after_value, expected):
    headers = httpx.Headers(
        {"Retry-After": retry_after_value} if retry_after_value is not None else {},
    )
    response = httpx.Response(429, headers=headers)
    assert JamaClient._parse_retry_after(response) == expected
