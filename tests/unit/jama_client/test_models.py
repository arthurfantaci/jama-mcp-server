"""Tests for jama_client Pydantic entity models."""

from __future__ import annotations

import json
from pathlib import Path

from jama_client.models import (
    Item,
    Project,
    Relationship,
    TestRun,
    User,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "jama_responses"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_user_parses_camelcase_payload():
    payload = _load("users_current.json")["data"]
    user = User.model_validate(payload)
    assert user.id == 100
    assert user.first_name == "Arthur"
    assert user.last_name == "Fantaci"
    assert user.email == "arthur@example.invalid"
    assert user.username == "afantaci"


def test_user_accepts_unknown_fields():
    payload = {"id": 1, "firstName": "A", "unexpectedNewField": "future"}
    user = User.model_validate(payload)
    assert user.id == 1
    assert user.model_dump(by_alias=True)["unexpectedNewField"] == "future"


def test_user_dumps_snake_case_by_default():
    user = User(id=1, first_name="A")
    dumped = user.model_dump()
    assert "first_name" in dumped
    assert "firstName" not in dumped


def test_project_parses_payload():
    payload = _load("projects_list.json")["data"][0]
    project = Project.model_validate(payload)
    assert project.id == 1
    assert project.project_key == "DEMO"
    assert project.fields["name"] == "Demo Project"


def test_item_parses_payload():
    payload = _load("items_get.json")["data"]
    item = Item.model_validate(payload)
    assert item.id == 42
    assert item.document_key == "DEMO-REQ-7"
    assert item.project == 1
    assert item.fields["name"] == "User can authenticate via OAuth"


def test_relationship_parses_payload():
    payload = _load("items_downstream_relationships.json")["data"][0]
    rel = Relationship.model_validate(payload)
    assert rel.id == 9001
    assert rel.from_item == 42
    assert rel.to_item == 84
    assert rel.relationship_type == 5


def test_test_run_parses_payload():
    payload = _load("items_test_runs.json")["data"][0]
    run = TestRun.model_validate(payload)
    assert run.id == 7001
    assert run.document_key == "DEMO-TR-1"
    assert run.fields["testRunStatus"] == "PASSED"


def test_models_round_trip_json():
    payload = _load("users_current.json")["data"]
    user = User.model_validate(payload)
    again = User.model_validate(json.loads(user.model_dump_json(by_alias=True)))
    assert again == user
