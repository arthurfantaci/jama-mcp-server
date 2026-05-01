# Jama MCP Server — Design Specification

**Document type:** Design specification
**Date:** 2026-04-28
**Status:** Draft pending author approval (Phase 0 deliverable)
**Author:** Arthur Fantaci

This document specifies the architecture, conventions, tooling, and phased delivery plan for the Jama MCP Server, a Model Context Protocol server providing programmatic access to a hosted Jamacloud SaaS instance via its REST API. The specification governs Phase 0 (initialization) directly and frames Phases 1–2 (functional MVP, containerization) at a level sufficient for subsequent implementation planning.

## 1. Project Overview

The Jama MCP Server is a Python application demonstrating Agentic AI Application Engineering through the design, implementation, and deployment of a Model Context Protocol (MCP) server. The server connects authenticated MCP clients (initially Claude Desktop and Claude Code) to a Jamacloud sandbox instance and exposes a curated set of REST API operations as MCP tools.

### Goals

The project pursues three goals in priority order, all framed within Agentic AI Application Design, Development, and Engineering:

1. Establish authenticated, well-typed access to Jamacloud's REST API through a reusable Python client library.
2. Expose a curated set of read operations as MCP tools that demonstrate end-to-end traceability — a flagship Jama Software workflow connecting requirements to test runs.
3. Demonstrate professional Agentic AI engineering capability for paid contract work with Jama Software, Jama Software customers, or both.

### Audience

The repository is public on GitHub from inception and is reviewed by three audiences:

- **Primary:** the author, for ongoing Agentic AI engineering practice.
- **Secondary:** Jama Software Product Development and Application Development engineers who clone and evaluate the repository.
- **Tertiary:** prospective contract employers reviewing the public repository when evaluating engineering capability.

### Non-goals

The following are explicitly excluded from Phases 0 and 1:

- Multi-tenant deployment serving non-author users.
- Write operations against Jamacloud (creation, modification, or deletion of items, relationships, or test runs).
- Comprehensive coverage of the Jamacloud REST API surface; the Phase 1 tool set is intentionally narrow.
- A separate REST or HTTP API service alongside the MCP server.
- Production-grade observability beyond structured logging (Sentry, OpenTelemetry, and structured metrics are deferred).

## 2. Repository Visibility and Professional Portrayal Constraint

### Binding rule

The repository is public from inception and is reviewed by potential employers. Every file in the repository's public surface — source, configuration, documentation, commit messages — must portray the project, the author, and the role of AI-assisted development as serious, professional, and disciplined Agentic AI Application Engineering work.

### What this excludes from the public repository

- Debug `print` statements, commented-out code blocks, and inline markers indicating incomplete work in committed source.
- Author personality artifacts: scratch files, personal task lists, half-finished thought experiments.
- AI-collaboration artifacts: comments narrating how a piece of code was generated, conversation excerpts in code or documentation, attribution comments referencing the assistant by name.
- Empty placeholder files that exist only to structure the project without content.
- Any file whose presence would prompt a reviewer to question the author's discipline or judgment.

### What this includes

- Idiomatic, fully type-annotated, fully docstring'd source code following the conventions in Section 8.
- Design documents, architecture overviews, setup guides, and contributing guides written for an external technical reader.
- Tests with descriptive names and explicit assertions.
- Conventional commit messages with imperative-mood subjects.
- Reproducible build and run instructions.

### Mechanical enforcement

The constraint is enforced through mechanical layers, not author discipline alone:

- **`.claude/hooks/validate-docs-placement.sh`** — a PreToolUse hook on the Bash tool. The hook scans staged markdown files in `docs/` for internal markers and warns to stderr. The rule the hook applies is: *"Would a hiring manager see this as expertise or learning in progress?"*
- **`gitleaks`** — a pre-commit hook scanning every commit for accidentally staged credentials, API tokens, or other sensitive material.
- **`.gitignore` curation** — `docs/internal/` and `docs/plans/` are deliberately gitignored escape hatches for working notes that must not appear in the public repository.
- **PR template checklist item** — *"Reviewed staged files for content that does not meet professional standards."*

### Working-notes escape hatch

