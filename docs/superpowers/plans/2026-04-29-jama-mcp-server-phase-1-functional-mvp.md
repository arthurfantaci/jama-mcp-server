# Phase 1 — Functional MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the six client operations and six MCP tools that demonstrate Jama Connect requirements-to-test-runs traceability, with both `stdio` and `streamable-http` transports working end-to-end against the Jamacloud sandbox.

**Architecture:** Bottom-up build of the two-layer architecture defined in the design spec. `jama_client` lands first in dependency order (exceptions → entity models → OAuth + token cache → core async transport with retry policy → six client operations → public surface re-exports), each layer fully covered by `respx`-mocked unit tests. `jama_mcp_server` then wires the client into FastMCP (settings → transport-aware logging → server + lifespan + entry points → six `@mcp.tool()` functions), covered by FastMCP in-process protocol tests with a mock `JamaClient` injected through the lifespan context — the same wiring the production server uses. An opt-in integration suite exercises the live Jama sandbox manually.

**Tech Stack:** Python 3.12, `uv`, FastMCP (from `mcp` SDK ≥1.0), `httpx` async, Pydantic v2 + `pydantic-settings`, `structlog`, `respx` for HTTP mocking, `pytest` + `pytest-asyncio` (`asyncio_mode = "auto"`).

**Reference spec:** [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](../specs/2026-04-28-jama-mcp-server-design.md) — Sections 4 (Component Breakdown), 5 (Data Flow), 6 (Error Handling Policy), 7 (Testing Strategy), and 10 (Phase Roadmap → Phase 1).

---

## Branch and PR workflow

Per [`CONTRIBUTING.md`](../../../CONTRIBUTING.md), Phase 1 is the first phase to use the Issue → Branch → PR workflow.

1. Open a GitHub issue titled **"Phase 1: Functional MVP — six MCP tools across both transports"** linking this plan and the design spec's Section 10 Phase 1 entry.
2. Create branch `feat/phase-1-functional-mvp` off `main`.
3. Land each task as its own conventional commit on the branch (frequent commits keep blame and review surface clean).
4. Open one PR `feat/phase-1-functional-mvp → main` after Task 22 verification passes.
5. PR description summarizes the six tools delivered, links the issue, and confirms the Phase 1 verifiable end state from the design spec.
6. Squash-merge is acceptable but not required; preserving the conventional-commit history is preferred.

---

## File structure

Files created or modified during Phase 1. Paths are relative to the repository root.

### `jama_client` package — fully implemented in this phase

- **Modify:** `src/jama_client/__init__.py` — export the public surface.
- **Modify:** `src/jama_client/exceptions.py` — implement the seven-class exception hierarchy.
- **Modify:** `src/jama_client/models.py` — implement seven Pydantic v2 entity models.
- **Modify:** `src/jama_client/auth.py` — implement `OAuthCredentials`, `Token`, `TokenCache`, and `fetch_token`.
- **Modify:** `src/jama_client/client.py` — implement the `JamaClient` async context manager and the six client methods.

### `jama_mcp_server` package — fully implemented in this phase

- **Modify:** `src/jama_mcp_server/__init__.py` — re-export the `mcp` instance.
- **Modify:** `src/jama_mcp_server/config.py` — implement the `Settings` `BaseSettings` class.
- **Modify:** `src/jama_mcp_server/logging_config.py` — implement transport-aware `configure_logging`.
- **Modify:** `src/jama_mcp_server/server.py` — implement the FastMCP instance, lifespan, and `main_stdio` / `main_http`.
- **Modify:** `src/jama_mcp_server/tools.py` — implement the six `@mcp.tool()` functions.
- **Unchanged:** `src/jama_mcp_server/__main__.py` (the existing dispatcher already routes to `main_stdio` / `main_http`).

### Test suite — Phase 1 fills in the unit and protocol tiers

- **Modify:** `tests/conftest.py` — shared fixtures (sample tokens, envelope responses, mock-client factory).
- **Replace:** `tests/unit/test_smoke.py` — replace the placeholder with a real importability sanity check (or delete; superseded by per-module tests).
- **Create:** `tests/unit/jama_client/test_exceptions.py`
- **Create:** `tests/unit/jama_client/test_models.py`
- **Create:** `tests/unit/jama_client/test_auth.py`
- **Create:** `tests/unit/jama_client/test_client_transport.py`
- **Create:** `tests/unit/jama_client/test_client_operations.py`
- **Create:** `tests/unit/jama_mcp_server/test_config.py`
- **Create:** `tests/unit/jama_mcp_server/test_logging_config.py`
- **Create:** `tests/unit/jama_mcp_server/test_server_lifespan.py`
- **Create:** `tests/unit/jama_mcp_server/test_tools.py`
- **Create:** `tests/unit/jama_mcp_server/test_protocol.py`
- **Create:** `tests/integration/test_smoke.py`

### Test fixtures — hand-crafted JSON sanitized samples

- **Create:** `tests/fixtures/jama_responses/oauth_token.json`
- **Create:** `tests/fixtures/jama_responses/users_current.json`
- **Create:** `tests/fixtures/jama_responses/projects_list.json`
- **Create:** `tests/fixtures/jama_responses/items_get.json`
- **Create:** `tests/fixtures/jama_responses/abstractitems_search.json`
- **Create:** `tests/fixtures/jama_responses/items_downstream_relationships.json`
- **Create:** `tests/fixtures/jama_responses/items_test_runs.json`
- **Create:** `tests/fixtures/jama_responses/error_404.json`
- **Create:** `tests/fixtures/jama_responses/error_429.json`
- **Delete:** `tests/fixtures/jama_responses/.gitkeep` (no longer needed once real fixtures land).

### Documentation

- **Modify:** `README.md` — flip Phase 1 status to "Complete", expand Quick Start with OAuth provisioning + smoke instructions.
- **Modify:** `docs/setup.md` — extend with the credential provisioning walkthrough and MCP Inspector smoke procedure.
- **Modify:** `MEMORY.md` — flip phase pointer, log Phase 1 decisions.
- **Modify:** `CLAUDE.md` — add any conventions codified during Phase 1 (e.g., model alias generator usage).

### Endpoint assumptions documented in this plan

The following Jamacloud REST URLs are used in the plan's `respx` mocks and client implementation:

| Operation | Method | URL template |
|-----------|--------|--------------|
| `fetch_token` | `POST` | `/rest/oauth/token` |
| `get_current_user` | `GET` | `/rest/latest/users/current` |
| `list_projects` | `GET` | `/rest/latest/projects` |
| `get_item` | `GET` | `/rest/latest/items/{item_id}` |
| `search_items` | `GET` | `/rest/latest/abstractitems?project={project_id}&contains={query}` |
| `get_downstream_relationships` | `GET` | `/rest/latest/items/{item_id}/downstreamrelationships` |
| `get_test_runs_for_item` | `GET` | `/rest/latest/items/{item_id}/testruns` |

These are the canonical Jama REST endpoints. **Verify against the live sandbox during Task 21 (integration smoke).** If any URL or response shape differs, adjust the implementation and the affected fixtures, and update this table in a follow-on commit on the same branch.

### Out-of-scope for Phase 1 (deferred to later phases)

- Full pagination handling. Phase 1 returns the first page only and includes the raw `pageInfo` in the AI-shaped response so the AI can reason about totals. Pagination iteration is a deliberate Phase 2+ enhancement.
- Write operations (per design spec Section 1 non-goals).
- Comprehensive endpoint coverage beyond the six operations.
- Persistent token storage (token cache is in-memory per-process).

---

## Pre-flight setup steps (one-time, before Task 1)

- [ ] **Provision the OAuth credential.** In Jama Connect (`https://pm2.jamacloud.com`), create a dedicated API credential named `jama-mcp-server-dev` via the OAuth 2.0 panel. This must be a new credential, not a reuse of an existing one — see `MEMORY.md` "Known constraints".

- [ ] **Populate `.env` locally.**

```bash
cp .env.example .env
# Edit .env and fill in JAMA_OAUTH_CLIENT_ID and JAMA_OAUTH_CLIENT_SECRET.
```

Verify `.env` is gitignored:

```bash
git check-ignore -v .env
```

Expected: `.gitignore:<lineno>:.env	.env` (the file is ignored).

- [ ] **Open the Phase 1 GitHub issue.**

```bash
gh issue create \
  --title "Phase 1: Functional MVP — six MCP tools across both transports" \
  --body "Implement the six client operations and six MCP tools defined in docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md Section 10 (Phase 1). Plan: docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md."
```

Note the issue number; reference it in the PR description at the end.

- [ ] **Create the working branch.**

```bash
git checkout main
git pull --ff-only
git checkout -b feat/phase-1-functional-mvp
```

- [ ] **Confirm baseline is green before adding code.**

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -m "not integration"
```

Expected: all four commands succeed against the Phase 0 skeleton. If any fail, stop and resolve before starting Task 1.

---

## Task 1: Exception hierarchy

**Files:**
- Modify: `src/jama_client/exceptions.py`
- Create: `tests/unit/jama_client/test_exceptions.py`

The exception hierarchy is the foundation every later layer imports — client transport raises these, retry logic dispatches on them, server-layer translation catches them. Implement seven classes per design spec Section 6 (the `jama_client` layer subsection).

- [ ] **Step 1: Write the failing test.**

Create `tests/unit/jama_client/test_exceptions.py`:

```python
"""Tests for the jama_client exception hierarchy."""

from __future__ import annotations

import pytest

from jama_client.exceptions import (
    JamaAuthError,
    JamaError,
    JamaForbiddenError,
    JamaNetworkError,
    JamaNotFoundError,
    JamaRateLimitError,
    JamaServerError,
    JamaValidationError,
)


def test_jama_error_is_base_exception():
    assert issubclass(JamaError, Exception)


@pytest.mark.parametrize(
    "subclass",
    [
        JamaAuthError,
        JamaForbiddenError,
        JamaNotFoundError,
        JamaRateLimitError,
        JamaServerError,
        JamaNetworkError,
        JamaValidationError,
    ],
)
def test_subclasses_inherit_from_jama_error(subclass):
    assert issubclass(subclass, JamaError)


def test_rate_limit_error_exposes_retry_after():
    err = JamaRateLimitError("rate limited", retry_after=42)
    assert err.retry_after == 42
    assert "rate limited" in str(err)


def test_rate_limit_error_default_retry_after_is_none():
    err = JamaRateLimitError("rate limited")
    assert err.retry_after is None


def test_validation_error_exposes_payload():
    payload = {"unexpected": "shape"}
    err = JamaValidationError("bad shape", payload=payload)
    assert err.payload is payload


def test_validation_error_default_payload_is_none():
    err = JamaValidationError("bad shape")
    assert err.payload is None
```

- [ ] **Step 2: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/jama_client/test_exceptions.py -v
```

Expected: import errors / `AttributeError` because the classes are not yet defined.

- [ ] **Step 3: Implement `src/jama_client/exceptions.py`.**

Replace the placeholder with:

```python
"""Exception hierarchy for the Jamacloud REST API client.

The :class:`JamaError` base class roots a typed hierarchy mapping Jamacloud
HTTP error semantics onto Python exceptions. The :mod:`jama_client.client`
transport layer raises these directly; the :mod:`jama_mcp_server` layer
catches expected absences (404) and re-raises everything else. See
``docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`` Section 6.
"""

from __future__ import annotations

from typing import Any


class JamaError(Exception):
    """Base class for every error raised by the Jama client."""


class JamaAuthError(JamaError):
    """The Jamacloud API rejected the request with HTTP 401."""


class JamaForbiddenError(JamaError):
    """The Jamacloud API rejected the request with HTTP 403."""


class JamaNotFoundError(JamaError):
    """The Jamacloud API responded with HTTP 404 for a resource lookup."""


class JamaRateLimitError(JamaError):
    """The Jamacloud API rate-limited the request with HTTP 429.

    Args:
        message: Human-readable description of the rate-limit response.
        retry_after: ``Retry-After`` header value in seconds, if provided.
    """

    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class JamaServerError(JamaError):
    """The Jamacloud API responded with an HTTP 5xx status."""


class JamaNetworkError(JamaError):
    """A transport-level failure occurred (connection, timeout, DNS, TLS)."""


class JamaValidationError(JamaError):
    """A Jamacloud response failed Pydantic validation.

    Args:
        message: Description of the validation mismatch.
        payload: The raw response payload that failed to validate, if available.
    """

    def __init__(self, message: str, *, payload: Any | None = None) -> None:
        super().__init__(message)
        self.payload = payload
```

