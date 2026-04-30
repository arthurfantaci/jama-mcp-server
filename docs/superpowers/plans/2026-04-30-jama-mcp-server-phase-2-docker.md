# Phase 2 — Docker Containerization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package the streamable-HTTP MCP server as a multi-stage Docker container suitable for local development and demonstration use, with a build-only CI guardrail. The verifiable end state is `docker compose up -d` starting the server, `curl http://localhost:8765/health` returning 200, and an MCP Inspector session connecting to the containerized server and successfully invoking a tool against `pm2.jamacloud.com`.

**Architecture:** A two-stage Dockerfile uses `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` as the builder, syncs a `.venv` from `pyproject.toml` + `uv.lock` via two-step `uv sync` for layered caching, then copies that venv (with `--chown=jama:jama`) into a `python:3.12-slim-bookworm` runtime that drops to a fixed non-root UID 1001. A new `/health` route registered via `FastMCP.custom_route` serves as a stable liveness endpoint, probed by a Python-stdlib `urllib` healthcheck (no curl install required). Docker Compose at `docker/docker-compose.yml` wires the host's gitignored `.env` (OAuth secrets, `JAMA_BASE_URL`) plus an inline `environment:` block (transport overrides) into a single service exposed on port 8765. A build-only CI workflow under `.github/workflows/docker-build.yml` runs `docker buildx build` with GHA layer caching on PR + main with path filters, plus an in-image import smoke test.

**Tech Stack:** Docker (BuildKit / Compose v2), Astral uv (lockfile-pinned dependency sync), Python 3.12, FastMCP `custom_route`, Starlette (`Request` / `JSONResponse`), `docker/build-push-action@v6` with GHA cache, GitHub Actions `actions/checkout@v6`.

**Spec reference:** [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](../specs/2026-04-28-jama-mcp-server-design.md) Section 10 (Phase 2 — Containerization).

