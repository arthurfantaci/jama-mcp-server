# Jama MCP Server — Claude Code Instructions

## Project overview

Model Context Protocol server providing access to Jamacloud (Jama Connect SaaS) via its REST API. Two-layer architecture: `jama_client` (async REST client) and `jama_mcp_server` (FastMCP server). Phase 1 MVP exposes six tools demonstrating requirements-to-test-runs traceability.

Full design: [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md).

## Repository visibility

This repository is public on GitHub from inception and is reviewed by potential employers, including Jama Software engineers and their hiring managers. Every committed file must portray the project, the author, and the role of AI-assisted development as serious, professional Agentic AI Application Engineering work.

**Mechanical enforcement:**

- `.claude/hooks/validate-docs-placement.sh` warns on staged docs containing internal markers.
- `gitleaks` (pre-commit) scans every commit for staged credentials.
- `docs/internal/` and `docs/plans/` are gitignored escape hatches for working notes.
- The PR template includes a "Professional Portrayal" checklist.

**Excluded from public surface:** debug `print` statements, commented-out code, AI-collaboration artifacts (e.g., narrative comments referencing the assistant by name), scratch files, half-finished thought experiments.

## Project layout

- `src/jama_client/` — async Jamacloud REST client. Owns auth, transport, models, exceptions.
- `src/jama_mcp_server/` — FastMCP server, tool definitions, transport entry points, lifespan management.
- `tests/{unit,integration}/` — three-tier test suite (unit, integration, MCP-protocol).
- `docker/` — Phase 2 containerization: `Dockerfile` (multi-stage, uv builder + slim runtime, non-root UID 1001) and `docker-compose.yml` (single-service, env_file + transport overrides, port 8765, healthcheck on `/health`).
- `.github/workflows/` — CI: Lint, Mypy strict, Test, Dependency Review, codecov, and Phase 2's Docker build (build-only, GHA buildx cache).
- `docs/superpowers/specs/` — design specifications.
- `docs/superpowers/plans/` — implementation plans.

## Conventions

- **Python 3.12**, managed with `uv`. `uv.lock` is committed.
- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `ci:`.
- **Issue → Branch → PR** for all phases after Phase 0.
- **Documentation-only changes do NOT get separate issues, branches, or PRs.** Bundle into the next phase's PR or commit directly to the working branch.
- **Async throughout.** New code in `jama_client` and `jama_mcp_server` is async by default.
- **Type annotations and Google-style docstrings on every public surface.** Enforced by ruff `ANN` and `D` rules.
- **Errors map to typed exceptions** per the two-layer policy in the design spec.

## Phase 1 conventions codified

Patterns discovered or sanctioned during Phase 1. Apply uniformly to new code.

- **Pydantic v2 entity models** inherit `_JamaModel` with `alias_generator=to_camel`, `populate_by_name=True`, `extra="allow"`, `serialize_by_alias=False`. Never write per-field `Field(alias=...)`. `model_dump()` returns snake_case (the AI tool surface).
- **MCP tools return snake_case via `model.model_dump()`**; do not pass `by_alias=True`.
- **`get_item` translates 404 to `{"found": False, "item_id": id, "message": ...}`**; all other tools propagate exceptions to FastMCP. The asymmetry is documented in `tools.py`'s module docstring.
- **`Context` is a runtime import in `tools.py`**, not under `TYPE_CHECKING`. FastMCP's tool registration calls `typing.get_type_hints()` against module globals; a TYPE_CHECKING-only import raises `NameError`. `_Context = Context[Any, Any, Any]` is the canonical alias on tool function signatures.
- **MCP-tool unit tests** use a synthetic `RequestContext` (`_make_context` helper) with `lifespan_context={"jama_client": mock_client}`, then `patch.object(server, "get_context", return_value=ctx)` before `await server.call_tool(...)`. FastMCP v1.27+ returns a `(unstructured, structured)` tuple — assert against `result[1]` (or `result[1]["result"]` for list-returning tools).
- **`FastMCP.__init__(host=..., port=...)`** — host/port go on the constructor, not `run()`. Verified via `inspect.signature(FastMCP.__init__)`.
- **403 → `JamaForbiddenError`**, 401 → `JamaAuthError`. Both `fetch_token` and `_request._raise_for_status` distinguish.
- **`__test__ = False`** on domain classes whose names start with `Test` (e.g., `TestRun`) to suppress pytest collection warnings.
- **`asyncio.sleep` patching** in retry tests (`tests/unit/jama_client/test_client_transport.py` patches `jama_client.client.asyncio.sleep`) keeps suite runtime under 0.2s. Apply to any future retry tests.
- **Shared fixtures in `tests/conftest.py`**: `jama_credentials`, `jama_base_url`, `jama_token_url`, `jama_token_stub` (client tests), `mock_jama_client` (MCP-tool tests). No local `_creds()` / `_BASE_URL` helpers in unit-test files. Integration tests use raw `os.environ` directly (different domain, sanctioned).
- **`from __future__ import annotations`** on every `.py` (project-wide).
- **`-> NoReturn`** on functions that always raise.
- **Lazy import inside `build_server`**: `from jama_mcp_server import tools  # noqa: PLC0415` — intentional to avoid import cycles.