- [ ] **Step 4: Run the test to verify it passes.**

```bash
uv run pytest tests/unit/jama_client/test_exceptions.py -v
```

Expected: all six tests pass.

- [ ] **Step 5: Lint and type-check the new file.**

```bash
uv run ruff check src/jama_client/exceptions.py tests/unit/jama_client/test_exceptions.py
uv run ruff format --check src/jama_client/exceptions.py tests/unit/jama_client/test_exceptions.py
uv run mypy src/jama_client/exceptions.py
```

Expected: clean.

- [ ] **Step 6: Commit.**

```bash
git add src/jama_client/exceptions.py tests/unit/jama_client/test_exceptions.py
git commit -m "feat(jama_client): implement typed exception hierarchy"
```

---

## Task 2: Pydantic entity models and JSON fixtures

**Files:**
- Modify: `src/jama_client/models.py`
- Create: `tests/unit/jama_client/test_models.py`
- Create: `tests/fixtures/jama_responses/users_current.json`
- Create: `tests/fixtures/jama_responses/projects_list.json`
- Create: `tests/fixtures/jama_responses/items_get.json`
- Create: `tests/fixtures/jama_responses/abstractitems_search.json`
- Create: `tests/fixtures/jama_responses/items_downstream_relationships.json`
- Create: `tests/fixtures/jama_responses/items_test_runs.json`
- Delete: `tests/fixtures/jama_responses/.gitkeep`

Pydantic v2 with `extra="allow"` for forward compatibility, and an `alias_generator=to_camel` so Python-idiomatic snake_case fields accept Jama's camelCase JSON without per-field `Field(alias=...)` boilerplate. `populate_by_name=True` lets tests construct models from either casing.

- [ ] **Step 1: Author the JSON fixtures (sanitized samples).**

Create `tests/fixtures/jama_responses/users_current.json`:

```json
{
  "meta": {
    "status": "OK",
    "timestamp": "2026-04-29T12:00:00.000+0000"
  },
  "links": {},
  "data": {
    "id": 100,
    "firstName": "Arthur",
    "lastName": "Fantaci",
    "email": "arthur@example.invalid",
    "username": "afantaci",
    "licenseType": "NAMED",
    "active": true
  }
}
```

Create `tests/fixtures/jama_responses/projects_list.json`:

```json
{
  "meta": {
    "status": "OK",
    "timestamp": "2026-04-29T12:00:00.000+0000",
    "pageInfo": {
      "startIndex": 0,
      "resultCount": 2,
      "totalResults": 2
    }
  },
  "links": {},
  "data": [
    {
      "id": 1,
      "projectKey": "DEMO",
      "fields": {
        "name": "Demo Project",
        "description": "Sample project for traceability demo."
      },
      "isFolder": false,
      "createdDate": "2026-01-01T00:00:00.000+0000",
      "modifiedDate": "2026-04-01T00:00:00.000+0000"
    },
    {
      "id": 2,
      "projectKey": "PILOT",
      "fields": {
        "name": "Pilot",
        "description": null
      },
      "isFolder": false,
      "createdDate": "2026-01-15T00:00:00.000+0000",
      "modifiedDate": "2026-03-15T00:00:00.000+0000"
    }
  ]
}
```

Create `tests/fixtures/jama_responses/items_get.json`:

```json
{
  "meta": {
    "status": "OK",
    "timestamp": "2026-04-29T12:00:00.000+0000"
  },
  "links": {},
  "data": {
    "id": 42,
    "documentKey": "DEMO-REQ-7",
    "globalId": "GID-42",
    "itemType": 22,
    "project": 1,
    "fields": {
      "name": "User can authenticate via OAuth",
      "description": "<p>The system shall accept OAuth 2.0 client credentials.</p>",
      "status": 100,
      "priority": 200
    },
    "createdDate": "2026-02-01T00:00:00.000+0000",
    "modifiedDate": "2026-04-15T00:00:00.000+0000"
  }
}
```

Create `tests/fixtures/jama_responses/abstractitems_search.json`:

```json
{
  "meta": {
    "status": "OK",
    "timestamp": "2026-04-29T12:00:00.000+0000",
    "pageInfo": {
      "startIndex": 0,
      "resultCount": 1,
      "totalResults": 1
    }
  },
  "links": {},
  "data": [
    {
      "id": 42,
      "documentKey": "DEMO-REQ-7",
      "globalId": "GID-42",
      "itemType": 22,
      "project": 1,
      "fields": {
        "name": "User can authenticate via OAuth",
        "description": "<p>The system shall accept OAuth 2.0 client credentials.</p>"
      },
      "createdDate": "2026-02-01T00:00:00.000+0000",
      "modifiedDate": "2026-04-15T00:00:00.000+0000"
    }
  ]
}
```

Create `tests/fixtures/jama_responses/items_downstream_relationships.json`:

```json
{
  "meta": {
    "status": "OK",
    "timestamp": "2026-04-29T12:00:00.000+0000",
    "pageInfo": {
      "startIndex": 0,
      "resultCount": 1,
      "totalResults": 1
    }
  },
  "links": {},
  "data": [
    {
      "id": 9001,
      "fromItem": 42,
      "toItem": 84,
      "relationshipType": 5,
      "suspect": false
    }
  ]
}
```

Create `tests/fixtures/jama_responses/items_test_runs.json`:

```json
{
  "meta": {
    "status": "OK",
    "timestamp": "2026-04-29T12:00:00.000+0000",
    "pageInfo": {
      "startIndex": 0,
      "resultCount": 1,
      "totalResults": 1
    }
  },
  "links": {},
  "data": [
    {
      "id": 7001,
      "documentKey": "DEMO-TR-1",
      "fields": {
        "name": "OAuth login happy path",
        "executionDate": "2026-04-20T10:30:00.000+0000",
        "testRunStatus": "PASSED",
        "assignedTo": 100
      },
      "createdDate": "2026-04-20T10:00:00.000+0000",
      "modifiedDate": "2026-04-20T10:35:00.000+0000"
    }
  ]
}
```

Remove the placeholder marker:

```bash
git rm tests/fixtures/jama_responses/.gitkeep
```

- [ ] **Step 2: Write the failing test.**

Create `tests/unit/jama_client/test_models.py`:

```python
"""Tests for jama_client Pydantic entity models."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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
```

- [ ] **Step 3: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/jama_client/test_models.py -v
```

Expected: import errors — `User`, `Project`, `Item`, `Relationship`, `TestRun` are not defined.

- [ ] **Step 4: Implement `src/jama_client/models.py`.**

Replace the placeholder with:

```python
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

    id: int
    document_key: str | None = None
    fields: dict[str, Any] = {}
    created_date: str | None = None
    modified_date: str | None = None
```

- [ ] **Step 5: Run the test to verify it passes.**

```bash
uv run pytest tests/unit/jama_client/test_models.py -v
```

Expected: all eight tests pass.

- [ ] **Step 6: Lint and type-check.**

```bash
uv run ruff check src/jama_client/models.py tests/unit/jama_client/test_models.py
uv run ruff format --check src/jama_client/models.py tests/unit/jama_client/test_models.py
uv run mypy src/jama_client/models.py
```

Expected: clean.

- [ ] **Step 7: Commit.**

```bash
git add src/jama_client/models.py tests/unit/jama_client/test_models.py tests/fixtures/jama_responses/
git rm tests/fixtures/jama_responses/.gitkeep 2>/dev/null || true
git commit -m "feat(jama_client): add Pydantic v2 entity models with hand-crafted fixtures"
```

---

## Task 3: OAuth credentials, Token, and TokenCache

**Files:**
- Modify: `src/jama_client/auth.py`
- Create: `tests/unit/jama_client/test_auth.py` (initial portion — `fetch_token` lands in Task 4)
- Create: `tests/fixtures/jama_responses/oauth_token.json`

The token cache refreshes proactively at ≥90% of TTL per design spec Section 6. A 401 from the API after a fresh token is **not** retried — that signals a real authorization problem.

- [ ] **Step 1: Author the OAuth token fixture.**

Create `tests/fixtures/jama_responses/oauth_token.json`:

```json
{
  "access_token": "test-access-token-abcdef",
  "token_type": "bearer",
  "expires_in": 3600
}
```

- [ ] **Step 2: Write the failing test.**

Create `tests/unit/jama_client/test_auth.py`:

```python
"""Tests for jama_client OAuth helpers (credentials, token, cache)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from jama_client.auth import OAuthCredentials, Token, TokenCache


def _now() -> datetime:
    return datetime(2026, 4, 29, 12, 0, 0, tzinfo=timezone.utc)


def test_oauth_credentials_immutable():
    creds = OAuthCredentials(client_id="cid", client_secret="cs", base_url="https://j.example")
    with pytest.raises(Exception):  # pydantic ValidationError or FrozenInstanceError
        creds.client_id = "other"  # type: ignore[misc]


def test_token_expiry_calculation():
    issued = _now()
    token = Token(access_token="t", expires_in=3600, issued_at=issued)
    assert token.expires_at == issued + timedelta(seconds=3600)


def test_token_cache_returns_none_when_empty():
    cache = TokenCache()
    assert cache.get(now=_now()) is None


def test_token_cache_returns_token_when_fresh():
    cache = TokenCache()
    token = Token(access_token="fresh", expires_in=3600, issued_at=_now())
    cache.set(token)
    assert cache.get(now=_now() + timedelta(seconds=60)) is token


def test_token_cache_returns_none_at_or_above_ninety_percent_ttl():
    cache = TokenCache()
    issued = _now()
    cache.set(Token(access_token="aging", expires_in=3600, issued_at=issued))
    # 90% of 3600 = 3240 seconds.
    assert cache.get(now=issued + timedelta(seconds=3239)) is not None
    assert cache.get(now=issued + timedelta(seconds=3240)) is None
    assert cache.get(now=issued + timedelta(seconds=3241)) is None


def test_token_cache_clear_evicts_token():
    cache = TokenCache()
    cache.set(Token(access_token="t", expires_in=3600, issued_at=_now()))
    cache.clear()
    assert cache.get(now=_now()) is None
```

- [ ] **Step 3: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/jama_client/test_auth.py -v
```

Expected: import errors — `OAuthCredentials`, `Token`, `TokenCache` are undefined.

- [ ] **Step 4: Implement the three classes in `src/jama_client/auth.py`.**

Replace the placeholder with:

```python
"""OAuth 2.0 client_credentials authentication for Jamacloud.

Exposes :class:`OAuthCredentials` (immutable configuration), :class:`Token`
(access token plus issuance metadata), :class:`TokenCache` (in-memory cache
with proactive refresh at or above 90 percent of TTL), and the
:func:`fetch_token` wire call against ``/rest/oauth/token``. See
``docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`` Section 6.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from pydantic import BaseModel, ConfigDict, Field

from jama_client.exceptions import (
    JamaAuthError,
    JamaForbiddenError,
    JamaNetworkError,
    JamaServerError,
    JamaValidationError,
)

_REFRESH_FRACTION = 0.9


class OAuthCredentials(BaseModel):
    """Immutable OAuth 2.0 client_credentials configuration."""

    model_config = ConfigDict(frozen=True)

    client_id: str
    client_secret: str
    base_url: str


class Token(BaseModel):
    """An OAuth access token with issuance metadata."""

    model_config = ConfigDict(frozen=True)

    access_token: str
    expires_in: int
    issued_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @property
    def expires_at(self) -> datetime:
        """Return the absolute expiry instant."""
        return self.issued_at + timedelta(seconds=self.expires_in)

    def is_stale(self, *, now: datetime) -> bool:
        """Return ``True`` once at or beyond 90 percent of the token's TTL."""
        elapsed = (now - self.issued_at).total_seconds()
        return elapsed >= _REFRESH_FRACTION * self.expires_in


