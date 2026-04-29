"""MCP tool definitions for the Jama traceability slice.

Each tool retrieves the shared :class:`jama_client.JamaClient` from the
lifespan context and returns AI-shaped dictionaries with snake_case keys
(via Pydantic's default ``model_dump``). Expected absences (404 from
``get_item``) are converted to structured ``found: false`` responses; all
other exceptions propagate so FastMCP returns tool-call errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp.server import Context

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from jama_client import JamaClient

# Fully-parameterised alias avoids mypy [type-arg] errors in strict mode.
_Context = Context[Any, Any, Any]


def _client(ctx: _Context) -> JamaClient:
    """Extract the shared :class:`JamaClient` from the lifespan context."""
    client: JamaClient = ctx.request_context.lifespan_context["jama_client"]
    return client


def register(server: FastMCP) -> None:
    """Register the six Phase 1 tools on the given FastMCP server."""

    @server.tool()
    async def whoami(ctx: _Context) -> dict[str, Any]:
        """Identify the user whose OAuth credentials authenticate the server."""
        user = await _client(ctx).get_current_user()
        return user.model_dump()

    @server.tool()
    async def list_projects(ctx: _Context) -> list[dict[str, Any]]:
        """Return projects accessible to the configured Jama credentials."""
        projects = await _client(ctx).list_projects()
        return [p.model_dump() for p in projects]
