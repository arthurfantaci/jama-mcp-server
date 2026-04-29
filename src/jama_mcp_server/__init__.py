"""FastMCP server exposing Jamacloud REST operations as MCP tools.

The package defines the FastMCP application instance, transport-specific
entry points (stdio and streamable HTTP), the lifespan context that owns
the shared ``JamaClient``, and six MCP tool functions implementing the
Phase 1 traceability slice.
"""
