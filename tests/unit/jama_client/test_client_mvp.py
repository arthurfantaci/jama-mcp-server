"""Unit tests for the MVP client methods added in the MVP build phase.

Covers: list_item_types, list_relationship_types, list_items_by_type,
create_item, create_relationship, create_path_a_trace, and the private
resolution helpers that back the workflow tool.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from jama_client.client import JamaClient
from jama_client.exceptions import JamaNotFoundError, JamaValidationError
from jama_client.models import Item, ItemType, Relationship, RelationshipType

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "jama_responses"


def _fixture(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text())


# ---------------------------------------------------------------------------
# list_item_types
# ---------------------------------------------------------------------------


@respx.mock
async def test_list_item_types_returns_item_type_models(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/projects/127/itemtypes").mock(
        return_value=httpx.Response(200, json=_fixture("itemtypes_list.json")),
    )
    async with JamaClient(jama_credentials) as client:
        item_types = await client.list_item_types(127)
    assert len(item_types) == 3
    assert all(isinstance(it, ItemType) for it in item_types)
    keys = {it.type_key for it in item_types}
    assert keys == {"SET", "SUBSR", "CODE"}


@respx.mock
async def test_list_item_types_caches_result_on_second_call(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.get(f"{jama_base_url}/rest/latest/projects/127/itemtypes").mock(
        return_value=httpx.Response(200, json=_fixture("itemtypes_list.json")),
    )
    async with JamaClient(jama_credentials) as client:
        await client.list_item_types(127)
        await client.list_item_types(127)
    assert route.call_count == 1


# ---------------------------------------------------------------------------
# list_relationship_types
# ---------------------------------------------------------------------------


@respx.mock
async def test_list_relationship_types_returns_rel_type_models(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.get(f"{jama_base_url}/rest/latest/relationshiptypes").mock(
        return_value=httpx.Response(200, json=_fixture("relationshiptypes_list.json")),
    )
    async with JamaClient(jama_credentials) as client:
        rel_types = await client.list_relationship_types(127)
    assert len(rel_types) == 2
    assert all(isinstance(rt, RelationshipType) for rt in rel_types)
    names = {rt.name for rt in rel_types}
    assert "Implemented by" in names
    assert route.calls.last.request.url.params["project"] == "127"


@respx.mock
async def test_list_relationship_types_caches_result_on_second_call(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.get(f"{jama_base_url}/rest/latest/relationshiptypes").mock(
        return_value=httpx.Response(200, json=_fixture("relationshiptypes_list.json")),
    )
    async with JamaClient(jama_credentials) as client:
        await client.list_relationship_types(127)
        await client.list_relationship_types(127)
    assert route.call_count == 1


# ---------------------------------------------------------------------------
# list_items_by_type
# ---------------------------------------------------------------------------


@respx.mock
async def test_list_items_by_type_returns_items_and_not_capped(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.get(f"{jama_base_url}/rest/latest/abstractitems").mock(
        return_value=httpx.Response(200, json=_fixture("abstractitems_by_type.json")),
    )
    async with JamaClient(jama_credentials) as client:
        items, max_items_reached = await client.list_items_by_type(127, 87)
    assert len(items) == 2
    assert all(isinstance(i, Item) for i in items)
    assert max_items_reached is False
    assert route.calls.last.request.url.params["project"] == "127"
    assert route.calls.last.request.url.params["itemType"] == "87"


@respx.mock
async def test_list_items_by_type_signals_max_items_reached_when_capped(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    """max_items_reached is True when cap is hit before all results fetched."""
    single_item_page = {
        "meta": {
            "status": "OK",
            "pageInfo": {"startIndex": 0, "resultCount": 1, "totalResults": 5},
        },
        "data": [
            {
                "id": 1,
                "documentKey": "X-1",
                "itemType": 87,
                "project": 127,
                "fields": {"name": "Item 1"},
            }
        ],
    }
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/abstractitems").mock(
        return_value=httpx.Response(200, json=single_item_page),
    )
    async with JamaClient(jama_credentials) as client:
        items, max_items_reached = await client.list_items_by_type(127, 87, max_items=1)
    assert len(items) == 1
    assert max_items_reached is True


@respx.mock
async def test_list_items_by_type_paginates_across_multiple_pages(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    """Multiple API calls are made when results span more than one page."""

    def _page(start: int, page_items: list[dict], total: int) -> dict:
        return {
            "meta": {
                "status": "OK",
                "pageInfo": {
                    "startIndex": start,
                    "resultCount": len(page_items),
                    "totalResults": total,
                },
            },
            "data": page_items,
        }

    def _item(item_id: int) -> dict:
        return {
            "id": item_id,
            "documentKey": f"X-{item_id}",
            "itemType": 87,
            "project": 127,
            "fields": {"name": f"Item {item_id}"},
        }

    responses = [
        httpx.Response(200, json=_page(0, [_item(1), _item(2)], total=3)),
        httpx.Response(200, json=_page(2, [_item(3)], total=3)),
    ]
    call_index = 0

    def _next_page(_request: httpx.Request) -> httpx.Response:
        nonlocal call_index
        resp = responses[call_index]
        call_index += 1
        return resp

    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/abstractitems").mock(side_effect=_next_page)
    async with JamaClient(jama_credentials) as client:
        items, max_items_reached = await client.list_items_by_type(127, 87, max_items=200)
    assert len(items) == 3
    assert max_items_reached is False


# ---------------------------------------------------------------------------
# create_item
# ---------------------------------------------------------------------------


@respx.mock
async def test_create_item_posts_canonical_payload_and_returns_item(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.post(f"{jama_base_url}/rest/latest/items").mock(
        return_value=httpx.Response(201, json=_fixture("items_create.json")),
    )
    async with JamaClient(jama_credentials) as client:
        item = await client.create_item(
            project_id=127,
            item_type=114,
            parent=212,
            name="occlusion_detector.py",
            fields={"path$114": "src/foo.py", "code_version$114": "v1.0.0"},
        )
    assert isinstance(item, Item)
    assert item.id == 115200
    assert item.item_type == 114
    assert item.project == 127
    assert item.fields["name"] == "occlusion_detector.py"
    assert item.fields["path$114"] == "src/foo.py"
    sent = json.loads(route.calls.last.request.content)
    assert sent["project"] == 127
    assert sent["itemType"] == 114
    assert sent["location"] == {"parent": {"item": 212}}
    assert sent["fields"]["name"] == "occlusion_detector.py"


@respx.mock
async def test_create_item_raises_when_response_missing_id(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.post(f"{jama_base_url}/rest/latest/items").mock(
        return_value=httpx.Response(201, json={"meta": {"status": "Created"}}),
    )
    async with JamaClient(jama_credentials) as client:
        with pytest.raises(JamaValidationError, match="did not include a new item ID"):
            await client.create_item(project_id=127, item_type=114, parent=212, name="x")


# ---------------------------------------------------------------------------
# create_relationship
# ---------------------------------------------------------------------------


@respx.mock
async def test_create_relationship_posts_canonical_payload_and_returns_relationship(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.post(f"{jama_base_url}/rest/latest/relationships").mock(
        return_value=httpx.Response(201, json=_fixture("relationships_create.json")),
    )
    async with JamaClient(jama_credentials) as client:
        rel = await client.create_relationship(
            from_item=115100,
            to_item=115200,
            relationship_type=19,
        )
    assert isinstance(rel, Relationship)
    assert rel.id == 18600
    assert rel.from_item == 115100
    assert rel.to_item == 115200
    assert rel.relationship_type == 19
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"fromItem": 115100, "toItem": 115200, "relationshipType": 19}


@respx.mock
async def test_create_relationship_raises_when_response_missing_id(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.post(f"{jama_base_url}/rest/latest/relationships").mock(
        return_value=httpx.Response(201, json={"meta": {"status": "Created"}}),
    )
    async with JamaClient(jama_credentials) as client:
        with pytest.raises(JamaValidationError, match="did not include a new relationship ID"):
            await client.create_relationship(from_item=1, to_item=2, relationship_type=19)


# ---------------------------------------------------------------------------
# create_path_a_trace — unit test with mocked sub-methods
# ---------------------------------------------------------------------------


async def test_create_path_a_trace_composes_primitives_and_returns_ids():
    """create_path_a_trace delegates to the correct client methods."""
    client = AsyncMock(spec=JamaClient)
    client._type_cache = {}
    client._http = object()

    source_item = Item(id=115100, item_type=87, project=127, document_key="AF-SUBSS-25")
    code_item = Item(id=115200, item_type=114, project=127)
    relationship = Relationship(id=18600, from_item=115100, to_item=115200, relationship_type=19)

    client._find_item_by_key = AsyncMock(return_value=source_item)
    client._resolve_code_item_type = AsyncMock(return_value=114)
    client._resolve_implemented_by_rel_type = AsyncMock(return_value=19)
    client._resolve_implementation_code_set = AsyncMock(return_value=212)
    client.create_item = AsyncMock(return_value=code_item)
    client.create_relationship = AsyncMock(return_value=relationship)

    result = await JamaClient.create_path_a_trace(
        client,
        project_id=127,
        source_requirement_key="AF-SUBSS-25",
        code_path="src/occlusion_detection/occlusion_detector.py:7-42",
        code_version="v1.0.0-rc1",
    )

    assert result["source_item_id"] == 115100
    assert result["code_item_id"] == 115200
    assert result["relationship_id"] == 18600

    client._find_item_by_key.assert_called_once_with(127, "AF-SUBSS-25")
    client.create_item.assert_called_once()
    call_kwargs = client.create_item.call_args.kwargs
    assert call_kwargs["name"] == "occlusion_detector.py"
    assert call_kwargs["fields"]["path$114"] == "src/occlusion_detection/occlusion_detector.py:7-42"
    assert call_kwargs["fields"]["code_version$114"] == "v1.0.0-rc1"


async def test_create_path_a_trace_uses_explicit_name_when_provided():
    """An explicit name overrides the basename derivation."""
    client = AsyncMock(spec=JamaClient)
    client._type_cache = {}

    source_item = Item(id=1, item_type=87, project=127)
    code_item = Item(id=2, item_type=114, project=127)
    relationship = Relationship(id=3, from_item=1, to_item=2, relationship_type=19)

    client._find_item_by_key = AsyncMock(return_value=source_item)
    client._resolve_code_item_type = AsyncMock(return_value=114)
    client._resolve_implemented_by_rel_type = AsyncMock(return_value=19)
    client._resolve_implementation_code_set = AsyncMock(return_value=212)
    client.create_item = AsyncMock(return_value=code_item)
    client.create_relationship = AsyncMock(return_value=relationship)

    await JamaClient.create_path_a_trace(
        client,
        project_id=127,
        source_requirement_key="AF-SUBSS-25",
        code_path="src/foo/bar.py",
        code_version="v2.0.0",
        name="explicit_name.py",
    )

    call_kwargs = client.create_item.call_args.kwargs
    assert call_kwargs["name"] == "explicit_name.py"


async def test_create_path_a_trace_propagates_not_found_for_missing_source():
    """JamaNotFoundError from _find_item_by_key propagates before any write."""
    client = AsyncMock(spec=JamaClient)
    client._type_cache = {}
    client._find_item_by_key = AsyncMock(side_effect=JamaNotFoundError("not found"))
    client._resolve_code_item_type = AsyncMock(return_value=114)
    client._resolve_implemented_by_rel_type = AsyncMock(return_value=19)
    client._resolve_implementation_code_set = AsyncMock(return_value=212)

    with pytest.raises(JamaNotFoundError):
        await JamaClient.create_path_a_trace(
            client,
            project_id=127,
            source_requirement_key="INVALID-KEY",
            code_path="src/foo.py",
            code_version="v1.0.0",
        )

    client.create_item.assert_not_called()
    client.create_relationship.assert_not_called()


# ---------------------------------------------------------------------------
# _resolve_code_item_type
# ---------------------------------------------------------------------------


@respx.mock
async def test_resolve_code_item_type_finds_code_type_key(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/projects/127/itemtypes").mock(
        return_value=httpx.Response(200, json=_fixture("itemtypes_list.json")),
    )
    async with JamaClient(jama_credentials) as client:
        code_type_id = await client._resolve_code_item_type(127)
    assert code_type_id == 114


@respx.mock
async def test_resolve_code_item_type_raises_when_no_code_type_exists(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    no_code_types = {
        "meta": {"status": "OK"},
        "data": [{"id": 87, "typeKey": "SUBSR", "display": "Subsystem Requirement"}],
    }
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/projects/127/itemtypes").mock(
        return_value=httpx.Response(200, json=no_code_types),
    )
    async with JamaClient(jama_credentials) as client:
        with pytest.raises(JamaNotFoundError, match="typeKey 'CODE'"):
            await client._resolve_code_item_type(127)


# ---------------------------------------------------------------------------
# _resolve_implementation_code_set
# ---------------------------------------------------------------------------


@respx.mock
async def test_resolve_implementation_code_set_finds_by_name_substring(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    sets_page = {
        "meta": {
            "status": "OK",
            "pageInfo": {"startIndex": 0, "resultCount": 2, "totalResults": 2},
        },
        "data": [
            {
                "id": 212,
                "documentKey": "AF-SET-212",
                "itemType": 31,
                "project": 127,
                "fields": {"name": "Implementation Code (for trace)"},
            },
            {
                "id": 180,
                "documentKey": "AF-SET-180",
                "itemType": 31,
                "project": 127,
                "fields": {"name": "Software Requirements"},
            },
        ],
    }
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/abstractitems").mock(
        return_value=httpx.Response(200, json=sets_page),
    )
    async with JamaClient(jama_credentials) as client:
        set_id = await client._resolve_implementation_code_set(127)
    assert set_id == 212


@respx.mock
async def test_resolve_implementation_code_set_raises_when_no_match(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    empty_page = {
        "meta": {
            "status": "OK",
            "pageInfo": {"startIndex": 0, "resultCount": 0, "totalResults": 0},
        },
        "data": [],
    }
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/abstractitems").mock(
        return_value=httpx.Response(200, json=empty_page),
    )
    async with JamaClient(jama_credentials) as client:
        with pytest.raises(JamaNotFoundError, match="Implementation Code"):
            await client._resolve_implementation_code_set(127)


@respx.mock
async def test_resolve_implementation_code_set_raises_when_multiple_matches(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    ambiguous_page = {
        "meta": {
            "status": "OK",
            "pageInfo": {"startIndex": 0, "resultCount": 2, "totalResults": 2},
        },
        "data": [
            {
                "id": 211,
                "itemType": 31,
                "project": 127,
                "fields": {"name": "Implementation Code A"},
            },
            {
                "id": 212,
                "itemType": 31,
                "project": 127,
                "fields": {"name": "Implementation Code B"},
            },
        ],
    }
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/abstractitems").mock(
        return_value=httpx.Response(200, json=ambiguous_page),
    )
    async with JamaClient(jama_credentials) as client:
        with pytest.raises(JamaNotFoundError, match="Multiple Sets"):
            await client._resolve_implementation_code_set(127)


# ---------------------------------------------------------------------------
# _find_item_by_key
# ---------------------------------------------------------------------------


@respx.mock
async def test_find_item_by_key_returns_matching_item(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    found_page = {
        "meta": {
            "status": "OK",
            "pageInfo": {"startIndex": 0, "resultCount": 1, "totalResults": 1},
        },
        "data": [
            {
                "id": 115100,
                "documentKey": "AF-SUBSS-25",
                "itemType": 87,
                "project": 127,
                "fields": {"name": "SWR-OD-001"},
            }
        ],
    }
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.get(f"{jama_base_url}/rest/latest/abstractitems").mock(
        return_value=httpx.Response(200, json=found_page),
    )
    async with JamaClient(jama_credentials) as client:
        item = await client._find_item_by_key(127, "AF-SUBSS-25")
    assert item.id == 115100
    assert route.calls.last.request.url.params["documentKey"] == "AF-SUBSS-25"
    assert route.calls.last.request.url.params["project"] == "127"


@respx.mock
async def test_find_item_by_key_raises_when_not_found(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    empty_page = {
        "meta": {
            "status": "OK",
            "pageInfo": {"startIndex": 0, "resultCount": 0, "totalResults": 0},
        },
        "data": [],
    }
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/abstractitems").mock(
        return_value=httpx.Response(200, json=empty_page),
    )
    async with JamaClient(jama_credentials) as client:
        with pytest.raises(JamaNotFoundError, match="AF-MISSING"):
            await client._find_item_by_key(127, "AF-MISSING")
