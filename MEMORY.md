# Jama MCP Server — Working State

## Current phase

**Maintenance mode for Phases 0–2.** Phases 0–2 complete; **orchestration-layer pivot pending** (Use Cases 1 & 2 from Preston Mitchell at Jama Software). Fresh-session brainstorming via `superpowers:brainstorming` is the next step. Strategic framing in `docs/internal/jama-poc-strategic-positioning.md` (gitignored).

**Active branch:** `main`
**Open PR:** none
**Most recent merge:** [PR #7](https://github.com/arthurfantaci/jama-mcp-server/pull/7) — Phase 2 Docker containerization (squash-merged 2026-04-30, merge commit `b4b8f7e`)

**Verifiable end state:** the streamable-HTTP MCP server runs via `docker compose -f docker/docker-compose.yml up -d`, or stdio via `uv run jama-mcp-stdio`. Live MCP integration verified 2026-05-01 — both Claude Code (stdio) and Claude Desktop (stdio, configured 2026-05-02) invoke all six read-only tools end-to-end against `pm2.jamacloud.com`; full traceability flow demonstrated against the Smart Thermostat sample dataset in project 127 ("Arthur Sandbox").

## Phase status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Repository scaffolding, CI/CD, memory hygiene apparatus | Complete |
| 1 | Functional MVP — six client operations + six MCP tools, both transports | Complete (PR #5 merged 2026-04-29) |
| 2 | Docker containerization | Complete (PR #7 merged 2026-04-30) |
| 4.5 | `create_comment` write tool — narrow Phase 4.5 carve-out for compliance-agent runtime | Complete (PR #10 merged 2026-05-02, merge commit `6e28b9f`) |

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

**Phase 4.5 — `create_comment` write tool:**

- **`Comment` Pydantic model** in `src/jama_client/models.py` (nested `body` and `location` fields per Jama's request schema).
- **`JamaClient._request` extension** — accepts optional `json_body` parameter and treats both HTTP 200 and HTTP 201 as success. Shared retry/auth/envelope logic applies uniformly across read and write paths.
- **`JamaClient._parse_envelope` loosened** — permits `data`-less envelopes when caller passes `return_envelope=True`. Required because Jama's `POST /comments` returns a `meta`-only response with no `data` field.
- **`JamaClient.create_comment(item_id, project_id, body, *, in_reply_to=None, comment_type="GENERAL")`** posts to `POST /rest/latest/comments` with the canonical Jama nested shape. `inReplyTo` is omitted entirely for top-level comments (sending `0` triggers a server-side NPE on Jamacloud). Returned `Comment` is synthesised from the new ID plus inputs because the POST response is `meta`-only.
- **`@server.tool() create_comment(ctx, item_id, project_id, body, comment_type="GENERAL")`** in `tools.py` — same shape as read tools; HITL checkpoint is the orchestrating skill's responsibility, not the server's. Accepts any of Jama's eight `commentType` enum values (`GENERAL`, `QUESTION`, `PROPOSED_CHANGE`, `ACCEPTED_COMMENT`, `REJECTED_COMMENT`, `ISSUE`, `DECISION`, `DECISION_REQUEST`); compliance-review workflows should use `ISSUE` for non-compliant findings.
- **Tests** — 91 unit/protocol tests passing (Phase 1+2's 84 + 7 for `create_comment`: happy path, threaded reply, non-default comment_type, missing-id error, non-dict response error, MCP-tool default, MCP-tool ISSUE pass-through). Live integration test gated on `JAMA_INTEGRATION_COMMENT_ITEM_ID` + `JAMA_INTEGRATION_COMMENT_PROJECT_ID`; leaves a timestamped self-identifying comment behind. Verified live against `pm2.jamacloud.com` item 114270 (project 127) before merge.

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
| 2026-04-30 | Phase 2 design decisions sanctioned (slim runtime + uv builder multi-stage; `/health` route via `FastMCP.custom_route`; healthcheck duplicated between Dockerfile and Compose; build-only CI with GHA buildx cache; no separate Phase 2 spec doc) | Local-dev/demo target favors slim's debug ergonomics over distroless minimum-attack-surface; full pattern set codified in `CLAUDE.md` Phase 2 conventions section and KG entity `Phase 2 Docker Containerization (Jama MCP Server)` |
| 2026-04-30 | Phase 2 PR #7 squash-merged to main; all 6 CI checks green; Issue #6 auto-closed; merge commit `b4b8f7e` | Phase 2 closed. MCP Inspector smoke confirmed live `whoami` invocation against `pm2.jamacloud.com` from the containerized server before PR open |
| 2026-05-01 | Phase 3 (Kubernetes / Minikube) descoped; project entered maintenance mode at end of Phase 2; engineering record at git tag `archive/phase-3-attempt-2026-05-01`; Issue #8 closed; docs updated on main in commit `2daa6e7` | FastMCP's user `lifespan=` does not run at HTTP server startup in streamable-HTTP mode (only per-MCP-session). Architectural mitigations intersected with a Calico CNI startup race and an Apple Virtualization.framework watchdog kernel panic on macOS 26.5 (Tahoe) under sustained Docker Desktop + Minikube load. KG entities `Phase 3 K8s Deployment Attempt (Jama MCP Server, descoped)`, `FastMCP HTTP Lifespan Gotcha`, `macOS Tahoe Docker Desktop Hypervisor Watchdog Panic` preserve the insights |
| 2026-05-01 | MCP integration verification — Jama MCP server registered via `claude mcp add jama-mcp-server` (stdio); live demonstration against `pm2.jamacloud.com` exercised all six tools end-to-end (whoami → list_projects → search_items → get_item → get_downstream_relationships → get_test_runs_for_item); 404 asymmetry on `get_item` and 401-vs-404 distinction on cross-project items both validated under live conditions; KG entity `Jamacloud per-item authorization scoping` (gotcha) added with relations to project + Two-Layer Error Policy pattern; navigation blind spot identified (no `get_children` tool) | Closes Phase 2's "Verifiable end state" against a real Jamacloud sandbox; surfaces one cross-project gotcha worth preserving; identifies one specific tool gap as the natural Phase 4 candidate |
| 2026-05-02 | Strategic pivot: do **NOT** build Phase 5 (write tools); pivot next chapter to **orchestration layer**. Triggered by (a) Jama Software shipping their own official Jama MCP Server, (b) two use cases received from Preston Mitchell at Jama Software (Software Engineer requirement→code trace; System Engineer AI compliance officer agent), (c) anticipated access to the Jama-hosted official MCP server within 2-5 days. Planned scope: (i) one small read-side addition (`get_children`, possibly `get_comments`); (ii) `.claude/skills/jama-trace/SKILL.md` + `.claude/skills/jama-compliance-review/SKILL.md`; (iii) Agent Team templates for the compliance reviewer; (iv) documentation of the composition pattern. Strategic positioning doc at `docs/internal/jama-poc-strategic-positioning.md` (gitignored). Claude Desktop also configured with the Jama MCP server | Avoids reinventing what the vendor now ships; positions the PoC as a reference architecture for agentic Jama workflows rather than a competing implementation; both use cases ship as read-only proof-of-shape during the 2-5 day window, then close the loop via the official MCP's write tools when access is granted |
| 2026-05-02 | Phase 4.5 PR #10 squash-merged to main; all 6 CI checks green (Lint, Dependency Review, Test, Mypy strict, codecov/patch, Docker build); Issue #9 auto-closed; merge commit `6e28b9f`. Live-integration smoke against `pm2.jamacloud.com` item 114270 confirmed write path before merge. Discovered three undocumented Jama API behaviours during implementation — all codified in CLAUDE.md Phase 4.5 conventions: (1) `inReplyTo: 0` triggers a server-side `NullPointerException` (the Swagger Example Value is misleading; Schema tab confirms the field is optional, must be omitted for top-level); (2) `POST /comments` returns a `meta`-only envelope with no `data` field, so `JamaClient._parse_envelope` was loosened to permit data-less envelopes when `return_envelope=True`, and the returned `Comment` is synthesised from inputs; (3) `commentType` enum has eight values (`GENERAL`, `QUESTION`, `PROPOSED_CHANGE`, `ACCEPTED_COMMENT`, `REJECTED_COMMENT`, `ISSUE`, `DECISION`, `DECISION_REQUEST`); MCP tool exposes `comment_type` parameter so Persona 2 can emit `ISSUE`-typed findings rather than generic `GENERAL` comments. Also confirmed: no `DELETE /comments/{id}` endpoint exists in Jama's REST API — write-test artifacts must be cleaned via Jama UI | Phase 4.5 closed. Comments are additive-only (no delete, no modify after write) so the AI-safety blast radius is much smaller than `create_item`/`update_item`/`delete_item`. This special-case carve-out does NOT reverse the broader 2026-05-02 strategic decision to defer Phase 5's full write surface to the official Jama MCP Server. If the official MCP also exposes comment creation when access lands, this tool can be deprecated in favour of composition |

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
