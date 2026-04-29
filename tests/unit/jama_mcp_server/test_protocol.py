"""Protocol-level tests using FastMCP's in-process test client.

Verifies tool registration completeness, input-schema generation, and
end-to-end protocol round-trip via ``server.list_tools()`` and
``server.call_tool()``.  FastMCP v1.27+ returns a ``(unstructured, structured)``
tuple from ``call_tool`` when an output schema exists; tests assert against
``result[1]`` for the structured half.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Context
from mcp.shared.context import RequestContext

from jama_client.models import User
from jama_mcp_server import tools


def _make_context(mock_client: AsyncMock, server: FastMCP) -> Context:
    """Build a synthetic Context with mock_client in the lifespan dict."""
    req_ctx: RequestContext[Any, Any, Any] = RequestContext(
        request_id="test-request",
        meta=None,
        session=MagicMock(),
        lifespan_context={"jama_client": mock_client},
    )
    return Context(request_context=req_ctx, fastmcp=server)


@pytest.fixture
def server(mock_jama_client: AsyncMock) -> FastMCP:
    """FastMCP with all six tools registered and a stubbed lifespan."""

    @asynccontextmanager
    async def _lifespan(_server: FastMCP) -> Any:
        yield {"jama_client": mock_jama_client}

    s = FastMCP("jama-mcp-server-test", lifespan=_lifespan)
    tools.register(s)
    return s


async def test_server_lists_six_tools(server: FastMCP) -> None:
    """All six Phase 1 tools are registered and discoverable."""
    listed = await server.list_tools()
    names = {tool.name for tool in listed}
    assert names == {
        "whoami",
        "list_projects",
        "get_item",
        "search_items",
        "get_downstream_relationships",
        "get_test_runs_for_item",
    }


async def test_get_item_schema_declares_item_id_argument(server: FastMCP) -> None:
    """get_item's input schema lists item_id as an integer property."""
    listed = await server.list_tools()
    by_name = {tool.name: tool for tool in listed}
    schema = by_name["get_item"].inputSchema
    assert "item_id" in schema["properties"]
    assert schema["properties"]["item_id"]["type"] == "integer"


async def test_whoami_call_round_trips_via_protocol(
    server: FastMCP,
    mock_jama_client: AsyncMock,
) -> None:
    """whoami round-trips through call_tool with the structured-content tuple."""
    mock_jama_client.get_current_user.return_value = User(id=100, username="afantaci")
    ctx = _make_context(mock_jama_client, server)
    with patch.object(server, "get_context", return_value=ctx):
        response = await server.call_tool("whoami", {})
    data: dict[str, Any] = response[1]
    assert data["id"] == 100
    assert data["username"] == "afantaci"
