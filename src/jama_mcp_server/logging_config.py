"""Transport-aware structlog configuration.

The MCP stdio transport reserves stdout for JSON-RPC framing; logs must
therefore go to stderr. The streamable HTTP transport runs in containers
that expect logs on stdout. The ``configure_logging(transport)`` function
selects the correct sink based on the transport name. Phase 0 contains
only this placeholder.
"""
