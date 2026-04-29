"""Transport-aware structlog configuration.

The MCP stdio transport reserves stdout for JSON-RPC framing, so logs are
sent to stderr in that mode. The streamable-HTTP transport runs in
container environments where stdout is the conventional log sink.
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(transport: str) -> None:
    """Configure root logging and ``structlog`` for the given transport.

    Args:
        transport: ``"stdio"`` (logs to stderr) or ``"streamable-http"`` (logs to stdout).

    Raises:
        ValueError: When ``transport`` is not a recognised value.
    """
    if transport == "stdio":
        stream = sys.stderr
    elif transport == "streamable-http":
        stream = sys.stdout
    else:
        msg = f"Unknown transport: {transport!r}. Expected 'stdio' or 'streamable-http'."
        raise ValueError(msg)

    handler = logging.StreamHandler(stream=stream)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