class TokenCache:
    """Single-token in-memory cache with proactive refresh."""

    def __init__(self) -> None:
        self._token: Token | None = None

    def get(self, *, now: datetime) -> Token | None:
        """Return the cached token if present and not stale, else ``None``."""
        token = self._token
        if token is None or token.is_stale(now=now):
            return None
        return token

    def set(self, token: Token) -> None:
        """Replace the cached token."""
        self._token = token

    def clear(self) -> None:
        """Evict the cached token."""
        self._token = None


async def fetch_token(creds: OAuthCredentials, http: httpx.AsyncClient) -> Token:
    """Exchange OAuth client credentials for an access token.

    Args:
        creds: Immutable OAuth credentials including ``base_url``.
        http: Pre-constructed ``httpx.AsyncClient`` used to issue the request.

    Returns:
        A :class:`Token` representing the access token.

    Raises:
        JamaAuthError: The token endpoint returned 401.
        JamaForbiddenError: The token endpoint returned 403.
        JamaServerError: The token endpoint returned a 5xx status.
        JamaNetworkError: A transport-level error occurred.
        JamaValidationError: The response body did not include the expected fields.
    """
    url = f"{creds.base_url.rstrip('/')}/rest/oauth/token"
    try:
        response = await http.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(creds.client_id, creds.client_secret),
        )
    except httpx.HTTPError as exc:
        msg = f"OAuth token request failed at the transport layer: {exc!r}"
        raise JamaNetworkError(msg) from exc

    if response.status_code == 401:
        msg = "OAuth token endpoint rejected client credentials (HTTP 401)."
        raise JamaAuthError(msg)
    if response.status_code == 403:
        msg = "OAuth token endpoint forbade the request (HTTP 403)."
        raise JamaForbiddenError(msg)
    if 500 <= response.status_code < 600:
        msg = f"OAuth token endpoint returned HTTP {response.status_code}."
        raise JamaServerError(msg)
    if response.status_code != 200:
        msg = f"Unexpected status {response.status_code} from OAuth token endpoint."
        raise JamaAuthError(msg)

    try:
        payload = response.json()
        access_token = payload["access_token"]
        expires_in = int(payload["expires_in"])
    except (KeyError, ValueError, TypeError) as exc:
        msg = "OAuth token response missing required fields."
        raise JamaValidationError(msg, payload=response.text) from exc

    return Token(access_token=access_token, expires_in=expires_in)
```

- [ ] **Step 5: Run the test to verify the cache-related tests pass.**

```bash
uv run pytest tests/unit/jama_client/test_auth.py -v
```

Expected: the six cache/token tests pass. `fetch_token` is covered in Task 4.

- [ ] **Step 6: Lint and type-check.**

```bash
uv run ruff check src/jama_client/auth.py tests/unit/jama_client/test_auth.py
uv run ruff format --check src/jama_client/auth.py tests/unit/jama_client/test_auth.py
uv run mypy src/jama_client/auth.py
```

Expected: clean.

- [ ] **Step 7: Commit.**

```bash
git add src/jama_client/auth.py tests/unit/jama_client/test_auth.py tests/fixtures/jama_responses/oauth_token.json
git commit -m "feat(jama_client): add OAuth credentials, Token, and TokenCache"
```

---

## Task 4: `fetch_token` wire call (HTTP path)

**Files:**
- Modify: `tests/unit/jama_client/test_auth.py` (extend with HTTP tests)
- Modify: `docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md` (add the 403 test to the plan's Task 4 listing)

`fetch_token` was implemented in Task 3 alongside the data classes. This task adds `respx`-mocked tests covering the success path, 401, 403, 5xx, transport failure, malformed responses, and unexpected/redirect status codes.

- [ ] **Step 1: Append failing tests to `tests/unit/jama_client/test_auth.py`.**

Append after the existing tests:

```python
import json
from pathlib import Path

import httpx
import respx

from jama_client.auth import OAuthCredentials, fetch_token
from jama_client.exceptions import (
    JamaAuthError,
    JamaForbiddenError,
    JamaNetworkError,
    JamaServerError,
    JamaValidationError,
)

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "jama_responses"
_BASE_URL = "https://jama.example"


def _creds() -> OAuthCredentials:
    return OAuthCredentials(client_id="cid", client_secret="cs", base_url=_BASE_URL)


@respx.mock
async def test_fetch_token_success_returns_token():
    payload = json.loads((_FIXTURES / "oauth_token.json").read_text())
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(return_value=httpx.Response(200, json=payload))
    async with httpx.AsyncClient() as client:
        token = await fetch_token(_creds(), client)
    assert token.access_token == payload["access_token"]
    assert token.expires_in == payload["expires_in"]


@respx.mock
async def test_fetch_token_uses_basic_auth_and_form_body():
    route = respx.post(f"{_BASE_URL}/rest/oauth/token").mock(
        return_value=httpx.Response(200, json={"access_token": "x", "expires_in": 60}),
    )
    async with httpx.AsyncClient() as client:
        await fetch_token(_creds(), client)
    request = route.calls.last.request
    assert request.headers["authorization"].startswith("Basic ")
    assert request.headers["content-type"].startswith("application/x-www-form-urlencoded")
    assert b"grant_type=client_credentials" in request.content


@respx.mock
async def test_fetch_token_raises_auth_error_on_401():
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(return_value=httpx.Response(401))
    async with httpx.AsyncClient() as client:
        with pytest.raises(JamaAuthError):
            await fetch_token(_creds(), client)


@respx.mock
async def test_fetch_token_raises_forbidden_error_on_403():
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(return_value=httpx.Response(403))
    async with httpx.AsyncClient() as client:
        with pytest.raises(JamaForbiddenError):
            await fetch_token(_creds(), client)


@respx.mock
async def test_fetch_token_raises_server_error_on_503():
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(return_value=httpx.Response(503))
    async with httpx.AsyncClient() as client:
        with pytest.raises(JamaServerError):
            await fetch_token(_creds(), client)


@respx.mock
async def test_fetch_token_raises_network_error_on_transport_failure():
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(side_effect=httpx.ConnectError("boom"))
    async with httpx.AsyncClient() as client:
        with pytest.raises(JamaNetworkError):
            await fetch_token(_creds(), client)


@respx.mock
async def test_fetch_token_raises_validation_error_on_missing_fields():
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(
        return_value=httpx.Response(200, json={"unexpected": "shape"}),
    )
    async with httpx.AsyncClient() as client:
        with pytest.raises(JamaValidationError):
            await fetch_token(_creds(), client)


@respx.mock
async def test_fetch_token_raises_auth_error_on_unexpected_status():
    respx.post(f"{_BASE_URL}/rest/oauth/token").mock(return_value=httpx.Response(302))
    async with httpx.AsyncClient() as client:
        with pytest.raises(JamaAuthError):
            await fetch_token(_creds(), client)
```

- [ ] **Step 2: Run the test to verify all paths pass.**

```bash
uv run pytest tests/unit/jama_client/test_auth.py -v
```

Expected: the eight new HTTP tests pass alongside the cache tests from Task 3 (fourteen total).

- [ ] **Step 3: Lint and type-check.**

```bash
uv run ruff check tests/unit/jama_client/test_auth.py
uv run ruff format --check tests/unit/jama_client/test_auth.py
uv run mypy src/jama_client/auth.py
```

Expected: clean.

- [ ] **Step 4: Commit.**

```bash
git add tests/unit/jama_client/test_auth.py
git commit -m "test(jama_client): cover fetch_token HTTP success and error paths"
```

---

## Task 5: `JamaClient` async context manager and `_request` core

**Files:**
- Modify: `src/jama_client/client.py`
- Create: `tests/unit/jama_client/test_client_transport.py`

Implements the async context manager, the `_request` helper (auth header injection, envelope unwrapping, status-to-exception mapping), and the narrow retry policy from design spec Section 6. Operations land in Tasks 6–9.

- [ ] **Step 1: Write the failing test.**

Create `tests/unit/jama_client/test_client_transport.py`:

```python
"""Tests for JamaClient transport: lifecycle, _request envelope, retry policy."""

from __future__ import annotations

import httpx
import pytest
import respx

from jama_client.auth import OAuthCredentials
from jama_client.client import JamaClient
from jama_client.exceptions import (
    JamaAuthError,
    JamaForbiddenError,
    JamaNetworkError,
    JamaNotFoundError,
    JamaRateLimitError,
    JamaServerError,
    JamaValidationError,
)

_BASE_URL = "https://jama.example"
_TOKEN_URL = f"{_BASE_URL}/rest/oauth/token"


def _creds() -> OAuthCredentials:
    return OAuthCredentials(client_id="cid", client_secret="cs", base_url=_BASE_URL)


def _stub_token() -> dict:
    return {"access_token": "tok", "expires_in": 3600}


@respx.mock
async def test_client_is_async_context_manager_and_closes_http():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_stub_token()))
    async with JamaClient(_creds()) as client:
        assert client.is_open
    assert not client.is_open


@respx.mock
async def test_request_unwraps_envelope_and_returns_data():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_stub_token()))
    respx.get(f"{_BASE_URL}/rest/latest/ping").mock(
        return_value=httpx.Response(200, json={"meta": {}, "links": {}, "data": {"ok": True}}),
    )
    async with JamaClient(_creds()) as client:
        result = await client._request("GET", "/rest/latest/ping")
    assert result == {"ok": True}


@respx.mock
async def test_request_returns_envelope_when_caller_requests_it():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_stub_token()))
    payload = {"meta": {"pageInfo": {"totalResults": 1}}, "links": {}, "data": []}
    respx.get(f"{_BASE_URL}/rest/latest/ping").mock(return_value=httpx.Response(200, json=payload))
    async with JamaClient(_creds()) as client:
        envelope = await client._request("GET", "/rest/latest/ping", return_envelope=True)
    assert envelope == payload


@respx.mock
async def test_request_injects_bearer_token():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_stub_token()))
    route = respx.get(f"{_BASE_URL}/rest/latest/ping").mock(
        return_value=httpx.Response(200, json={"meta": {}, "links": {}, "data": {}}),
    )
    async with JamaClient(_creds()) as client:
        await client._request("GET", "/rest/latest/ping")
    assert route.calls.last.request.headers["authorization"] == "Bearer tok"


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, JamaAuthError),
        (403, JamaForbiddenError),
        (404, JamaNotFoundError),
        (500, JamaServerError),
    ],
)
@respx.mock
async def test_request_maps_status_codes_to_typed_exceptions(status, expected):
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_stub_token()))
    respx.get(f"{_BASE_URL}/rest/latest/ping").mock(return_value=httpx.Response(status))
    async with JamaClient(_creds()) as client:
        with pytest.raises(expected):
            await client._request("GET", "/rest/latest/ping")


@respx.mock
async def test_request_rate_limit_retries_once_with_retry_after():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_stub_token()))
    route = respx.get(f"{_BASE_URL}/rest/latest/ping").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"meta": {}, "links": {}, "data": {"ok": True}}),
        ],
    )
    async with JamaClient(_creds()) as client:
        result = await client._request("GET", "/rest/latest/ping")
    assert result == {"ok": True}
    assert route.call_count == 2


@respx.mock
async def test_request_rate_limit_raises_after_second_failure():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_stub_token()))
    respx.get(f"{_BASE_URL}/rest/latest/ping").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "0"}),
    )
    async with JamaClient(_creds()) as client:
        with pytest.raises(JamaRateLimitError):
            await client._request("GET", "/rest/latest/ping")


@respx.mock
async def test_request_server_error_retries_once():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_stub_token()))
    route = respx.get(f"{_BASE_URL}/rest/latest/ping").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json={"meta": {}, "links": {}, "data": {"ok": True}}),
        ],
    )
    async with JamaClient(_creds()) as client:
        result = await client._request("GET", "/rest/latest/ping")
    assert result == {"ok": True}
    assert route.call_count == 2


