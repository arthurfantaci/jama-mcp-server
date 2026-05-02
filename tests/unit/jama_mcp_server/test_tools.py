"""Unit tests for the six Phase 1 MCP tools.

Tools are exercised through FastMCP's in-process call_tool API with a mock
JamaClient injected via a synthetic RequestContext.  FastMCP v1.27+ returns a
tuple of (unstructured_content, structured_content) when a tool has an output
schema; the tests use the structured half (result[1]) for assertions so they
are not coupled to JSON serialisation details.

Note: All six tool tests are present (whoami, list_projects, get_item,
search_items, get_downstream_relationships, get_test_runs_for_item).
Imports are tightly scoped — each model class is now used.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Context
from mcp.shared.context import RequestContext

from jama_client.exceptions import JamaNotFoundError
from jama_client.models import Comment, Item, Project, Relationship, TestRun, User
from jama_mcp_server import tools


def _make_context(mock_client: AsyncMock, server: FastMCP) -> Context:
    """Build a synthetic Context with ``mock_client`` in the lifespan dict."""
    req_ctx: RequestContext[Any, Any, Any] = RequestContext(
        request_id="test-request",
        meta=None,
        session=MagicMock(),
        lifespan_context={"jama_client": mock_client},
    )
    return Context(request_context=req_ctx, fastmcp=server)


@pytest.fixture
def server_with_mock_client(mock_jama_client: AsyncMock) -> tuple[FastMCP, AsyncMock]:
    """Return a FastMCP server with tools registered and the mock client ready."""

    @asynccontextmanager
    async def _lifespan(_server: FastMCP) -> Any:
        yield {"jama_client": mock_jama_client}

    server = FastMCP("jama-mcp-server-test", lifespan=_lifespan)
    tools.register(server)
    return server, mock_jama_client


async def test_whoami_returns_ai_shaped_user(
    server_with_mock_client: tuple[FastMCP, AsyncMock],
) -> None:
    server, client = server_with_mock_client
    client.get_current_user.return_value = User(id=100, first_name="A", username="a")
    ctx = _make_context(client, server)
    with patch.object(server, "get_context", return_value=ctx):
        # result is (unstructured_content, structured_dict) — use structured half
        result = await server.call_tool("whoami", {})
    data: dict[str, Any] = result[1]
    assert data["id"] == 100
    assert data["username"] == "a"
    assert "first_name" in data


async def test_list_projects_returns_ai_shaped_list(
    server_with_mock_client: tuple[FastMCP, AsyncMock],
) -> None:
    server, client = server_with_mock_client
    client.list_projects.return_value = [
        Project(id=1, project_key="DEMO"),
        Project(id=2, project_key="PILOT"),
    ]
    ctx = _make_context(client, server)
    with patch.object(server, "get_context", return_value=ctx):
        # list-returning tools are wrapped: result[1] == {"result": [...]}
        result = await server.call_tool("list_projects", {})
    projects: list[dict[str, Any]] = result[1]["result"]
    assert isinstance(projects, list)
    assert {p["project_key"] for p in projects} == {"DEMO", "PILOT"}


async def test_get_item_returns_ai_shaped_item(
    server_with_mock_client: tuple[FastMCP, AsyncMock],
) -> None:
    server, client = server_with_mock_client
    client.get_item.return_value = Item(id=42, document_key="DEMO-REQ-7")
    ctx = _make_context(client, server)
    with patch.object(server, "get_context", return_value=ctx):
        result = await server.call_tool("get_item", {"item_id": 42})
    data: dict[str, Any] = result[1]
    assert data["id"] == 42
    assert data["document_key"] == "DEMO-REQ-7"


async def test_get_item_translates_not_found_to_structured_response(
    server_with_mock_client: tuple[FastMCP, AsyncMock],
) -> None:
    server, client = server_with_mock_client
    client.get_item.side_effect = JamaNotFoundError("not found")
    ctx = _make_context(client, server)
    with patch.object(server, "get_context", return_value=ctx):
        result = await server.call_tool("get_item", {"item_id": 999})
    data: dict[str, Any] = result[1]
    assert data == {"found": False, "item_id": 999, "message": "not found"}


async def test_search_items_returns_ai_shaped_list(
    server_with_mock_client: tuple[FastMCP, AsyncMock],
) -> None:
    server, client = server_with_mock_client
    client.search_items.return_value = [Item(id=42, document_key="DEMO-REQ-7")]
    ctx = _make_context(client, server)
    with patch.object(server, "get_context", return_value=ctx):
        result = await server.call_tool(
            "search_items",
            {"project_id": 1, "query": "OAuth"},
        )
    items: list[dict[str, Any]] = result[1]["result"]
    assert isinstance(items, list)
    assert items[0]["document_key"] == "DEMO-REQ-7"
    client.search_items.assert_awaited_once_with(project_id=1, query="OAuth")


async def test_get_downstream_relationships_returns_ai_shaped_list(
    server_with_mock_client: tuple[FastMCP, AsyncMock],
) -> None:
    server, client = server_with_mock_client
    client.get_downstream_relationships.return_value = [
        Relationship(id=9001, from_item=42, to_item=84, relationship_type=5),
    ]
    ctx = _make_context(client, server)
    with patch.object(server, "get_context", return_value=ctx):
        result = await server.call_tool("get_downstream_relationships", {"item_id": 42})
    rels: list[dict[str, Any]] = result[1]["result"]
    assert rels[0]["from_item"] == 42
    assert rels[0]["to_item"] == 84


async def test_get_test_runs_for_item_returns_ai_shaped_list(
    server_with_mock_client: tuple[FastMCP, AsyncMock],
) -> None:
    server, client = server_with_mock_client
    client.get_test_runs_for_item.return_value = [
        TestRun(id=7001, document_key="DEMO-TR-1"),
    ]
    ctx = _make_context(client, server)
    with patch.object(server, "get_context", return_value=ctx):
        result = await server.call_tool("get_test_runs_for_item", {"item_id": 42})
    runs: list[dict[str, Any]] = result[1]["result"]
    assert runs[0]["id"] == 7001
    assert runs[0]["document_key"] == "DEMO-TR-1"


async def test_create_comment_returns_ai_shaped_comment(
    server_with_mock_client: tuple[FastMCP, AsyncMock],
) -> None:
    server, client = server_with_mock_client
    client.create_comment.return_value = Comment(
        id=5001,
        in_reply_to=None,
        body={"text": "Hello world"},
        comment_type="GENERAL",
        location={"item": 42, "project": 1},
    )
    ctx = _make_context(client, server)
    with patch.object(server, "get_context", return_value=ctx):
        result = await server.call_tool(
            "create_comment",
            {"item_id": 42, "project_id": 1, "body": "Hello world"},
        )
    data: dict[str, Any] = result[1]
    assert data["id"] == 5001
    assert data["in_reply_to"] is None
    assert data["body"] == {"text": "Hello world"}
    assert data["comment_type"] == "GENERAL"
    assert data["location"] == {"item": 42, "project": 1}
    client.create_comment.assert_awaited_once_with(
        item_id=42,
        project_id=1,
        body="Hello world",
        comment_type="GENERAL",
    )


async def test_create_comment_passes_through_non_default_comment_type(
    server_with_mock_client: tuple[FastMCP, AsyncMock],
) -> None:
    """ISSUE comment_type round-trips through the MCP tool to the client.

    Persona 2 (compliance reviewer) needs to post ISSUE-typed comments
    rather than GENERAL so Jama UI renders them with the appropriate
    issue affordance. This test verifies the parameter pass-through; the
    schema validity of "ISSUE" itself is guaranteed by the Jama Swagger
    enum (verified 2026-05-02 against pm2.jamacloud.com/api-docs/) and
    therefore not exercised against the live API.
    """
    server, client = server_with_mock_client
    client.create_comment.return_value = Comment(
        id=5002,
        in_reply_to=None,
        body={"text": "Missing classification"},
        comment_type="ISSUE",
        location={"item": 42, "project": 1},
    )
    ctx = _make_context(client, server)
    with patch.object(server, "get_context", return_value=ctx):
        result = await server.call_tool(
            "create_comment",
            {
                "item_id": 42,
                "project_id": 1,
                "body": "Missing classification",
                "comment_type": "ISSUE",
            },
        )
    data: dict[str, Any] = result[1]
    assert data["comment_type"] == "ISSUE"
    client.create_comment.assert_awaited_once_with(
        item_id=42,
        project_id=1,
        body="Missing classification",
        comment_type="ISSUE",
    )