The `docs/internal/` directory exists, is gitignored, and is the correct location for raw plans, working notes, exploratory writing, and any content that does not meet the professional-portrayal standard. The same applies to `docs/plans/`. The intent is to provide a frictionless place for in-progress thinking that never enters the public repository.

## 3. Architecture

The project comprises two top-level Python modules in a single source tree, deliberately separated so the lower layer has no dependency on the upper layer:

- **`jama_client`** — an asynchronous Python library wrapping a curated subset of the Jamacloud REST API. Owns authentication, transport, retry policy, response unwrapping, and Pydantic-typed entity models. Has no knowledge of the Model Context Protocol.
- **`jama_mcp_server`** — a FastMCP server that imports `jama_client` and exposes its operations as MCP tools. Owns transport selection (stdio versus streamable HTTP), tool schema generation, lifespan management, and the AI-facing response shaping.

### Reasons for the split

1. The boundary between "talks to Jama" and "talks MCP protocol" is a genuine separation of concerns. A single-file MCP server tangles them and resists testing and refactoring as the surface grows.
2. `jama_client` is reusable independently of the MCP server. A future MCP client application, a command-line utility, or a Jupyter notebook for ad-hoc API exploration can import `jama_client` directly without adopting MCP.
3. The two layers have distinct testing strategies. `jama_client` is tested against `respx`-mocked HTTP responses; `jama_mcp_server` is tested via FastMCP's in-process test client with a mock `jama_client`. Mixing the layers would force every test to mock both transport and protocol simultaneously.

### Single project, single source tree

The two modules ship from one `pyproject.toml`:

```text
src/
├── jama_client/
└── jama_mcp_server/
```

A `uv` workspace with two separately-published packages is mechanically achievable later if `jama_client` is published to PyPI independently. Premature workspace setup adds tooling friction without current benefit, and the architectural boundary is already enforced by Python's import system across the two top-level packages.

## 4. Component Breakdown

### `src/jama_client/`

- `__init__.py` — public API surface; re-exports `JamaClient`, the exception hierarchy, and the entity models.
- `auth.py` — OAuth 2.0 client_credentials grant. Implements `OAuthCredentials` (immutable configuration), `Token` (access token plus expiry), `TokenCache` (in-memory cache with proactive refresh at or above 90 percent of TTL), and `fetch_token(creds, http)` (the wire call to `/rest/oauth/token`).
- `client.py` — the `JamaClient` class. Async context manager wrapping `httpx.AsyncClient`. Owns the `TokenCache`. Internal `_request()` handles authorization header injection, response envelope unwrapping (`meta` / `links` / `data`), HTTP-status-to-exception mapping, and retry policy. Public methods: `get_current_user()`, `list_projects()`, `get_item(item_id)`, `search_items(project_id, query)`, `get_downstream_relationships(item_id)`, `get_test_runs_for_item(item_id)`.
- `exceptions.py` — the `JamaError` base class and subclasses: `JamaAuthError` (401), `JamaForbiddenError` (403), `JamaNotFoundError` (404), `JamaRateLimitError` (429, exposing `retry_after`), `JamaServerError` (5xx), `JamaNetworkError` (transport-level failures), `JamaValidationError` (response shape mismatch).
- `models.py` — Pydantic v2 entity models with `model_config = ConfigDict(extra="allow")` for forward compatibility: `User`, `Project`, `Item`, `ItemFields`, `Relationship`, `RelationshipType`, `TestRun`.

### `src/jama_mcp_server/`