## Phase 2 conventions codified

Patterns discovered or sanctioned during Phase 2 (Docker containerization). Apply uniformly to new code that touches the deployment surface.

- **`_health` is module-level**, not a closure inside `build_server`. Registered imperatively via `server.custom_route("/health", methods=["GET"])(_health)` BEFORE tool registration so the route is available the moment streamable-HTTP starts accepting connections. Module-level placement also makes the handler directly unit-testable without exercising the lifespan or `JamaClient`.
- **Multi-stage Dockerfile uses two-step `uv sync`.** Layer 1 (`COPY pyproject.toml uv.lock`) runs `uv sync --frozen --no-install-project --no-dev`. Layer 2 (`COPY README.md ./` then `COPY src/`) runs `uv sync --frozen --no-dev`. `README.md` MUST be in Layer 2 because `pyproject.toml` declares `readme = "README.md"` and hatchling reads it during package-metadata validation. Without that COPY, the build fails with `OSError: Readme file does not exist`.
- **`UV_LINK_MODE=copy`** in the builder is required for cross-stage `COPY --from=builder` to work across Docker's union FS (hardlinks don't survive cross-stage copy).
- **`.dockerignore` lives at repo ROOT**, not in `docker/`. Compose's `context: ..` makes the build context the repo root, which is where Docker reads `.dockerignore` from.
- **Dockerfile `HEALTHCHECK` and Compose `healthcheck:` are intentionally duplicated** (same Python-stdlib `urllib` probe of `/health`). Compose users get one via the service block; `docker run` users without compose get one via the Dockerfile directive. Future maintenance MUST keep them in sync.
- **`name: jama-mcp-server`** at the top of `docker/docker-compose.yml`. Without it, Compose derives the project name from the compose file's parent directory (`docker`), producing identifiers like `docker-jama-mcp-server-1`.
- **Fixed UID/GID 1001 (`jama` user)** in Dockerfile RUN. Pinned for Phase 3 K8s `securityContext.runAsUser` parity. The `useradd warning: jama's uid 1001 is greater than SYS_UID_MAX 999` in the build log is expected and intentional.
- **Compose `environment:` block overrides `MCP_TRANSPORT`/`MCP_HTTP_HOST`/`MCP_HTTP_PORT`** for the container regardless of `.env`. This lets a user's `.env` set up for native stdio runs work with Docker without edits. `.env.example` documents the precedence so users don't troubleshoot this.
- **Pydantic Settings defaults stay at `mcp_http_host="127.0.0.1"`** (loopback, safe for native runs). The container overrides via the Compose `environment:` block, never via Settings default — protects native runs from accidental LAN exposure.

## Tooling rigor

- **Ruff** (21 rule families): E, W, F, I, N, D, UP, ANN, S, B, C4, SIM, TCH, RUF, TRY, EM, PIE, PT, RET, ARG, PL. Google docstring convention. Per-file relaxations for tests.
- **Mypy strict** (blocking CI check): `strict = true`, pydantic plugin, no implicit reexport.
- **Pytest** with `asyncio_mode = "auto"` and `--strict-markers`.
- **Pre-commit**: ruff, mypy, gitleaks, validate-docs-placement, standard hygiene hooks.

## Verification before PR

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -m "not integration"
```

## Memory hygiene

This project maintains two memory tiers:

- **Public** (in repo, version-controlled): `CLAUDE.md` (this file, ~150 lines max), `MEMORY.md` (~100 lines max), `docs/superpowers/{specs,plans}/`.
- **Private** (per-user): `~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/memory/MEMORY.md` (auto-memory tier with companion fact files), plus the Knowledge Graph via the `memory` MCP server. The user-private project-scoped `CLAUDE.md` is intentionally unused for this project — project conventions live in the public `CLAUDE.md` above; cross-project knowledge lives in the KG.

**Slash commands:**

- `/memory-audit` — invoke the memory-hygiene skill.
- `/pre-compact` — Pre-Compaction Protocol (persist findings, update MEMORY.md).
- `/phase-handoff` — Phase Handoff Protocol (merge PR, clean branches, update memory).

**Triggers** for memory updates: phase completion, new convention codified, non-obvious gotcha discovered, architectural change, approach to auto-compaction, post-PR-merge with path/convention changes.

See [`.claude/skills/memory-hygiene/SKILL.md`](.claude/skills/memory-hygiene/SKILL.md) for the audit checklist.

## Pointers to global protocols

The author's `~/.claude/CLAUDE.md` defines:

- Knowledge Graph Memory Protocol (when to write to KG via `memory` MCP server).
- Context Recovery Protocol (re-establishing state at the receiving end of a fresh session).
- Session Handoff Protocol (commit + MEMORY.md row + copy-paste-ready prompt when deferring work to a fresh session).
- Phase Handoff Protocol (cross-phase memory hygiene).
- Pre-Compaction Protocol (persist findings before auto-compact).

This project follows those protocols; do not duplicate them here.
