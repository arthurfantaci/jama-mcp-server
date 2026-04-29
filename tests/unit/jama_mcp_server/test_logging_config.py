"""Tests for jama_mcp_server.logging_config.configure_logging."""

from __future__ import annotations

import logging
import sys

import pytest

from jama_mcp_server.logging_config import configure_logging


@pytest.fixture(autouse=True)
def _reset_logging():
    yield
    # Reset root handlers between tests so per-test stream selection sticks.
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)


def test_stdio_transport_logs_to_stderr():
    configure_logging("stdio")
    root = logging.getLogger()
    streams = {getattr(h, "stream", None) for h in root.handlers}
    assert sys.stderr in streams
    assert sys.stdout not in streams


def test_streamable_http_transport_logs_to_stdout():
    configure_logging("streamable-http")
    root = logging.getLogger()
    streams = {getattr(h, "stream", None) for h in root.handlers}
    assert sys.stdout in streams
    assert sys.stderr not in streams


def test_unknown_transport_raises_value_error():
    with pytest.raises(ValueError):
        configure_logging("telepathy")