**Tracking issue:** [#6](https://github.com/arthurfantaci/jama-mcp-server/issues/6).

---

## File structure / decomposition

**Files created:**

| Path | Purpose |
|------|---------|
| `docker/Dockerfile` | Multi-stage build, uv builder + slim runtime, non-root, HEALTHCHECK |
| `docker/docker-compose.yml` | Single-service compose, env_file integration, environment overrides, healthcheck |
| `.dockerignore` (repo root) | Exclude `.env`, `.git/`, tests, docs, IDE/cache noise from the build context |
| `.github/workflows/docker-build.yml` | Build-only CI with path filters, buildx GHA cache, import smoke step |
| `tests/unit/jama_mcp_server/test_server_health.py` | Unit test for the `/health` route handler |

**Files modified:**

| Path | Change |
|------|--------|
| `src/jama_mcp_server/server.py` | Add module-level `_health` async function; register via `server.custom_route(...)(...)` inside `build_server` |
| `.env.example` | Add comment clarifying that Compose's `environment:` block overrides three values inside the container |
| `README.md` | New top-level `## Docker quickstart` section between `## Quick start` and `## Tool reference`. The Phase 2 status row update lands at PR-merge time, not in this work. |
| `MEMORY.md` | Append four "Recent decisions" rows for Phase 2 plan-author choices, plus update "Current phase" block to reflect Phase 2 active. |

**Decomposition principles applied:**
- One responsibility per file: Dockerfile is build-only, compose is deployment, CI workflow is drift detection.
- The `/health` handler is a module-level function (not a closure inside `build_server`) so it's directly testable without dragging Settings/JamaClient into the unit test.
- The `.dockerignore` lives at repo root (not in `docker/`) because Docker reads it relative to the build context root, which compose sets to `..`.

---

## Conventions to follow (project-specific)

- **Conventional Commits.** Tasks use `feat:`, `chore:`, `docs:`, `ci:`, `test:` as appropriate.
- **`from __future__ import annotations`** on every new `.py` file.
- **Google-style docstrings** on every public surface; ruff `D` and `ANN` rule families enforce.
- **Pydantic Settings defaults stay at `mcp_http_host="127.0.0.1"`** (loopback, safe for native runs). The container overrides via env var, never via Settings default.
- **No new top-level dependencies.** `starlette` is transitive via `mcp`; do not add it to `pyproject.toml`.
- **MEMORY.md updates** bundle into the Phase 2 PR per the no-separate-workflow rule for memory/config files.
- **Each task ends with a commit.** Conventional Commit message + `Refs: #6` footer + `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` footer.

---

## Verification commands (canonical)

Run after tasks that touch Python or test code:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -m "not integration"
```

Run after tasks that touch Docker artifacts:

```bash
docker compose -f docker/docker-compose.yml config       # validates compose syntax
docker build -f docker/Dockerfile -t jama-mcp-server:dev .  # local build
```

---

## Task 1: Add the `/health` route handler (TDD)

**Files:**
- Create: `tests/unit/jama_mcp_server/test_server_health.py`
- Modify: `src/jama_mcp_server/server.py:1-78` (full file rewrite)

**Rationale:** A stable liveness endpoint serves both the Phase 2 healthcheck and Phase 3's K8s liveness/readiness probes. Adding it now means Phase 3 doesn't have to retrofit. The `/health` route is registered via `FastMCP.custom_route` per the sanctioned ASGI sub-application mounting pattern.

- [ ] **Step 1.1: Write the failing test**

Create `tests/unit/jama_mcp_server/test_server_health.py` with:

```python
"""Tests for the streamable-HTTP /health route handler."""

from __future__ import annotations

from unittest.mock import MagicMock

from starlette.responses import JSONResponse

from jama_mcp_server.server import _health


async def test_health_returns_status_ok() -> None:
    """The _health handler returns 200 with the canonical liveness payload."""
    request = MagicMock()  # _health does not read the request
    response = await _health(request)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    assert response.body == b'{"status":"ok"}'
```

- [ ] **Step 1.2: Run the test — verify it fails**

```bash
uv run pytest tests/unit/jama_mcp_server/test_server_health.py -v
```

Expected: `ImportError` on `from jama_mcp_server.server import _health` because `_health` does not yet exist. The collection itself fails, which is the canonical TDD red state for an undefined import.

- [ ] **Step 1.3: Add the `_health` handler and register it**

Replace the contents of `src/jama_mcp_server/server.py` with:

```python
"""FastMCP application instance and transport entry points."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

from jama_client import JamaClient, OAuthCredentials
from jama_mcp_server.config import Settings
from jama_mcp_server.logging_config import configure_logging

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from starlette.requests import Request


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


async def _health(_request: Request) -> JSONResponse:
    """Return a static liveness payload for HTTP healthcheck probes.

    The handler is intentionally cheap and stateless: it does not touch
    the JamaClient or any external service. A deeper readiness probe
    (e.g., verifying the OAuth token is fresh) is a Phase 3 concern when
    K8s separates liveness from readiness.
    """
    return JSONResponse({"status": "ok"})


def build_server(*, settings: Settings | None = None) -> FastMCP:
    """Build a :class:`FastMCP` instance bound to the given settings."""
    cfg = settings or Settings()

    @asynccontextmanager
    async def _bound_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
        async with jama_lifespan(server, settings=cfg) as ctx:
            yield ctx

    server = FastMCP(
        "jama-mcp-server",
        host=cfg.mcp_http_host,
        port=cfg.mcp_http_port,
        lifespan=_bound_lifespan,
    )

    # Register the liveness probe before tools so the route is available
    # the moment the streamable-HTTP server begins accepting connections.
    server.custom_route("/health", methods=["GET"])(_health)

    # Register tools.
    from jama_mcp_server import tools  # noqa: PLC0415

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
    server.run(transport="streamable-http")
```

Notes on the diff:
- `JSONResponse` imports at module level (used by `_health`).
- `Request` imports under `TYPE_CHECKING` only — the handler annotates but does not construct one.
- `_health` is module-level (not a closure inside `build_server`) so the unit test imports it directly.
- `server.custom_route("/health", methods=["GET"])(_health)` is the imperative call form of the decorator. Functionally identical to `@server.custom_route(...)` over `_health`, but lets `_health` stay outside `build_server`'s closure.
- The handler accepts `_request` (underscore-prefixed) to satisfy `ARG002` ruff rule even though the request object is unused.

- [ ] **Step 1.4: Run the test — verify it passes**

```bash
uv run pytest tests/unit/jama_mcp_server/test_server_health.py -v
```

Expected: 1 passed.

- [ ] **Step 1.5: Run the full unit suite to confirm no regressions**

```bash
uv run pytest -m "not integration" -q
```

Expected: 84 passed (the previous 83 + the new `_health` test).

- [ ] **Step 1.6: Run linters and type checker**

```bash
uv run ruff check src/jama_mcp_server/server.py tests/unit/jama_mcp_server/test_server_health.py
uv run ruff format --check src/jama_mcp_server/server.py tests/unit/jama_mcp_server/test_server_health.py
uv run mypy src/
```

Expected: all clean.

- [ ] **Step 1.7: Commit**

```bash
git add src/jama_mcp_server/server.py tests/unit/jama_mcp_server/test_server_health.py
git commit -m "$(cat <<'EOF'
feat(server): add /health route for liveness probes

Register a module-level async _health handler via FastMCP.custom_route
inside build_server. Returns a static {"status": "ok"} JSON payload at
GET /health on the streamable-HTTP transport.

Phase 2 (Docker containerization) probes this endpoint from its
HEALTHCHECK directive; Phase 3 (Kubernetes) will reuse it for liveness
and readiness probes. Keeping the handler stateless and module-level
makes it directly unit-testable without exercising the lifespan or
JamaClient.

starlette is a transitive dependency via mcp/fastmcp; no new top-level
dependency added.

Refs: #6

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Create `.dockerignore` at repo root

**Files:**
- Create: `.dockerignore`

**Rationale:** A correctly-scoped build context speeds up `docker build` (less data sent to the Docker daemon) and is a defense-in-depth against accidentally baking secrets into image layers. Docker reads `.dockerignore` from the build context root, which compose sets to `..` (the repo root).

- [ ] **Step 2.1: Create the file**

Create `.dockerignore` at the repo root with:

```
# Version control
.git/
.gitignore
.gitattributes

# CI / tooling configs not needed in build context
.github/

# Python build artifacts and caches
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
ENV/
build/
dist/
*.egg-info/
*.egg

# Test / lint caches and reports
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
.coverage.*
htmlcov/
coverage.xml

# Secrets — never bake into images
.env
.env.local
.env.*.local

# Project surfaces that don't belong in the runtime image
tests/
docs/
.claude/

# IDE / OS noise
.vscode/
.idea/
.DS_Store
Thumbs.db
```

- [ ] **Step 2.2: Confirm `.env.example` is NOT excluded**

```bash
grep -E '^\.env\.example' .dockerignore || echo ".env.example not excluded (correct)"
```

Expected: `.env.example not excluded (correct)`. The Dockerfile does not COPY `.env.example`, but if a future change does, this guarantees it's available.

- [ ] **Step 2.3: Commit**

```bash
git add .dockerignore
git commit -m "$(cat <<'EOF'
chore(docker): add .dockerignore for Phase 2 build context

Exclude VCS, Python build/cache artifacts, test+lint caches, secrets,
test/doc directories, and IDE/OS noise from the Docker build context.
The file lives at repo root because Docker reads .dockerignore relative
to the build context root, which compose sets to .. via context: ..

Defense-in-depth note: gitleaks already blocks committing .env files,
but excluding them from the image build context as well prevents any
local-only .env from being baked into image layers if a future
Dockerfile change were to COPY the working tree wholesale.

Refs: #6

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Create `docker/Dockerfile` and verify the local build

**Files:**
- Create: `docker/Dockerfile`

**Rationale:** Multi-stage build with `uv` builder pins dependencies to `uv.lock` and keeps the runtime image small. Non-root user (UID 1001) matches the spec's "non-root user" requirement and gives Phase 3 a fixed UID for `securityContext.runAsUser`.

- [ ] **Step 3.1: Create the docker/ directory and the Dockerfile**

```bash
mkdir -p docker
```

Create `docker/Dockerfile` with:

```dockerfile
# syntax=docker/dockerfile:1.7
# =============================================================================
# Builder stage — install dependencies and the project into a uv-managed venv.
# =============================================================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# UV_COMPILE_BYTECODE=1 pre-compiles .pyc at install time (faster cold start).
# UV_LINK_MODE=copy forces uv to copy files into the venv rather than hardlink,
# which is required for cross-stage COPY --from=builder to work cleanly across
# Docker's union filesystem.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Layer 1: dependencies only. Cached unless pyproject.toml or uv.lock change,
# which keeps the cache hot across src/ edits.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Layer 2: install the project itself. Re-runs only when src/ changes.
COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# =============================================================================
# Runtime stage — slim Python with the prebuilt venv copied in.
# =============================================================================
FROM python:3.12-slim-bookworm AS runtime

# Fixed UID/GID 1001 — Phase 3's K8s securityContext.runAsUser pins this value
# for consistency between Compose and Kubernetes runs.
RUN groupadd --system --gid 1001 jama \
 && useradd  --system --uid 1001 --gid jama --no-create-home jama

WORKDIR /app
COPY --from=builder --chown=jama:jama /app /app

# PATH puts the venv first so `python` and console scripts resolve from it.
# PYTHONUNBUFFERED ensures structlog output flushes through `docker logs` in
# real time. PYTHONDONTWRITEBYTECODE prevents .pyc creation at runtime
# (the builder already compiled bytecode under UV_COMPILE_BYTECODE).
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER jama
EXPOSE 8765

# Probe the /health route via Python stdlib so the runtime image does not
# need curl. start_period=30s accommodates lifespan startup including the
# proactive OAuth token fetch to Jamacloud.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request, sys; \
        sys.exit(0 if urllib.request.urlopen('http://localhost:8765/health', timeout=2).status == 200 else 1)"

# CMD uses `python -m jama_mcp_server` (not the jama-mcp-http console script)
# so MCP_TRANSPORT remains the routing seam in __main__.py — the same image
# can serve either transport mode if needed in the future.
CMD ["python", "-m", "jama_mcp_server"]
```

- [ ] **Step 3.2: Build the image locally**

```bash
DOCKER_BUILDKIT=1 docker build -f docker/Dockerfile -t jama-mcp-server:dev .
```

Expected output (last lines):

```
=> exporting to image
=> => exporting layers
=> => writing image sha256:...
=> => naming to docker.io/library/jama-mcp-server:dev
```

If the build fails, common causes:
- `# syntax=...` comment missing → cache mounts unavailable, cache mount syntax fails.
- `uv.lock` out of sync with `pyproject.toml` → `uv sync --frozen` errors. Run `uv lock` locally first.
- `.dockerignore` excluding something the Dockerfile needs (e.g., `pyproject.toml` or `uv.lock`) → COPY fails.

- [ ] **Step 3.3: Smoke-check the image: imports succeed**

```bash
docker run --rm --entrypoint python jama-mcp-server:dev \
    -c "import jama_mcp_server, jama_client; print('imports ok')"
```

Expected output: `imports ok`.

- [ ] **Step 3.4: Smoke-check the image: non-root user is active**

```bash
docker run --rm --entrypoint id jama-mcp-server:dev
```

Expected output: `uid=1001(jama) gid=1001(jama) groups=1001(jama)`.

- [ ] **Step 3.5: Confirm image size is reasonable**

```bash
docker images jama-mcp-server:dev --format '{{.Size}}'
```

Expected: ~150–200 MB. (Slim base ~50 MB + Python install ~40 MB + venv with 5 deps ~60 MB.) If significantly larger, check `.dockerignore` for missing exclusions.

- [ ] **Step 3.6: Commit**

```bash
git add docker/Dockerfile
git commit -m "$(cat <<'EOF'
feat(docker): add multi-stage Dockerfile for streamable-HTTP transport

Two-stage build: ghcr.io/astral-sh/uv:python3.12-bookworm-slim builder
syncs a .venv from pyproject.toml + uv.lock via the canonical two-step
uv sync pattern (deps cached separately from project), then copies the
venv into a python:3.12-slim-bookworm runtime that drops to a fixed
non-root user (UID/GID 1001 = jama:jama).

Healthcheck probes /health via Python stdlib urllib so the runtime
image needs no curl install. start_period=30s accommodates the
proactive OAuth token fetch during lifespan startup.

CMD uses `python -m jama_mcp_server` so MCP_TRANSPORT remains the
routing seam in __main__.py — the same image works for either transport
mode if needed in the future.

Refs: #6

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Create `docker/docker-compose.yml` and smoke-test it locally

**Files:**
- Create: `docker/docker-compose.yml`

**Rationale:** Single-service compose wires `.env` (host secrets) plus `environment:` (transport overrides) into the container, exposes port 8765, and runs the same healthcheck the Dockerfile defines. The `name:` field at the top prevents Compose from defaulting to "docker" as the project name (because the compose file lives in `docker/`).

- [ ] **Step 4.1: Create the compose file**

Create `docker/docker-compose.yml` with:

```yaml
name: jama-mcp-server

services:
  jama-mcp-server:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    image: jama-mcp-server:dev
    env_file:
      - ../.env
    environment:
      MCP_TRANSPORT: streamable-http
      MCP_HTTP_HOST: 0.0.0.0
      MCP_HTTP_PORT: "8765"
    ports:
      - "8765:8765"
    restart: unless-stopped
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - |
          import urllib.request, sys
          sys.exit(0 if urllib.request.urlopen('http://localhost:8765/health', timeout=2).status == 200 else 1)
      interval: 30s
      timeout: 5s
      start_period: 30s
      retries: 3
```

Key design points:
- `name: jama-mcp-server` at the top sets the project name explicitly. Without this, Compose derives the name from the parent directory of the compose file, which would be `docker` and produce ugly identifiers like `docker-jama-mcp-server-1` in `docker ps`.
- `context: ..` and `env_file: ../.env` are relative to the compose file's location. They resolve correctly regardless of the user's cwd as long as `-f docker/docker-compose.yml` is passed.
- `environment:` overrides three values that are container-specific concerns: transport, bind host, and port. These take precedence over anything in `.env`, which is the right behavior — a user's existing `.env` (set up for native stdio runs) does not need editing to also work with Docker.

- [ ] **Step 4.2: Validate compose syntax**

```bash
docker compose -f docker/docker-compose.yml config
```

Expected: the rendered, fully-resolved compose YAML printed to stdout. No errors. (`config` performs validation without starting any containers.)

- [ ] **Step 4.3: Verify `.env` exists and has the required secrets**

```bash
test -f .env && grep -E '^JAMA_OAUTH_CLIENT_ID=.+$' .env && grep -E '^JAMA_OAUTH_CLIENT_SECRET=.+$' .env && echo ".env populated" || echo "WARNING: .env missing or incomplete"
```

Expected: `.env populated`. If not, the user must populate `.env` from `.env.example` before continuing.

- [ ] **Step 4.4: Start the stack**

```bash
docker compose -f docker/docker-compose.yml up -d
```

Expected output:

```
[+] Running 2/2
 ✔ Network jama-mcp-server_default              Created
 ✔ Container jama-mcp-server-jama-mcp-server-1  Started
```

- [ ] **Step 4.5: Wait for the healthcheck to pass, then probe `/health`**

```bash
sleep 10
docker compose -f docker/docker-compose.yml ps
curl -sS http://localhost:8765/health
```

Expected:
- `docker compose ps` shows the service as `running` and (within ~30s of starting) `healthy`.
- `curl` returns `{"status":"ok"}` (compact JSON, no whitespace — Starlette's `JSONResponse` uses `separators=(",", ":")`).

- [ ] **Step 4.6: Inspect the container logs for clean startup**

```bash
docker compose -f docker/docker-compose.yml logs jama-mcp-server | tail -20
```

Expected: structlog output showing FastMCP server startup and bind on `0.0.0.0:8765`. No tracebacks.

- [ ] **Step 4.7: Tear down**

```bash
docker compose -f docker/docker-compose.yml down
```

Expected:

```
[+] Running 2/2
 ✔ Container jama-mcp-server-jama-mcp-server-1  Removed
 ✔ Network jama-mcp-server_default              Removed
```

- [ ] **Step 4.8: Commit**

```bash
git add docker/docker-compose.yml
git commit -m "$(cat <<'EOF'
feat(docker): add docker-compose.yml for local Phase 2 deployment

Single-service compose with explicit project name, build context at the
repo root, env_file integration with the user's gitignored .env (OAuth
secrets + JAMA_BASE_URL), and an inline environment block that
overrides MCP_TRANSPORT, MCP_HTTP_HOST, and MCP_HTTP_PORT for the
container path. The override block lets a user's existing .env (set up
for native stdio runs) work with Docker without edits.

Healthcheck uses the same Python stdlib urllib probe as the Dockerfile,
defined here as well so users running `docker run` (without compose)
also get a healthcheck. start_period=30s accommodates the proactive
OAuth token fetch during lifespan startup.

restart: unless-stopped keeps the container running across host reboots
when started with `up -d` while still respecting explicit
`compose stop`.

Refs: #6

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Update `.env.example` comments for Docker override behavior

**Files:**
- Modify: `.env.example`

**Rationale:** The existing `.env.example` doesn't call out that `docker compose` overrides `MCP_TRANSPORT`, `MCP_HTTP_HOST`, and `MCP_HTTP_PORT`. Without this note, users may waste time troubleshooting "why does setting `MCP_TRANSPORT=stdio` in my `.env` not switch the Docker container to stdio?"

- [ ] **Step 5.1: Read the current contents**

```bash
cat .env.example
```

Confirm it matches the version shipped from Phase 0 (six variables: `JAMA_BASE_URL`, `JAMA_OAUTH_CLIENT_ID`, `JAMA_OAUTH_CLIENT_SECRET`, `MCP_TRANSPORT`, `MCP_HTTP_HOST`, `MCP_HTTP_PORT`).

- [ ] **Step 5.2: Replace the file with the updated comments**

Overwrite `.env.example` with:

```
# Jamacloud REST API endpoint (no trailing slash).
JAMA_BASE_URL=https://pm2.jamacloud.com

# OAuth 2.0 client credentials provisioned via Jama Connect's
# "Set API Credentials using OAuth 2.0" panel. Create a dedicated
# credential named "jama-mcp-server-dev" rather than reusing existing
# credentials so it can be revoked independently if needed.
JAMA_OAUTH_CLIENT_ID=
JAMA_OAUTH_CLIENT_SECRET=

# MCP server transport. Use "stdio" for local development with Claude
# Desktop or Claude Code. Use "streamable-http" for the HTTP transport.
#
# Note: Docker Compose (docker/docker-compose.yml) sets this to
# "streamable-http" inside the container regardless of the value here.
MCP_TRANSPORT=stdio

# HTTP transport binding (only used when MCP_TRANSPORT=streamable-http).
#
# Note: Docker Compose sets MCP_HTTP_HOST=0.0.0.0 and MCP_HTTP_PORT=8765
# inside the container regardless of the values here. The container
# overrides protect users running natively from accidentally exposing
# their server on a LAN by leaving the loopback default unchanged here.
MCP_HTTP_HOST=127.0.0.1
MCP_HTTP_PORT=8765
```

- [ ] **Step 5.3: Verify gitleaks is satisfied (no real secrets)**

```bash
uv run pre-commit run gitleaks --files .env.example
```

Expected: passes (placeholders are not real secrets).

- [ ] **Step 5.4: Commit**

```bash
git add .env.example
git commit -m "$(cat <<'EOF'
docs(env): clarify Docker Compose override behavior for transport vars

The Compose service block in docker/docker-compose.yml overrides
MCP_TRANSPORT, MCP_HTTP_HOST, and MCP_HTTP_PORT inside the container
regardless of values in the user's .env. Add comments to .env.example
calling this out so users running both native and Docker workflows
don't waste time troubleshooting why their .env transport setting is
not honored in the container.

Also documents the security rationale for keeping MCP_HTTP_HOST at the
loopback default — protects native runs from accidental LAN exposure.

Refs: #6

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Add `## Docker quickstart` section to README

**Files:**
- Modify: `README.md` (insert new section between `## Quick start` and `## Tool reference`)

**Rationale:** Docker is an alternate entry path peer to native install, so a top-level section parallel to `## Quick start` reads cleanly. Updating the Phase 2 status row in the table at the top of the README waits until PR-merge time (the row currently says "Planned"; closure of #6 is when it flips to "Complete").

- [ ] **Step 6.1: Read the existing README to identify the insertion point**

```bash
grep -n "^## " README.md
```

Expected (sections at line numbers near these — actual numbers may shift):

```
5:## Status
16:## Architecture
25:## Phase 1 tool surface
36:## Quick start
55:## Tool reference
66:## Configuration
77:## Development
95:## Documentation
103:## Security
107:## License
```

The insertion point is the blank line immediately before `## Tool reference`.

- [ ] **Step 6.2: Insert the new section**

Use the Edit tool to insert the following content immediately before the `## Tool reference` line. The exact `old_string` to match is the literal text `## Tool reference` (preceded by a blank line). The `new_string` is the section content followed by `## Tool reference`.

The section content to insert (with literal triple-backtick fences in the file):

````markdown
## Docker quickstart

Run the streamable-HTTP transport in a container.

**One-time setup** — copy the env template and fill in your Jama OAuth credentials:

```bash
cp .env.example .env
$EDITOR .env  # set JAMA_OAUTH_CLIENT_ID and JAMA_OAUTH_CLIENT_SECRET
```

(See [Configuration](#configuration) for how to provision an OAuth credential
in Jama Connect.)

**Build and start the container:**

```bash
docker compose -f docker/docker-compose.yml up -d
curl http://localhost:8765/health  # {"status":"ok"}
```

Compose sets `MCP_TRANSPORT=streamable-http` and `MCP_HTTP_HOST=0.0.0.0`
inside the container regardless of what your `.env` says — only the OAuth
credentials and `JAMA_BASE_URL` come from `.env`.

**Connect with MCP Inspector:**

```bash
npx @modelcontextprotocol/inspector
# Then point it at http://localhost:8765/mcp
```

The container runs as a non-root user (UID 1001), exposes only port 8765,
and reads configuration from your `.env` via Compose's `env_file` directive.

**Stop with:**

```bash
docker compose -f docker/docker-compose.yml down
```

````

- [ ] **Step 6.3: Verify the README still renders cleanly**

```bash
grep -n "^## " README.md
```

Expected: `## Docker quickstart` appears between `## Quick start` and `## Tool reference`.

- [ ] **Step 6.4: Run the prose hygiene checks pre-commit catches**

```bash
uv run pre-commit run trailing-whitespace --files README.md
uv run pre-commit run end-of-file-fixer --files README.md
```

Expected: passes.

- [ ] **Step 6.5: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs(readme): add Docker quickstart section

New top-level section between Quick start (native) and Tool reference,
documenting the docker compose -f docker/docker-compose.yml workflow,
the .env setup, the curl /health smoke check, and MCP Inspector
connection. Calls out the Compose override behavior for transport
variables so users don't waste time troubleshooting that.

The Phase 2 status row in the README's status table flips from Planned
to Complete at PR-merge time, not in this commit.

Refs: #6

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Create `.github/workflows/docker-build.yml`

**Files:**
- Create: `.github/workflows/docker-build.yml`

**Rationale:** Build-only CI catches Dockerfile drift the day it's introduced. Path filters keep the job from running on docs-only PRs. GHA buildx cache makes warm rebuilds ~30 seconds. The smoke step confirms the built image's imports resolve, catching the most common rot mode (broken venv copy across stages).

- [ ] **Step 7.1: Create the workflow**

Create `.github/workflows/docker-build.yml` with:

```yaml
name: Docker build

on:
  pull_request:
    paths:
      - 'docker/**'
      - 'src/**'
      - 'pyproject.toml'
      - 'uv.lock'
      - '.dockerignore'
      - '.github/workflows/docker-build.yml'
  push:
    branches: [main]
    paths:
      - 'docker/**'
      - 'src/**'
      - 'pyproject.toml'
      - 'uv.lock'
      - '.dockerignore'

jobs:
  build:
    name: Build image (no push)
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: docker/Dockerfile
          push: false
          load: true
          tags: jama-mcp-server:ci
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Smoke-check the built image (imports resolve)
        run: |
          docker run --rm --entrypoint python jama-mcp-server:ci \
            -c "import jama_mcp_server, jama_client; print('imports ok')"

      - name: Confirm runtime user is non-root
        run: |
          docker run --rm --entrypoint id jama-mcp-server:ci | grep 'uid=1001(jama)'
```

Key design points:
- **`actions/checkout@v6`** matches the version Phase 0 dependabot bumped to (commit `5463e2e`). Consistent with the other workflows in `.github/workflows/`.
- **`docker/build-push-action@v6` + `cache-from/to: type=gha, mode=max`** — `mode=max` caches all layers, not just the final image. Most aggressive caching available.
- **`load: true`** loads the built image into the runner's local Docker daemon so subsequent steps can `docker run` it without registry access.
- **Smoke step is one shell line** — no compose, no live Jama connection, no secrets in CI. Just imports.
- **Non-root smoke** verifies the runtime image isn't accidentally running as root, which would defeat the security posture.

- [ ] **Step 7.2: Validate the YAML locally**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/docker-build.yml')); print('YAML ok')" 2>&1 \
  || python3 -c "
import pathlib
content = pathlib.Path('.github/workflows/docker-build.yml').read_text()
assert 'name:' in content
assert 'runs-on:' in content
assert 'docker/build-push-action@v6' in content
assert 'actions/checkout@v6' in content
print('basic checks ok (PyYAML unavailable)')
"
```

Expected: `YAML ok` or `basic checks ok (PyYAML unavailable)`.

- [ ] **Step 7.3: Commit**

```bash
git add .github/workflows/docker-build.yml
git commit -m "$(cat <<'EOF'
ci: add Docker build workflow with path filters and GHA cache

New build-only workflow that runs on PRs and pushes to main when
docker/, src/, pyproject.toml, uv.lock, or .dockerignore changes. Uses
docker/build-push-action@v6 with type=gha cache-from/to (mode=max) for
warm rebuilds in ~30 seconds.

Smoke steps confirm the built image's imports resolve and the runtime
container runs as the non-root jama user (UID 1001). No registry push,
no secrets needed in CI — image-publish CI is a Phase 3 concern when
there is a deployment consumer for the artifact.

Path filters keep the job from running on docs-only PRs, which this
repo gets a steady stream of given the memory-hygiene workflow.

Refs: #6

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Update MEMORY.md with Phase 2 decisions and active status

**Files:**
- Modify: `MEMORY.md`

**Rationale:** Per the chosen "Option C" approach from brainstorming, four "Recent decisions" rows capture the Phase 2 plan-author choices. The "Current phase" block flips from "Phase 2 — Docker containerization (planned, not yet started)" to active. The phase-status table row stays at "Planned" until PR-merge to main (handled at closure time, not here).

- [ ] **Step 8.1: Read the current MEMORY.md to identify insertion points**

```bash
grep -n "^## \|^| 2026" MEMORY.md | head -30
```

Identify:
- The `## Current phase` block to update with active branch / open issue / next action.
- The Recent decisions table — append four new rows after the most recent existing row.

- [ ] **Step 8.2: Update the `## Current phase` block**

Replace the existing block (which currently says "Phase 2 — Docker containerization (planned, not yet started)" with active branch `main`) with:

```markdown
**Phase 2 — Docker containerization (active)**

**Active branch:** `feat/phase-2-docker`
**Tracking issue:** [#6](https://github.com/arthurfantaci/jama-mcp-server/issues/6)
**Most recent merge:** [PR #5](https://github.com/arthurfantaci/jama-mcp-server/pull/5) — Phase 1 Functional MVP (squash-merged 2026-04-29)

**Next action:** execute the Phase 2 plan at [`docs/superpowers/plans/2026-04-30-jama-mcp-server-phase-2-docker.md`](docs/superpowers/plans/2026-04-30-jama-mcp-server-phase-2-docker.md). On completion, open the Phase 2 PR closing #6.
```

- [ ] **Step 8.3: Append four new Recent decisions rows**

After the most recent row in the Recent decisions table, append:

```markdown
| 2026-04-30 | Phase 2 base image: `python:3.12-slim-bookworm` runtime + `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` builder, multi-stage with venv copy across stages | Local-dev/demo target favors slim's debug ergonomics over distroless's minimum attack surface; uv builder image gives lockfile-pinned dependencies end-to-end and matches local-dev tooling exactly |
| 2026-04-30 | Phase 2 healthcheck: add `/health` route via `FastMCP.custom_route` + Python stdlib urllib probe | Stable probe semantics (vs probing /mcp with awkward 4xx-as-alive); no curl install needed; future-proofs Phase 3 K8s liveness/readiness probes which will reuse the same endpoint |
| 2026-04-30 | Phase 2 CI: build-only on PR + main with path filters + GHA buildx cache | Catches Dockerfile drift cheaply (~30s warm rebuild); image push deferred to Phase 3 when a deployment consumer (Minikube) justifies registry permissions and a tag strategy |
| 2026-04-30 | Phase 2 spec doc: no new spec written; decisions live in plan + this MEMORY.md | Existing design spec Section 10 sanctions deliverables; plan-author decisions belong in the implementation plan as task-level rationale, with an index-row summary here. Matches Phase 1's pattern (no separate decisions doc) |
```

- [ ] **Step 8.4: Confirm total line count is still in the ballpark of the 100-line target from the memory-hygiene SKILL**

```bash
wc -l MEMORY.md
```

Expected: <120 lines (slight overage tolerated for transition; full audit at PR-merge time via `/memory-audit`).

- [ ] **Step 8.5: Commit**

```bash
git add MEMORY.md
git commit -m "$(cat <<'EOF'
docs(memory): record Phase 2 active status and four plan-author decisions

Update Current phase block to reflect feat/phase-2-docker active and
issue #6 open. Append four Recent decisions rows per the brainstorming
session's Option C (no separate Phase 2 decisions doc):

- Base image + builder strategy (slim runtime + uv builder, multi-stage)
- Healthcheck (add /health route, urllib probe)
- CI scope (build-only on PR + main)
- Spec-doc decision (decisions captured in plan + MEMORY rather than a
  fourth artifact under specs/)

Phase status table row flips from Planned to Complete at PR-merge time,
not in this commit.

Refs: #6

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Verify the verifiable end state — MCP Inspector against the containerized server

**Files:** none modified.

**Rationale:** The design spec Section 10 defines the verifiable end state: `docker compose up` starts the server, MCP Inspector connects, and a tool invocation succeeds against `pm2.jamacloud.com`. This is a manual verification step, not an automated test. Required before opening the PR.

- [ ] **Step 9.1: Start the stack**

```bash
docker compose -f docker/docker-compose.yml up -d
```

Expected: container starts, `docker compose ps` shows `running`.

- [ ] **Step 9.2: Wait for healthy status (~30–40s)**

```bash
for i in $(seq 1 30); do
  state=$(docker inspect --format '{{.State.Health.Status}}' jama-mcp-server-jama-mcp-server-1 2>/dev/null || echo "starting")
  if [ "$state" = "healthy" ]; then echo "healthy after ~$((i*2))s"; break; fi
  sleep 2
done
docker compose -f docker/docker-compose.yml ps
```

Expected: `healthy after ~Xs` with X in the 30–40 range, then `ps` shows the service `(healthy)`.

- [ ] **Step 9.3: Confirm `/health` returns 200 + correct body**

```bash
curl -i http://localhost:8765/health
```

Expected:

```
HTTP/1.1 200 OK
content-type: application/json
...
{"status":"ok"}
```

- [ ] **Step 9.4: Launch MCP Inspector and connect**

```bash
npx @modelcontextprotocol/inspector
```

In the Inspector UI:

1. Set transport to **Streamable HTTP**.
2. Set URL to `http://localhost:8765/mcp`.
3. Click **Connect**.
4. Confirm the six tools are listed: `whoami`, `list_projects`, `get_item`, `search_items`, `get_downstream_relationships`, `get_test_runs_for_item`.

- [ ] **Step 9.5: Invoke a tool — `whoami`**

In Inspector, select `whoami` → invoke. Expected: a structured response containing the OAuth credential's identity (e.g., user/email associated with the `jama-mcp-server-dev` credential).

If `whoami` succeeds, the verifiable end state is met: container starts, healthcheck flips to healthy, MCP Inspector connects to the streamable-HTTP transport, and a tool invocation completes a live round-trip to `pm2.jamacloud.com`.

- [ ] **Step 9.6: Tear down**

```bash
docker compose -f docker/docker-compose.yml down
```

- [ ] **Step 9.7: No commit needed**

This task is verification only; no code changed.

---

## Task 10: Open Phase 2 PR and verify CI green

**Files:** none modified.

**Rationale:** Final closure task. Pushes any remaining commits from Tasks 1–8, opens a PR closing #6, and verifies the new `Docker build` CI workflow passes alongside the existing CI checks (Lint, Mypy strict, Test, Dependency Review, codecov).

- [ ] **Step 10.1: Confirm the working tree is clean and on `feat/phase-2-docker`**

```bash
git status
git rev-parse --abbrev-ref HEAD
```

Expected: working tree clean; branch is `feat/phase-2-docker`.

- [ ] **Step 10.2: Push any remaining local commits**

```bash
git push
```

Expected: push succeeds (the branch was set upstream during initial branch creation, so plain `git push` works).

- [ ] **Step 10.3: Open the PR**

```bash
gh pr create --title "Phase 2 — Docker containerization (closes #6)" --body "$(cat <<'EOF'
## Summary

Phase 2 packages the streamable-HTTP MCP server as a multi-stage Docker container suitable for local development and demonstration use, per design spec Section 10.

- `docker/Dockerfile` — multi-stage with `ghcr.io/astral-sh/uv` builder + `python:3.12-slim-bookworm` runtime, non-root user (UID 1001), `/health` HEALTHCHECK via Python stdlib urllib.
- `docker/docker-compose.yml` — single-service compose with explicit project name, env_file integration, environment-block transport overrides, port 8765, healthcheck.
- `.dockerignore` at repo root — excludes secrets, VCS, tests, docs, IDE/cache noise.
- `.github/workflows/docker-build.yml` — build-only CI with path filters and GHA buildx cache; in-image import + non-root smoke checks.
- `src/jama_mcp_server/server.py` — module-level `_health` async handler registered via `FastMCP.custom_route`. starlette is transitively available; no new top-level dependencies.
- `.env.example` — comment tweak documenting Compose's transport-variable overrides.
- `README.md` — new `## Docker quickstart` section between Quick start and Tool reference.
- `MEMORY.md` — Phase 2 active status + four Recent decisions rows.

## Verifiable end state

- [x] `docker compose -f docker/docker-compose.yml up -d` starts the streamable-HTTP server.
- [x] Container's healthcheck flips to `healthy` within ~30 seconds.
- [x] `curl http://localhost:8765/health` returns `200 {"status":"ok"}`.
- [x] MCP Inspector connects to `http://localhost:8765/mcp` via Streamable HTTP transport.
- [x] `whoami` tool invocation returns a structured response from `pm2.jamacloud.com`.

## Out of scope (deferred to Phase 3)

- Image push to a registry — needs tag/release strategy and a deployment consumer.
- Distroless or Chainguard runtime images — better fit when production hardening matters.
- Liveness/readiness probe split — K8s-specific concern.

## Test plan

- [x] `uv run pytest -m "not integration"` — 84 passed (1 new test in `test_server_health.py`).
- [x] `uv run ruff check .` — clean.
- [x] `uv run ruff format --check .` — clean.
- [x] `uv run mypy src/` — clean.
- [x] `docker build -f docker/Dockerfile .` — succeeds locally.
- [x] `docker compose up -d` + `curl /health` — verified locally.
- [x] MCP Inspector smoke against the containerized server — verified.

## Professional Portrayal checklist

- [x] No debug `print` statements in committed code.
- [x] No commented-out code.
- [x] No AI-collaboration narrative comments.
- [x] No scratch files or half-finished thought experiments.
- [x] Public documentation (README, .env.example, design-spec adherence) reads professionally.
- [x] Commits follow Conventional Commits and reference #6.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Expected: PR URL printed.

- [ ] **Step 10.4: Watch CI**

```bash
gh pr checks --watch
```

Expected: all checks pass — Lint, Dependency Review, Mypy strict, Test, codecov/patch, and the new Docker build workflow.

If any check fails, fix on the branch and push; CI re-runs automatically.

- [ ] **Step 10.5: No further commit needed in this task**

Once CI is green, the user reviews and squash-merges the PR. PR-merge handles closing #6 automatically (via the `closes #6` in the PR title). The README Phase 2 status row update (currently still says "Planned" in the README's status table) is a small follow-on commit — bundle into a Phase 3-prep commit or address as a hot-fix to main right after merge. Not in scope for this task.

---

## Self-review

This is the inline self-review per the writing-plans skill checklist.

**1. Spec coverage**

Design spec Section 10 lists three deliverables and a verifiable end state. Cross-check:

- ✅ `docker/Dockerfile` — Task 3.
- ✅ `docker/docker-compose.yml` — Task 4.
- ✅ README updates — Task 6.
- ✅ Verifiable end state (`docker compose up` + MCP Inspector + tool invocation) — Task 9.

Plan-author additions beyond the spec (sanctioned by brainstorming):

- ✅ `/health` route in `server.py` — Task 1.
- ✅ `.dockerignore` — Task 2.
- ✅ Build-only CI — Task 7.
- ✅ `.env.example` comment tweak — Task 5.
- ✅ MEMORY.md decisions/status — Task 8.

No spec gaps.

**2. Placeholder scan**

Searched the plan for "TBD", "TODO", "implement later", "fill in details", "add appropriate error handling", "similar to Task N", "(without actual test code)". No placeholder gaps. The README Phase 2 status row update is explicitly deferred to PR-merge time, with a clear rationale and a named follow-on path — that's a deferral, not a placeholder.

**3. Type consistency**

- `_health` signature is consistent across Task 1's test (`MagicMock` request) and the implementation (`Request` annotated under TYPE_CHECKING).
- `JSONResponse` import path consistent (`starlette.responses.JSONResponse`).
- Docker image tags consistent: `jama-mcp-server:dev` (local) vs `jama-mcp-server:ci` (CI). Different intentionally; documented in each task.
- UID 1001 referenced consistently in Dockerfile, smoke test, CI smoke step.
- Port 8765 referenced consistently in Dockerfile EXPOSE, compose ports, healthcheck URL, README, and verification commands.
- `start_period: 30s` consistent in Dockerfile HEALTHCHECK and compose healthcheck block.

No type / naming inconsistencies.

**4. Scope check**

10 tasks for 5 created files + 4 modified files + 1 verification + 1 PR open. Each task has 3–8 bite-sized steps. Tasks fit the user's ~8–12 target. No decomposition needed.