- `__init__.py` — package marker; exports the `mcp` instance for entry-point discovery.
- `server.py` — creates the `FastMCP("jama-mcp-server", lifespan=...)` instance. Defines the `lifespan` async context manager that constructs and tears down a shared `JamaClient`. Provides `main_stdio()` and `main_http()` console-script entry points.
- `tools.py` — six `@mcp.tool()`-decorated async functions. Each tool retrieves the shared `JamaClient` from `ctx.request_context.lifespan_context`, calls the corresponding client method, and returns AI-shaped dictionaries with trimmed fields and predictable structure.
- `config.py` — the `Settings(BaseSettings)` class reading `JAMA_BASE_URL`, `JAMA_OAUTH_CLIENT_ID`, `JAMA_OAUTH_CLIENT_SECRET`, `MCP_TRANSPORT`, `MCP_HTTP_HOST`, and `MCP_HTTP_PORT`. Fails loud at startup if required values are missing.
- `logging_config.py` — `configure_logging(transport: str)` initializes structlog. Logs are written to **stderr** when `transport == "stdio"` (stdout is reserved for the MCP JSON-RPC protocol stream), and to **stdout** when `transport == "streamable-http"` (containers expect logs on stdout).
- `__main__.py` — the `python -m jama_mcp_server` entry point. Reads `MCP_TRANSPORT` from the environment and dispatches to `main_stdio()` or `main_http()`.

## 5. Data Flow

A single tool call traced end-to-end (`get_item(item_id=42)`):

1. **MCP client** sends a `tools/call` JSON-RPC request: `{"name": "get_item", "arguments": {"item_id": 42}}`.
2. **FastMCP** dispatches to the registered tool function.
3. **The tool function** retrieves the shared `JamaClient` from `ctx.request_context.lifespan_context["jama_client"]`.
4. **`JamaClient.get_item(42)`** delegates to `self._request("GET", "/rest/latest/items/42")`.
5. **`_request`** queries the `TokenCache` for a valid access token. If absent or within 10 percent of expiry, it calls `auth.fetch_token()` and stores the result.
6. **`httpx.AsyncClient`** issues `GET https://pm2.jamacloud.com/rest/latest/items/42` with `Authorization: Bearer <token>`.
7. **Response handling** — `_request` checks the HTTP status. Non-2xx maps to a typed `Jama*Error` (`JamaNotFoundError` for 404, `JamaAuthError` for 401, and so on). 2xx unwraps the `meta` / `links` / `data` envelope and returns the `data` payload.
8. **`JamaClient.get_item`** parses the dictionary via `Item.model_validate(data)` and returns the model instance.
9. **The tool function** calls `item.model_dump(mode="json")`, trims fields not relevant to AI consumption, and returns the dictionary.
10. **FastMCP** serializes the dictionary to JSON-RPC and transmits to the MCP client.

## 6. Error Handling Policy

The project applies a two-layer policy that mirrors the conventions in the reference project: the client layer fails loud, and the server layer translates errors based on intent.

### `jama_client` layer

- Non-2xx HTTP responses raise typed exceptions immediately; no swallowing.
- The retry policy is narrow:
  - `JamaRateLimitError` — wait `retry_after` seconds, retry once, raise on second failure.
  - `JamaNetworkError` — exponential backoff, retry up to two times.
  - `JamaServerError` (5xx) — retry once.
  - All other errors — no retry, raise immediately.
- Token refresh is proactive (at or above 90 percent of TTL), not reactive (on 401). A 401 from the API after a fresh token signals a real authorization problem and is not retried.
- Pydantic parse failures raise `JamaValidationError`. A parse failure indicates either Jama schema drift or a model bug; both warrant a loud failure rather than silent coercion.

### `jama_mcp_server` layer

- **Expected absences** (404 from `get_item` and similar) are caught and converted to structured "not found" responses (`{"found": False, "item_id": ..., "message": "..."}`). The AI can reason about these as data, not as tool failures.
- **Actual errors** (authorization, permission, network, server, validation) are re-raised. FastMCP converts them to MCP `tools/call` error responses, which the AI sees as tool failures.
- All caught exceptions are logged via `structlog.get_logger().exception(...)` to preserve tracebacks.

### Configuration errors

Configuration errors fail at startup. `Settings()` instantiation in `config.py` happens outside any try/except. Missing or malformed environment variables produce a `pydantic.ValidationError` at server start, not a 500-equivalent on the first tool call.

## 7. Testing Strategy

The test suite is organized in three tiers with deliberate boundaries.

### Tier 1 — Unit tests (`tests/unit/`)

