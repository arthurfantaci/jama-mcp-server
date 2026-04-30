# Jama MCP Server — Working State

## Current phase

**Phase 3 — Kubernetes deployment (Minikube) (planned, not yet started)**

**Active branch:** `main`
**Open PR:** none
**Most recent merge:** [PR #7](https://github.com/arthurfantaci/jama-mcp-server/pull/7) — Phase 2 Docker containerization (squash-merged 2026-04-30, merge commit `b4b8f7e`)

**Next action:** open Phase 3 tracking issue and create `feat/phase-3-minikube` branch when ready to begin K8s work. The `/health` endpoint and fixed UID/GID 1001 already in place specifically to support Phase 3's liveness/readiness probes and `securityContext.runAsUser`.

## Phase status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Repository scaffolding, CI/CD, memory hygiene apparatus | Complete |
| 1 | Functional MVP — six client operations + six MCP tools, both transports | Complete (PR #5 merged 2026-04-29) |
| 2 | Docker containerization | Complete (PR #7 merged 2026-04-30) |
| 3 | Kubernetes deployment (Minikube) | Planned |

## Surface delivered

**Phase 1 — application layer:**

- **`jama_client`** — async REST client, OAuth credentials/token cache, six operations (`get_current_user`, `list_projects`, `get_item`, `search_items`, `get_downstream_relationships`, `get_test_runs_for_item`), Pydantic v2 models, typed exceptions.
- **`jama_mcp_server`** — `Settings` (pydantic-settings), transport-aware `configure_logging`, FastMCP `build_server`/`jama_lifespan`, six `@server.tool()` closures, two transport entry points (`main_stdio`, `main_http`), `__main__.py` dispatcher.
- **Tests** — 84 unit/protocol tests passing, 0 warnings; integration suite verified against `pm2.jamacloud.com` (whoami + list_projects passed live; get_item gated on `JAMA_KNOWN_ITEM_ID`).

**Phase 2 — containerization:**

- **`docker/Dockerfile`** — multi-stage `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` builder + `python:3.12-slim-bookworm` runtime, non-root UID/GID 1001, Python-stdlib `urllib` HEALTHCHECK on `/health` (no curl install). Image size 266 MB.
- **`docker/docker-compose.yml`** — single-service compose, explicit `name: jama-mcp-server`, env_file integration with `../.env`, inline `environment:` block overrides `MCP_TRANSPORT`/`MCP_HTTP_HOST`/`MCP_HTTP_PORT` for the container path.
- **`/health` route** — module-level `_health` async handler in `server.py` registered via `FastMCP.custom_route` before tool registration; covered by `tests/unit/jama_mcp_server/test_server_health.py`.
- **`.dockerignore`** at repo root + **`.github/workflows/docker-build.yml`** — build-only CI with path filters and GHA buildx cache (mode=max). Cold build ~1m on the GHA runner; warm rebuild ~30s.

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

## Sanctioned conventions established during Phase 2

15. **`_health` handler is module-level**, not a closure inside `build_server`. Registered imperatively via `server.custom_route("/health", methods=["GET"])(_health)` before tools so the route is available the moment streamable-HTTP starts. Module-level placement makes it directly unit-testable without exercising the lifespan or `JamaClient`.
16. **Multi-stage Dockerfile uses two-step `uv sync`** — Layer 1 (`COPY pyproject.toml uv.lock`) runs `uv sync --frozen --no-install-project --no-dev`; Layer 2 (`COPY README.md ./` then `COPY src/`) runs `uv sync --frozen --no-dev`. README.md is required in Layer 2 because `pyproject.toml` declares `readme = "README.md"` and hatchling reads it during package-metadata validation.
17. **`UV_LINK_MODE=copy`** in the builder is required for cross-stage `COPY --from=builder` to work cleanly across Docker's union FS (hardlinks don't survive cross-stage copy).
18. **`.dockerignore` at REPO ROOT** (not `docker/`) — Docker reads `.dockerignore` relative to the build context root, which compose sets to `..` via `context: ..`.
19. **Healthcheck duplicated between Dockerfile `HEALTHCHECK` and compose `healthcheck`** — intentional defense for `docker run` users without compose. Same Python-stdlib `urllib` probe in both. Future maintenance must keep them in sync.
20. **`name: jama-mcp-server`** at the top of `docker/docker-compose.yml` — without it, Compose derives the project name from the parent directory (`docker`), producing ugly identifiers like `docker-jama-mcp-server-1`.

## Plan corrections applied inline

The Phase 1 plan at `docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md` was updated inline at Tasks 3, 4, 8, 9, 11, 12, 13. The Phase 2 plan at `docs/superpowers/plans/2026-04-30-jama-mcp-server-phase-2-docker.md` was corrected inline at Task 3 (commit `27c6f64`: added `COPY README.md ./` before `COPY src/` in the builder stage). Future re-runs should read HEAD's plan, not the original commit. Notable corrections:

- Phase 1 Task 11: `transport: Transport` → `transport: str`; dropped unused `Transport` alias and `Literal` import.
- Phase 1 Task 12: `host`/`port` moved to `FastMCP.__init__`; tightened lazy-import noqa from `F401, PLC0415` to `PLC0415`.
- Phase 1 Task 13: `Context` runtime import + `_Context` alias; synthetic-context test pattern + `result[1]` indexing.
- Phase 2 Task 3: `COPY README.md ./` added before `COPY src/`. Without it, `uv sync --frozen --no-dev` fails at Layer 2 with `OSError: Readme file does not exist` because hatchling reads `pyproject.toml`'s `readme` field during project install.

## Recent decisions

Older Phase 0/1 decisions (architectural approach, Python 3.12, FastMCP both transports, Pydantic alias generator, 403 mapping, `Context` runtime import, etc.) are now codified in `CLAUDE.md`'s conventions sections and removed from this rolling table.

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-29 | `get_test_runs_for_item` endpoint corrected from `/items/{id}/testruns` to `/testruns?testCase={id}` | Discovered during MCP Inspector smoke at Phase 1 closure; the path-style endpoint returns 404 even for known items |
| 2026-04-29 | Phase 1 PR #5 squash-merged to main; CI green across all 5 checks | Phase 1 closed |
| 2026-04-30 | Refreshed KG protocol tool names in `~/.claude/CLAUDE.md` (`search_nodes` → `search_memories`); repaired two typeless KG entities | mcp-neo4j-memory API rename had drifted the global protocol prose; typeless entities were blocking `search_memories` with a Pydantic validation error |
| 2026-04-30 | Phase 2 split across three Claude Code sessions (hygiene → plan-writing → execution) | Controller-context discipline (cf. 2026-04-29 Phase 1 Tasks 9/10 split). Each session ended with a copy-paste-ready prompt for the next per the global Session Handoff Protocol |
| 2026-04-30 | Phase 2 base image: `python:3.12-slim-bookworm` runtime + `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` builder, multi-stage with venv copy across stages | Local-dev/demo target favors slim's debug ergonomics over distroless's minimum attack surface; uv builder image gives lockfile-pinned dependencies end-to-end and matches local-dev tooling exactly |
| 2026-04-30 | Phase 2 healthcheck: add `/health` route via `FastMCP.custom_route` + Python stdlib urllib probe | Stable probe semantics (vs probing /mcp with awkward 4xx-as-alive); no curl install needed; future-proofs Phase 3 K8s liveness/readiness probes which will reuse the same endpoint |
| 2026-04-30 | Phase 2 CI: build-only on PR + main with path filters + GHA buildx cache | Catches Dockerfile drift cheaply (~30s warm rebuild, ~1m cold); image push deferred to Phase 3 when a deployment consumer (Minikube) justifies registry permissions and a tag strategy |
| 2026-04-30 | Phase 2 spec doc: no new spec written; decisions live in plan + this MEMORY.md | Existing design spec Section 10 sanctions deliverables; plan-author decisions belong in the implementation plan as task-level rationale, with an index-row summary here. Matches Phase 1's pattern (no separate decisions doc) |
| 2026-04-30 | Phase 2 PR #7 squash-merged to main; all 6 CI checks green (Lint, Dependency Review, Test, Mypy strict, codecov/patch, Docker build); Issue #6 auto-closed; merge commit `b4b8f7e` | Phase 2 closed. Docker build CI ran cold in 1m0s on the GHA runner. MCP Inspector smoke confirmed live `whoami` invocation against `pm2.jamacloud.com` from the containerized server before PR open |

## Known constraints

- **Repository visibility:** public on GitHub; reviewed by potential employers including Jama Software. Every commit must meet professional standards.
- **OAuth credential discipline:** dedicated `jama-mcp-server-dev` credential (not reused).
- **Sandbox URL:** `https://pm2.jamacloud.com`.
- **Author identity:** Arthur Fantaci, `arthur.fantaci@mac.com`.

## References

- Design spec: [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md)
- Phase 2 plan (live; updated inline at Task 3): [`docs/superpowers/plans/2026-04-30-jama-mcp-server-phase-2-docker.md`](docs/superpowers/plans/2026-04-30-jama-mcp-server-phase-2-docker.md)
- Phase 1 plan (live; updated inline): [`docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md`](docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md)
- Phase 0 plan: [`docs/superpowers/plans/2026-04-28-jama-mcp-server-phase-0-initialization.md`](docs/superpowers/plans/2026-04-28-jama-mcp-server-phase-0-initialization.md)
- Conventions: [`CLAUDE.md`](CLAUDE.md)
- Author's global Claude Code protocols: `~/.claude/CLAUDE.md`
