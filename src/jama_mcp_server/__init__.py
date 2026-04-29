"""FastMCP server exposing Jamacloud REST operations as MCP tools."""

from __future__ import annotations

from jama_mcp_server.server import build_server, jama_lifespan, main_http, main_stdio

__all__ = ["build_server", "jama_lifespan", "main_http", "main_stdio"]