- Run on every save and in continuous integration.
- No network access, no real API access.
- `respx` mocks `httpx` at the transport layer for `jama_client` tests.
- Pydantic model tests use hand-crafted JSON fixtures stored in `tests/fixtures/jama_responses/` (sanitized samples of real Jama responses), reviewable in pull requests.
- MCP tool tests inject a mock `JamaClient` via the `lifespan` context — the same mechanism the production server uses, so the wiring itself is exercised.
- Coverage target: at least 80 percent for `jama_client`. No fixed target for `jama_mcp_server` since most of it is thin wrapping; the goal is "every error class has at least one test that triggers it."

### Tier 2 — Integration tests (`tests/integration/`)

- Opt-in via `pytest -m integration`.
- Hit the real Jamacloud sandbox at `https://pm2.jamacloud.com`.
- A module-level fixture skips the entire suite if `JAMA_OAUTH_CLIENT_ID` and `JAMA_OAUTH_CLIENT_SECRET` are not present.
- Smoke tests only: `whoami` succeeds, `list_projects` returns at least one project, `get_item(known_id)` returns the expected structure.
- Never run in CI to avoid storing secrets in GitHub Actions.

### Tier 3 — MCP-protocol tests (`tests/unit/jama_mcp_server/test_protocol.py`)

- Use FastMCP's in-process test client to drive the server end-to-end.
- Verify JSON-RPC framing, tool schema generation, and protocol-level error translation.
- Run alongside unit tests.

### Test infrastructure

`pytest` plus `pytest-asyncio` (`asyncio_mode = "auto"`) plus `respx`. Shared fixtures in `tests/conftest.py` provide sample tokens, sample envelope responses, and a mock-client factory.

## 8. Tooling Rigor

### Dependency management

- **Python 3.12** (`requires-python = ">=3.12"`).
- **`uv`** for dependency resolution and lockfile management; `uv.lock` is committed.
- **`hatchling`** as the build backend.

### Linting and formatting — Ruff

Twenty-one lint rule families are enabled: `E`, `W`, `F`, `I`, `N`, `D`, `UP`, `ANN`, `S`, `B`, `C4`, `SIM`, `TCH`, `RUF`, `TRY`, `EM`, `PIE`, `PT`, `RET`, `ARG`, `PL`.

- `D` (pydocstyle) enforces docstrings on every public function, class, and method.
- `ANN` (flake8-annotations) enforces type annotations on every function signature.
- `convention = "google"` for docstring style.
- `line-length = 100`, double-quote string style, four-space indentation.
- Per-file relaxations for `tests/**/*.py`: `S101` (assertions allowed), `D` (docstrings not required), `ANN` (annotations not required), `PLR2004` (magic values in assertions allowed).

### Type checking — mypy strict

- `strict = true` plus `warn_unused_ignores`, `warn_redundant_casts`, `disallow_untyped_defs`, `check_untyped_defs`, `no_implicit_reexport`.
- `plugins = ["pydantic.mypy"]` for Pydantic-aware inference.
- Test directory exempt from strict annotation rules.
- mypy is a **blocking** check in CI, not advisory.

### Pre-commit hooks

- Local-repo `ruff check --fix` and `ruff format` (ensures version consistency between local and CI).
- Local-repo `mypy` (matches CI).
- Local-repo `validate-docs-placement.sh` (memory-hygiene enforcement).
- `gitleaks` for secret scanning.
- `pre-commit/pre-commit-hooks`: `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-added-large-files` (max 1000 KB), `check-merge-conflict`.

### Continuous integration — GitHub Actions

- Triggers on push to `main` and on pull requests targeting `main`.
- Concurrency cancel-in-progress for resource hygiene.
- Jobs:
  - **lint** — `ruff check`, `ruff format --check`.
  - **test** — `pytest --cov` (unit and protocol tests; integration suite excluded by `-m "not integration"`).
  - **type-check** — `mypy src/` (blocking).
  - **dependency-review** — `actions/dependency-review-action@v4` on pull requests.
- Coverage reports uploaded to Codecov.

### Editor and IDE