@respx.mock
async def test_request_network_error_retries_with_backoff_then_raises():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_stub_token()))
    respx.get(f"{_BASE_URL}/rest/latest/ping").mock(side_effect=httpx.ConnectError("boom"))
    async with JamaClient(_creds()) as client:
        with pytest.raises(JamaNetworkError):
            await client._request("GET", "/rest/latest/ping")


@respx.mock
async def test_request_raises_validation_error_on_missing_envelope():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_stub_token()))
    respx.get(f"{_BASE_URL}/rest/latest/ping").mock(return_value=httpx.Response(200, text="not-json"))
    async with JamaClient(_creds()) as client:
        with pytest.raises(JamaValidationError):
            await client._request("GET", "/rest/latest/ping")


async def test_client_request_outside_context_raises_runtime_error():
    client = JamaClient(_creds())
    with pytest.raises(RuntimeError):
        await client._request("GET", "/rest/latest/ping")
```

- [ ] **Step 2: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/jama_client/test_client_transport.py -v
```

Expected: import errors / `AttributeError` because `JamaClient` is unimplemented.

- [ ] **Step 3: Implement `src/jama_client/client.py`.**

Replace the placeholder with:

```python
"""Asynchronous HTTP client for the Jamacloud REST API.

The :class:`JamaClient` class is an async context manager wrapping
``httpx.AsyncClient``, owning the OAuth :class:`TokenCache`, performing
response envelope unwrapping (``meta`` / ``links`` / ``data``), and
mapping HTTP status codes to typed :mod:`jama_client.exceptions`. The
retry policy is the narrow one defined in Section 6 of the design spec.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import TracebackType
from typing import Any

import httpx

from jama_client.auth import OAuthCredentials, Token, TokenCache, fetch_token
from jama_client.exceptions import (
    JamaAuthError,
    JamaForbiddenError,
    JamaNetworkError,
    JamaNotFoundError,
    JamaRateLimitError,
    JamaServerError,
    JamaValidationError,
)

_DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_NETWORK_RETRY_LIMIT = 2
_NETWORK_RETRY_BASE_DELAY = 0.5


class JamaClient:
    """Async client wrapping a curated subset of the Jamacloud REST API."""

    def __init__(
        self,
        creds: OAuthCredentials,
        *,
        timeout: httpx.Timeout | None = None,
    ) -> None:
        """Initialize the client; the underlying HTTP transport opens on ``__aenter__``.

        Args:
            creds: Immutable OAuth credentials (including the ``base_url``).
            timeout: Optional ``httpx.Timeout`` override; defaults to a sensible value.
        """
        self._creds = creds
        self._timeout = timeout or _DEFAULT_TIMEOUT
        self._http: httpx.AsyncClient | None = None
        self._tokens = TokenCache()

    @property
    def is_open(self) -> bool:
        """Return ``True`` when the underlying HTTP client is open."""
        return self._http is not None

    async def __aenter__(self) -> "JamaClient":
        """Open the underlying ``httpx.AsyncClient``."""
        self._http = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the underlying ``httpx.AsyncClient`` and clear the token cache."""
        if self._http is not None:
            await self._http.aclose()
            self._http = None
        self._tokens.clear()

    async def _ensure_token(self) -> Token:
        """Return a valid token, refreshing proactively at or above 90 percent of TTL."""
        now = datetime.now(tz=timezone.utc)
        cached = self._tokens.get(now=now)
        if cached is not None:
            return cached
        if self._http is None:
            msg = "JamaClient must be used as an async context manager."
            raise RuntimeError(msg)
        token = await fetch_token(self._creds, self._http)
        self._tokens.set(token)
        return token

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        return_envelope: bool = False,
    ) -> Any:
        """Issue an authenticated request against the Jamacloud API.

        Args:
            method: HTTP verb.
            path: Path under the configured ``base_url`` (must start with ``/``).
            params: Optional query parameters.
            return_envelope: When ``True`` returns the full ``{meta,links,data}`` envelope;
                otherwise returns just the unwrapped ``data`` field.

        Returns:
            Parsed JSON ``data`` field by default, or the full envelope when requested.

        Raises:
            JamaAuthError, JamaForbiddenError, JamaNotFoundError, JamaRateLimitError,
            JamaServerError, JamaNetworkError, JamaValidationError: per design spec
            Section 6.
            RuntimeError: When invoked outside the async context manager.
        """
        if self._http is None:
            msg = "JamaClient must be used as an async context manager."
            raise RuntimeError(msg)

        url = f"{self._creds.base_url.rstrip('/')}{path}"

        rate_retried = False
        server_retried = False
        network_attempt = 0

        while True:
            token = await self._ensure_token()
            headers = {"Authorization": f"Bearer {token.access_token}"}
            try:
                response = await self._http.request(method, url, params=params, headers=headers)
            except httpx.HTTPError as exc:
                if network_attempt < _NETWORK_RETRY_LIMIT:
                    network_attempt += 1
                    await asyncio.sleep(_NETWORK_RETRY_BASE_DELAY * (2 ** (network_attempt - 1)))
                    continue
                msg = f"Network failure contacting Jamacloud: {exc!r}"
                raise JamaNetworkError(msg) from exc

            status = response.status_code

            if status == 200:
                return self._parse_envelope(response, return_envelope=return_envelope)

            if status == 429:
                if not rate_retried:
                    rate_retried = True
                    retry_after = self._parse_retry_after(response)
                    await asyncio.sleep(retry_after)
                    continue
                msg = "Jamacloud rate limit exceeded after retry."
                raise JamaRateLimitError(msg, retry_after=self._parse_retry_after(response))

            if 500 <= status < 600:
                if not server_retried:
                    server_retried = True
                    continue
                msg = f"Jamacloud returned HTTP {status}."
                raise JamaServerError(msg)

            self._raise_for_status(status)

    @staticmethod
    def _parse_envelope(response: httpx.Response, *, return_envelope: bool) -> Any:
        try:
            payload = response.json()
        except ValueError as exc:
            msg = "Jamacloud response was not valid JSON."
            raise JamaValidationError(msg, payload=response.text) from exc
        if not isinstance(payload, dict) or "data" not in payload:
            msg = "Jamacloud response missing expected meta/links/data envelope."
            raise JamaValidationError(msg, payload=payload)
        return payload if return_envelope else payload["data"]

    @staticmethod
    def _parse_retry_after(response: httpx.Response) -> int:
        raw = response.headers.get("Retry-After", "1")
        try:
            return max(0, int(raw))
        except ValueError:
            return 1

    @staticmethod
    def _raise_for_status(status: int) -> None:
        mapping: dict[int, type[Exception]] = {
            401: JamaAuthError,
            403: JamaForbiddenError,
            404: JamaNotFoundError,
        }
        exc_cls = mapping.get(status)
        if exc_cls is not None:
            raise exc_cls(f"Jamacloud returned HTTP {status}.")
        msg = f"Jamacloud returned unexpected HTTP {status}."
        raise JamaValidationError(msg)
```

- [ ] **Step 4: Run the test to verify it passes.**

```bash
uv run pytest tests/unit/jama_client/test_client_transport.py -v
```

Expected: all transport tests pass.

- [ ] **Step 5: Lint and type-check.**

```bash
uv run ruff check src/jama_client/client.py tests/unit/jama_client/test_client_transport.py
uv run ruff format --check src/jama_client/client.py tests/unit/jama_client/test_client_transport.py
uv run mypy src/jama_client/client.py
```

Expected: clean. The retry-policy `while True` may need a `# noqa: PLR0911`/`# noqa: PLR0912` or refactor if Pylint complains; prefer extracting helpers to keep complexity below the threshold rather than disabling rules. Adjust inline if needed.

- [ ] **Step 6: Commit.**

```bash
git add src/jama_client/client.py tests/unit/jama_client/test_client_transport.py
git commit -m "feat(jama_client): add JamaClient transport with envelope unwrapping and retry policy"
```

---

## Task 6: Client operations — `get_current_user` and `list_projects`

**Files:**
- Modify: `src/jama_client/client.py`
- Create: `tests/unit/jama_client/test_client_operations.py`

Each operation is a thin layer over `_request` plus Pydantic validation.

- [ ] **Step 1: Write the failing test.**

Create `tests/unit/jama_client/test_client_operations.py`:

```python
"""Tests for JamaClient operations (get_current_user, list_projects, get_item, ...)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from jama_client.auth import OAuthCredentials
from jama_client.client import JamaClient
from jama_client.models import Item, Project, Relationship, TestRun, User

_BASE_URL = "https://jama.example"
_TOKEN_URL = f"{_BASE_URL}/rest/oauth/token"
_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "jama_responses"


def _creds() -> OAuthCredentials:
    return OAuthCredentials(client_id="cid", client_secret="cs", base_url=_BASE_URL)


def _token_stub() -> dict:
    return {"access_token": "tok", "expires_in": 3600}


def _fixture(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text())


@respx.mock
async def test_get_current_user_returns_user_model():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_token_stub()))
    respx.get(f"{_BASE_URL}/rest/latest/users/current").mock(
        return_value=httpx.Response(200, json=_fixture("users_current.json")),
    )
    async with JamaClient(_creds()) as client:
        user = await client.get_current_user()
    assert isinstance(user, User)
    assert user.id == 100
    assert user.username == "afantaci"


@respx.mock
async def test_list_projects_returns_list_of_project_models():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_token_stub()))
    respx.get(f"{_BASE_URL}/rest/latest/projects").mock(
        return_value=httpx.Response(200, json=_fixture("projects_list.json")),
    )
    async with JamaClient(_creds()) as client:
        projects = await client.list_projects()
    assert len(projects) == 2
    assert all(isinstance(p, Project) for p in projects)
    assert {p.project_key for p in projects} == {"DEMO", "PILOT"}
```

- [ ] **Step 2: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/jama_client/test_client_operations.py -v
```

Expected: `AttributeError` — `get_current_user` and `list_projects` undefined.

- [ ] **Step 3: Add the methods to `JamaClient` in `src/jama_client/client.py`.**

Append inside the `JamaClient` class (before the trailing static methods). Also add the model imports at the top of the file.

Add at the top, alongside existing imports:

```python
from jama_client.models import Item, Project, Relationship, TestRun, User
```

Add inside the class:

```python
    async def get_current_user(self) -> User:
        """Return the user identified by the current OAuth credentials."""
        data = await self._request("GET", "/rest/latest/users/current")
        return self._validate(User, data)

    async def list_projects(self) -> list[Project]:
        """Return the first page of accessible Jama projects."""
        data = await self._request("GET", "/rest/latest/projects")
        return [self._validate(Project, item) for item in data]

    @staticmethod
    def _validate(model_cls, payload):
        try:
            return model_cls.model_validate(payload)
        except Exception as exc:
            msg = f"Failed to validate {model_cls.__name__} response."
            raise JamaValidationError(msg, payload=payload) from exc
```

Add the type annotation refinements as needed for mypy strict (use `from typing import TypeVar` and parametrize `_validate` with `T = TypeVar("T", bound=BaseModel)` so mypy keeps the return type narrow):

```python
from typing import TypeVar
from pydantic import BaseModel

_M = TypeVar("_M", bound=BaseModel)
```

Update `_validate`:

```python
    @staticmethod
    def _validate(model_cls: type[_M], payload: Any) -> _M:
        try:
            return model_cls.model_validate(payload)
        except Exception as exc:
            msg = f"Failed to validate {model_cls.__name__} response."
            raise JamaValidationError(msg, payload=payload) from exc
```

- [ ] **Step 4: Run the test to verify it passes.**

```bash
uv run pytest tests/unit/jama_client/test_client_operations.py -v
```

Expected: both tests pass.

- [ ] **Step 5: Lint and type-check.**

```bash
uv run ruff check src/jama_client/client.py tests/unit/jama_client/test_client_operations.py
uv run mypy src/jama_client/client.py
```

Expected: clean.

- [ ] **Step 6: Commit.**

```bash
git add src/jama_client/client.py tests/unit/jama_client/test_client_operations.py
git commit -m "feat(jama_client): add get_current_user and list_projects operations"
```

---

## Task 7: Client operations — `get_item` and `search_items`

**Files:**
- Modify: `src/jama_client/client.py`
- Modify: `tests/unit/jama_client/test_client_operations.py`

- [ ] **Step 1: Append failing tests.**

Append to `tests/unit/jama_client/test_client_operations.py`:

```python
@respx.mock
async def test_get_item_returns_item_model():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_token_stub()))
    respx.get(f"{_BASE_URL}/rest/latest/items/42").mock(
        return_value=httpx.Response(200, json=_fixture("items_get.json")),
    )
    async with JamaClient(_creds()) as client:
        item = await client.get_item(42)
    assert isinstance(item, Item)
    assert item.id == 42
    assert item.document_key == "DEMO-REQ-7"


