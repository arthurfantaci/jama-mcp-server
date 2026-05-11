"""Unit tests for DX-testing phase changes to JamaClient.create_path_a_trace.

Covers: name-derivation truncation regex correctness (baseline preservation on
non-line-range colons; regression on trailing ``:N-M``), description-text
format (with and without line range), and ``repo_origin`` propagation through
to the ``create_item`` request payload.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from jama_client.client import JamaClient
from jama_client.models import Item, Relationship

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client() -> AsyncMock:
    """Return an AsyncMock configured as a JamaClient with stubbed sub-methods."""
    client = AsyncMock(spec=JamaClient)
    client._type_cache = {}
    client._http = object()
    client._find_item_by_key = AsyncMock(
        return_value=Item(id=115100, item_type=87, project=127, document_key="AF-SUBSS-25")
    )
    client._resolve_code_item_type = AsyncMock(return_value=114)
    client._resolve_implemented_by_rel_type = AsyncMock(return_value=19)
    client._resolve_implementation_code_set = AsyncMock(return_value=212)
    client.create_item = AsyncMock(return_value=Item(id=115200, item_type=114, project=127))
    client.create_relationship = AsyncMock(
        return_value=Relationship(id=18600, from_item=115100, to_item=115200, relationship_type=19)
    )
    return client


# ---------------------------------------------------------------------------
# Truncation regex — Change A
# ---------------------------------------------------------------------------


async def test_name_derivation_preserves_basename_on_non_line_range_colon() -> None:
    """Basename is unchanged when code_path contains a colon that is not a trailing line range.

    The old first-colon truncation would have produced ``events`` from
    ``src/handlers/events:custom-handler.py``; the anchored ``:\\d+-\\d+$``
    regex must leave the basename ``events:custom-handler.py`` intact.
    """
    client = _make_client()
    await JamaClient.create_path_a_trace(
        client,
        project_id=127,
        source_requirement_key="AF-SUBSS-25",
        code_path="src/handlers/events:custom-handler.py",
        code_version="v1.0.0",
    )
    call_kwargs = client.create_item.call_args.kwargs
    assert call_kwargs["name"] == "events:custom-handler.py"


async def test_name_derivation_strips_trailing_line_range() -> None:
    """Trailing ``:N-M`` is stripped from the basename; the rest of the path is preserved."""
    client = _make_client()
    await JamaClient.create_path_a_trace(
        client,
        project_id=127,
        source_requirement_key="AF-SUBSS-25",
        code_path="src/detection/occlusion_detector.py:7-42",
        code_version="v1.0.0-rc1",
    )
    call_kwargs = client.create_item.call_args.kwargs
    assert call_kwargs["name"] == "occlusion_detector.py"


# ---------------------------------------------------------------------------
# Description population — Change B
# ---------------------------------------------------------------------------


async def test_description_populated_with_line_range_matches_html_format() -> None:
    """Description is HTML-formatted with explicit anchor tag when a line range is present.

    Jama's Type 114 ``description`` field is RICHTEXT-typed and silently drops
    plain-text content on POST ``/items`` (verified against pm2.jamacloud.com
    2026-05-11; tracked in issue #17). The HTML wrapping ensures the field
    persists; the explicit ``<a href>`` tag ensures the link is clickable in
    Jama's UI regardless of tenant link-detection settings.
    """
    client = _make_client()
    await JamaClient.create_path_a_trace(
        client,
        project_id=127,
        source_requirement_key="AF-SUBSS-26",
        code_path="src/jama_mcp_server/tools/workflow.py:78-130",
        code_version="v1.0.0",
        repo_origin="github.com/arthurfantaci/jama-mcp-server",
    )
    call_kwargs = client.create_item.call_args.kwargs
    description: str = call_kwargs["fields"]["description"]
    url = (
        "https://github.com/arthurfantaci/jama-mcp-server"
        "/blob/v1.0.0/src/jama_mcp_server/tools/workflow.py#L78-L130"
    )
    expected = (
        "<p>Repository: github.com/arthurfantaci/jama-mcp-server<br>"
        "Version: v1.0.0<br>"
        "Path: src/jama_mcp_server/tools/workflow.py (lines 78-130)<br>"
        f'Link: <a href="{url}">{url}</a></p>'
    )
    assert description == expected


async def test_description_populated_without_line_range_omits_annotation_and_fragment() -> None:
    """Description omits the ``(lines N-M)`` annotation and ``#LN-LM`` fragment when absent.

    HTML wrapping is unchanged; only the ``Path:`` line and the URL itself
    adapt to the missing line range.
    """
    client = _make_client()
    await JamaClient.create_path_a_trace(
        client,
        project_id=127,
        source_requirement_key="AF-SUBSS-27",
        code_path="src/jama_client/client.py",
        code_version="v1.0.0",
        repo_origin="github.com/arthurfantaci/jama-mcp-server",
    )
    call_kwargs = client.create_item.call_args.kwargs
    description: str = call_kwargs["fields"]["description"]
    url = "https://github.com/arthurfantaci/jama-mcp-server/blob/v1.0.0/src/jama_client/client.py"
    expected = (
        "<p>Repository: github.com/arthurfantaci/jama-mcp-server<br>"
        "Version: v1.0.0<br>"
        "Path: src/jama_client/client.py<br>"
        f'Link: <a href="{url}">{url}</a></p>'
    )
    assert description == expected


async def test_repo_origin_propagates_description_to_create_item_fields() -> None:
    """When repo_origin is supplied, description is present in the fields passed to create_item."""
    client = _make_client()
    await JamaClient.create_path_a_trace(
        client,
        project_id=127,
        source_requirement_key="AF-SUBSS-25",
        code_path="src/jama_client/client.py:523-628",
        code_version="abc1234",
        repo_origin="github.com/arthurfantaci/jama-mcp-server",
    )
    call_kwargs = client.create_item.call_args.kwargs
    assert "description" in call_kwargs["fields"]
    assert "github.com/arthurfantaci/jama-mcp-server" in call_kwargs["fields"]["description"]
    assert "abc1234" in call_kwargs["fields"]["description"]
    assert "#L523-L628" in call_kwargs["fields"]["description"]


async def test_description_absent_when_repo_origin_is_none() -> None:
    """No description field is added to create_item when repo_origin is omitted."""
    client = _make_client()
    await JamaClient.create_path_a_trace(
        client,
        project_id=127,
        source_requirement_key="AF-SUBSS-25",
        code_path="src/jama_client/client.py:7-42",
        code_version="v1.0.0",
    )
    call_kwargs = client.create_item.call_args.kwargs
    assert "description" not in call_kwargs["fields"]
