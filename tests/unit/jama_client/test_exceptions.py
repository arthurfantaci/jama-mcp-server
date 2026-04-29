"""Tests for the jama_client exception hierarchy."""

from __future__ import annotations

import pytest

from jama_client.exceptions import (
    JamaAuthError,
    JamaError,
    JamaForbiddenError,
    JamaNetworkError,
    JamaNotFoundError,
    JamaRateLimitError,
    JamaServerError,
    JamaValidationError,
)


def test_jama_error_is_base_exception():
    assert issubclass(JamaError, Exception)


@pytest.mark.parametrize(
    "subclass",
    [
        JamaAuthError,
        JamaForbiddenError,
        JamaNotFoundError,
        JamaRateLimitError,
        JamaServerError,
        JamaNetworkError,
        JamaValidationError,
    ],
)
def test_subclasses_inherit_from_jama_error(subclass):
    assert issubclass(subclass, JamaError)


def test_rate_limit_error_exposes_retry_after():
    err = JamaRateLimitError("rate limited", retry_after=42)
    assert err.retry_after == 42
    assert "rate limited" in str(err)


def test_rate_limit_error_default_retry_after_is_none():
    err = JamaRateLimitError("rate limited")
    assert err.retry_after is None


def test_validation_error_exposes_payload():
    payload = {"unexpected": "shape"}
    err = JamaValidationError("bad shape", payload=payload)
    assert err.payload is payload


def test_validation_error_default_payload_is_none():
    err = JamaValidationError("bad shape")
    assert err.payload is None