@respx.mock
async def test_get_item_propagates_not_found():
    from jama_client.exceptions import JamaNotFoundError

    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_token_stub()))
    respx.get(f"{_BASE_URL}/rest/latest/items/999").mock(return_value=httpx.Response(404))
    async with JamaClient(_creds()) as client:
        with pytest.raises(JamaNotFoundError):
            await client.get_item(999)


@respx.mock
async def test_search_items_returns_items_within_project():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_token_stub()))
    route = respx.get(f"{_BASE_URL}/rest/latest/abstractitems").mock(
        return_value=httpx.Response(200, json=_fixture("abstractitems_search.json")),
    )
    async with JamaClient(_creds()) as client:
        items = await client.search_items(project_id=1, query="OAuth")
    assert len(items) == 1
    assert items[0].document_key == "DEMO-REQ-7"
    assert route.calls.last.request.url.params["project"] == "1"
    assert route.calls.last.request.url.params["contains"] == "OAuth"
```

- [ ] **Step 2: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/jama_client/test_client_operations.py -v
```

Expected: `AttributeError` for the new methods.

- [ ] **Step 3: Add the methods to `JamaClient`.**

Inside the class, add:

```python
    async def get_item(self, item_id: int) -> Item:
        """Return a single Jama item by ID.

        Args:
            item_id: The Jama internal item ID.

        Raises:
            JamaNotFoundError: When the item does not exist.
        """
        data = await self._request("GET", f"/rest/latest/items/{item_id}")
        return self._validate(Item, data)

    async def search_items(self, project_id: int, query: str) -> list[Item]:
        """Search Jama items within a project for ``query``.

        Args:
            project_id: The Jama project ID to scope the search.
            query: Free-text search query (matched against item content).
        """
        data = await self._request(
            "GET",
            "/rest/latest/abstractitems",
            params={"project": project_id, "contains": query},
        )
        return [self._validate(Item, item) for item in data]
```

- [ ] **Step 4: Run the test to verify it passes.**

```bash
uv run pytest tests/unit/jama_client/test_client_operations.py -v
```

Expected: all five operations tests pass.

- [ ] **Step 5: Lint and type-check.**

```bash
uv run ruff check src/jama_client/client.py tests/unit/jama_client/test_client_operations.py
uv run mypy src/jama_client/client.py
```

- [ ] **Step 6: Commit.**

```bash
git add src/jama_client/client.py tests/unit/jama_client/test_client_operations.py
git commit -m "feat(jama_client): add get_item and search_items operations"
```

---

## Task 8: Client operations — `get_downstream_relationships` and `get_test_runs_for_item`

**Files:**
- Modify: `src/jama_client/client.py`
- Modify: `tests/unit/jama_client/test_client_operations.py`

- [ ] **Step 1: Append failing tests.**

```python
@respx.mock
async def test_get_downstream_relationships_returns_relationship_models():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_token_stub()))
    respx.get(f"{_BASE_URL}/rest/latest/items/42/downstreamrelationships").mock(
        return_value=httpx.Response(200, json=_fixture("items_downstream_relationships.json")),
    )
    async with JamaClient(_creds()) as client:
        rels = await client.get_downstream_relationships(42)
    assert len(rels) == 1
    assert isinstance(rels[0], Relationship)
    assert rels[0].from_item == 42
    assert rels[0].to_item == 84


@respx.mock
async def test_get_test_runs_for_item_returns_test_run_models():
    respx.post(_TOKEN_URL).mock(return_value=httpx.Response(200, json=_token_stub()))
    respx.get(f"{_BASE_URL}/rest/latest/items/42/testruns").mock(
        return_value=httpx.Response(200, json=_fixture("items_test_runs.json")),
    )
    async with JamaClient(_creds()) as client:
        runs = await client.get_test_runs_for_item(42)
    assert len(runs) == 1
    assert isinstance(runs[0], TestRun)
    assert runs[0].fields["testRunStatus"] == "PASSED"
```

- [ ] **Step 2: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/jama_client/test_client_operations.py -v
```

Expected: `AttributeError`.

- [ ] **Step 3: Add the methods.**

```python
    async def get_downstream_relationships(self, item_id: int) -> list[Relationship]:
        """Return downstream relationships originating from ``item_id``."""
        data = await self._request(
            "GET",
            f"/rest/latest/items/{item_id}/downstreamrelationships",
        )
        return [self._validate(Relationship, rel) for rel in data]

    async def get_test_runs_for_item(self, item_id: int) -> list[TestRun]:
        """Return test runs that exercise ``item_id``."""
        data = await self._request("GET", f"/rest/latest/items/{item_id}/testruns")
        return [self._validate(TestRun, run) for run in data]
```

- [ ] **Step 4: Run the test to verify it passes.**

```bash
uv run pytest tests/unit/jama_client/test_client_operations.py -v
```

Expected: all seven operations tests pass.

- [ ] **Step 5: Lint and type-check.**

```bash
uv run ruff check src/jama_client/client.py tests/unit/jama_client/test_client_operations.py
uv run mypy src/jama_client/client.py
```

- [ ] **Step 6: Commit.**

```bash
git add src/jama_client/client.py tests/unit/jama_client/test_client_operations.py
git commit -m "feat(jama_client): add downstream relationships and test runs operations"
```

---

## Task 9: `jama_client` public API surface

**Files:**
- Modify: `src/jama_client/__init__.py`
- Create: `tests/unit/test_smoke.py`
- Delete: `tests/test_smoke.py` (Phase 0 placeholder; superseded)

Re-export the surface so external callers (and the MCP server) can do `from jama_client import JamaClient, JamaError`.

- [ ] **Step 1: Write the importability test.**

Replace `tests/unit/test_smoke.py` with a real importability check. Open the file, replace its contents with:

```python
"""Top-level importability checks for the public surfaces."""

from __future__ import annotations


def test_jama_client_public_surface_imports():
    from jama_client import (
        Item,
        JamaAuthError,
        JamaClient,
        JamaError,
        JamaForbiddenError,
        JamaNetworkError,
        JamaNotFoundError,
        JamaRateLimitError,
        JamaServerError,
        JamaValidationError,
        OAuthCredentials,
        Project,
        Relationship,
        TestRun,
        Token,
        User,
    )

    assert JamaClient is not None
    assert issubclass(JamaAuthError, JamaError)
    for cls in (User, Project, Item, Relationship, TestRun, Token, OAuthCredentials):
        assert cls is not None


def test_jama_mcp_server_package_imports():
    import jama_mcp_server  # noqa: F401
```

- [ ] **Step 2: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/test_smoke.py -v
```

Expected: `ImportError` because `jama_client/__init__.py` does not yet re-export.

- [ ] **Step 3: Update `src/jama_client/__init__.py`.**

Replace the placeholder with:

```python
"""Asynchronous Python client for the Jamacloud REST API.

Public re-exports: :class:`JamaClient`, the :class:`JamaError` hierarchy,
the OAuth helpers (:class:`OAuthCredentials`, :class:`Token`), and the
Pydantic entity models.
"""

from __future__ import annotations

from jama_client.auth import OAuthCredentials, Token, TokenCache
from jama_client.client import JamaClient
from jama_client.exceptions import (
    JamaAuthError,
    JamaError,
    JamaForbiddenError,
    JamaNetworkError,
    JamaNotFoundError,
    JamaRateLimitError,
    JamaServerError,
    JamaValidationError,
)
from jama_client.models import (
    Item,
    ItemFields,
    Project,
    Relationship,
    RelationshipType,
    TestRun,
    User,
)

__all__ = [
    "Item",
    "ItemFields",
    "JamaAuthError",
    "JamaClient",
    "JamaError",
    "JamaForbiddenError",
    "JamaNetworkError",
    "JamaNotFoundError",
    "JamaRateLimitError",
    "JamaServerError",
    "JamaValidationError",
    "OAuthCredentials",
    "Project",
    "Relationship",
    "RelationshipType",
    "TestRun",
    "Token",
    "TokenCache",
    "User",
]
```

- [ ] **Step 4: Run the test to verify it passes.**

```bash
uv run pytest tests/unit/test_smoke.py -v
```

Expected: both tests pass.

- [ ] **Step 5: Run the entire `jama_client` test suite to confirm no regressions.**

```bash
uv run pytest tests/unit/jama_client/ tests/unit/test_smoke.py -v
```

Expected: all `jama_client` tests pass.

- [ ] **Step 6: Lint and type-check.**

```bash
uv run ruff check src/jama_client/ tests/unit/
uv run ruff format --check src/jama_client/ tests/unit/
uv run mypy src/jama_client/
```

Expected: clean.

- [ ] **Step 7: Commit.**

```bash
git add src/jama_client/__init__.py tests/unit/test_smoke.py
git commit -m "feat(jama_client): expose public package surface"
```

---

## Task 10: `Settings` configuration

**Files:**
- Modify: `src/jama_mcp_server/config.py`
- Create: `tests/unit/jama_mcp_server/test_config.py`

Reads required environment variables (or `.env`); fails loud with `pydantic.ValidationError` at startup when required values are missing — per design spec Section 6 ("Configuration errors").

- [ ] **Step 1: Write the failing test.**

Create `tests/unit/jama_mcp_server/test_config.py`:

```python
"""Tests for jama_mcp_server.config.Settings."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from jama_mcp_server.config import Settings


def test_settings_loads_from_environment(monkeypatch):
    monkeypatch.setenv("JAMA_BASE_URL", "https://jama.example")
    monkeypatch.setenv("JAMA_OAUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("JAMA_OAUTH_CLIENT_SECRET", "cs")
    monkeypatch.setenv("MCP_TRANSPORT", "stdio")
    monkeypatch.setenv("MCP_HTTP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_HTTP_PORT", "8765")

    settings = Settings()

    assert settings.jama_base_url == "https://jama.example"
    assert settings.jama_oauth_client_id == "cid"
    assert settings.jama_oauth_client_secret.get_secret_value() == "cs"
    assert settings.mcp_transport == "stdio"
    assert settings.mcp_http_host == "127.0.0.1"
    assert settings.mcp_http_port == 8765


def test_settings_defaults_for_optional_fields(monkeypatch):
    monkeypatch.delenv("MCP_HTTP_HOST", raising=False)
    monkeypatch.delenv("MCP_HTTP_PORT", raising=False)
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.setenv("JAMA_BASE_URL", "https://jama.example")
    monkeypatch.setenv("JAMA_OAUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("JAMA_OAUTH_CLIENT_SECRET", "cs")

    settings = Settings()

    assert settings.mcp_transport == "stdio"
    assert settings.mcp_http_host == "127.0.0.1"
    assert settings.mcp_http_port == 8765


def test_settings_raises_when_required_missing(monkeypatch):
    for var in ("JAMA_BASE_URL", "JAMA_OAUTH_CLIENT_ID", "JAMA_OAUTH_CLIENT_SECRET"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_rejects_unknown_transport(monkeypatch):
    monkeypatch.setenv("JAMA_BASE_URL", "https://jama.example")
    monkeypatch.setenv("JAMA_OAUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("JAMA_OAUTH_CLIENT_SECRET", "cs")
    monkeypatch.setenv("MCP_TRANSPORT", "telepathy")
    with pytest.raises(ValidationError):
        Settings()
```

