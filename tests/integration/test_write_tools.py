"""Integration tests for MVP write tools against the live Jamacloud sandbox.

These run only when the JAMA_* base credentials AND the MVP-specific
item/project env vars are set. All tests are skip-by-default; they leave
timestamped artifacts in the Sandbox (project 127 on pm2.jamacloud.com)
that must be cleaned via the Jama UI if desired.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest

from jama_client import JamaClient, OAuthCredentials

pytestmark = pytest.mark.integration


def _creds() -> OAuthCredentials:
    return OAuthCredentials(
        client_id=os.environ["JAMA_OAUTH_CLIENT_ID"],
        client_secret=os.environ["JAMA_OAUTH_CLIENT_SECRET"],
        base_url=os.environ["JAMA_BASE_URL"],
    )


async def test_create_item_against_live_sandbox():
    """Live smoke for create_item — gated on env vars; leaves an item behind.

    Creates a Code item inside the parent Set identified by
    ``JAMA_INTEGRATION_CREATE_ITEM_PARENT`` (project ID from
    ``JAMA_INTEGRATION_CREATE_ITEM_PROJECT``). The item name is
    timestamped for easy manual identification and cleanup.
    """
    project_id = int(os.environ.get("JAMA_INTEGRATION_CREATE_ITEM_PROJECT", "0"))
    parent_id = int(os.environ.get("JAMA_INTEGRATION_CREATE_ITEM_PARENT", "0"))
    item_type = int(os.environ.get("JAMA_INTEGRATION_CREATE_ITEM_TYPE", "0"))
    if project_id <= 0 or parent_id <= 0 or item_type <= 0:
        pytest.skip(
            "Set JAMA_INTEGRATION_CREATE_ITEM_PROJECT, "
            "JAMA_INTEGRATION_CREATE_ITEM_PARENT, and "
            "JAMA_INTEGRATION_CREATE_ITEM_TYPE to enable this test. "
            "Note: this test creates a real item in the configured Jama sandbox.",
        )

    ts = datetime.now(tz=UTC).isoformat()
    name = f"integration-smoke-create-item-{ts}"
    async with JamaClient(_creds()) as client:
        item = await client.create_item(
            project_id=project_id,
            item_type=item_type,
            parent=parent_id,
            name=name,
        )
    assert item.id > 0
    assert item.project == project_id
    assert item.item_type == item_type
    assert item.fields["name"] == name


async def test_create_relationship_against_live_sandbox():
    """Live smoke for create_relationship — gated on env vars; leaves a relationship behind.

    Creates a relationship from the item identified by
    ``JAMA_INTEGRATION_REL_FROM`` to ``JAMA_INTEGRATION_REL_TO`` using
    the relationship type ``JAMA_INTEGRATION_REL_TYPE``.
    """
    from_item = int(os.environ.get("JAMA_INTEGRATION_REL_FROM", "0"))
    to_item = int(os.environ.get("JAMA_INTEGRATION_REL_TO", "0"))
    rel_type = int(os.environ.get("JAMA_INTEGRATION_REL_TYPE", "0"))
    if from_item <= 0 or to_item <= 0 or rel_type <= 0:
        pytest.skip(
            "Set JAMA_INTEGRATION_REL_FROM, JAMA_INTEGRATION_REL_TO, and "
            "JAMA_INTEGRATION_REL_TYPE to enable this test. "
            "Note: this test creates a real relationship in the configured Jama sandbox.",
        )

    async with JamaClient(_creds()) as client:
        rel = await client.create_relationship(
            from_item=from_item,
            to_item=to_item,
            relationship_type=rel_type,
        )
    assert rel.id > 0
    assert rel.from_item == from_item
    assert rel.to_item == to_item
    assert rel.relationship_type == rel_type


async def test_create_path_a_trace_against_live_sandbox():
    """Live smoke for create_path_a_trace — composes primitives into a single trace creation.

    Gated on JAMA_INTEGRATION_PATH_A_TRACE_PROJECT (project ID),
    JAMA_INTEGRATION_PATH_A_TRACE_SOURCE (source requirement document key,
    e.g. 'AF-SUBSS-25'), JAMA_INTEGRATION_PATH_A_TRACE_CODE_PATH (code file
    path), JAMA_INTEGRATION_PATH_A_TRACE_CODE_VERSION (code version string).

    Leaves a new Code item AND a new relationship in the Sandbox; manual UI
    cleanup expected.
    """
    project_id = int(os.environ.get("JAMA_INTEGRATION_PATH_A_TRACE_PROJECT", "0"))
    source_key = os.environ.get("JAMA_INTEGRATION_PATH_A_TRACE_SOURCE", "")
    code_path = os.environ.get("JAMA_INTEGRATION_PATH_A_TRACE_CODE_PATH", "")
    code_version = os.environ.get("JAMA_INTEGRATION_PATH_A_TRACE_CODE_VERSION", "")
    if project_id <= 0 or not source_key or not code_path or not code_version:
        pytest.skip(
            "Set JAMA_INTEGRATION_PATH_A_TRACE_PROJECT, "
            "JAMA_INTEGRATION_PATH_A_TRACE_SOURCE, "
            "JAMA_INTEGRATION_PATH_A_TRACE_CODE_PATH, and "
            "JAMA_INTEGRATION_PATH_A_TRACE_CODE_VERSION to enable this test. "
            "Note: this test creates a real Code item AND a real relationship "
            "in the configured Jama sandbox.",
        )

    ts = datetime.now(tz=UTC).isoformat()
    timestamped_path = f"{code_path}:smoke-{ts}"
    async with JamaClient(_creds()) as client:
        result = await client.create_path_a_trace(
            project_id=project_id,
            source_requirement_key=source_key,
            code_path=timestamped_path,
            code_version=code_version,
        )
    assert isinstance(result, dict)
    assert result["source_item_id"] > 0
    assert result["code_item_id"] > 0
    assert result["relationship_id"] > 0
