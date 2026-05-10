"""Core MCP tool definitions — read/write primitives anticipating Jama Connect MCP™.

Each tool in this module mirrors functionality expected in the Jama Connect MCP™
vendor product and maps directly to a Jamacloud REST endpoint. Tools retrieve the
shared :class:`jama_client.JamaClient` from the lifespan context and return
AI-shaped dictionaries with snake_case keys via Pydantic's default
``model_dump``.

Expected absences (404 from ``get_item``) are converted to structured
``found: false`` responses; all other exceptions propagate so FastMCP returns
tool-call errors. The asymmetry is intentional: ``get_item`` is the primary
entry-point for agentic requirement lookup and a "not found" result is a useful
AI signal, while write-tool failures (``create_item``, ``create_relationship``)
are programming errors that warrant a full error response.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp.server import Context

from jama_client.exceptions import JamaNotFoundError, JamaValidationError

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from jama_client import JamaClient

# Fully-parameterised alias avoids mypy [type-arg] errors in strict mode.
_Context = Context[Any, Any, Any]

_SET_ITEM_TYPE = 31


def _client(ctx: _Context) -> JamaClient:
    """Extract the shared :class:`JamaClient` from the lifespan context."""
    client: JamaClient = ctx.request_context.lifespan_context["jama_client"]
    return client


def register(server: FastMCP) -> None:
    """Register the twelve core tools on ``server``.

    Seven Phase 1 / Phase 4.5 tools plus the five new MVP core tools.
    """

    @server.tool()
    async def whoami(ctx: _Context) -> dict[str, Any]:
        """Identify the user whose OAuth credentials authenticate the server.

        Anticipates ``GET /rest/latest/users/current`` from Jama Connect MCP™.
        """
        user = await _client(ctx).get_current_user()
        return user.model_dump()

    @server.tool()
    async def list_projects(ctx: _Context) -> list[dict[str, Any]]:
        """Return projects accessible to the configured Jama credentials.

        Anticipates ``GET /rest/latest/projects`` from Jama Connect MCP™.
        """
        projects = await _client(ctx).list_projects()
        return [p.model_dump() for p in projects]

    @server.tool()
    async def get_item(ctx: _Context, item_id: int) -> dict[str, Any]:
        """Retrieve a Jama item by its numeric ``item_id``.

        Anticipates ``GET /rest/latest/items/{id}`` from Jama Connect MCP™.
        Returns ``{"found": False, "item_id": id, "message": ...}`` when the
        item does not exist; otherwise returns the item's snake_case
        serialization.
        """
        try:
            item = await _client(ctx).get_item(item_id)
        except JamaNotFoundError as exc:
            return {"found": False, "item_id": item_id, "message": str(exc)}
        return item.model_dump()

    @server.tool()
    async def search_items(
        ctx: _Context,
        project_id: int,
        query: str,
    ) -> list[dict[str, Any]]:
        """Search Jama items within ``project_id`` for ``query``.

        Anticipates ``GET /rest/latest/abstractitems`` from Jama Connect MCP™.
        ``query`` is matched against item content as a free-text search.
        """
        items = await _client(ctx).search_items(project_id=project_id, query=query)
        return [item.model_dump() for item in items]

    @server.tool()
    async def get_downstream_relationships(
        ctx: _Context,
        item_id: int,
    ) -> list[dict[str, Any]]:
        """Return downstream relationships originating from ``item_id``.

        Anticipates ``GET /rest/latest/items/{id}/downstreamrelationships`` from
        Jama Connect MCP™.
        """
        rels = await _client(ctx).get_downstream_relationships(item_id)
        return [rel.model_dump() for rel in rels]

    @server.tool()
    async def get_test_runs_for_item(
        ctx: _Context,
        item_id: int,
    ) -> list[dict[str, Any]]:
        """Return test runs that exercise the test case identified by ``item_id``.

        Anticipates ``GET /rest/latest/testruns`` from Jama Connect MCP™.
        ``item_id`` should be the ID of an item whose item type is a test case.
        """
        runs = await _client(ctx).get_test_runs_for_item(item_id)
        return [run.model_dump() for run in runs]

    @server.tool()
    async def create_comment(
        ctx: _Context,
        item_id: int,
        project_id: int,
        body: str,
        comment_type: str = "GENERAL",
    ) -> dict[str, Any]:
        """Create a top-level comment on the Jama item identified by ``item_id``.

        Anticipates ``POST /rest/latest/comments`` from Jama Connect MCP™.
        The comment is created with the specified ``comment_type`` (default
        ``"GENERAL"``) and no parent — ``inReplyTo`` is omitted from the
        request payload entirely (sending ``0`` triggers a server-side NPE
        on Jamacloud). Both ``item_id`` and ``project_id`` are required by
        Jama's request schema; obtain ``project_id`` from a prior
        ``get_item`` call's ``project`` field or from ``list_projects``.

        Valid ``comment_type`` enum values per the Jama Swagger schema:
        ``"GENERAL"`` (default), ``"QUESTION"``, ``"PROPOSED_CHANGE"``,
        ``"ACCEPTED_COMMENT"``, ``"REJECTED_COMMENT"``, ``"ISSUE"``,
        ``"DECISION"``, ``"DECISION_REQUEST"``. Jama validates the value
        server-side and rejects unrecognised strings with HTTP 400.
        """
        comment = await _client(ctx).create_comment(
            item_id=item_id,
            project_id=project_id,
            body=body,
            comment_type=comment_type,
        )
        return comment.model_dump()

    @server.tool()
    async def list_item_types(
        ctx: _Context,
        project_id: int,
    ) -> list[dict[str, Any]]:
        """Enumerate all item types configured for ``project_id``.

        Anticipates ``GET /rest/latest/projects/{id}/itemtypes`` from Jama
        Connect MCP™. Required for the agent to discover correct type IDs
        before calling ``create_item``. Results are cached for the session.
        """
        item_types = await _client(ctx).list_item_types(project_id)
        return [it.model_dump() for it in item_types]

    @server.tool()
    async def list_relationship_types(
        ctx: _Context,
        project_id: int,
    ) -> list[dict[str, Any]]:
        """Enumerate all relationship types available within ``project_id``.

        Anticipates ``GET /rest/latest/relationshiptypes`` from Jama Connect
        MCP™. Required for the agent to discover the correct relationship type
        ID (e.g. ``"Implemented by"``) before calling ``create_relationship``.
        Results are cached for the session.
        """
        rel_types = await _client(ctx).list_relationship_types(project_id)
        return [rt.model_dump() for rt in rel_types]

    @server.tool()
    async def list_items_by_type(
        ctx: _Context,
        project_id: int,
        item_type: int,
        max_items: int = 200,
    ) -> dict[str, Any]:
        """List items of ``item_type`` within ``project_id``, up to ``max_items``.

        Anticipates ``GET /rest/latest/abstractitems`` filtered by project and
        item type from Jama Connect MCP™. Aggregates across pages internally;
        ``max_items`` caps the total (default 200). Returns
        ``{"items": [...], "max_items_reached": bool}`` — check
        ``max_items_reached`` to detect when the cap was hit before all results
        were collected.
        """
        items, max_items_reached = await _client(ctx).list_items_by_type(
            project_id=project_id,
            item_type=item_type,
            max_items=max_items,
        )
        return {
            "items": [item.model_dump() for item in items],
            "max_items_reached": max_items_reached,
        }

    @server.tool()
    async def create_item(
        ctx: _Context,
        project_id: int,
        item_type: int,
        parent: int,
        name: str,
        fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new Jama item of ``item_type`` within the parent identified by ``parent``.

        Anticipates ``POST /rest/latest/items`` from Jama Connect MCP™. Use
        ``list_item_types`` to discover valid ``item_type`` IDs; ``parent`` is
        the numeric ID of the parent Set or container item. The optional
        ``fields`` dict is merged with ``{"name": name}`` before submission;
        type-specific field keys follow Jama's ``<fieldName>$<typeId>`` pattern
        (e.g. ``"path$114"``).

        The returned representation is synthesised from the assigned ID plus the
        request inputs; issue a follow-up ``get_item`` call for a fully-populated
        representation with all server-assigned fields.
        """
        item = await _client(ctx).create_item(
            project_id=project_id,
            item_type=item_type,
            parent=parent,
            name=name,
            fields=fields,
        )
        return item.model_dump()

    @server.tool()
    async def create_relationship(
        ctx: _Context,
        from_item: int,
        to_item: int,
        relationship_type: int,
    ) -> dict[str, Any]:
        """Create a directed relationship from ``from_item`` to ``to_item``.

        Anticipates ``POST /rest/latest/relationships`` from Jama Connect MCP™.
        Neither ``from_item`` nor ``to_item`` may be a Set (item type 31) —
        Sets carry no relationships in Jama. Use ``list_relationship_types`` to
        discover valid ``relationship_type`` IDs.
        """
        from_obj = await _client(ctx).get_item(from_item)
        if from_obj.item_type == _SET_ITEM_TYPE:
            msg = (
                f"Cannot create relationship: from_item {from_item} is a "
                f"Set (item type 31); Sets carry no relationships in Jama."
            )
            raise JamaValidationError(msg)
        to_obj = await _client(ctx).get_item(to_item)
        if to_obj.item_type == _SET_ITEM_TYPE:
            msg = (
                f"Cannot create relationship: to_item {to_item} is a "
                f"Set (item type 31); Sets carry no relationships in Jama."
            )
            raise JamaValidationError(msg)

        rel = await _client(ctx).create_relationship(
            from_item=from_item,
            to_item=to_item,
            relationship_type=relationship_type,
        )
        return rel.model_dump()