- [ ] **Step 2: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_config.py -v
```

Expected: `ImportError` — `Settings` undefined.

- [ ] **Step 3: Implement `src/jama_mcp_server/config.py`.**

Replace the placeholder with:

```python
"""Settings management for the Jama MCP Server.

Reads configuration from environment variables (or a local ``.env`` file).
The class fails loud with ``pydantic.ValidationError`` at startup if any
required value is missing or malformed; this is intentional per the
design spec's Section 6 error-handling policy.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

Transport = Literal["stdio", "streamable-http"]


class Settings(BaseSettings):
    """Runtime configuration for the Jama MCP Server."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    jama_base_url: str = Field(...)
    jama_oauth_client_id: str = Field(...)
    jama_oauth_client_secret: SecretStr = Field(...)

    mcp_transport: Transport = "stdio"
    mcp_http_host: str = "127.0.0.1"
    mcp_http_port: int = 8765
```

- [ ] **Step 4: Run the test to verify it passes.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_config.py -v
```

Expected: all four tests pass.

- [ ] **Step 5: Lint and type-check.**

```bash
uv run ruff check src/jama_mcp_server/config.py tests/unit/jama_mcp_server/test_config.py
uv run mypy src/jama_mcp_server/config.py
```

- [ ] **Step 6: Commit.**

```bash
git add src/jama_mcp_server/config.py tests/unit/jama_mcp_server/test_config.py
git commit -m "feat(jama_mcp_server): add Settings configuration with env + .env loader"
```

---

## Task 11: Transport-aware logging

**Files:**
- Modify: `src/jama_mcp_server/logging_config.py`
- Create: `tests/unit/jama_mcp_server/test_logging_config.py`

`stdio` transport reserves stdout for JSON-RPC framing — logs MUST go to stderr. `streamable-http` runs in containers where stdout is the convention.

- [ ] **Step 1: Write the failing test.**

Create `tests/unit/jama_mcp_server/test_logging_config.py`:

```python
"""Tests for jama_mcp_server.logging_config.configure_logging."""

from __future__ import annotations

import logging
import sys

import pytest

from jama_mcp_server.logging_config import configure_logging


@pytest.fixture(autouse=True)
def _reset_logging():
    yield
    # Reset root handlers between tests so per-test stream selection sticks.
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)


def test_stdio_transport_logs_to_stderr():
    configure_logging("stdio")
    root = logging.getLogger()
    streams = {getattr(h, "stream", None) for h in root.handlers}
    assert sys.stderr in streams
    assert sys.stdout not in streams


def test_streamable_http_transport_logs_to_stdout():
    configure_logging("streamable-http")
    root = logging.getLogger()
    streams = {getattr(h, "stream", None) for h in root.handlers}
    assert sys.stdout in streams
    assert sys.stderr not in streams


def test_unknown_transport_raises_value_error():
    with pytest.raises(ValueError):
        configure_logging("telepathy")
```

- [ ] **Step 2: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_logging_config.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `src/jama_mcp_server/logging_config.py`.**

Replace the placeholder with:

```python
"""Transport-aware structlog configuration.

The MCP stdio transport reserves stdout for JSON-RPC framing, so logs are
sent to stderr in that mode. The streamable-HTTP transport runs in
container environments where stdout is the conventional log sink.
"""

from __future__ import annotations

import logging
import sys
from typing import Literal

import structlog

Transport = Literal["stdio", "streamable-http"]


def configure_logging(transport: Transport) -> None:
    """Configure root logging and ``structlog`` for the given transport.

    Args:
        transport: ``"stdio"`` (logs to stderr) or ``"streamable-http"`` (logs to stdout).

    Raises:
        ValueError: When ``transport`` is not a recognised value.
    """
    if transport == "stdio":
        stream = sys.stderr
    elif transport == "streamable-http":
        stream = sys.stdout
    else:
        msg = f"Unknown transport: {transport!r}. Expected 'stdio' or 'streamable-http'."
        raise ValueError(msg)

    handler = logging.StreamHandler(stream=stream)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

- [ ] **Step 4: Run the test to verify it passes.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_logging_config.py -v
```

Expected: all three tests pass.

- [ ] **Step 5: Lint and type-check.**

```bash
uv run ruff check src/jama_mcp_server/logging_config.py tests/unit/jama_mcp_server/test_logging_config.py
uv run mypy src/jama_mcp_server/logging_config.py
```

- [ ] **Step 6: Commit.**

```bash
git add src/jama_mcp_server/logging_config.py tests/unit/jama_mcp_server/test_logging_config.py
git commit -m "feat(jama_mcp_server): add transport-aware structlog configuration"
```

---

## Task 12: FastMCP instance, lifespan, and entry points

**Files:**
- Modify: `src/jama_mcp_server/server.py`
- Modify: `src/jama_mcp_server/__init__.py`
- Create: `tests/unit/jama_mcp_server/test_server_lifespan.py`

Lifespan owns the shared `JamaClient`. Tools retrieve it via `ctx.request_context.lifespan_context["jama_client"]`. Tests inject a mock `JamaClient` through the same lifespan, exercising the production wiring.

- [ ] **Step 1: Write the failing test.**

Create `tests/unit/jama_mcp_server/test_server_lifespan.py`:

```python
"""Tests for the FastMCP lifespan and server construction."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from jama_mcp_server.server import build_server, jama_lifespan


class _FakeClient:
    """Stand-in for JamaClient supporting async-context-manager lifecycle."""

    def __init__(self):
        self.entered = False
        self.exited = False

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.exited = True
        return None


async def test_jama_lifespan_yields_client_and_cleans_up(monkeypatch):
    fake = _FakeClient()

    def _factory(_settings):
        return fake

    settings = MagicMock(jama_base_url="https://jama.example", jama_oauth_client_id="cid")
    settings.jama_oauth_client_secret.get_secret_value = MagicMock(return_value="cs")

    server = MagicMock()
    async with jama_lifespan(server, settings=settings, client_factory=_factory) as ctx:
        assert ctx["jama_client"] is fake
        assert fake.entered
    assert fake.exited


def test_build_server_returns_fastmcp_instance(monkeypatch):
    settings = MagicMock(jama_base_url="https://jama.example", jama_oauth_client_id="cid")
    settings.jama_oauth_client_secret.get_secret_value = MagicMock(return_value="cs")
    server = build_server(settings=settings)
    assert server is not None
    assert hasattr(server, "tool")  # FastMCP exposes the @tool decorator
```

- [ ] **Step 2: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_server_lifespan.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `src/jama_mcp_server/server.py`.**

Replace the placeholder with:

```python
"""FastMCP application instance and transport entry points."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from jama_client import JamaClient, OAuthCredentials
from jama_mcp_server.config import Settings
from jama_mcp_server.logging_config import configure_logging


def _default_client_factory(settings: Settings) -> JamaClient:
    creds = OAuthCredentials(
        client_id=settings.jama_oauth_client_id,
        client_secret=settings.jama_oauth_client_secret.get_secret_value(),
        base_url=settings.jama_base_url,
    )
    return JamaClient(creds)


@asynccontextmanager
async def jama_lifespan(
    _server: Any,
    *,
    settings: Settings,
    client_factory: Callable[[Settings], JamaClient] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Construct and tear down the shared :class:`JamaClient` for the server."""
    factory = client_factory or _default_client_factory
    client = factory(settings)
    async with client:
        yield {"jama_client": client}


def build_server(*, settings: Settings | None = None) -> FastMCP:
    """Build a :class:`FastMCP` instance bound to the given settings."""
    cfg = settings or Settings()

    @asynccontextmanager
    async def _bound_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
        async with jama_lifespan(server, settings=cfg) as ctx:
            yield ctx

    server = FastMCP("jama-mcp-server", lifespan=_bound_lifespan)

    # Register tools (Task 13+ populates these).
    from jama_mcp_server import tools  # noqa: F401, import for side-effect registration

    tools.register(server)
    return server


def main_stdio() -> None:
    """Run the MCP server using the stdio transport."""
    settings = Settings()
    configure_logging(settings.mcp_transport)
    server = build_server(settings=settings)
    server.run(transport="stdio")


def main_http() -> None:
    """Run the MCP server using the streamable-HTTP transport."""
    settings = Settings()
    configure_logging(settings.mcp_transport)
    server = build_server(settings=settings)
    server.run(
        transport="streamable-http",
        host=settings.mcp_http_host,
        port=settings.mcp_http_port,
    )
```

- [ ] **Step 4: Update `src/jama_mcp_server/__init__.py` to expose `build_server`.**

Replace the placeholder with:

```python
"""FastMCP server exposing Jamacloud REST operations as MCP tools."""

from __future__ import annotations

from jama_mcp_server.server import build_server, jama_lifespan, main_http, main_stdio

__all__ = ["build_server", "jama_lifespan", "main_http", "main_stdio"]
```

- [ ] **Step 5: Add a placeholder `register` in `src/jama_mcp_server/tools.py` so `build_server` imports cleanly.**

Replace the placeholder with:

```python
"""MCP tool definitions for the Jama traceability slice."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(_server: "FastMCP") -> None:
    """Register the six Phase 1 tools on the given server.

    The registration body is filled in by Tasks 13-17.
    """
    return
```

- [ ] **Step 6: Run the test to verify it passes.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_server_lifespan.py -v
```

Expected: both tests pass.

- [ ] **Step 7: Lint and type-check.**

```bash
uv run ruff check src/jama_mcp_server/ tests/unit/jama_mcp_server/
uv run mypy src/jama_mcp_server/
```

Expected: clean. Note: importing `tools` inside `build_server` is intentional to keep registration lazy and avoid import cycles. Add `# noqa: PLC0415` if Pylint flags the local import.

- [ ] **Step 8: Commit.**

```bash
git add src/jama_mcp_server/server.py src/jama_mcp_server/__init__.py src/jama_mcp_server/tools.py tests/unit/jama_mcp_server/test_server_lifespan.py
git commit -m "feat(jama_mcp_server): add FastMCP server, lifespan, and transport entry points"
```

---

## Task 13: MCP tools — `whoami` and `list_projects`

**Files:**
- Modify: `src/jama_mcp_server/tools.py`
- Create: `tests/unit/jama_mcp_server/test_tools.py`

Each tool retrieves the shared `JamaClient` from the lifespan context, calls the matching client method, and returns an AI-shaped dictionary (snake_case, trimmed verbosity, predictable structure).

- [ ] **Step 1: Set up the shared mock-client fixture in `tests/conftest.py`.**

Replace `tests/conftest.py` with:

```python
"""Shared pytest fixtures for the Jama MCP Server test suite."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from jama_client import JamaClient


@pytest.fixture
def mock_jama_client() -> AsyncMock:
    """Return an ``AsyncMock`` configured to behave as a :class:`JamaClient`."""
    client = AsyncMock(spec=JamaClient)
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    return client
```

- [ ] **Step 2: Write the failing tools tests.**

Create `tests/unit/jama_mcp_server/test_tools.py`:

```python
"""Unit tests for the six Phase 1 MCP tools.

Tools are exercised through FastMCP's in-process call_tool API with a mock
JamaClient injected via the lifespan context — the same wiring the real
server uses.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import FastMCP

from jama_client.exceptions import JamaNotFoundError
from jama_client.models import Item, Project, Relationship, TestRun, User
from jama_mcp_server import tools


@pytest.fixture
def server_with_mock_client(mock_jama_client: AsyncMock) -> tuple[FastMCP, AsyncMock]:
    @asynccontextmanager
    async def _lifespan(_server: FastMCP):
        yield {"jama_client": mock_jama_client}

    server = FastMCP("jama-mcp-server-test", lifespan=_lifespan)
    tools.register(server)
    return server, mock_jama_client


async def test_whoami_returns_ai_shaped_user(server_with_mock_client):
    server, client = server_with_mock_client
    client.get_current_user.return_value = User(id=100, first_name="A", username="a")
    result = await server.call_tool("whoami", {})
    assert result["id"] == 100
    assert result["username"] == "a"
    assert "first_name" in result


async def test_list_projects_returns_ai_shaped_list(server_with_mock_client):
    server, client = server_with_mock_client
    client.list_projects.return_value = [
        Project(id=1, project_key="DEMO"),
        Project(id=2, project_key="PILOT"),
    ]
    result = await server.call_tool("list_projects", {})
    assert isinstance(result, list)
    assert {p["project_key"] for p in result} == {"DEMO", "PILOT"}
```

