# Jama MCP Server — Working State

## Current phase

**Phase 2 — Docker containerization (planned, not yet started)**

**Active branch:** `main`
**Open PR:** none
**Most recent merge:** [PR #5](https://github.com/arthurfantaci/jama-mcp-server/pull/5) — Phase 1 Functional MVP (squash-merged 2026-04-29)

**Next action:** open Phase 2 tracking issue and create `feat/phase-2-docker` branch when ready to begin Docker work.

## Phase status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Repository scaffolding, CI/CD, memory hygiene apparatus | Complete |
| 1 | Functional MVP — six client operations + six MCP tools, both transports | Complete (PR #5 merged 2026-04-29) |
| 2 | Docker containerization | Planned |
| 3 | Kubernetes deployment (Minikube) | Planned |

## Phase 1 surface (delivered)

- **`jama_client`** — async REST client, OAuth credentials/token cache, six operations (`get_current_user`, `list_projects`, `get_item`, `search_items`, `get_downstream_relationships`, `get_test_runs_for_item`), Pydantic v2 models, typed exceptions.
- **`jama_mcp_server`** — `Settings` (pydantic-settings), transport-aware `configure_logging`, FastMCP `build_server`/`jama_lifespan`, six `@server.tool()` closures, two transport entry points (`main_stdio`, `main_http`), `__main__.py` dispatcher.
- **Tests** — 83 unit/protocol tests passing, 0 warnings; integration suite verified against `pm2.jamacloud.com` (whoami + list_projects passed live; get_item gated on `JAMA_KNOWN_ITEM_ID`).

## Sanctioned conventions established during Phase 1

These are codified across the codebase, plan, and tests. Do not undo or re-litigate.

1. **Pydantic v2 alias generator.** `_JamaModel` uses `alias_generator=to_camel`, `populate_by_name=True`, `extra="allow"`, `serialize_by_alias=False`. Per-field `Field(alias=...)` is forbidden. `model_dump()` returns snake_case for AI tool responses.
2. **`__test__ = False`** on domain classes whose names start with `Test` (currently `TestRun`) to suppress pytest collection warnings.
3. **403 → `JamaForbiddenError`**, 401 → `JamaAuthError`. Both `fetch_token` and `_request._raise_for_status` distinguish.
4. **Retry tests patch `asyncio.sleep`** in `jama_client.client.asyncio.sleep` so suite runtime stays under 0.2s. Same pattern applies to any future retry-policy tests.
5. **Shared fixtures in `tests/conftest.py`**: `jama_credentials`, `jama_base_url`, `jama_token_url`, `jama_token_stub` (client tests), `mock_jama_client` (MCP-tool tests). No local helpers in test files.
6. **`_validate(model_cls, payload)` static helper** with `TypeVar("_M", bound=BaseModel)` is the canonical Pydantic-validation translator on `JamaClient`.
7. **`Context` is a runtime import**, not TYPE_CHECKING. FastMCP's tool registration uses `typing.get_type_hints()` which resolves string annotations at runtime. `_Context = Context[Any, Any, Any]` alias satisfies mypy strict's `[type-arg]`. `JamaClient` and `FastMCP` stay under TYPE_CHECKING.
8. **MCP-tool tests use synthetic `RequestContext` + `patch.object(server, "get_context", return_value=ctx)`** to inject the lifespan dict. FastMCP v1.27+ `call_tool` returns a `(unstructured, structured)` tuple; tests assert `result[1]` (or `result[1]["result"]` for list-returning tools).
9. **`get_item` translates `JamaNotFoundError` to `{"found": false, item_id, message}`**; all other tools propagate exceptions normally. The asymmetry is documented in the `tools.py` module docstring.
10. **`from __future__ import annotations`** on every `.py` (project-wide; inert on 3.12 but retained).
11. **`-> NoReturn`** on functions that always raise (e.g., `JamaClient._raise_for_status`).
12. **`logging_config.configure_logging(transport: str)`** — parameter is `str`, not `Literal`. Mypy strict's `warn_unreachable` flagged the `else` branch as unreachable under a Literal. The third test (`test_unknown_transport_raises_value_error`) needs to exercise that branch with a non-Literal value.
13. **`FastMCP.__init__(host=..., port=...)`** — host/port are constructor arguments, not `run()` arguments. Verified via `inspect.signature(FastMCP.__init__)`.
14. **Tool closures in `register()`** — six `@server.tool()` closures inside one `register()` function. Lazy-import `tools` inside `build_server` (with `# noqa: PLC0415`) avoids import cycles.

## Plan corrections applied inline

The Phase 1 plan at `docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md` was updated inline at Tasks 3, 4, 8, 9, 11, 12, 13. Future re-runs should read HEAD's plan, not the original at `c402be1`. Notable corrections beyond Tasks 1–9:

- Task 11: `transport: Transport` → `transport: str`; dropped unused `Transport` alias and `Literal` import.
- Task 12: `host`/`port` moved to `FastMCP.__init__`; tightened lazy-import noqa from `F401, PLC0415` to `PLC0415`.
- Task 13: `Context` runtime import + `_Context` alias; synthetic-context test pattern + `result[1]` indexing.

## Recent decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-28 | Approach 1 (two-layer split) approved | Clean separation; client lib reusable later |
| 2026-04-28 | Python 3.12; mypy strict; Apache 2.0 | Compatibility, maturity signal, contributor-friendly |
| 2026-04-28 | Public GitHub from Day 1 | Public engineering deliverable from inception |
| 2026-04-28 | FastMCP both transports (stdio + streamable-http) | Same module supports both |
| 2026-04-29 | Pydantic alias generator over per-field aliases | Idiomatic; avoids `N815` ruff rule on camelCase attrs |
| 2026-04-29 | `403 → JamaForbiddenError` (not `JamaAuthError`) | Operational distinction: 403 = scope/permission; 401 = bad credentials |
| 2026-04-29 | Phase 1 split across multiple sessions at Tasks 9/10 boundary | Controller context stays tight |
| 2026-04-29 | `Context` runtime import + synthetic-context test pattern | FastMCP's `get_type_hints` requires runtime presence; `call_tool` returns a tuple |
| 2026-04-29 | Six MCP tools landed; live OAuth flow validated against `pm2.jamacloud.com` | Phase 1 feature-complete |
| 2026-04-29 | `get_test_runs_for_item` endpoint corrected from `/items/{id}/testruns` to `/testruns?testCase={id}` | Discovered during MCP Inspector smoke; Task 19 Step 4 sanctioned correction loop |
| 2026-04-29 | Phase 1 PR #5 squash-merged to main; CI green across all 5 checks | Phase 1 closed |

## Known constraints

- **Repository visibility:** public on GitHub; reviewed by potential employers including Jama Software. Every commit must meet professional standards.
- **OAuth credential discipline:** dedicated `jama-mcp-server-dev` credential (not reused).
- **Sandbox URL:** `https://pm2.jamacloud.com`.
- **Author identity:** Arthur Fantaci, `arthur.fantaci@mac.com`.

## References

- Design spec: [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md)
- Phase 1 plan (live; updated inline): [`docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md`](docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md)
- Phase 0 plan: [`docs/superpowers/plans/2026-04-28-jama-mcp-server-phase-0-initialization.md`](docs/superpowers/plans/2026-04-28-jama-mcp-server-phase-0-initialization.md)
- Conventions: [`CLAUDE.md`](CLAUDE.md)
- Author's global Claude Code protocols: `~/.claude/CLAUDE.md`