- `.vscode/settings.json` configures Ruff as the Python formatter, format-on-save, organize-imports-on-save, ruler at 100, Pylance basic type checking, and file associations for `.env` files.
- `.vscode/settings.json` uses `python.venvPath` and `python.venvFolders`, **not** `python.defaultInterpreterPath`. The latter is forbidden by the author's global Claude Code conventions.
- `.vscode/extensions.json` recommends `ms-python.python`, `ms-python.vscode-pylance`, `charliermarsh.ruff`, `ms-python.debugpy`, `tamasfe.even-better-toml`, `mikestead.dotenv`, `eamodio.gitlens`, `usernamehw.errorlens`, and `ms-azuretools.vscode-docker`.
- `.vscode/extensions.json` lists unwanted recommendations: `ms-python.black-formatter`, `ms-python.isort`, `ms-python.flake8` (Ruff replaces all three).
- `.vscode/launch.json` provides debugpy configurations for `jama-mcp-stdio`, `jama-mcp-http`, current test file, and full test suite.

## 9. Memory Hygiene Apparatus

The project maintains two tiers of Claude memory and an explicit hygiene routine for both, integrating with the author's global Claude Code memory protocols.

### Tier 1 — Public memory (in repo, version-controlled)

- `CLAUDE.md` — project conventions, professional-portrayal constraint, pointers to global protocols. Capped at approximately 150 lines.
- `MEMORY.md` — working state: active phase, current branch, current task pointer, recent decisions. Capped at approximately 100 lines.
- `docs/superpowers/specs/` — design documents, including this specification.
- `docs/internal/` — gitignored escape hatch for working notes that must not appear in the public repository.

### Tier 2 — Private memory (per-user, never in repo)

- `~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/CLAUDE.md` — the author's private session instructions.
- `~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/memory/MEMORY.md` — accumulated session learnings.
- Knowledge Graph — Neo4j-backed via the `memory` MCP server. Stores accumulated facts, architectural decisions, and cross-project patterns. Governed by the author's global Knowledge Graph Memory Protocol.

### Hygiene mechanisms

- `.claude/skills/memory-hygiene/SKILL.md` — audit checklist invoked manually or by command. Verifies file references resolve, architecture sections match the codebase, line counts stay under cap, and stale patterns are removed.
- `.claude/hooks/validate-docs-placement.sh` — PreToolUse Bash hook that scans staged markdown for internal markers and warns to stderr. Recommends moving flagged content to `docs/internal/`.
- `.claude/commands/memory-audit.md` — `/memory-audit` slash command invoking the memory-hygiene skill.
- `.claude/commands/pre-compact.md` — `/pre-compact` slash command codifying the Pre-Compaction Protocol from the author's global CLAUDE.md (persist findings to the Knowledge Graph, update `MEMORY.md`, audit file caps).
- `.claude/commands/phase-handoff.md` — `/phase-handoff` slash command codifying the Phase Handoff Protocol (merge PR, clean branches, verify tests, update `MEMORY.md`, update `CLAUDE.md`, invoke memory-hygiene skill).

### Trigger events that require memory updates

- Completion of a development phase (for example, Phase 1 closing).
- Establishment of a new convention or pattern worth codifying.
- Discovery of a non-obvious gotcha that future sessions should not re-discover.
- Architectural changes that invalidate references in `CLAUDE.md`.
- Approach to memory auto-compaction.
- After every PR merge that changes paths, conventions, or core file layout.

## 10. Phase Roadmap

### Phase 0 — Initialization (this session)

**Scope:** repository scaffolding, design specification, CI/CD configuration, memory hygiene apparatus, inception commit, GitHub repository creation.

**Deliverables:**

