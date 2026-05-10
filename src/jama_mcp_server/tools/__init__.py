"""MCP tool registration for the Jama traceability slice.

Tools are split into two namespaces:

- :mod:`jama_mcp_server.tools.core` — read/write primitives that anticipate
  the Jama Connect MCP™ vendor product's expected surface area.
- :mod:`jama_mcp_server.tools.workflow` — AI-consumption macro tools that
  compose core primitives; explicitly NOT expected in Jama Connect MCP™.

The :func:`register` function registers both namespaces onto a FastMCP server
instance and is the sole entry point called by
:func:`jama_mcp_server.server.build_server`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from jama_mcp_server.tools import core, workflow

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(server: FastMCP) -> None:
    """Register all core and workflow tools on ``server``.

    Args:
        server: The :class:`~mcp.server.fastmcp.FastMCP` instance to register
            tools on.
    """
    core.register(server)
    workflow.register(server)
