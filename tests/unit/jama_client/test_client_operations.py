"""Tests for JamaClient operations (get_current_user, list_projects, get_item, ...)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from jama_client.client import JamaClient
from jama_client.exceptions import JamaNotFoundError
from jama_client.models import Comment, Item, Project, Relationship, TestRun, User

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "jama_responses"


def _fixture(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text())


@respx.mock
async def test_get_current_user_returns_user_model(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/users/current").mock(
        return_value=httpx.Response(200, json=_fixture("users_current.json")),
    )
    async with JamaClient(jama_credentials) as client:
        user = await client.get_current_user()
    assert isinstance(user, User)
    assert user.id == 100
    assert user.username == "afantaci"


@respx.mock
async def test_list_projects_returns_list_of_project_models(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/projects").mock(
        return_value=httpx.Response(200, json=_fixture("projects_list.json")),
    )
    async with JamaClient(jama_credentials) as client:
        projects = await client.list_projects()
    assert len(projects) == 2
    assert all(isinstance(p, Project) for p in projects)
    assert {p.project_key for p in projects} == {"DEMO", "PILOT"}


@respx.mock
async def test_get_item_returns_item_model(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/items/42").mock(
        return_value=httpx.Response(200, json=_fixture("items_get.json")),
    )
    async with JamaClient(jama_credentials) as client:
        item = await client.get_item(42)
    assert isinstance(item, Item)
    assert item.id == 42
    assert item.document_key == "DEMO-REQ-7"


@respx.mock
async def test_get_item_propagates_not_found(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/items/999").mock(return_value=httpx.Response(404))
    async with JamaClient(jama_credentials) as client:
        with pytest.raises(JamaNotFoundError):
            await client.get_item(999)


@respx.mock
async def test_search_items_returns_items_within_project(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.get(f"{jama_base_url}/rest/latest/abstractitems").mock(
        return_value=httpx.Response(200, json=_fixture("abstractitems_search.json")),
    )
    async with JamaClient(jama_credentials) as client:
        items = await client.search_items(project_id=1, query="OAuth")
    assert len(items) == 1
    assert items[0].document_key == "DEMO-REQ-7"
    assert route.calls.last.request.url.params["project"] == "1"
    assert route.calls.last.request.url.params["contains"] == "OAuth"


@respx.mock
async def test_get_downstream_relationships_returns_relationship_models(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    respx.get(f"{jama_base_url}/rest/latest/items/42/downstreamrelationships").mock(
        return_value=httpx.Response(200, json=_fixture("items_downstream_relationships.json")),
    )
    async with JamaClient(jama_credentials) as client:
        rels = await client.get_downstream_relationships(42)
    assert len(rels) == 1
    assert isinstance(rels[0], Relationship)
    assert rels[0].from_item == 42
    assert rels[0].to_item == 84


@respx.mock
async def test_get_test_runs_for_item_returns_test_run_models(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.get(f"{jama_base_url}/rest/latest/testruns").mock(
        return_value=httpx.Response(200, json=_fixture("items_test_runs.json")),
    )
    async with JamaClient(jama_credentials) as client:
        runs = await client.get_test_runs_for_item(42)
    assert len(runs) == 1
    assert isinstance(runs[0], TestRun)
    assert runs[0].fields["testRunStatus"] == "PASSED"
    assert route.calls.last.request.url.params["testCase"] == "42"


@respx.mock
async def test_create_comment_posts_canonical_payload_and_returns_comment(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.post(f"{jama_base_url}/rest/latest/comments").mock(
        return_value=httpx.Response(201, json=_fixture("comments_create.json")),
    )
    async with JamaClient(jama_credentials) as client:
        comment = await client.create_comment(
            item_id=42,
            project_id=1,
            body="Hello world",
        )
    # Comment is synthesised from the new ID plus inputs (Jama POST returns
    # meta-only envelope with no full comment body).
    assert isinstance(comment, Comment)
    assert comment.id == 5001
    assert comment.in_reply_to is None
    assert comment.body == {"text": "Hello world"}
    assert comment.comment_type == "GENERAL"
    assert comment.location == {"item": 42, "project": 1}
    # Top-level comments must omit inReplyTo entirely (sending 0 NPEs Jamacloud).
    sent = json.loads(route.calls.last.request.content)
    assert sent == {
        "body": {"text": "Hello world"},
        "commentType": "GENERAL",
        "location": {"item": 42, "project": 1},
    }
    assert "inReplyTo" not in sent


@respx.mock
async def test_create_comment_with_in_reply_to_includes_field(
    jama_credentials,
    jama_base_url,
    jama_token_url,
    jama_token_stub,
):
    respx.post(jama_token_url).mock(return_value=httpx.Response(200, json=jama_token_stub))
    route = respx.post(f"{jama_base_url}/rest/latest/comments").mock(
        return_value=httpx.Response(201, json=_fixture("comments_create.json")),
    )
    async with JamaClient(jama_credentials) as client:
        comment = await client.create_comment(
            item_id=42,
            project_id=1,
            body="Replying",
            in_reply_to=300,
        )
    assert comment.in_reply_to == 300
    sent = json.loads(route.calls.last.request.content)
    assert sent["inReplyTo"] == 300
