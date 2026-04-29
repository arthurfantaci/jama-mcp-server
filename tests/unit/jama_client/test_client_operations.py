"""Tests for JamaClient operations (get_current_user, list_projects, get_item, ...)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx

from jama_client.client import JamaClient
from jama_client.models import Project, User

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
