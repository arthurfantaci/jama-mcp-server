"""Pydantic v2 entity models for Jamacloud API responses.

Models use ``alias_generator=to_camel`` plus ``populate_by_name=True`` so
Python-idiomatic snake_case attribute names accept Jamacloud's camelCase
JSON without per-field aliases. ``extra='allow'`` keeps the models
forward-compatible with future Jamacloud schema additions; the AI-shaped
tool responses dump snake_case by default.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _JamaModel(BaseModel):
    """Shared base for Jama entity models."""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=to_camel,
        serialize_by_alias=False,
    )


class User(_JamaModel):
    """A Jamacloud user."""

    id: int
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    username: str | None = None
    license_type: str | None = None
    active: bool | None = None


class Project(_JamaModel):
    """A Jamacloud project."""

    id: int
    project_key: str | None = None
    fields: dict[str, Any] = {}
    is_folder: bool | None = None
    created_date: str | None = None
    modified_date: str | None = None


class ItemFields(_JamaModel):
    """Convenience wrapper around an item's free-form ``fields`` dictionary.

    Phase 1 retains the dictionary verbatim under :attr:`Item.fields`; this
    type exists for downstream callers that want a typed accessor without
    losing forward compatibility.
    """

    name: str | None = None
    description: str | None = None
    status: int | None = None
    priority: int | None = None


class Item(_JamaModel):
    """A Jamacloud item (requirement, test case, defect, etc.)."""

    id: int
    document_key: str | None = None
    global_id: str | None = None
    item_type: int | None = None
    project: int | None = None
    fields: dict[str, Any] = {}
    created_date: str | None = None
    modified_date: str | None = None


class ItemType(_JamaModel):
    """A Jamacloud item type definition.

    Returned by ``GET /rest/latest/projects/{id}/itemtypes``. The ``type_key``
    field (e.g. ``"CODE"``, ``"SUBSR"``) is used by workflow tools to identify
    specific item types without hardcoding numeric IDs.
    """

    id: int
    type_key: str | None = None
    display: str | None = None
    display_plural: str | None = None
    description: str | None = None
    category: str | None = None


class RelationshipType(_JamaModel):
    """A Jamacloud relationship type definition."""

    id: int
    name: str | None = None


class Relationship(_JamaModel):
    """A relationship between two Jamacloud items."""

    id: int
    from_item: int
    to_item: int
    relationship_type: int | None = None
    suspect: bool | None = None


class TestRun(_JamaModel):
    """A Jamacloud test run."""

    __test__ = False  # not a pytest test class; suppresses PytestCollectionWarning

    id: int
    document_key: str | None = None
    fields: dict[str, Any] = {}
    created_date: str | None = None
    modified_date: str | None = None


class Comment(_JamaModel):
    """A comment on a Jamacloud item.

    Comments wrap their text in a nested ``body`` object (``{"text": "..."}``)
    and identify their target via a nested ``location`` object
    (``{"item": <id>, "project": <id>}``). The ``comment_type`` enumeration
    typically defaults to ``"GENERAL"``; ``in_reply_to`` is ``0`` for
    top-level comments.
    """

    id: int
    in_reply_to: int | None = None
    body: dict[str, Any] | None = None
    comment_type: str | None = None
    location: dict[str, Any] | None = None
    created_date: str | None = None
    modified_date: str | None = None
    last_activity_date: str | None = None
    created_by: int | None = None
    modified_by: int | None = None
