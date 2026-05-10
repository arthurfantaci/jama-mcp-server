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

from jama_client.models import Item, ItemType, Relationship, RelationshipType, User
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
    """FastMCP with all thirteen tools registered and a stubbed lifespan."""

    @asynccontextmanager
    async def _lifespan(_server: FastMCP) -> Any:
        yield {"jama_client": mock_jama_client}

    s = FastMCP("jama-mcp-server-test", lifespan=_lifespan)
    tools.register(s)
    return s


async def test_server_lists_all_registered_tools(server: FastMCP) -> None:
    """All thirteen tools across core/* and workflow/* are discoverable."""
    listed = await server.list_tools()
    names = {tool.name for tool in listed}
    assert names == {
        "whoami",
        "list_projects",
        "get_item",
        "search_items",
        "get_downstream_relationships",
        "get_test_runs_for_item",
        "create_comment",
        "list_item_types",
        "list_relationship_types",
        "list_items_by_type",
        "create_item",
        "create_relationship",
        "create_path_a_trace",
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


async def test_list_item_types_call_round_trips_via_protocol(
    server: FastMCP,
    mock_jama_client: AsyncMock,
) -> None:
    """list_item_types returns a list of item-type dicts via protocol."""
    mock_jama_client.list_item_types.return_value = [
        ItemType(id=114, type_key="CODE", display="Code"),
        ItemType(id=87, type_key="SUBSR", display="Subsystem Requirement"),
    ]
    ctx = _make_context(mock_jama_client, server)
    with patch.object(server, "get_context", return_value=ctx):
        response = await server.call_tool("list_item_types", {"project_id": 127})
    # FastMCP wraps list returns in {"result": [...]}; assert against the inner list.
    result: list[dict[str, Any]] = response[1]["result"]
    assert len(result) == 2
    type_keys = {it["type_key"] for it in result}
    assert type_keys == {"CODE", "SUBSR"}
    mock_jama_client.list_item_types.assert_called_once_with(127)


async def test_list_relationship_types_call_round_trips_via_protocol(
    server: FastMCP,
    mock_jama_client: AsyncMock,
) -> None:
    """list_relationship_types returns a list of relationship-type dicts via protocol."""
    mock_jama_client.list_relationship_types.return_value = [
        RelationshipType(id=19, name="Implemented by"),
    ]
    ctx = _make_context(mock_jama_client, server)
    with patch.object(server, "get_context", return_value=ctx):
        response = await server.call_tool("list_relationship_types", {"project_id": 127})
    # FastMCP wraps list returns in {"result": [...]}; assert against the inner list.
    result: list[dict[str, Any]] = response[1]["result"]
    assert len(result) == 1
    assert result[0]["name"] == "Implemented by"


async def test_list_items_by_type_returns_items_and_flag(
    server: FastMCP,
    mock_jama_client: AsyncMock,
) -> None:
    """list_items_by_type wraps items and max_items_reached flag."""
    items = [Item(id=115100, item_type=87, project=127, document_key="AF-SUBSS-25")]
    mock_jama_client.list_items_by_type.return_value = (items, False)
    ctx = _make_context(mock_jama_client, server)
    with patch.object(server, "get_context", return_value=ctx):
        response = await server.call_tool(
            "list_items_by_type",
            {"project_id": 127, "item_type": 87},
        )
    result: dict[str, Any] = response[1]
    assert result["max_items_reached"] is False
    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == 115100


async def test_create_item_call_round_trips_via_protocol(
    server: FastMCP,
    mock_jama_client: AsyncMock,
) -> None:
    """create_item returns the synthesised item dict via protocol."""
    mock_jama_client.create_item.return_value = Item(
        id=115200,
        item_type=114,
        project=127,
        fields={"name": "occlusion_detector.py"},
    )
    ctx = _make_context(mock_jama_client, server)
    with patch.object(server, "get_context", return_value=ctx):
        response = await server.call_tool(
            "create_item",
            {
                "project_id": 127,
                "item_type": 114,
                "parent": 212,
                "name": "occlusion_detector.py",
            },
        )
    result: dict[str, Any] = response[1]
    assert result["id"] == 115200
    assert result["item_type"] == 114


async def test_create_relationship_validates_set_endpoint(
    server: FastMCP,
    mock_jama_client: AsyncMock,
) -> None:
    """create_relationship raises ToolError when from_item is a Set (type 31).

    FastMCP wraps tool-raised exceptions in ToolError at the protocol layer.
    The error message is preserved in the ToolError's string representation.
    """
    from mcp.server.fastmcp.exceptions import ToolError

    mock_jama_client.get_item.return_value = Item(id=31, item_type=31, project=127)
    ctx = _make_context(mock_jama_client, server)
    with (
        patch.object(server, "get_context", return_value=ctx),
        pytest.raises(ToolError, match="Set"),
    ):
        await server.call_tool(
            "create_relationship",
            {"from_item": 31, "to_item": 115200, "relationship_type": 19},
        )


async def test_create_relationship_call_round_trips_via_protocol(
    server: FastMCP,
    mock_jama_client: AsyncMock,
) -> None:
    """create_relationship returns relationship dict when neither endpoint is a Set."""
    mock_jama_client.get_item.side_effect = [
        Item(id=115100, item_type=87, project=127),
        Item(id=115200, item_type=114, project=127),
    ]
    mock_jama_client.create_relationship.return_value = Relationship(
        id=18600,
        from_item=115100,
        to_item=115200,
        relationship_type=19,
    )
    ctx = _make_context(mock_jama_client, server)
    with patch.object(server, "get_context", return_value=ctx):
        response = await server.call_tool(
            "create_relationship",
            {"from_item": 115100, "to_item": 115200, "relationship_type": 19},
        )
    result: dict[str, Any] = response[1]
    assert result["id"] == 18600
    assert result["from_item"] == 115100
    assert result["to_item"] == 115200


async def test_create_path_a_trace_call_round_trips_via_protocol(
    server: FastMCP,
    mock_jama_client: AsyncMock,
) -> None:
    """create_path_a_trace returns source, code, and relationship IDs via protocol."""
    mock_jama_client.create_path_a_trace.return_value = {
        "source_item_id": 115100,
        "code_item_id": 115200,
        "relationship_id": 18600,
    }
    ctx = _make_context(mock_jama_client, server)
    with patch.object(server, "get_context", return_value=ctx):
        response = await server.call_tool(
            "create_path_a_trace",
            {
                "project_id": 127,
                "source_requirement_key": "AF-SUBSS-25",
                "code_path": "src/detection/detector.py:7-42",
                "code_version": "v1.0.0-rc1",
            },
        )
    result: dict[str, Any] = response[1]
    assert result["source_item_id"] == 115100
    assert result["code_item_id"] == 115200
    assert result["relationship_id"] == 18600
    mock_jama_client.create_path_a_trace.assert_called_once_with(
        project_id=127,
        source_requirement_key="AF-SUBSS-25",
        code_path="src/detection/detector.py:7-42",
        code_version="v1.0.0-rc1",
        name=None,
        code_set_id=None,
        code_item_type=None,
        relationship_type=None,
    )