- [ ] **Step 3: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_tools.py -v
```

Expected: `KeyError` or "tool not registered" — `whoami` and `list_projects` tools are not defined.

- [ ] **Step 4: Implement the two tools.**

Replace `src/jama_mcp_server/tools.py` with:

```python
"""MCP tool definitions for the Jama traceability slice.

Each tool retrieves the shared :class:`jama_client.JamaClient` from the
lifespan context and returns AI-shaped dictionaries with snake_case keys
(via Pydantic's default ``model_dump``). Expected absences (404 from
``get_item``) are converted to structured ``found: false`` responses; all
other exceptions propagate so FastMCP returns tool-call errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from jama_client import JamaClient
from jama_client.exceptions import JamaNotFoundError

if TYPE_CHECKING:
    from mcp.server.fastmcp import Context, FastMCP


def _client(ctx: "Context") -> JamaClient:
    return ctx.request_context.lifespan_context["jama_client"]


def register(server: "FastMCP") -> None:
    """Register the six Phase 1 tools on the given FastMCP server."""

    @server.tool()
    async def whoami(ctx: "Context") -> dict[str, Any]:
        """Identify the user whose OAuth credentials authenticate the server."""
        user = await _client(ctx).get_current_user()
        return user.model_dump()

    @server.tool()
    async def list_projects(ctx: "Context") -> list[dict[str, Any]]:
        """Return projects accessible to the configured Jama credentials."""
        projects = await _client(ctx).list_projects()
        return [p.model_dump() for p in projects]
```

- [ ] **Step 5: Run the test to verify it passes.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_tools.py -v
```

Expected: both tests pass.

- [ ] **Step 6: Lint and type-check.**

```bash
uv run ruff check src/jama_mcp_server/tools.py tests/unit/jama_mcp_server/test_tools.py tests/conftest.py
uv run mypy src/jama_mcp_server/tools.py
```

Expected: clean.

- [ ] **Step 7: Commit.**

```bash
git add src/jama_mcp_server/tools.py tests/unit/jama_mcp_server/test_tools.py tests/conftest.py
git commit -m "feat(jama_mcp_server): add whoami and list_projects MCP tools"
```

---

## Task 14: MCP tool — `get_item` (with 404 → `found: false`)

**Files:**
- Modify: `src/jama_mcp_server/tools.py`
- Modify: `tests/unit/jama_mcp_server/test_tools.py`

This is the only Phase 1 tool that translates a `JamaNotFoundError` into a structured "not found" response so the AI can reason about absence as data rather than as a tool failure (design spec Section 6 → "Expected absences").

- [ ] **Step 1: Append failing tests.**

Append to `tests/unit/jama_mcp_server/test_tools.py`:

```python
async def test_get_item_returns_ai_shaped_item(server_with_mock_client):
    server, client = server_with_mock_client
    client.get_item.return_value = Item(id=42, document_key="DEMO-REQ-7")
    result = await server.call_tool("get_item", {"item_id": 42})
    assert result["id"] == 42
    assert result["document_key"] == "DEMO-REQ-7"


async def test_get_item_translates_not_found_to_structured_response(server_with_mock_client):
    server, client = server_with_mock_client
    client.get_item.side_effect = JamaNotFoundError("not found")
    result = await server.call_tool("get_item", {"item_id": 999})
    assert result == {"found": False, "item_id": 999, "message": "not found"}
```

- [ ] **Step 2: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_tools.py -v
```

Expected: `KeyError` for the unregistered `get_item` tool.

- [ ] **Step 3: Add the tool inside `register()` in `src/jama_mcp_server/tools.py`.**

Append within `register`, after `list_projects`:

```python
    @server.tool()
    async def get_item(ctx: "Context", item_id: int) -> dict[str, Any]:
        """Retrieve a Jama item by ID.

        Returns ``{"found": False, "item_id": id, "message": ...}`` when the
        item does not exist; otherwise returns the item's snake_case
        serialization.
        """
        try:
            item = await _client(ctx).get_item(item_id)
        except JamaNotFoundError as exc:
            return {"found": False, "item_id": item_id, "message": str(exc)}
        return item.model_dump()
```

- [ ] **Step 4: Run the test to verify it passes.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_tools.py -v
```

Expected: all four tests pass.

- [ ] **Step 5: Lint and type-check, then commit.**

```bash
uv run ruff check src/jama_mcp_server/tools.py tests/unit/jama_mcp_server/test_tools.py
uv run mypy src/jama_mcp_server/tools.py
git add src/jama_mcp_server/tools.py tests/unit/jama_mcp_server/test_tools.py
git commit -m "feat(jama_mcp_server): add get_item tool with structured not-found response"
```

---

## Task 15: MCP tool — `search_items`

**Files:**
- Modify: `src/jama_mcp_server/tools.py`
- Modify: `tests/unit/jama_mcp_server/test_tools.py`

- [ ] **Step 1: Append failing test.**

```python
async def test_search_items_returns_ai_shaped_list(server_with_mock_client):
    server, client = server_with_mock_client
    client.search_items.return_value = [Item(id=42, document_key="DEMO-REQ-7")]
    result = await server.call_tool(
        "search_items",
        {"project_id": 1, "query": "OAuth"},
    )
    assert isinstance(result, list)
    assert result[0]["document_key"] == "DEMO-REQ-7"
    client.search_items.assert_awaited_once_with(project_id=1, query="OAuth")
```

- [ ] **Step 2: Run the test to verify it fails.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_tools.py::test_search_items_returns_ai_shaped_list -v
```

- [ ] **Step 3: Add the tool inside `register()`.**

```python
    @server.tool()
    async def search_items(
        ctx: "Context",
        project_id: int,
        query: str,
    ) -> list[dict[str, Any]]:
        """Search Jama items within ``project_id`` for ``query``."""
        items = await _client(ctx).search_items(project_id=project_id, query=query)
        return [item.model_dump() for item in items]
```

- [ ] **Step 4: Run, lint, commit.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_tools.py -v
uv run ruff check src/jama_mcp_server/tools.py tests/unit/jama_mcp_server/test_tools.py
uv run mypy src/jama_mcp_server/tools.py
git add src/jama_mcp_server/tools.py tests/unit/jama_mcp_server/test_tools.py
git commit -m "feat(jama_mcp_server): add search_items tool"
```

---

## Task 16: MCP tool — `get_downstream_relationships`

**Files:**
- Modify: `src/jama_mcp_server/tools.py`
- Modify: `tests/unit/jama_mcp_server/test_tools.py`

- [ ] **Step 1: Append failing test.**

```python
async def test_get_downstream_relationships_returns_ai_shaped_list(server_with_mock_client):
    server, client = server_with_mock_client
    client.get_downstream_relationships.return_value = [
        Relationship(id=9001, from_item=42, to_item=84, relationship_type=5),
    ]
    result = await server.call_tool("get_downstream_relationships", {"item_id": 42})
    assert result[0]["from_item"] == 42
    assert result[0]["to_item"] == 84
```

- [ ] **Step 2: Run, fail.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_tools.py::test_get_downstream_relationships_returns_ai_shaped_list -v
```

- [ ] **Step 3: Add the tool.**

```python
    @server.tool()
    async def get_downstream_relationships(
        ctx: "Context",
        item_id: int,
    ) -> list[dict[str, Any]]:
        """Return downstream relationships originating from ``item_id``."""
        rels = await _client(ctx).get_downstream_relationships(item_id)
        return [rel.model_dump() for rel in rels]
```

- [ ] **Step 4: Run, lint, commit.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_tools.py -v
uv run ruff check src/jama_mcp_server/tools.py tests/unit/jama_mcp_server/test_tools.py
uv run mypy src/jama_mcp_server/tools.py
git add src/jama_mcp_server/tools.py tests/unit/jama_mcp_server/test_tools.py
git commit -m "feat(jama_mcp_server): add get_downstream_relationships tool"
```

---

## Task 17: MCP tool — `get_test_runs_for_item`

**Files:**
- Modify: `src/jama_mcp_server/tools.py`
- Modify: `tests/unit/jama_mcp_server/test_tools.py`

- [ ] **Step 1: Append failing test.**

```python
async def test_get_test_runs_for_item_returns_ai_shaped_list(server_with_mock_client):
    server, client = server_with_mock_client
    client.get_test_runs_for_item.return_value = [
        TestRun(id=7001, document_key="DEMO-TR-1"),
    ]
    result = await server.call_tool("get_test_runs_for_item", {"item_id": 42})
    assert result[0]["id"] == 7001
    assert result[0]["document_key"] == "DEMO-TR-1"
```

- [ ] **Step 2: Run, fail.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_tools.py::test_get_test_runs_for_item_returns_ai_shaped_list -v
```

- [ ] **Step 3: Add the tool.**

```python
    @server.tool()
    async def get_test_runs_for_item(
        ctx: "Context",
        item_id: int,
    ) -> list[dict[str, Any]]:
        """Return test runs that exercise ``item_id``."""
        runs = await _client(ctx).get_test_runs_for_item(item_id)
        return [run.model_dump() for run in runs]
```

- [ ] **Step 4: Run, lint, commit.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_tools.py -v
uv run ruff check src/jama_mcp_server/tools.py tests/unit/jama_mcp_server/test_tools.py
uv run mypy src/jama_mcp_server/tools.py
git add src/jama_mcp_server/tools.py tests/unit/jama_mcp_server/test_tools.py
git commit -m "feat(jama_mcp_server): add get_test_runs_for_item tool"
```

---

## Task 18: MCP protocol-level smoke tests

**Files:**
- Create: `tests/unit/jama_mcp_server/test_protocol.py`

Verifies JSON-RPC framing, tool schema generation, and protocol-level error translation using FastMCP's in-process test client.

- [ ] **Step 1: Write the failing tests.**

Create `tests/unit/jama_mcp_server/test_protocol.py`:

```python
"""Protocol-level tests using FastMCP's in-process test client."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import FastMCP

from jama_client import JamaClient
from jama_client.models import User
from jama_mcp_server import tools


@pytest.fixture
def server(mock_jama_client: AsyncMock) -> FastMCP:
    @asynccontextmanager
    async def _lifespan(_server: FastMCP):
        yield {"jama_client": mock_jama_client}

    server = FastMCP("jama-mcp-server-test", lifespan=_lifespan)
    tools.register(server)
    return server


async def test_server_lists_six_tools(server: FastMCP):
    listed = await server.list_tools()
    names = {tool.name for tool in listed}
    assert names == {
        "whoami",
        "list_projects",
        "get_item",
        "search_items",
        "get_downstream_relationships",
        "get_test_runs_for_item",
    }


async def test_get_item_schema_declares_item_id_argument(server: FastMCP):
    listed = await server.list_tools()
    by_name = {tool.name: tool for tool in listed}
    schema = by_name["get_item"].inputSchema
    assert "item_id" in schema["properties"]
    assert schema["properties"]["item_id"]["type"] == "integer"


async def test_whoami_call_round_trips_via_protocol(server: FastMCP, mock_jama_client: AsyncMock):
    mock_jama_client.get_current_user.return_value = User(id=100, username="afantaci")
    response = await server.call_tool("whoami", {})
    assert response["id"] == 100
    assert response["username"] == "afantaci"
