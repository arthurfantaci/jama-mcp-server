# Jama MCP Server — Working State

## Current phase

**Phase 1 — Functional MVP (in progress, Tasks 1–9 of 22 complete)**

**Active branch:** `feat/phase-1-functional-mvp`
**Latest commit:** `8436d5a` (Task 9 — `feat(jama_client): expose public package surface`)
**Open PR:** none yet (opens at Task 22)
**Tracking issue:** [#4](https://github.com/arthurfantaci/jama-mcp-server/issues/4)

**Next task:** Task 10 — `Settings` configuration (start of `jama_mcp_server` layer).

## Phase status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Repository scaffolding, CI/CD, memory hygiene apparatus | Complete |
| 1 | Functional MVP — six client operations + six MCP tools, both transports | In progress (jama_client done; jama_mcp_server pending) |
| 2 | Docker containerization | Planned |
| 3 | Kubernetes deployment (Minikube) | Planned |

## Phase 1 progress

- ✅ Tasks 1–9 (jama_client layer): exceptions, models + fixtures, OAuth (credentials/token/cache/fetch_token), JamaClient transport + retry policy, all six operations (`get_current_user`, `list_projects`, `get_item`, `search_items`, `get_downstream_relationships`, `get_test_runs_for_item`), public package surface re-exports.
- ⏳ Tasks 10–22 (jama_mcp_server layer + verification): Settings, logging, FastMCP lifespan, six `@mcp.tool()` functions, protocol smoke tests, integration suite, README/docs, final verification + PR.

**Test count after Task 9:** 64 passing, 0 warnings, 0 integration tests run yet.

## Pre-flight status (all done; new session can skip)

- ✅ Phase 1 GitHub issue #4 open
- ✅ `feat/phase-1-functional-mvp` branch created
- ✅ Baseline checks green at branch creation
- ✅ `.env` populated with OAuth credentials (per user 2026-04-29) — unblocks Tasks 19 + 22

## Sanctioned conventions established during Tasks 1–9

These came up during reviews and should be preserved (do NOT undo or re-litigate):

1. **Pydantic v2 serialization.** `_JamaModel` config uses `alias_generator=to_camel`, `populate_by_name=True`, `extra="allow"`, AND `serialize_by_alias=False` (so `model_dump()` returns snake_case for AI tool responses). Per-field `Field(alias=...)` is forbidden — use the alias generator.
2. **Pytest collection guard.** Domain classes whose names start with `Test` (currently only `TestRun`) carry `__test__ = False` to suppress pytest's `PytestCollectionWarning`. Apply this idiom to any new `Test*` model classes.
3. **403 → `JamaForbiddenError`.** Both `fetch_token` and `_request._raise_for_status` correctly distinguish 401 (`JamaAuthError`) from 403 (`JamaForbiddenError`). Don't conflate them.
4. **`asyncio.sleep` patching in retry tests.** `tests/unit/jama_client/test_client_transport.py` patches `jama_client.client.asyncio.sleep` in retry tests so suite runtime stays under 0.2s. Continue this pattern for any future retry-policy tests (e.g., MCP-layer retries).
5. **Shared test fixtures in `tests/conftest.py`.** `jama_credentials`, `jama_base_url`, `jama_token_url`, `jama_token_stub` are the canonical fixtures for `respx`-mocked client tests. Do NOT reintroduce local `_creds()` / `_BASE_URL` helpers in new test files. For MCP-tool tests (Task 13+), add a `mock_jama_client` fixture using the same naming pattern.
6. **`_validate(model_cls, payload)` static helper** with `TypeVar("_M", bound=BaseModel)` is the canonical Pydantic-validation translator on `JamaClient`. Reuse it for any model coming from `_request`.
7. **Pagination docstring.** All 4 list-returning client methods share the same Phase-2-forward-looking pagination disclosure paragraph. Keep this verbatim across new list-returning surfaces (e.g., MCP tool docstrings).
8. **`from __future__ import annotations` is project convention** — retained on every `.py` even though inert on 3.12. Do not strip via UP rules.
9. **`-> NoReturn`** on functions that always raise (e.g., `JamaClient._raise_for_status`). Tighten any new always-raise function's annotation.
10. **`asyncio.sleep` patching, fixtures, `__test__`, alias generator** are codified in Task 21's CLAUDE.md update.

## Known false positives (do not chase)

- **VSCode "Even Better TOML" extension** repeatedly reports the `[tool.ruff.lint]` block (`pyproject.toml` lines 72/110/113) as schema-invalid. The extension's bundled JSON Schema doesn't recognize ruff's nested config. `tomllib.loads()` parses fine; `ruff check` is happy; pre-commit clean. Ignore.
- **markdownlint warnings on `docs/superpowers/plans/2026-04-29-...md`** (MD032, MD031, MD040, MD060, MD010) — pre-existing, not blocked by pre-commit. Triage during Task 21 if desired.

## Plan-vs-reality divergences (the live plan, not `c402be1`, is the source of truth)

The plan file at `docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md` was updated inline during Tasks 3, 4, 8, and 9 (controller-sanctioned). Future re-runs should read HEAD's plan, not the original at `c402be1`. Notable corrections:
- Task 3: `fetch_token` 401/403 split + `JamaForbiddenError` import.
- Task 4: 7th test (`test_fetch_token_raises_unexpected_status`) + 403 test added; total now 14, not the original 12.
- Task 8: `search_items` docstring aligned with `list_projects` (pagination paragraph + section ordering).
- Task 9: `tests/test_smoke.py` (Phase 0 placeholder) deleted; new `tests/unit/test_smoke.py` is the smoke surface.

## `pyproject.toml` test per-file-ignores accumulated (12 entries)

`S101, S105, S106, S311, ANN, B017, D, PLR2004, PT011, ARG, F401, PLC0415` — added incrementally as tasks needed them. Each addition is justified, but Task 21 should review whether `F401` should be scoped to `tests/unit/test_smoke.py` only rather than all `tests/**/*.py`.

## Recent decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-28 | Approach 1 (two-layer split) approved | Clean separation; client lib reusable later |
| 2026-04-28 | Python 3.12 (not 3.13) | Broader compatibility for clone-and-play audience |
| 2026-04-28 | mypy strict (blocking), not ty | Maturity signal — mypy is widely-recognized |
| 2026-04-28 | Apache 2.0 license | Patent grant; contributor-friendly |
| 2026-04-28 | Public GitHub from Day 1 | Public engineering deliverable from inception |
| 2026-04-28 | FastMCP both transports (stdio + streamable-http) | Same module supports both |
| 2026-04-28 | Three-phase deployment plan (P1 code, P2 Docker, P3 K8s) | Clean troubleshooting boundaries |
| 2026-04-28 | Professional portrayal constraint binding via `validate-docs-placement.sh` | Mechanical enforcement |
| 2026-04-29 | Dependabot bumps (#1, #2, #3) merged + Dependency Graph enabled | Phase 0 fully closed |
| 2026-04-29 | Phase 1 split across two sessions at Task 9/10 boundary | Controller context stays tight; jama_client done is a clean handoff seam |
| 2026-04-29 | Pydantic alias generator (`to_camel` + `populate_by_name=True`) over per-field aliases | Idiomatic; avoids `N815` ruff rule on camelCase attributes |
| 2026-04-29 | `403 → JamaForbiddenError` (not `JamaAuthError`) | Operational distinction: 403 = scope/permission wrong; 401 = bad credentials |
| 2026-04-29 | Shared `tests/conftest.py` fixtures established at Task 6 | Avoid duplication across `test_auth.py`, `test_client_transport.py`, `test_client_operations.py` |

## Known constraints

- **Repository visibility:** public on GitHub; reviewed by potential employers including Jama Software. Every commit must meet professional standards.
- **OAuth credential discipline:** dedicated `jama-mcp-server-dev` credential (not reused).
- **Sandbox URL:** `https://pm2.jamacloud.com`.
- **Author identity:** Arthur Fantaci, `arthur.fantaci@mac.com`.

## References

- Design spec: [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md)
- Phase 1 plan (live; updated inline through Task 9): [`docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md`](docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md)
- Phase 0 plan: [`docs/superpowers/plans/2026-04-28-jama-mcp-server-phase-0-initialization.md`](docs/superpowers/plans/2026-04-28-jama-mcp-server-phase-0-initialization.md)
- Conventions: [`CLAUDE.md`](CLAUDE.md)
- Author's global Claude Code protocols: `~/.claude/CLAUDE.md`
