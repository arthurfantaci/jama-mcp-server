"""Command-line entry point for ``python -m jama_mcp_server``.

The Phase 0 skeleton dispatches to the placeholder entry points in
``server.py`` based on the ``MCP_TRANSPORT`` environment variable.
"""

from __future__ import annotations

import os
import sys

from jama_mcp_server.server import main_http, main_stdio


def _dispatch() -> None:
    """Dispatch to the transport entry point named by ``MCP_TRANSPORT``."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()
    if transport == "stdio":
        main_stdio()
    elif transport == "streamable-http":
        main_http()
    else:
        msg = f"Unknown MCP_TRANSPORT value: {transport!r}. Expected 'stdio' or 'streamable-http'."
        print(msg, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    _dispatch()