- `pyproject.toml` with full ruff, mypy, pytest, and coverage configuration.
- Source skeletons under `src/jama_client/` and `src/jama_mcp_server/` — importable modules with one-line responsibility docstrings, no implementation.
- Test skeletons under `tests/{unit,integration}/` with `conftest.py` infrastructure but no test cases.
- Configuration files: `.gitignore`, `.python-version`, `.env.example`, `.editorconfig`, `.markdownlint.jsonc`, `.pre-commit-config.yaml`, `.gitleaks.toml`.
- Editor configuration: `.vscode/{settings.json, extensions.json, launch.json}`.
- GitHub configuration: `.github/workflows/ci.yml`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/*`, `.github/CODEOWNERS`, `.github/dependabot.yml`.
- Documentation: `README.md`, `LICENSE` (Apache 2.0), `CONTRIBUTING.md`, `SECURITY.md`, `docs/setup.md`, this design specification.
- Memory hygiene: `CLAUDE.md`, `MEMORY.md`, `.claude/{settings.json, hooks/validate-docs-placement.sh, skills/memory-hygiene/SKILL.md, commands/{plan,implement,review,test,memory-audit,pre-compact,phase-handoff}.md}`.
- Inception git commit on `main`.
- Public GitHub repository with the inception commit pushed.

**Verifiable end state:** a clean clone of the public repository can run `uv sync`, `uv run ruff check`, `uv run mypy src/`, and `uv run pytest` successfully against the skeleton-only codebase. The repository renders professionally on GitHub.

**Explicit non-deliverables:** any working `jama_client` operation, any working MCP tool, the Dockerfile (Phase 2).

### Phase 1 — Functional MVP, both transports

**Scope:** implement the six client operations and six MCP tools with full test coverage and working stdio plus streamable-HTTP transports.

**Deliverables:**

- `jama_client.auth` and `jama_client.client` fully implemented.
- All six client methods implemented and unit-tested.
- All six MCP tools implemented and protocol-tested.
- Integration test suite operational against `pm2.jamacloud.com` (manually invoked).
- README updated with setup, OAuth credential provisioning, and smoke-test instructions.

**Verifiable end state:** Claude Desktop or the MCP Inspector connects to `jama-mcp-stdio` and `jama-mcp-http`. Both successfully invoke `whoami` against the sandbox, and an AI agent completes a traceability query end-to-end (project, item, relationships, test runs).

### Phase 2 — Containerization

**Scope:** package the streamable-HTTP server as a Docker container suitable for local deployment.

**Deliverables:**

- `docker/Dockerfile` — multi-stage build, slim base image, non-root user.
- `docker/docker-compose.yml` — service definition with health check and env-file integration.
- README updates with Docker quickstart.

**Verifiable end state:** `docker compose up` starts the server. The MCP Inspector connects to the containerized server and successfully invokes a tool.

## 11. Repository Hygiene Rules

- **Secrets never enter the repository.** `.env` files (other than `.env.example`) are gitignored. `gitleaks` scans every commit. Jama OAuth credentials are provisioned per-user and stored in `.env` (local development) or container-orchestrator secret stores (production deployments).
- **Working notes do not enter the public repository.** `docs/internal/` and `docs/plans/` are gitignored by convention. Working notes, raw plans, and exploratory writing live in `docs/internal/`.
- **The `validate-docs-placement.sh` hook warns when staged docs contain internal markers.** Authors review and either remove the marker or move the document to `docs/internal/`.
- **Conventional commits.** Commit messages follow the conventional-commits specification with imperative-mood subjects: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `ci:`.
- **Issue, branch, PR workflow** for all phases after Phase 0. Phase 0 is the inception commit and uses no PR.
- **Documentation-only changes do not get separate issues, branches, or PRs.** Changes that touch only `CLAUDE.md`, `MEMORY.md`, or `~/.claude/` memory files are bundled into the next phase's PR or committed directly to the working branch (per the author's global CLAUDE.md rule).
- **Pre-commit hooks must pass before commit.** Ruff violations, mypy failures, secret detections, and large-file additions block the commit.
- **CI must pass before merge.** Lint, test, type-check, and dependency-review jobs must all succeed.

## 12. Open Decisions Deferred to Implementation Planning

The following decisions are intentionally not made in this specification and will be resolved during the Phase 0 implementation plan produced by the `writing-plans` skill:

- Exact ruff `ignore` list (the reference project's list is a starting point but contains project-specific entries that may not apply).
- Exact mypy strict configuration values (some strict flags can produce noise that requires per-module overrides).
- Exact `pyproject.toml` `[project]` metadata: classifiers, keywords, repository URL, author email visibility.
- Choice between `gitleaks` and an alternative secret-scanning tool.
- README structure and depth (placeholder versus comprehensive on day one).
- Whether to include a `CODE_OF_CONDUCT.md` (Contributor Covenant) at Phase 0 or defer.

These items are flagged here so the implementation plan addresses them explicitly rather than implicitly.
