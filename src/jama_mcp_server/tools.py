"""MCP tool definitions for the Jama traceability slice."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(_server: FastMCP) -> None:
    """Register the six Phase 1 tools on the given server.

    The registration body is filled in by Tasks 13-17.
    """
    return
