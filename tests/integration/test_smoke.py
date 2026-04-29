"""Integration smoke tests against the live Jamacloud sandbox.

These run only when the JAMA_* environment variables are configured. The
suite is skipped at collection time otherwise — see ``conftest.py``.
"""

from __future__ import annotations

import os

import pytest

from jama_client import JamaClient, OAuthCredentials

pytestmark = pytest.mark.integration


def _creds() -> OAuthCredentials:
    return OAuthCredentials(
        client_id=os.environ["JAMA_OAUTH_CLIENT_ID"],
        client_secret=os.environ["JAMA_OAUTH_CLIENT_SECRET"],
        base_url=os.environ["JAMA_BASE_URL"],
    )


async def test_whoami_against_live_sandbox():
    async with JamaClient(_creds()) as client:
        user = await client.get_current_user()
    assert user.id > 0


async def test_list_projects_returns_at_least_one_project():
    async with JamaClient(_creds()) as client:
        projects = await client.list_projects()
    assert len(projects) >= 1


async def test_get_item_returns_valid_item_for_known_id():
    known_item_id = int(os.environ.get("JAMA_KNOWN_ITEM_ID", "0"))
    if known_item_id <= 0:
        pytest.skip("Set JAMA_KNOWN_ITEM_ID to a real item ID to enable this test.")
    async with JamaClient(_creds()) as client:
        item = await client.get_item(known_item_id)
    assert item.id == known_item_id