```

> **Note on the FastMCP test API:** The exact method names (`list_tools`, `call_tool`) reflect FastMCP's documented in-process surface. If the installed `mcp` SDK exposes them under a different attribute (e.g., `server._tool_manager.list_tools()`), adjust the calls to match. Verify via `python -c "from mcp.server.fastmcp import FastMCP; help(FastMCP)"` and update before committing.

- [ ] **Step 2: Run the tests.**

```bash
uv run pytest tests/unit/jama_mcp_server/test_protocol.py -v
```

Expected: all three tests pass against the implementation from Tasks 13–17.

- [ ] **Step 3: Lint and type-check.**

```bash
uv run ruff check tests/unit/jama_mcp_server/test_protocol.py
uv run mypy src/jama_mcp_server/
```

- [ ] **Step 4: Commit.**

```bash
git add tests/unit/jama_mcp_server/test_protocol.py
git commit -m "test(jama_mcp_server): add MCP protocol-level smoke tests"
```

---

## Task 19: Integration test smoke suite

**Files:**
- Create: `tests/integration/test_smoke.py`

Opt-in via `pytest -m integration`. Skipped automatically when `JAMA_OAUTH_CLIENT_ID` / `JAMA_OAUTH_CLIENT_SECRET` are missing (Phase 0's `tests/integration/conftest.py` provides this gate). Covers `whoami`, `list_projects`, and a `get_item` round trip against the live sandbox.

- [ ] **Step 1: Author the integration smoke test.**

Create `tests/integration/test_smoke.py`:

```python
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
```

- [ ] **Step 2: Verify the suite is skipped without credentials.**

```bash
uv run pytest tests/integration -v
```

Expected: tests collected but skipped with the message defined in `tests/integration/conftest.py`.

- [ ] **Step 3: Verify the suite runs (manually) with credentials.**

With a populated `.env`:

```bash
uv run pytest -m integration -v
```

Expected: `whoami` and `list_projects` pass; `get_item` either passes (if `JAMA_KNOWN_ITEM_ID` is set) or skips. If any test fails, **stop** and adjust the endpoint URLs or response handling in `jama_client/client.py` (the canonical Jamacloud paths in this plan are documented assumptions and may need correction).

- [ ] **Step 4: Update endpoint assumptions if needed.**

If integration testing reveals different URL paths or response shapes, update:

1. The corresponding fixtures in `tests/fixtures/jama_responses/`.
2. The relevant `JamaClient` method.
3. The "Endpoint assumptions" table in this plan document.

Land each correction as its own conventional commit (e.g., `fix(jama_client): correct downstream relationships endpoint path`).

- [ ] **Step 5: Lint and commit.**

```bash
uv run ruff check tests/integration/
git add tests/integration/test_smoke.py
git commit -m "test(integration): add live-sandbox smoke suite (opt-in via pytest -m integration)"
```

---

## Task 20: README and `docs/setup.md` updates

**Files:**
- Modify: `README.md`
- Modify: `docs/setup.md`
- Modify: `pyproject.toml` (development status classifier)

- [ ] **Step 1: Update the Status table and Quick Start in `README.md`.**

In `README.md`:

- Change the Phase 1 row's status from `Planned` to `Complete`.
- Remove the "Phase 1 not yet implemented" warning above the Quick Start block.
- Replace the Quick Start with a working flow that includes `uv run jama-mcp-stdio` plus a brief MCP Inspector smoke recipe.
- Add a short "Tool reference" subsection mirroring the six tools with expected arguments.

Concrete diff (paste into `README.md`):

```markdown
## Quick start

```bash
git clone https://github.com/arthurfantaci/jama-mcp-server.git
cd jama-mcp-server
uv sync --extra dev
cp .env.example .env
# Populate .env with your Jamacloud OAuth credentials.
uv run jama-mcp-stdio
```

Smoke-test the server with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run jama-mcp-stdio
```

The Inspector lists six tools; invoking `whoami` round-trips through the server to your Jamacloud sandbox and returns the authenticated user.
```

Add a "Tool reference" subsection:

```markdown
## Tool reference

| Tool | Arguments | Returns |
|------|-----------|---------|
| `whoami` | none | The authenticated user. |
| `list_projects` | none | Accessible Jama projects (first page). |
| `get_item` | `item_id: int` | The item, or `{"found": false, ...}` on 404. |
| `search_items` | `project_id: int`, `query: str` | Items within the project matching the query. |
| `get_downstream_relationships` | `item_id: int` | Downstream relationships from the item. |
| `get_test_runs_for_item` | `item_id: int` | Test runs that exercise the item. |
```

- [ ] **Step 2: Extend `docs/setup.md`.**

Add a section walking through:
1. Provisioning the `jama-mcp-server-dev` OAuth credential in Jama Connect.
2. Populating `.env` and verifying with `uv run python -c "from jama_mcp_server.config import Settings; print(Settings().jama_base_url)"`.
3. Starting the stdio server: `uv run jama-mcp-stdio`.
4. Starting the streamable-HTTP server: `MCP_TRANSPORT=streamable-http uv run jama-mcp-http`.
5. Connecting via MCP Inspector and invoking `whoami`.

Keep the section under 80 lines; link to the design spec for deeper detail.

- [ ] **Step 3: Update `pyproject.toml` development status classifier.**

Change:

```toml
"Development Status :: 1 - Planning",
```

to:

```toml
"Development Status :: 3 - Alpha",
```

- [ ] **Step 4: Run docs lint.**

```bash
uv run pre-commit run --files README.md docs/setup.md pyproject.toml
```

- [ ] **Step 5: Commit.**

```bash
git add README.md docs/setup.md pyproject.toml
git commit -m "docs: document Phase 1 quick start, tool reference, and MCP Inspector smoke"
```

---

## Task 21: Update `MEMORY.md` and `CLAUDE.md`

**Files:**
- Modify: `MEMORY.md`
- Modify: `CLAUDE.md`

Per the user's global "no separate workflow for memory files" rule, these edits ride along with the Phase 1 PR (no separate issue/branch/PR).

- [ ] **Step 1: Update `MEMORY.md`.**

- Flip phase pointer: Phase 1 → Complete (will be true once the PR merges); Phase 2 → Active (planned).
- Add Phase 1 decisions to the "Recent decisions" table:
  - `2026-04-29` — six MCP tools landed; both transports verified via MCP Inspector.
  - `2026-04-29` — Pydantic v2 `alias_generator=to_camel` adopted for entity models.
  - Any endpoint-URL corrections discovered during integration testing.
- Move "Open items deferred to Phase 1" into a "Closed items" section or remove.
- Confirm line count remains ≤100.

- [ ] **Step 2: Update `CLAUDE.md`.**

Append (or update) a "Phase 1 conventions codified" subsection if any new convention was introduced:

- Pydantic models use `alias_generator=to_camel` plus `populate_by_name=True`; do not write per-field aliases.
- MCP tools return snake_case via `model.model_dump()` (no `by_alias=True`).
- `get_item` translates 404 to `{"found": false, ...}`; other operations re-raise.

Keep `CLAUDE.md` under ~150 lines.

- [ ] **Step 3: Run docs lint and commit.**

```bash
uv run pre-commit run --files MEMORY.md CLAUDE.md
git add MEMORY.md CLAUDE.md
git commit -m "docs: refresh MEMORY.md and CLAUDE.md for Phase 1 closure"
```

---

## Task 22: Final verification, MCP Inspector smoke, and PR

**Files:**
- None (verification + PR creation).

- [ ] **Step 1: Run the complete local check suite.**

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -m "not integration"
```

Expected: every command exits 0. If any fails, fix on the same branch and add a follow-on commit before opening the PR.

- [ ] **Step 2: Run the integration suite manually.**

With `.env` populated:

```bash
uv run pytest -m integration -v
```

Expected: `whoami` and `list_projects` pass against `pm2.jamacloud.com`. `get_item` passes if `JAMA_KNOWN_ITEM_ID` is set.

- [ ] **Step 3: Manual MCP Inspector smoke (stdio).**

```bash
npx @modelcontextprotocol/inspector uv run jama-mcp-stdio
```

Verify in the Inspector UI:

1. Six tools are listed: `whoami`, `list_projects`, `get_item`, `search_items`, `get_downstream_relationships`, `get_test_runs_for_item`.
2. Invoking `whoami` returns the configured user.
3. Invoking `list_projects` returns at least one project.
4. Invoking `get_item` with a real item ID returns the item.
5. Invoking `get_item` with a bogus ID (e.g., `99999999`) returns `{"found": false, ...}`, not an error.
6. Invoking `get_downstream_relationships` and `get_test_runs_for_item` with a real item ID returns lists.

Take a screenshot of the successful traceability flow (item → relationships → test runs) for the PR description.

- [ ] **Step 4: Manual MCP Inspector smoke (streamable-HTTP).**

In one terminal:

```bash
MCP_TRANSPORT=streamable-http uv run jama-mcp-http
```

In another terminal, point the Inspector at the HTTP endpoint per the [MCP Inspector HTTP transport docs](https://github.com/modelcontextprotocol/inspector). Re-run the same smoke checks as Step 3.

- [ ] **Step 5: Push the branch and open the PR.**

```bash
git push -u origin feat/phase-1-functional-mvp
gh pr create \
  --title "feat: Phase 1 — Functional MVP, six MCP tools across both transports" \
  --body "$(cat <<'EOF'
## Summary

- Implements the seven-class `jama_client` exception hierarchy, Pydantic v2 entity models with hand-crafted JSON fixtures, OAuth 2.0 client_credentials flow with proactive token refresh, and the async `JamaClient` transport with envelope unwrapping and the design-spec retry policy.
- Implements the six client operations: `get_current_user`, `list_projects`, `get_item`, `search_items`, `get_downstream_relationships`, `get_test_runs_for_item`.
- Wires `jama_mcp_server` end to end: `Settings`, transport-aware structlog, FastMCP instance with shared-`JamaClient` lifespan, and the six `@mcp.tool()` functions. `get_item` translates 404 to `{"found": false, ...}` so the AI reasons about absence as data.
- Verified via `respx`-mocked unit tests, FastMCP in-process protocol tests, and live integration smoke against `pm2.jamacloud.com`.
- Closes #<ISSUE_NUMBER>.

## Test plan

- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src/`
- [x] `uv run pytest -m "not integration"`
- [x] `uv run pytest -m integration` (manual, against sandbox)
- [x] MCP Inspector smoke against `jama-mcp-stdio`
- [x] MCP Inspector smoke against `jama-mcp-http`

## Professional portrayal checklist

- [x] No debug prints, commented-out code, or AI-collaboration artifacts.
- [x] All public functions, classes, methods carry Google-style docstrings.
- [x] All function signatures are type-annotated; `mypy --strict` clean.
- [x] Conventional commits, imperative mood subjects, focused diffs.
- [x] Secrets never staged (`.env` gitignored; `gitleaks` clean).
EOF
)"
```

- [ ] **Step 6: Watch CI, address feedback, merge.**

```bash
gh pr checks --watch
```

When CI is green and the PR is approved, squash- or merge-commit per the team's preference. The user's global Phase Handoff Protocol (`/phase-handoff`) handles post-merge cleanup (branch deletion, MEMORY.md flip to "Phase 1 complete", CLAUDE.md re-audit).

---

## Verifiable end state

Per the design spec Section 10 Phase 1 "Verifiable end state":

> Claude Desktop or the MCP Inspector connects to `jama-mcp-stdio` and `jama-mcp-http`. Both successfully invoke `whoami` against the sandbox, and an AI agent completes a traceability query end-to-end (project, item, relationships, test runs).

This plan satisfies that end state via Tasks 12–17 (server + tools), Task 18 (protocol tests), Task 19 (live integration smoke), and Task 22 Steps 3–4 (MCP Inspector smoke against both transports).

---

## Self-review notes

The author of this plan ran the following self-review pass before handing it off:

1. **Spec coverage.** Each Phase 1 deliverable in design spec Section 10 maps to a task: `jama_client.auth` → Tasks 3–4, `jama_client.client` → Tasks 5–8, six client methods → Tasks 6–8, six MCP tools → Tasks 13–17, integration suite → Task 19, README updates → Task 20.
2. **Placeholder scan.** No "TBD", "implement later", "fill in details", or hand-waved error handling. Every test step shows the failing assertion; every implementation step shows the actual code.
3. **Type consistency.** `JamaClient.search_items(project_id: int, query: str)` is the same signature in the client (Task 7), the test (Task 7), and the MCP tool (Task 15). `get_item` raises `JamaNotFoundError` in the client (Task 7) and is caught by the same name in the tool (Task 14). Pydantic models use snake_case attributes consistently across model definitions, validation tests, mocks, and dump assertions.
4. **One acknowledged risk:** the Jamacloud REST endpoint URLs in the "Endpoint assumptions" table are canonical-best-effort but unverified against the live sandbox. Task 19 explicitly tests this and Step 4 of that task documents the correction loop. This is the right place to discover the truth — the unit-test fixtures are mocks anyway, so a wrong URL costs only the integration test cycle, not user time.
