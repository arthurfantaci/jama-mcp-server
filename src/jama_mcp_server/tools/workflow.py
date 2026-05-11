"""Workflow MCP tool definitions — AI-consumption macro tools.

Workflow tool — composes core primitives; NOT expected in Jama Connect MCP™.

Each tool in this module demonstrates the engineering practice of designing
MCP tools for agentic AI consumption: they compose primitive operations into
higher-level actions that reduce the number of tool calls an agent needs to
accomplish a complete workflow step.
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
    """Register the workflow tools on ``server``."""

    @server.tool()
    async def create_path_a_trace(
        ctx: _Context,
        project_id: int,
        source_requirement_key: str,
        code_path: str,
        code_version: str,
        repo_origin: str | None = None,
        name: str | None = None,
        code_set_id: int | None = None,
        code_item_type: int | None = None,
        relationship_type: int | None = None,
    ) -> dict[str, Any]:
        """Create a Path A trace link from a source requirement to a new Code item.

        Workflow tool — composes core primitives; NOT expected in Jama Connect
        MCP™. High-level workflow for ``project_id`` that, given
        ``source_requirement_key`` (a document key like ``"AF-SUBSS-25"``),
        ``code_path`` (e.g. ``"src/detection/detector.py:7-42"``),
        ``code_version`` (e.g. ``"v1.0.0-rc1"``), and optionally
        ``repo_origin`` (e.g. ``"github.com/arthurfantaci/jama-mcp-server"``):

        1. Validates the source requirement exists (returns an error before
           any write if the key cannot be resolved). ``source_requirement_key``
           is a Jama document key — no prior ``search_items`` call is needed.
           By contrast, ``create_relationship`` and ``create_comment`` accept
           numeric item IDs only.
        2. Creates a Code item in the Implementation Code Set with ``path``
           and ``code_version`` fields populated; the item ``name`` defaults to
           the basename of ``code_path`` with any trailing ``:N-M`` line-range
           suffix stripped (mid-path colons such as ISO timestamps are
           preserved). When ``repo_origin`` is supplied, also populates the
           item ``description`` with a four-line deep link in the form::

               Repository: <repo_origin>
               Version: <code_version>
               Path: <path-without-range> (lines N-M)
               Link: https://<repo_origin>/blob/<code_version>/<path>#LN-LM

           The ``(lines N-M)`` annotation and ``#LN-LM`` fragment are omitted
           when ``code_path`` carries no trailing line range.
        3. Creates an ``"Implemented by"`` relationship from the source
           requirement to the new Code item.

        Type IDs and the Set ID default to project-discovery when omitted:
        ``code_item_type`` is resolved by ``typeKey == "CODE"``;
        ``relationship_type`` is resolved by name ``"Implemented by"``;
        ``code_set_id`` is resolved by case-insensitive name containing
        ``"Implementation Code"``. Discovered IDs are cached for the session
        lifetime. Pass explicit overrides for projects that differ from this
        naming convention. Returns ``{"source_item_id": int, "code_item_id":
        int, "relationship_id": int}``.
        """
        result = await _client(ctx).create_path_a_trace(
            project_id=project_id,
            source_requirement_key=source_requirement_key,
            code_path=code_path,
            code_version=code_version,
            repo_origin=repo_origin,
            name=name,
            code_set_id=code_set_id,
            code_item_type=code_item_type,
            relationship_type=relationship_type,
        )
        return result
