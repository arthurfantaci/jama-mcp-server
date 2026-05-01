# Phase 3 — Kubernetes (Minikube) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the Phase 2 `jama-mcp-server:dev` container image to a local Minikube cluster as a stateless `Deployment` with a single replica, exposed via a `ClusterIP Service`, locked down by a `NetworkPolicy`, and made reachable for the MCP Inspector via `kubectl port-forward svc/jama-mcp-server 8765:8765`. The verifiable end state is a fresh `minikube start --cni=calico` cluster running the server, both probes healthy, MCP Inspector successfully invoking `whoami` against `pm2.jamacloud.com` through the K8s networking stack, and a green `K8s validate` CI check on the PR.

**Architecture:** Phase 3 inherits Phase 2's image unchanged (same `:dev` tag, same UID/GID 1001, same `/health` route). The only application-code addition is a `/readyz` deeper-readiness handler that verifies the JamaClient's cached OAuth token is fresh (in-memory check, no I/O). Two new public methods on `JamaClient` — `warm_token_cache()` and `is_token_fresh()` — encapsulate the token-state access without exposing the private `_tokens` attribute. The streamable-HTTP server lifespan eagerly calls `warm_token_cache()` at startup so readiness reports `ready` the moment startup completes (and surfaces credential errors at startup rather than on first request). A module-level mutable `_ServerState` container, populated by the lifespan and read by the `_readyz` Starlette route handler, bridges the gap between FastMCP's `lifespan_context` (visible to MCP tools via `ctx.request_context.lifespan_context`) and Starlette routes (which read `request.app.state` or module-level state). Kubernetes manifests use a flat Kustomize layout (no overlays — single deployment target). All resources land in a dedicated `jama-mcp` namespace set declaratively by `kustomization.yaml`'s top-level `namespace:` field, which makes the NetworkPolicy's same-namespace ingress rule meaningful and reduces teardown to `kubectl delete ns jama-mcp`.

**Tech Stack:** Kubernetes 1.30+, Minikube ≥1.33 (Calico CNI for NetworkPolicy enforcement), Kustomize (built into kubectl), kubeconform (manifest schema validator, CI), Python 3.12, FastMCP `custom_route`, Starlette `JSONResponse`, `actions/checkout@v6`, `imranismail/setup-kustomize@v2`.

**Spec reference:** [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](../specs/2026-04-28-jama-mcp-server-design.md) Section 10 (Phase 3 — Kubernetes (Minikube)).

**Tracking issue:** [#8](https://github.com/arthurfantaci/jama-mcp-server/issues/8).

---

## File structure / decomposition

**Files created:**

| Path | Purpose |
|------|---------|
| `tests/unit/jama_mcp_server/test_server_readyz.py` | Unit tests for the `/readyz` route handler — covers all three response branches (no client, fresh token, stale/absent token) |
| `k8s/configmap.yaml` | Non-secret config: `JAMA_BASE_URL`, `MCP_TRANSPORT`, `MCP_HTTP_HOST`, `MCP_HTTP_PORT`. (The OAuth token URL is derived in `jama_client/auth.py` as `{base_url}/rest/oauth/token` — not a Settings field, so not in the ConfigMap.) |
| `k8s/secret.example.yaml` | Placeholder Secret with `stringData:` for `JAMA_CLIENT_ID` and `JAMA_CLIENT_SECRET`. Real `secret.yaml` is gitignored and authored locally by the operator |
| `k8s/networkpolicy.yaml` | Ingress: same-namespace `podSelector`. Egress: kube-dns + 443/TCP to anywhere |
| `k8s/service.yaml` | ClusterIP, port 8765, targetPort 8765, selector matching the Deployment's labels |
| `k8s/deployment.yaml` | 1 replica; full pod and container `securityContext` (UID/GID 1001, `runAsNonRoot`, drop ALL caps, `readOnlyRootFilesystem` + `/tmp` emptyDir, `seccompProfile: RuntimeDefault`); liveness `/health`, readiness `/readyz`; resources (requests cpu=50m mem=128Mi, limits cpu=500m mem=256Mi); `imagePullPolicy: IfNotPresent`; env from ConfigMap + Secret references |
| `k8s/kustomization.yaml` | `namespace: jama-mcp`, `commonLabels`, `resources:` enumerating the five YAML files plus `secret.yaml` |
| `k8s/.gitignore` | Excludes `secret.yaml` from the directory |
| `.github/workflows/k8s-validate.yml` | Kubeconform schema validation on PR + push to `main`, scoped via path filters to `k8s/**` and the workflow file |

**Files modified:**

| Path | Change |
|------|--------|
| `src/jama_client/client.py` | Add two public methods: `warm_token_cache()` (eager token fetch — encapsulates the existing private `_ensure_token()`) and `is_token_fresh()` (synchronous check using the existing `TokenCache.get()` staleness logic) |
| `src/jama_mcp_server/server.py` | Add module-level `_ServerState` dataclass and `_state` instance; modify `jama_lifespan` to call `await client.warm_token_cache()` after `__aenter__` and populate/clear `_state.jama_client` around the `yield`; add module-level `_readyz` async handler reading `_state`; register `/readyz` via `server.custom_route("/readyz", methods=["GET"])(_readyz)` BEFORE tool registration in `build_server` |
| `tests/unit/jama_client/test_auth.py` | Extend with three new tests covering `is_token_fresh()` and `warm_token_cache()` against `JamaClient` (uses the existing `respx`-mocked transport pattern) |
| `tests/unit/jama_mcp_server/test_server_lifespan.py` | Extend with one new test verifying that `jama_lifespan` calls `warm_token_cache()` and that `_state.jama_client` is populated during the lifespan and cleared on teardown |
| `.gitignore` | Add `k8s/secret.yaml` exclusion line (defense-in-depth — the `k8s/.gitignore` already excludes it locally, but a top-level exclusion makes it visible to anyone reading the root `.gitignore`) |
| `README.md` | New top-level `## Kubernetes (Minikube) quickstart` section, placed AFTER `## Docker quickstart` and BEFORE `## Tool reference`. The Phase 3 status row in the Phases table is updated at PR-merge time (post-execution session), not during this work |
| `MEMORY.md` | At the FINAL task: append three "Recent decisions" rows for Phase 3 plan-author choices (probe split with `/readyz`, NetworkPolicy strictness, kubeconform CI). Also flip the `## Current phase` block from "Phase 2 complete; Phase 3 plan written" to "Phase 3 active" using the stale text as an Edit anchor (pattern from Phase 2 Task 8) |

**Decomposition principles applied:**
- One responsibility per file: each manifest holds exactly one Kubernetes resource (no `---`-separated multi-doc YAML).
- The `_readyz` handler is a module-level function (not a closure inside `build_server`) so it's directly unit-testable without spinning up the lifespan or `JamaClient` — same pattern as Phase 2's `_health`. Mock state is injected by setting `_state.jama_client` on the test's setup.
- Token-state queries are encapsulated as public `JamaClient` methods rather than the handler reaching into `_tokens` (private). Keeps the readiness probe's coupling to JamaClient narrow and well-typed.
- `k8s/.gitignore` lives in `k8s/` (not at repo root) because Kustomize's `resources: [secret.yaml]` reference fails fast and visibly when the file is missing — exactly the failure mode the design wants.

---

## Conventions to follow (project-specific)

- **Conventional Commits.** Tasks use `feat:`, `feat(k8s):`, `feat(server):`, `feat(client):`, `chore:`, `docs:`, `ci:`, `test:` as appropriate.
- **`from __future__ import annotations`** on every new `.py` file.
- **Google-style docstrings** on every public surface; ruff `D` and `ANN` rule families enforce.
- **Private attribute access stays inside the class.** `_readyz` does NOT touch `client._tokens`. New `JamaClient.is_token_fresh()` and `warm_token_cache()` public methods are the only sanctioned access path.
- **Pydantic Settings defaults stay at `mcp_http_host="127.0.0.1"`** (loopback, safe for native runs). The K8s ConfigMap overrides via env var (`MCP_HTTP_HOST=0.0.0.0`), never via Settings default — protects native runs from accidental LAN exposure. Same precedence pattern as Phase 2's Compose `environment:` block.
- **No new top-level Python dependencies.** All `_readyz` machinery uses already-imported names (`JSONResponse`, `JamaClient`).
- **MEMORY.md updates** bundle into the Phase 3 PR per the no-separate-workflow rule for memory/config files.
- **Each task ends with a commit.** Conventional Commit message + `Refs: #8` footer + `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` footer.
- **YAML indentation: 2 spaces.** Kubernetes manifests universally use 2-space indentation; mixing 4-space with the rest of the K8s ecosystem is non-idiomatic.

---

## Verification commands (canonical)

Run after tasks that touch Python or test code:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -m "not integration"
```

Run after tasks that touch K8s manifests:

```bash
# Stub secret.yaml for local kustomize build (required because secret.yaml is gitignored)
cp k8s/secret.example.yaml k8s/secret.yaml
kustomize build k8s/ > /tmp/rendered.yaml
kubeconform -strict -summary -kubernetes-version "1.30.0" /tmp/rendered.yaml
```

Run after tasks that touch the CI workflow:

```bash
# Local lint of the workflow YAML
yamllint .github/workflows/k8s-validate.yml || true   # yamllint may not be installed; the GitHub Actions parser is authoritative
```

The full Minikube smoke test runs only at Task 11. Earlier tasks rely on schema validation alone.

---

## Task 1: Add `JamaClient.is_token_fresh()` and `warm_token_cache()` (TDD)

**Files:**
- Modify: `src/jama_client/client.py` (add two public methods to `JamaClient`)
- Modify: `tests/unit/jama_client/test_auth.py` (extend with three new tests)

**Rationale:** The `/readyz` handler needs to know whether `JamaClient` has a fresh OAuth token in-memory. Reaching into `client._tokens` from the handler would couple the readiness probe to a private attribute. Two public methods on `JamaClient` keep the coupling narrow: `is_token_fresh()` (synchronous, returns `True` if the cached token exists and is not stale per the existing `TokenCache.get()` logic) and `warm_token_cache()` (async, eagerly fetches a token to populate the cache, used by the lifespan to make readiness meaningful at startup).

- [ ] **Step 1.1: Write the failing tests**

Open `tests/unit/jama_client/test_auth.py` and append the following test functions to the end of the file (after the existing tests):

```python
import pytest
import respx
from httpx import Response

from jama_client.client import JamaClient


@pytest.mark.asyncio
async def test_is_token_fresh_false_before_open(jama_credentials: OAuthCredentials) -> None:
    """`is_token_fresh()` returns False before the client is entered as an async context manager."""
    client = JamaClient(jama_credentials)
    # No __aenter__ called; transport is closed; cache is empty.
    assert client.is_token_fresh() is False


@pytest.mark.asyncio
async def test_is_token_fresh_true_after_warm(
    jama_credentials: OAuthCredentials,
    jama_token_url: str,
    jama_token_stub: dict[str, Any],
) -> None:
    """`is_token_fresh()` returns True immediately after `warm_token_cache()` populates the cache."""
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post(jama_token_url).mock(return_value=Response(200, json=jama_token_stub))
        async with JamaClient(jama_credentials) as client:
            assert client.is_token_fresh() is False  # cache is empty before warm
            await client.warm_token_cache()
            assert client.is_token_fresh() is True


@pytest.mark.asyncio
async def test_warm_token_cache_populates_cache(
    jama_credentials: OAuthCredentials,
    jama_token_url: str,
    jama_token_stub: dict[str, Any],
) -> None:
    """`warm_token_cache()` issues exactly one OAuth token fetch."""
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(jama_token_url).mock(return_value=Response(200, json=jama_token_stub))
        async with JamaClient(jama_credentials) as client:
            await client.warm_token_cache()
        assert route.call_count == 1
```

Add `from typing import Any` to the imports at the top of the file if not already present.

Notes:
- `respx` is the existing fixture pattern for mocking httpx in this project (see other tests in `test_auth.py` and `test_client_transport.py`).
- The `assert_all_called=False` argument lets the test pass even when no requests fire (e.g., the "before warm" assertion in test 2).
- `jama_credentials`, `jama_token_url`, `jama_token_stub` are existing shared fixtures from `tests/conftest.py`.

- [ ] **Step 1.2: Run the tests — verify they fail**

```bash
uv run pytest tests/unit/jama_client/test_auth.py -v -k "is_token_fresh or warm_token"
```

Expected: 3 tests fail with `AttributeError: 'JamaClient' object has no attribute 'is_token_fresh'` (and similar for `warm_token_cache`). This is the canonical TDD red state.

- [ ] **Step 1.3: Add the two methods to `JamaClient`**

Open `src/jama_client/client.py` and add the following two methods to the `JamaClient` class. Place them immediately AFTER the existing `is_open` property (around line 65) and BEFORE the existing `__aenter__` method:

```python
    def is_token_fresh(self) -> bool:
        """Return ``True`` if the cached OAuth token exists and has not aged out.

        The check is synchronous and in-memory. It uses the existing
        :meth:`TokenCache.get` staleness logic, which considers a token stale at
        or beyond 90 percent of its TTL (matching the proactive refresh
        threshold). Returns ``False`` when the underlying HTTP transport is not
        open (the client has not been entered as an async context manager).

        Used by the streamable-HTTP ``/readyz`` route handler to drive
        Kubernetes readiness probes without making a network call.

        Returns:
            ``True`` if the client is open and the cache holds a non-stale
            token, otherwise ``False``.
        """
        if self._http is None:
            return False
        return self._tokens.get(now=datetime.now(tz=UTC)) is not None

    async def warm_token_cache(self) -> None:
        """Eagerly fetch an OAuth token to populate the cache.

        Used at lifespan startup to make the readiness probe meaningful the
        moment startup completes, and to surface credential errors (HTTP 401
        from the OAuth endpoint) at startup rather than on the first
        user-driven tool call.

        Raises:
            JamaAuthError: When the OAuth endpoint rejects the credentials.
            JamaForbiddenError: When the OAuth endpoint returns 403.
            JamaServerError: When the OAuth endpoint returns 5xx after retry.
            JamaNetworkError: When transport-level errors persist after retry.
            RuntimeError: When invoked outside the async context manager.
        """
        await self._ensure_token()
```

The methods reuse `self._http`, `self._tokens`, and `self._ensure_token()` which already exist on `JamaClient`. No new imports are required (`datetime` and `UTC` are already imported at the top of `client.py`).

- [ ] **Step 1.4: Run the tests — verify they pass**

```bash
uv run pytest tests/unit/jama_client/test_auth.py -v -k "is_token_fresh or warm_token"
```

Expected: 3 passed.

- [ ] **Step 1.5: Run the full unit suite to confirm no regressions**

```bash
uv run pytest -m "not integration" -q
```

Expected: 87 passed (84 from end of Phase 2 + 3 new).

- [ ] **Step 1.6: Run linters and type checker**

```bash
uv run ruff check src/jama_client/client.py tests/unit/jama_client/test_auth.py
uv run ruff format --check src/jama_client/client.py tests/unit/jama_client/test_auth.py
uv run mypy src/
```

Expected: all clean.

- [ ] **Step 1.7: Commit**

```bash
git add src/jama_client/client.py tests/unit/jama_client/test_auth.py
git commit -m "$(cat <<'EOF'
feat(client): add is_token_fresh and warm_token_cache to JamaClient

Two new public methods encapsulate token-state access without exposing
the private _tokens attribute. is_token_fresh() is a synchronous
in-memory check using the existing TokenCache staleness logic (90% TTL
threshold). warm_token_cache() eagerly fetches a token via the existing
_ensure_token() machinery.

Both methods are introduced in support of Phase 3's K8s readiness probe:
the /readyz route handler will call is_token_fresh() to determine
whether the Pod should remain in the Service's endpoint pool, and the
streamable-HTTP lifespan will call warm_token_cache() at startup so
readiness reports 'ready' the moment startup completes (and credential
errors surface at startup rather than on first request).

Refs: #8

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Modify `jama_lifespan` to eagerly warm + add `_state` container (TDD)

**Files:**
- Modify: `src/jama_mcp_server/server.py`
- Modify: `tests/unit/jama_mcp_server/test_server_lifespan.py`

**Rationale:** The `_readyz` handler (added in Task 3) needs to read JamaClient state from a Starlette route, but FastMCP's `lifespan_context` dict is only accessible to MCP tools via `ctx.request_context.lifespan_context` — not from Starlette routes. A small module-level mutable container, populated by the lifespan and read by the route handler, bridges the gap. It's a controlled global: written exactly once at startup, cleared exactly once at shutdown, read-only otherwise. Eager `warm_token_cache()` ensures readiness is meaningful at startup AND surfaces credential errors at startup rather than 30 seconds after first user request.

- [ ] **Step 2.1: Write the failing test**

Open `tests/unit/jama_mcp_server/test_server_lifespan.py` and append:

```python
import pytest
from unittest.mock import AsyncMock, patch

from jama_mcp_server import server as server_module
from jama_mcp_server.config import Settings


@pytest.mark.asyncio
async def test_lifespan_warms_token_cache_and_populates_state(
    mock_jama_client: AsyncMock,
) -> None:
    """jama_lifespan calls warm_token_cache() and populates _state.jama_client during yield."""
    settings = Settings(
        jama_base_url="https://jama.example",
        jama_oauth_client_id="cid",
        jama_oauth_client_secret="cs",
    )

    def factory(_settings: Settings) -> AsyncMock:
        return mock_jama_client

    # Verify clean baseline.
    assert server_module._state.jama_client is None

    async with server_module.jama_lifespan(
        None, settings=settings, client_factory=factory
    ) as ctx:
        # During yield: client is in lifespan_context AND in _state
        assert ctx["jama_client"] is mock_jama_client
        assert server_module._state.jama_client is mock_jama_client
        # Eager warm was called exactly once
        mock_jama_client.warm_token_cache.assert_awaited_once()

    # After yield: _state is cleared
    assert server_module._state.jama_client is None
```

Notes:
- `mock_jama_client` is the existing shared `AsyncMock(spec=JamaClient)` fixture from `tests/conftest.py`. `AsyncMock(spec=JamaClient)` automatically creates async-mock methods for every public method on `JamaClient`, including `warm_token_cache` (added in Task 1).
- The test asserts both the existing `lifespan_context` dict semantics (`ctx["jama_client"]`) AND the new `_state` semantics — confirms the lifespan satisfies both consumers.
- `Settings(...)` is constructed explicitly with required fields rather than relying on env-var defaults to keep the test deterministic.

If the `Settings` constructor signature differs from what's shown, inspect `src/jama_mcp_server/config.py` and adjust the test's keyword arguments accordingly.

- [ ] **Step 2.2: Run the test — verify it fails**

```bash
uv run pytest tests/unit/jama_mcp_server/test_server_lifespan.py -v -k "warms_token_cache"
```

Expected: `AttributeError: module 'jama_mcp_server.server' has no attribute '_state'`. Canonical TDD red.

- [ ] **Step 2.3: Modify `src/jama_mcp_server/server.py`**

Open `src/jama_mcp_server/server.py` and replace the contents with:

```python
"""FastMCP application instance and transport entry points."""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

from jama_client import JamaClient, OAuthCredentials
from jama_mcp_server.config import Settings
from jama_mcp_server.logging_config import configure_logging

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from starlette.requests import Request


@dataclass
class _ServerState:
    """Mutable container for runtime state set by the lifespan and read by Starlette routes.

    FastMCP exposes ``lifespan_context`` only to MCP tools via
    ``ctx.request_context.lifespan_context``; Starlette route handlers
    registered via ``server.custom_route`` cannot reach it. This container
    bridges the gap. It is written exactly once at lifespan startup, cleared
    exactly once at shutdown, and read-only at all other times.
    """

    jama_client: JamaClient | None = None


_state = _ServerState()


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
    """Construct and tear down the shared :class:`JamaClient` for the server.

    Eagerly warms the OAuth token cache at startup so the readiness probe
    reports 'ready' the moment startup completes, and so credential errors
    surface at startup rather than on first user-driven tool call.
    """
    factory = client_factory or _default_client_factory
    client = factory(settings)
    async with client:
        await client.warm_token_cache()
        _state.jama_client = client
        try:
            yield {"jama_client": client}
        finally:
            _state.jama_client = None


async def _health(_request: Request) -> JSONResponse:
    """Return a static liveness payload for HTTP healthcheck probes.

    The handler is intentionally cheap and stateless: it does not touch
    the JamaClient or any external service. Kubernetes liveness probes
    (Phase 3) and the Phase 2 Docker HEALTHCHECK both target this endpoint.
    For deeper readiness checks (OAuth token freshness), see _readyz.
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

    # Register custom routes BEFORE tools so they're available the moment
    # the streamable-HTTP server begins accepting connections. Liveness
    # (/health) is static; readiness (/readyz) reads _state.jama_client.
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

Notes on the diff vs the Phase 2 file:
- Added `from dataclasses import dataclass`.
- Added the `_ServerState` dataclass and module-level `_state` instance.
- `jama_lifespan` now calls `await client.warm_token_cache()` after `__aenter__` and uses `try/finally` to guarantee `_state.jama_client` is cleared even if the wrapped server raises.
- `_health` docstring updated to reference `_readyz` (added in Task 3).
- A comment in `build_server` notes that `/readyz` will be registered in Task 3; the line itself is added in Task 3 to keep this task narrowly scoped.

- [ ] **Step 2.4: Run the test — verify it passes**

```bash
uv run pytest tests/unit/jama_mcp_server/test_server_lifespan.py -v -k "warms_token_cache"
```

Expected: 1 passed.

- [ ] **Step 2.5: Run the full unit suite to confirm no regressions**

```bash
uv run pytest -m "not integration" -q
```

Expected: 88 passed. If existing lifespan tests fail because they don't account for `warm_token_cache()` being awaited, update them to use the `mock_jama_client` fixture (which `AsyncMock(spec=JamaClient)` already supports) and assert the call shape matches.

- [ ] **Step 2.6: Run linters and type checker**

```bash
uv run ruff check src/jama_mcp_server/server.py tests/unit/jama_mcp_server/test_server_lifespan.py
uv run ruff format --check src/jama_mcp_server/server.py tests/unit/jama_mcp_server/test_server_lifespan.py
uv run mypy src/
```

Expected: all clean.

- [ ] **Step 2.7: Commit**

```bash
git add src/jama_mcp_server/server.py tests/unit/jama_mcp_server/test_server_lifespan.py
git commit -m "$(cat <<'EOF'
feat(server): eager token warm + _state container in lifespan

The streamable-HTTP server lifespan now eagerly calls
client.warm_token_cache() after __aenter__, so the upcoming /readyz
readiness probe reports 'ready' the moment startup completes.
Credential errors (HTTP 401 from OAuth) now surface at startup rather
than on the first user-driven tool call.

A new module-level _ServerState dataclass and _state instance bridge the
gap between FastMCP's lifespan_context (visible to MCP tools via
ctx.request_context.lifespan_context) and Starlette route handlers
registered via server.custom_route (which can't reach lifespan_context).
The container is written exactly once at startup, cleared exactly once
at shutdown via try/finally.

Sets up Task 3, where /readyz reads _state.jama_client and calls
client.is_token_fresh() to drive readiness.

Refs: #8

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Add `_readyz` handler + register custom_route (TDD)

**Files:**
- Create: `tests/unit/jama_mcp_server/test_server_readyz.py`
- Modify: `src/jama_mcp_server/server.py` (add `_readyz` function and one `custom_route` registration line)

**Rationale:** The K8s readiness probe needs an HTTP endpoint that reports whether the Pod should remain in the Service's endpoint pool. Unlike liveness (binary alive/dead), readiness reflects "ready to serve real traffic right now." For this server that means "OAuth token is fresh in cache." The handler reads `_state.jama_client` (populated by the lifespan in Task 2) and calls `is_token_fresh()` (added to JamaClient in Task 1). Module-level placement matches the Phase 2 `_health` pattern and keeps the handler unit-testable without lifespan setup.

- [ ] **Step 3.1: Write the failing tests**

Create `tests/unit/jama_mcp_server/test_server_readyz.py` with:

```python
"""Tests for the streamable-HTTP /readyz route handler."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from jama_client import JamaClient
from jama_mcp_server import server as server_module
from jama_mcp_server.server import _readyz


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    """Ensure the module-level _state.jama_client starts and ends as None for each test."""
    server_module._state.jama_client = None
    yield
    server_module._state.jama_client = None


async def test_readyz_returns_503_when_client_is_none() -> None:
    """No client in _state (e.g., before lifespan startup) returns 503 not_ready."""
    request = MagicMock()  # _readyz does not read the request
    response = await _readyz(request)

    assert response.status_code == 503
    body = json.loads(response.body)
    assert body == {"status": "not_ready", "reason": "client_not_initialized"}


async def test_readyz_returns_200_when_token_is_fresh() -> None:
    """A populated client with a fresh token returns 200 ready."""
    client = MagicMock(spec=JamaClient)
    client.is_token_fresh.return_value = True
    server_module._state.jama_client = client

    response = await _readyz(MagicMock())

    assert response.status_code == 200
    body = json.loads(response.body)
    assert body == {"status": "ready"}
    client.is_token_fresh.assert_called_once()


async def test_readyz_returns_503_when_token_is_stale() -> None:
    """A populated client with a stale or absent token returns 503 not_ready."""
    client = MagicMock(spec=JamaClient)
    client.is_token_fresh.return_value = False
    server_module._state.jama_client = client

    response = await _readyz(MagicMock())

    assert response.status_code == 503
    body = json.loads(response.body)
    assert body == {"status": "not_ready", "reason": "token_unavailable"}
    client.is_token_fresh.assert_called_once()
```

Notes:
- The autouse `_reset_state` fixture is critical: tests share the module-level `_state` instance and would leak state between tests without it.
- `MagicMock(spec=JamaClient)` (not `AsyncMock`) is correct because `is_token_fresh` is a SYNCHRONOUS method (no `await` involved).
- `json.loads(response.body)` parses the rendered Starlette `JSONResponse` body bytes, which lets us assert the full payload (including the `reason` field) without coupling to byte-string formatting.

- [ ] **Step 3.2: Run the tests — verify they fail**

```bash
uv run pytest tests/unit/jama_mcp_server/test_server_readyz.py -v
```

Expected: 3 tests fail with `ImportError: cannot import name '_readyz' from 'jama_mcp_server.server'`. Canonical TDD red.

- [ ] **Step 3.3: Add `_readyz` and register the custom_route**

Open `src/jama_mcp_server/server.py` and:

**(a)** Add the following function immediately AFTER `_health` (before `build_server`):

```python
async def _readyz(_request: Request) -> JSONResponse:
    """Return a deeper readiness payload that drives Kubernetes readiness probes.

    Unlike liveness (``/health``, static), readiness reflects whether the
    Pod should remain in the Service's endpoint pool. For this server that
    means: the JamaClient is initialized AND its cached OAuth token is
    fresh (not aged beyond 90 percent of TTL).

    The check is in-memory only (no I/O to Jamacloud) so that K8s probing
    every few seconds does not pressure the upstream OAuth endpoint. The
    lifespan's eager :meth:`JamaClient.warm_token_cache` call at startup
    plus the proactive refresh at >=90 percent TTL means a non-fresh token
    in steady state indicates a real problem - exactly when readiness
    should drop the Pod from rotation.

    Returns:
        JSONResponse with status_code 200 and body ``{"status": "ready"}``
        when the cached token is fresh; 503 with body
        ``{"status": "not_ready", "reason": ...}`` otherwise.
    """
    client = _state.jama_client
    if client is None:
        return JSONResponse(
            {"status": "not_ready", "reason": "client_not_initialized"},
            status_code=503,
        )
    if not client.is_token_fresh():
        return JSONResponse(
            {"status": "not_ready", "reason": "token_unavailable"},
            status_code=503,
        )
    return JSONResponse({"status": "ready"})
```

**(b)** In `build_server`, add ONE line registering `_readyz` immediately after the existing `_health` registration. The relevant block becomes:

```python
    # Register custom routes BEFORE tools so they're available the moment
    # the streamable-HTTP server begins accepting connections. Liveness
    # (/health) is static; readiness (/readyz) reads _state.jama_client.
    server.custom_route("/health", methods=["GET"])(_health)
    server.custom_route("/readyz", methods=["GET"])(_readyz)
```

- [ ] **Step 3.4: Run the tests — verify they pass**

```bash
uv run pytest tests/unit/jama_mcp_server/test_server_readyz.py -v
```

Expected: 3 passed.

- [ ] **Step 3.5: Run the full unit suite to confirm no regressions**

```bash
uv run pytest -m "not integration" -q
```

Expected: 91 passed (88 from end of Task 2 + 3 new).

- [ ] **Step 3.6: Run linters and type checker**

```bash
uv run ruff check src/jama_mcp_server/server.py tests/unit/jama_mcp_server/test_server_readyz.py
uv run ruff format --check src/jama_mcp_server/server.py tests/unit/jama_mcp_server/test_server_readyz.py
uv run mypy src/
```

Expected: all clean.

- [ ] **Step 3.7: Commit**

```bash
git add src/jama_mcp_server/server.py tests/unit/jama_mcp_server/test_server_readyz.py
git commit -m "$(cat <<'EOF'
feat(server): add /readyz route for K8s readiness probes

A module-level _readyz async handler returns 200 {"status":"ready"} when
the JamaClient cache holds a non-stale OAuth token, and 503 with a
specific reason otherwise (client_not_initialized, token_unavailable).
The check is in-memory only - readiness probes run every few seconds and
must not pressure the upstream OAuth endpoint.

Registered via server.custom_route BEFORE tools so the route is
available the moment streamable-HTTP starts accepting connections, same
pattern as Phase 2's /health.

Three unit tests cover all three response branches with module-level
_state isolation via an autouse reset fixture.

Refs: #8

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Author `k8s/configmap.yaml`

**Files:**
- Create: `k8s/` directory and `k8s/configmap.yaml`

**Rationale:** Non-secret runtime configuration belongs in a ConfigMap. The Deployment references it via `envFrom: configMapRef:` so any change to the ConfigMap requires only a Pod restart, not a rebuild. Pinning `MCP_HTTP_HOST=0.0.0.0` and `MCP_TRANSPORT=streamable-http` here matches the Phase 2 Compose `environment:` block precedence pattern.

- [ ] **Step 4.1: Create the directory and the manifest**

```bash
mkdir -p k8s
```

Create `k8s/configmap.yaml` with:

```yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: jama-mcp-config
data:
  # Jamacloud base URL. The OAuth token URL is derived in jama_client/auth.py
  # as f"{base_url}/rest/oauth/token" - not a separate Settings field, so not
  # surfaced here.
  JAMA_BASE_URL: "https://pm2.jamacloud.com"

  # Server transport configuration. Phase 2's Pydantic Settings default
  # for MCP_HTTP_HOST is 127.0.0.1 (loopback, safe for native runs); the
  # K8s Pod must bind to 0.0.0.0 so the Service's selector reaches it.
  MCP_TRANSPORT: "streamable-http"
  MCP_HTTP_HOST: "0.0.0.0"
  MCP_HTTP_PORT: "8765"
```

- [ ] **Step 4.2: Validate the manifest schema**

```bash
kubeconform -strict -summary -kubernetes-version "1.30.0" k8s/configmap.yaml
```

Expected: `Summary: 1 resource found in 1 file - Valid: 1, Invalid: 0, Errors: 0, Skipped: 0`.

If `kubeconform` is not installed locally, install it:

```bash
brew install kubeconform   # macOS Homebrew
# OR
go install github.com/yannh/kubeconform/cmd/kubeconform@latest
```

- [ ] **Step 4.3: Commit**

```bash
git add k8s/configmap.yaml
git commit -m "$(cat <<'EOF'
feat(k8s): add ConfigMap with non-secret runtime configuration

Phase 3 Kubernetes deliverable. Holds JAMA_BASE_URL, JAMA_TOKEN_URL,
MCP_TRANSPORT, MCP_HTTP_HOST=0.0.0.0, MCP_HTTP_PORT=8765 as
container env vars referenced by the Deployment via envFrom.

MCP_HTTP_HOST is intentionally 0.0.0.0 here (overrides the Pydantic
Settings default of 127.0.0.1) so the Service's selector can reach the
Pod. The Settings default stays at 127.0.0.1 to keep native runs safe
from accidental LAN exposure - same precedence pattern as Phase 2's
Compose environment: block.

Refs: #8

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Author `k8s/secret.example.yaml` and gitignore the real Secret

**Files:**
- Create: `k8s/secret.example.yaml`
- Create: `k8s/.gitignore`
- Modify: `.gitignore` (repo root)

**Rationale:** OAuth credentials must never reach git. The pattern is `secret.example.yaml` (placeholder values, committed) + `secret.yaml` (real values, gitignored). The kustomization references `secret.yaml`, so a missing file fails fast and visibly when the operator forgets to materialize it from the example — exactly the failure mode we want.

- [ ] **Step 5.1: Create `k8s/secret.example.yaml`**

```yaml
---
# Copy this file to k8s/secret.yaml and replace the placeholder values
# with your real Jama OAuth credentials. The real secret.yaml is
# gitignored; never commit it.
#
# To create the real file:
#   cp k8s/secret.example.yaml k8s/secret.yaml
#   # Edit k8s/secret.yaml: replace REPLACE_ME values
#
# Then apply via:
#   kubectl apply -k k8s/
apiVersion: v1
kind: Secret
metadata:
  name: jama-mcp-oauth
type: Opaque
stringData:
  JAMA_CLIENT_ID: "REPLACE_ME_WITH_YOUR_JAMA_OAUTH_CLIENT_ID"
  JAMA_CLIENT_SECRET: "REPLACE_ME_WITH_YOUR_JAMA_OAUTH_CLIENT_SECRET"
```

Notes:
- `stringData` (vs `data`) lets the operator paste plaintext credentials without base64-encoding manually. The Kubernetes API server encodes them on apply.
- `type: Opaque` is the canonical type for arbitrary user-supplied secrets.

- [ ] **Step 5.2: Create `k8s/.gitignore`**

```
# Real Secret (created by the operator from secret.example.yaml). Never commit.
secret.yaml
```

- [ ] **Step 5.3: Update root `.gitignore`**

Open `.gitignore` at the repo root. Find the section that excludes `.env` files (the existing `# Secrets — never commit` block from Phase 0). Append the following AFTER the existing `.env` exclusions:

```
# K8s real Secret (defense-in-depth; k8s/.gitignore also covers this)
k8s/secret.yaml
```

- [ ] **Step 5.4: Verify gitleaks does not flag the example file**

```bash
gitleaks detect --no-git --source k8s/secret.example.yaml --verbose
```

Expected: `no leaks found`. Placeholder values containing `REPLACE_ME` are not credential-shaped.

- [ ] **Step 5.5: Validate the manifest schema**

```bash
kubeconform -strict -summary -kubernetes-version "1.30.0" k8s/secret.example.yaml
```

Expected: 1 valid resource.

- [ ] **Step 5.6: Confirm `k8s/secret.yaml` is correctly gitignored**

```bash
cp k8s/secret.example.yaml k8s/secret.yaml
git status --porcelain k8s/secret.yaml
# Expected: empty output (file is ignored)
git check-ignore k8s/secret.yaml
# Expected: k8s/secret.yaml
rm k8s/secret.yaml   # Don't accidentally commit it
```

- [ ] **Step 5.7: Commit**

```bash
git add k8s/secret.example.yaml k8s/.gitignore .gitignore
git commit -m "$(cat <<'EOF'
feat(k8s): add Secret example template + gitignore real secret

k8s/secret.example.yaml is the committed template with REPLACE_ME
placeholder values for JAMA_CLIENT_ID and JAMA_CLIENT_SECRET. Operators
copy it to k8s/secret.yaml (gitignored) and fill in real values before
kubectl apply -k k8s/.

Two-layer .gitignore protection: k8s/.gitignore for the directory-local
rule, plus a defense-in-depth entry in the root .gitignore so anyone
reading the root rules sees the K8s exclusion alongside the existing
.env exclusions.

The kustomization.yaml (Task 9) references secret.yaml directly, so a
missing file fails visibly at kubectl apply time rather than silently
skipping the Secret resource - exactly the failure mode we want.

Refs: #8

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Author `k8s/networkpolicy.yaml`

**Files:**
- Create: `k8s/networkpolicy.yaml`

**Rationale:** Restrict ingress to same-namespace Pods (so only sibling clients in `jama-mcp` can reach the server) and egress to DNS + 443/TCP to anywhere (so the server can resolve and reach Jamacloud without pinning brittle IP CIDRs). Note that NetworkPolicy enforcement requires a CNI plugin that implements it — Minikube's default `auto` CNI does NOT enforce, so the README quickstart (Task 12) requires `minikube start --cni=calico`.

- [ ] **Step 6.1: Create the manifest**

Create `k8s/networkpolicy.yaml` with:

```yaml
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: jama-mcp-server
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: jama-mcp-server
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Allow any Pod in the same namespace to reach the server on 8765.
    # kubectl port-forward bypasses NetworkPolicy entirely (the kube-apiserver
    # talks directly to kubelet), so the README's port-forward verification
    # works regardless of this rule.
    - from:
        - podSelector: {}
      ports:
        - protocol: TCP
          port: 8765
  egress:
    # Allow kube-dns lookups (UDP+TCP/53 to the kube-system namespace).
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    # Allow HTTPS (443/TCP) egress to anywhere so the Pod can reach Jamacloud.
    # We do not pin Jamacloud IPs because the public Jama Cloud CDN's IP ranges
    # are not published as stable CIDRs and can change without notice.
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              # Standard private/link-local exclusions; defense in depth against
              # accidental egress to in-cluster services not covered by other rules.
              - 10.0.0.0/8
              - 172.16.0.0/12
              - 192.168.0.0/16
              - 169.254.0.0/16
      ports:
        - protocol: TCP
          port: 443
```

- [ ] **Step 6.2: Validate the manifest schema**

```bash
kubeconform -strict -summary -kubernetes-version "1.30.0" k8s/networkpolicy.yaml
```

Expected: 1 valid resource.

- [ ] **Step 6.3: Commit**

```bash
git add k8s/networkpolicy.yaml
git commit -m "$(cat <<'EOF'
feat(k8s): add NetworkPolicy restricting ingress and egress

Ingress: same-namespace podSelector on TCP/8765. Sibling Pods in the
jama-mcp namespace can reach the server. kubectl port-forward bypasses
NetworkPolicy by design (apiserver talks to kubelet directly), so the
demo verification path is unaffected.

Egress: kube-dns (UDP+TCP/53 to kube-system / k8s-app=kube-dns) plus
HTTPS (TCP/443) to 0.0.0.0/0 minus standard private/link-local CIDRs.
This supports Jamacloud connectivity without pinning the Jama Cloud
CDN's IP ranges, which are not published as stable CIDRs.

NetworkPolicy enforcement requires a CNI plugin that implements it.
Minikube's default 'auto' CNI does NOT enforce (manifests are accepted
but ignored). The README quickstart documents minikube start
--cni=calico to make the policy effective.

Refs: #8

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Author `k8s/service.yaml`

**Files:**
- Create: `k8s/service.yaml`

**Rationale:** A `ClusterIP` Service gives the Deployment a stable name (`jama-mcp-server`) reachable from inside the cluster on port 8765. `kubectl port-forward svc/jama-mcp-server 8765:8765` (used in the verification path) targets a Service rather than a Pod so it survives Pod recreation.

- [ ] **Step 7.1: Create the manifest**

Create `k8s/service.yaml` with:

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: jama-mcp-server
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: jama-mcp-server
  ports:
    - name: streamable-http
      protocol: TCP
      port: 8765
      targetPort: 8765
```

Notes:
- The selector key `app.kubernetes.io/name` matches the Deployment's pod template labels (Task 8). Kustomize's `commonLabels` in `kustomization.yaml` (Task 9) propagates the label to all resources, but explicit selectors are clearer than relying on commonLabels alone.
- `type: ClusterIP` is the default but explicit. `NodePort` would expose 8765 on the Minikube VM's IP, which is unnecessary because we use `kubectl port-forward` for the verification path.
- The named port (`name: streamable-http`) is good Kubernetes hygiene — it lets future probes or other consumers reference the port by name rather than number.

- [ ] **Step 7.2: Validate the manifest schema**

```bash
kubeconform -strict -summary -kubernetes-version "1.30.0" k8s/service.yaml
```

Expected: 1 valid resource.

- [ ] **Step 7.3: Commit**

```bash
git add k8s/service.yaml
git commit -m "$(cat <<'EOF'
feat(k8s): add ClusterIP Service exposing port 8765

ClusterIP service named jama-mcp-server selects Pods labeled
app.kubernetes.io/name=jama-mcp-server (matches the Deployment's pod
template labels in Task 8). Targets a named port (streamable-http) on
TCP/8765.

The verification path uses kubectl port-forward svc/jama-mcp-server
8765:8765, targeting the Service rather than a Pod so it survives Pod
recreation across the demo.

NodePort is intentionally not used: kubectl port-forward is the
sanctioned external access path per the design spec, and NodePort would
expose the server on Minikube's VM IP unnecessarily.

Refs: #8

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Author `k8s/deployment.yaml`

**Files:**
- Create: `k8s/deployment.yaml`

**Rationale:** The Deployment is the centerpiece manifest. It pins the image (`jama-mcp-server:dev` with `imagePullPolicy: IfNotPresent` so K8s uses Minikube's local Docker daemon image), wires the ConfigMap + Secret to env vars, configures the full pod and container `securityContext` (UID/GID 1001 inherited from the Phase 2 Dockerfile, drop ALL caps, `readOnlyRootFilesystem` with a `/tmp` `emptyDir`), and configures probes against `/health` (liveness) and `/readyz` (readiness). Resource requests/limits give the K8s scheduler enough information to place the Pod sensibly without runaway memory/CPU.

- [ ] **Step 8.1: Create the manifest**

Create `k8s/deployment.yaml` with:

```yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jama-mcp-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: jama-mcp-server
  template:
    metadata:
      labels:
        app.kubernetes.io/name: jama-mcp-server
    spec:
      # Pod-level securityContext applies to all containers in the Pod.
      # UID/GID 1001 matches the `jama` user pinned in the Phase 2 Dockerfile.
      securityContext:
        runAsUser: 1001
        runAsGroup: 1001
        runAsNonRoot: true
        fsGroup: 1001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: jama-mcp-server
          image: jama-mcp-server:dev
          # IfNotPresent uses Minikube's local Docker daemon image (built via
          # eval $(minikube docker-env) && docker build). Never pull.
          imagePullPolicy: IfNotPresent
          ports:
            - name: streamable-http
              containerPort: 8765
              protocol: TCP
          envFrom:
            - configMapRef:
                name: jama-mcp-config
            - secretRef:
                name: jama-mcp-oauth
          # Map the Secret's keys (JAMA_CLIENT_ID, JAMA_CLIENT_SECRET) to the
          # variable names Pydantic Settings expects. The Secret already uses
          # those names directly so envFrom is sufficient; keeping a single
          # naming convention prevents drift between the Settings field names
          # and the Secret keys.
          env:
            - name: JAMA_OAUTH_CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: jama-mcp-oauth
                  key: JAMA_CLIENT_ID
            - name: JAMA_OAUTH_CLIENT_SECRET
              valueFrom:
                secretKeyRef:
                  name: jama-mcp-oauth
                  key: JAMA_CLIENT_SECRET
          resources:
            requests:
              cpu: "50m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
          # Container-level securityContext locks down capabilities and the FS.
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
          # Liveness: cheap static /health. Failures restart the container.
          livenessProbe:
            httpGet:
              path: /health
              port: streamable-http
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 2
            failureThreshold: 3
          # Readiness: deeper /readyz that verifies cached OAuth token freshness.
          # Failures remove the Pod from the Service endpoints but do NOT restart.
          readinessProbe:
            httpGet:
              path: /readyz
              port: streamable-http
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 3
            successThreshold: 1
          # Startup probe: gives the lifespan up to 30 seconds to complete the
          # eager OAuth token fetch (matches the Phase 2 HEALTHCHECK start_period
          # rationale). Once startup succeeds, liveness and readiness take over.
          startupProbe:
            httpGet:
              path: /health
              port: streamable-http
            initialDelaySeconds: 2
            periodSeconds: 2
            timeoutSeconds: 2
            failureThreshold: 15
          volumeMounts:
            # readOnlyRootFilesystem: true requires writable mounts for any
            # path the application writes to. Python's tempfile module and
            # similar utilities default to /tmp.
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir:
            sizeLimit: 64Mi
```

Notes on key design choices:
- **`imagePullPolicy: IfNotPresent`** — without this, K8s's default policy for `:latest`-style or non-pinned tags is `Always`, which fails on Minikube because there's no registry to pull from. `IfNotPresent` uses the local image built via `eval $(minikube docker-env) && docker build`.
- **`startupProbe` with 15 × 2s = 30s window** — matches the Phase 2 KG note about start_period accommodating the eager OAuth token fetch. Without it, the readiness probe's 5×5s = 25s default would barely cover startup if Jamacloud is slow. The startup probe also DEFERS liveness checks until startup succeeds, preventing a slow OAuth fetch from triggering a restart loop.
- **`fsGroup: 1001`** — sets the GID of any mounted volume contents (only relevant if we add PVCs later, but harmless here and good defense-in-depth).
- **`sizeLimit: 64Mi` on the /tmp emptyDir** — prevents a runaway temp-file leak from filling node disk. 64MiB is more than enough for normal Python tempfile usage.
- **Two `envFrom` entries plus explicit `env:` mappings** — `envFrom` projects ConfigMap and Secret keys directly as env vars (the simple case). The explicit `env:` block additionally maps the Secret's `JAMA_CLIENT_ID` to `JAMA_OAUTH_CLIENT_ID` (the field name Pydantic Settings expects per `src/jama_mcp_server/config.py`). This is the spot most likely to need adjustment after running the full smoke test in Task 11 — verify by inspecting `Settings`.

- [ ] **Step 8.2: Verify the env-var name mapping is correct**

Inspect `src/jama_mcp_server/config.py` to confirm the Pydantic Settings field names:

```bash
grep -E "^\s+jama_oauth_client_id|^\s+jama_oauth_client_secret" src/jama_mcp_server/config.py
```

Expected output mentions `jama_oauth_client_id` and `jama_oauth_client_secret`. Pydantic Settings reads env vars by uppercasing the field name (so `jama_oauth_client_id` matches `JAMA_OAUTH_CLIENT_ID`). The deployment.yaml's `env:` block above maps `JAMA_CLIENT_ID` → `JAMA_OAUTH_CLIENT_ID`. Confirm this mapping is correct; if Pydantic Settings expects different env var names, adjust the manifest's `env:` block to match.

- [ ] **Step 8.3: Validate the manifest schema**

```bash
kubeconform -strict -summary -kubernetes-version "1.30.0" k8s/deployment.yaml
```

Expected: 1 valid resource.

- [ ] **Step 8.4: Commit**

```bash
git add k8s/deployment.yaml
git commit -m "$(cat <<'EOF'
feat(k8s): add Deployment with full securityContext and probes

Single-replica Deployment of jama-mcp-server:dev built into Minikube's
local Docker daemon (imagePullPolicy: IfNotPresent).

Pod-level securityContext: runAsUser 1001 (matches the Phase 2 jama
user), runAsNonRoot, fsGroup 1001, seccompProfile RuntimeDefault.

Container-level securityContext: allowPrivilegeEscalation false,
readOnlyRootFilesystem true (with a 64Mi emptyDir on /tmp for Python
tempfile usage), all capabilities dropped.

Probes: liveness on /health (cheap static), readiness on /readyz
(deeper OAuth-token-freshness check), startupProbe on /health with a
30-second budget (15 x 2s) to cover the lifespan's eager OAuth token
fetch on first start.

ConfigMap (jama-mcp-config) and Secret (jama-mcp-oauth) both projected
as env vars via envFrom, plus an explicit env: block mapping the
Secret's JAMA_CLIENT_ID/SECRET keys to the JAMA_OAUTH_CLIENT_ID/SECRET
names the Pydantic Settings layer expects.

Resources requests cpu=50m mem=128Mi, limits cpu=500m mem=256Mi -
defensible for a stateless HTTP server.

Refs: #8

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Author `k8s/kustomization.yaml`

**Files:**
- Create: `k8s/kustomization.yaml`

**Rationale:** Kustomize ties the per-resource manifests together into a single applyable unit (`kubectl apply -k k8s/`). The `namespace:` directive applies the `jama-mcp` namespace to every resource without per-file boilerplate. `commonLabels` propagates a consistent label set across resources, which makes selectors cleaner. Listing `secret.yaml` (gitignored) in `resources:` makes the missing-file failure mode loud and immediate.

- [ ] **Step 9.1: Create the manifest**

Create `k8s/kustomization.yaml` with:

```yaml
---
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

# All resources in this kustomization land in the jama-mcp namespace.
# A dedicated namespace makes the NetworkPolicy's same-namespace ingress
# rule meaningful (default would mix with whatever else is in the cluster)
# and reduces teardown to `kubectl delete ns jama-mcp`.
namespace: jama-mcp

# Apply consistent labels across all resources for selectors and discoverability.
commonLabels:
  app.kubernetes.io/name: jama-mcp-server
  app.kubernetes.io/part-of: jama-mcp
  app.kubernetes.io/managed-by: kustomize

resources:
  # Namespace must be created before any namespaced resource lands in it.
  - namespace.yaml
  - configmap.yaml
  # secret.yaml is gitignored; the operator copies it from secret.example.yaml
  # before `kubectl apply -k k8s/`. A missing file fails fast with a clear
  # kustomize error - exactly the failure mode we want.
  - secret.yaml
  - networkpolicy.yaml
  - service.yaml
  - deployment.yaml
```

- [ ] **Step 9.2: Create `k8s/namespace.yaml`**

The `namespace:` directive sets the namespace on resources but does NOT create the namespace itself. We need an explicit Namespace resource:

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: jama-mcp
```

Notes:
- The Namespace itself is not namespaced (it IS the namespace), so commonLabels still apply but the namespace: directive is a no-op for this resource.

- [ ] **Step 9.3: Add `namespace.yaml` to the resources list**

Re-open `k8s/kustomization.yaml` and verify `namespace.yaml` is the first entry in `resources:` (per Step 9.1's content). It is.

- [ ] **Step 9.4: Stub `secret.yaml` for local validation, then build and validate the rendered manifest**

```bash
cp k8s/secret.example.yaml k8s/secret.yaml
kustomize build k8s/ > /tmp/rendered.yaml
kubeconform -strict -summary -kubernetes-version "1.30.0" /tmp/rendered.yaml
```

Expected: `Summary: 6 resources found in 1 file - Valid: 6, Invalid: 0`.

- [ ] **Step 9.5: Inspect the rendered output**

```bash
head -60 /tmp/rendered.yaml
```

Expected: the Namespace resource appears first. Subsequent resources have `metadata.namespace: jama-mcp` and `metadata.labels` containing the three commonLabels keys.

- [ ] **Step 9.6: Clean up the stub**

```bash
rm k8s/secret.yaml /tmp/rendered.yaml
```

This avoids accidentally committing the stub.

- [ ] **Step 9.7: Validate kustomization.yaml schema by itself**

```bash
kubeconform -strict -summary -kubernetes-version "1.30.0" k8s/namespace.yaml
```

Expected: 1 valid resource. (kustomization.yaml itself is not a Kubernetes resource and kubeconform skips it.)

- [ ] **Step 9.8: Commit**

```bash
git add k8s/kustomization.yaml k8s/namespace.yaml
git commit -m "$(cat <<'EOF'
feat(k8s): add Kustomization + Namespace tying manifests together

Kustomization sets the jama-mcp namespace on all resources via the
top-level namespace: directive, applies commonLabels for consistent
selectors, and enumerates the per-resource manifests (including the
gitignored secret.yaml, which fails loudly when the operator forgets to
materialize it from secret.example.yaml).

A separate Namespace resource creates the namespace itself - the
kustomization namespace: directive only assigns existing namespace
membership, it does not create the namespace.

Resource ordering in resources: places namespace.yaml first to ensure
it exists before any namespaced resource is applied.

Refs: #8

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Add `.github/workflows/k8s-validate.yml` (kubeconform CI)

**Files:**
- Create: `.github/workflows/k8s-validate.yml`

**Rationale:** A schema-validation guardrail catches typos, wrong `apiVersion` strings, and unknown fields without spinning up a cluster. Mirrors Phase 2's `docker-build.yml` philosophy of running ONLY when relevant files change (path filters scoped to `k8s/**` and the workflow file itself).

- [ ] **Step 10.1: Create the workflow**

Create `.github/workflows/k8s-validate.yml` with:

```yaml
---
name: K8s validate

on:
  pull_request:
    paths:
      - 'k8s/**'
      - '.github/workflows/k8s-validate.yml'
  push:
    branches: [main]
    paths:
      - 'k8s/**'
      - '.github/workflows/k8s-validate.yml'

permissions:
  contents: read

jobs:
  validate:
    name: Validate Kubernetes manifests
    runs-on: ubuntu-24.04
    steps:
      - name: Check out repository
        uses: actions/checkout@v6

      - name: Install kustomize
        uses: imranismail/setup-kustomize@v2

      - name: Install kubeconform
        run: |
          set -euo pipefail
          KUBECONFORM_VERSION="0.6.7"
          curl -fsSL "https://github.com/yannh/kubeconform/releases/download/v${KUBECONFORM_VERSION}/kubeconform-linux-amd64.tar.gz" \
            -o kubeconform.tar.gz
          tar -xzf kubeconform.tar.gz kubeconform
          sudo mv kubeconform /usr/local/bin/kubeconform
          kubeconform -v

      - name: Stub secret.yaml from example (real secret.yaml is gitignored)
        run: cp k8s/secret.example.yaml k8s/secret.yaml

      - name: Render with kustomize and validate with kubeconform
        run: |
          set -euo pipefail
          kustomize build k8s/ > rendered.yaml
          kubeconform -strict -summary -kubernetes-version "1.30.0" rendered.yaml
```

Notes:
- **SHA256 pinning of the kubeconform tarball is deliberately deferred to a Phase 3.5+ hardening pass.** The risk for a demo project is acceptable (the tarball is fetched once per CI run, not stored, and is served from `github.com/yannh/kubeconform/releases` over HTTPS). When pinning is added later, fetch the SHA from `https://github.com/yannh/kubeconform/releases/download/v0.6.7/CHECKSUMS` and add a `sha256sum -c` step.
- The `cp k8s/secret.example.yaml k8s/secret.yaml` step is necessary because `kustomize build` requires `secret.yaml` to exist (the kustomization references it). The stub uses example values only — no real secrets reach CI logs.
- Pinned versions: kubeconform 0.6.7 (current stable), kubernetes-version 1.30.0 (Minikube's default at the time of writing). Both are explicit pins to avoid silent breakage when upstream releases ship.
- `permissions: contents: read` follows the principle of least privilege; this job does not write back to the repo.

- [ ] **Step 10.2: Lint the workflow YAML locally (best-effort)**

```bash
# yamllint may not be installed; the GitHub Actions parser is authoritative
yamllint .github/workflows/k8s-validate.yml || true
```

- [ ] **Step 10.3: Commit**

```bash
git add .github/workflows/k8s-validate.yml
git commit -m "$(cat <<'EOF'
ci: add kubeconform schema validation for k8s/ manifests

New workflow .github/workflows/k8s-validate.yml runs on PR and push to
main, scoped via path filters to k8s/** and the workflow file itself
(matches the Phase 2 docker-build.yml pattern of running only when
relevant files change).

Steps: install kustomize via setup-kustomize@v2, install kubeconform
0.6.7 from upstream tarball, stub k8s/secret.yaml from
k8s/secret.example.yaml so kustomize build resolves, then render and
validate with kubeconform -strict -summary -kubernetes-version 1.30.0.

Catches schema, apiVersion, and unknown-field regressions without
spinning up a cluster. Brings the project's CI check count from 6 to 7.

Refs: #8

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 10.4: Push the branch and observe the new check on GitHub**

```bash
git push
```

Open the PR (or the branch view) on GitHub and confirm `K8s validate` appears alongside the existing 6 checks. If the workflow fails on first run, fix the issue inline (likely a typo, wrong apiVersion, or path filter mismatch).

---

## Task 11: Live deploy to Minikube + smoke test

**Files:** None (verification-only task; produces no commit unless a defect is found).

**Rationale:** Schema validation catches syntax errors but not semantic ones — a Service with no selector, an env-var name mismatch with Pydantic Settings, a probe path that doesn't exist, a NetworkPolicy that drops too much. The full smoke test against a real Minikube cluster is the only way to verify the spec's verifiable end state.

> **Operator prerequisite:** Minikube ≥1.33, kubectl ≥1.30, Docker Desktop running. If not installed, follow the instructions in the Phase 3 README quickstart (added in Task 12) before proceeding.

- [ ] **Step 11.1: Start Minikube with Calico CNI**

```bash
minikube start --cni=calico
```

Expected: cluster comes up, `minikube status` reports Running. Calico CNI enforces NetworkPolicy (the default `auto` CNI does NOT — manifests would be silently ineffective).

- [ ] **Step 11.2: Build the image into Minikube's Docker daemon**

```bash
eval $(minikube docker-env)
docker build -f docker/Dockerfile -t jama-mcp-server:dev .
docker images | grep jama-mcp-server
```

Expected: `jama-mcp-server   dev   <imageid>   <created>   ~266MB`. The image is in Minikube's Docker daemon, not the host's.

- [ ] **Step 11.3: Materialize the real Secret**

```bash
cp k8s/secret.example.yaml k8s/secret.yaml
# Edit k8s/secret.yaml in your editor:
#   - Replace REPLACE_ME_WITH_YOUR_JAMA_OAUTH_CLIENT_ID with your real client_id
#   - Replace REPLACE_ME_WITH_YOUR_JAMA_OAUTH_CLIENT_SECRET with your real secret
# Save the file.
```

Confirm the file is gitignored:

```bash
git check-ignore k8s/secret.yaml
```

Expected: `k8s/secret.yaml`.

- [ ] **Step 11.4: Apply the kustomization**

```bash
kubectl apply -k k8s/
```

Expected output (order may vary):

```
namespace/jama-mcp created
configmap/jama-mcp-config created
secret/jama-mcp-oauth created
networkpolicy.networking.k8s.io/jama-mcp-server created
service/jama-mcp-server created
deployment.apps/jama-mcp-server created
```

- [ ] **Step 11.5: Wait for the Deployment to become Available**

```bash
kubectl wait --for=condition=Available deployment/jama-mcp-server -n jama-mcp --timeout=60s
```

Expected: `deployment.apps/jama-mcp-server condition met` within 60 seconds.

If it times out, debug:

```bash
kubectl describe pod -n jama-mcp -l app.kubernetes.io/name=jama-mcp-server
kubectl logs -n jama-mcp deploy/jama-mcp-server
```

Common failures:
- `ImagePullBackOff` — `eval $(minikube docker-env)` was skipped before docker build; rebuild.
- Pod crash with `RuntimeError: JamaClient must be used as an async context manager` — the lifespan ordering is wrong; should not happen given Task 2's structure but worth checking.
- `JamaAuthError` in logs — credentials in the Secret are wrong; re-edit `k8s/secret.yaml` and `kubectl apply -k k8s/` again.

- [ ] **Step 11.6: Verify both probes are healthy**

```bash
kubectl describe pod -n jama-mcp -l app.kubernetes.io/name=jama-mcp-server | grep -E "Liveness|Readiness|Startup|Events"
```

Expected: no `Liveness probe failed` or `Readiness probe failed` events. The startup probe should have succeeded (no events about it after the first 30 seconds).

- [ ] **Step 11.7: Port-forward and curl the probes**

In one terminal:

```bash
kubectl port-forward -n jama-mcp svc/jama-mcp-server 8765:8765
```

In another terminal:

```bash
curl -fsS http://localhost:8765/health
# Expected: {"status":"ok"}

curl -fsS http://localhost:8765/readyz
# Expected: {"status":"ready"}
```

- [ ] **Step 11.8: MCP Inspector smoke test against pm2.jamacloud.com**

With port-forward still running, open the MCP Inspector and connect to `http://localhost:8765/mcp`. Invoke the `whoami` tool. Expected: a successful response with the OAuth-credentialed user's identity (matches the live integration result from Phase 1 closure).

This is the same smoke test that closed Phase 1 and Phase 2 — the difference is the request now traverses the K8s networking stack: `host:8765 → port-forward → kubelet → Pod → JamaClient → pm2.jamacloud.com`.

- [ ] **Step 11.9: Verify NetworkPolicy is effective**

```bash
# Sibling Pod in the same namespace can reach the Service
kubectl run -n jama-mcp curl-test --rm -i --image=curlimages/curl --restart=Never -- \
  curl -fsS http://jama-mcp-server.jama-mcp.svc:8765/health
# Expected: {"status":"ok"}

# Pod in default namespace cannot reach the Service (NetworkPolicy blocks it)
kubectl run -n default curl-test --rm -i --image=curlimages/curl --restart=Never -- \
  curl --max-time 5 -fsS http://jama-mcp-server.jama-mcp.svc:8765/health
# Expected: timeout / connection refused / blocked
```

The second curl should hang or fail. If it succeeds, the NetworkPolicy isn't being enforced — re-confirm Minikube was started with `--cni=calico`.

- [ ] **Step 11.10: Capture verification evidence**

If everything passes, take a screenshot of the MCP Inspector showing the `whoami` response (mirrors Phase 1+2 closure evidence). Save it for the PR description.

- [ ] **Step 11.11: Tear down**

```bash
kubectl delete ns jama-mcp
# Optional: stop the cluster entirely
# minikube stop
# Or destroy it
# minikube delete
```

Expected: namespace deletion cascades to all resources within. `kubectl get ns` no longer shows `jama-mcp`.

- [ ] **Step 11.12: Plan-Inline correction (if needed)**

If any of steps 11.1-11.10 surfaced a defect in the plan (e.g., env-var name mismatch, missing volume mount, wrong probe path), update the plan inline AT THE TIME the deviation is sanctioned:

1. Edit the relevant task above with the corrected content.
2. Commit the correction with `docs(plan): fix <specific issue> in Phase 3 plan`.
3. Re-run the affected step.

This is the sanctioned plan-inline correction pattern (used in Phase 1 Tasks 3/4/8/9/11/12/13/19 and Phase 2 Task 3 for the COPY README.md omission). The pattern is: fix in the plan (so future re-runs don't re-introduce the bug), then re-run.

This task produces no commit unless a plan-inline correction is needed.

---

## Task 12: README Minikube quickstart section

**Files:**
- Modify: `README.md` (add a new top-level section)

**Rationale:** The README is the primary surface for an external reader (employer, contributor, future-you) to understand how to run the project. Phase 2 added a `## Docker quickstart` section; Phase 3 adds the analogous `## Kubernetes (Minikube) quickstart` section. This is also where the Calico CNI requirement gets documented — without that note, a reader's NetworkPolicy will be silently no-op'd.

- [ ] **Step 12.1: Locate the insertion point**

```bash
grep -nE "^## " README.md
```

Find the line numbers for `## Docker quickstart` and `## Tool reference`. The new section goes BETWEEN them.

- [ ] **Step 12.2: Insert the new section**

Edit `README.md` to add the following new section after `## Docker quickstart` and before `## Tool reference`:

```markdown
## Kubernetes (Minikube) quickstart

Phase 3 deploys the Phase 2 container image to a local Minikube cluster as a stateless `Deployment` with a `ClusterIP` `Service`, locked down by a `NetworkPolicy`, and made reachable for the MCP Inspector via `kubectl port-forward`.

### Prerequisites

- **Minikube ≥1.33** (for Kubernetes 1.30+ support and stable network policy enforcement). Install via `brew install minikube` on macOS — Homebrew handles the Apple Silicon `arm64` build automatically.
- **kubectl ≥1.30** — `brew install kubectl`.
- **kustomize** — bundled into recent kubectl versions; for an explicit install: `brew install kustomize`.
- **Docker Desktop** — required because the Minikube docker-env image-build path uses your existing Docker daemon and the docker driver.

### One-time setup

1. Start Minikube with the Calico CNI (required for NetworkPolicy enforcement):

   ```bash
   minikube start --cni=calico
   ```

   The default `auto` CNI accepts `NetworkPolicy` resources but does NOT enforce them — your manifests would be silently ineffective.

2. Build the image directly into Minikube's Docker daemon:

   ```bash
   eval $(minikube docker-env)
   docker build -f docker/Dockerfile -t jama-mcp-server:dev .
   ```

   Skipping `eval $(minikube docker-env)` builds into the host's Docker daemon, leaving Minikube with no way to find the image (and no registry to fall back on, because we don't push).

3. Materialize the Secret from your existing OAuth credentials:

   ```bash
   cp k8s/secret.example.yaml k8s/secret.yaml
   # Edit k8s/secret.yaml: replace REPLACE_ME values with your real Jama OAuth client_id and client_secret
   ```

   `k8s/secret.yaml` is gitignored — you will never accidentally commit it.

### Deploy

```bash
kubectl apply -k k8s/
kubectl wait --for=condition=Available deployment/jama-mcp-server -n jama-mcp --timeout=60s
```

### Verify

```bash
kubectl port-forward -n jama-mcp svc/jama-mcp-server 8765:8765
# In another terminal:
curl -fsS http://localhost:8765/health   # → {"status":"ok"}
curl -fsS http://localhost:8765/readyz   # → {"status":"ready"}
```

Open the MCP Inspector and connect to `http://localhost:8765/mcp`. Invoke `whoami` to confirm Jamacloud connectivity from inside the Pod.

### Teardown

```bash
kubectl delete ns jama-mcp
minikube stop          # or `minikube delete` to remove the cluster entirely
```

### Troubleshooting

- **`ImagePullBackOff` after apply** — you skipped `eval $(minikube docker-env)` before `docker build`. The image is on the host, not in Minikube. Fix: `eval $(minikube docker-env)` and re-build.
- **Pod stuck in `Pending`** — usually means insufficient resources. Check `kubectl describe pod -n jama-mcp <pod-name>`. Minikube's default 2 CPU / 4GB RAM is plenty for this server.
- **`/readyz` returns 503** — the JamaClient OAuth token isn't fresh. Check `kubectl logs -n jama-mcp deploy/jama-mcp-server` for token-fetch errors. Most common cause: wrong credentials in the Secret. Fix the Secret and `kubectl apply -k k8s/` again — Pods will roll automatically.
- **NetworkPolicy doesn't block traffic** — you started Minikube without `--cni=calico`. Stop and restart with the correct flag: `minikube delete && minikube start --cni=calico`.
```

- [ ] **Step 12.3: Verify the README still renders cleanly**

```bash
grep -E "^## " README.md | head -20
```

Expected: the new `## Kubernetes (Minikube) quickstart` heading appears between `## Docker quickstart` and `## Tool reference`. No duplicate headings.

- [ ] **Step 12.4: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs(readme): add Kubernetes (Minikube) quickstart section

New top-level section between Docker quickstart and Tool reference
documents the Phase 3 deployment path: prerequisites, one-time setup
(start with --cni=calico, build into Minikube's docker-env, materialize
secret.yaml from secret.example.yaml), deploy via kubectl apply -k,
verify via kubectl port-forward + curl + MCP Inspector, and teardown.

Troubleshooting subsection covers the four most likely failures:
ImagePullBackOff (skipped docker-env), Pending pod (resources),
/readyz 503 (bad credentials), NetworkPolicy no-op (wrong CNI).

Note: the Phase 3 status row in the Phases table remains unchanged
here. PR-merge time updates that row, mirroring the Phase 2 pattern.

Refs: #8

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: MEMORY.md status block update (FINAL task)

**Files:**
- Modify: `MEMORY.md`

**Rationale:** This is the FINAL task per the controller-context discipline used in Phase 2. The execution session flips the `## Current phase` block to "Phase 3 active" using the stale text as an Edit anchor; this triggers the visible signal that Phase 3 is in flight. The `## Recent decisions` section also gets three new rows for the Phase 3 plan-author choices (probe split with `/readyz`, NetworkPolicy strictness, kubeconform CI), mirroring the Phase 2 Task 8 pattern.

> **Important:** This task is intentionally LAST. Do not run it in parallel with other tasks — its output is the durable signal that all prior work has landed.

- [ ] **Step 13.1: Read the current MEMORY.md to find the Edit anchors**

```bash
cat MEMORY.md
```

Identify:
1. The `## Current phase` block that says something like "Phase 2 complete; Phase 3 plan written" — this is the stale text that becomes the Edit anchor.
2. The `## Recent decisions` section — new rows append here.

- [ ] **Step 13.2: Flip the `## Current phase` block**

Replace the stale "Phase 2 complete; Phase 3 plan written" block with:

```markdown
## Current phase

**Phase 3 — Kubernetes (Minikube) deployment.** Active on branch `feat/phase-3-minikube` (issue #8). Implementation plan: [`docs/superpowers/plans/2026-05-01-jama-mcp-server-phase-3-minikube.md`](docs/superpowers/plans/2026-05-01-jama-mcp-server-phase-3-minikube.md). Verifiable end state: a `minikube start --cni=calico` cluster runs the server, both probes healthy, MCP Inspector successfully invokes `whoami` against `pm2.jamacloud.com` through the K8s networking stack, and a green K8s validate CI check on the PR.
```

Use the exact stale text as the `old_string` in the Edit tool call so the edit is unambiguous. If the stale text differs from "Phase 2 complete; Phase 3 plan written", use whatever the current text actually is.

- [ ] **Step 13.3: Append three rows to `## Recent decisions`**

Append the following rows to the end of the `## Recent decisions` table (or list, depending on the existing format):

```markdown
- 2026-05-01 — Phase 3 deeper readiness probe: `_readyz` is a separate module-level handler that verifies in-memory OAuth token freshness via `JamaClient.is_token_fresh()`. Liveness stays at the static `/health`. Reason: K8s probe semantics differ (liveness restarts, readiness drops from rotation), and a transiently stale token should not flap into restart loops.
- 2026-05-01 — Phase 3 NetworkPolicy: same-namespace ingress + DNS/443 egress (no Jamacloud-IP allow-list, because Jama Cloud CDN ranges are not published as stable CIDRs). Requires `minikube start --cni=calico` for enforcement; default CNI silently no-ops the policy.
- 2026-05-01 — Phase 3 manifest CI: `.github/workflows/k8s-validate.yml` runs kubeconform schema validation on PR + push. Mirrors Phase 2's docker-build.yml philosophy of running ONLY when relevant files change. Brings the project's CI check count from 6 to 7.
```

- [ ] **Step 13.4: Run linters**

```bash
# MEMORY.md is markdown, not Python; no linter pass needed beyond visual inspection.
grep -nE "^## " MEMORY.md
```

Expected: section headers in the existing order with no duplicates.

- [ ] **Step 13.5: Commit**

```bash
git add MEMORY.md
git commit -m "$(cat <<'EOF'
docs(memory): flip Phase 3 active + capture plan-author decisions

Current phase block flipped from "Phase 2 complete; Phase 3 plan
written" to "Phase 3 active on feat/phase-3-minikube" with a pointer to
the implementation plan and the verifiable end state.

Three Recent decisions rows capture the Phase 3 plan-author choices:
deeper /readyz readiness probe (vs. shallow /health-only), NetworkPolicy
strictness (same-namespace ingress + DNS/443 egress), and kubeconform-
only manifest CI.

This is the final task in the Phase 3 plan, run after all preceding
tasks have committed and the live Minikube smoke test (Task 11) has
verified the end-state criteria.

Refs: #8

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Closing tasks (handled outside this plan)

The following close out Phase 3 once the plan tasks above all land. They are NOT part of the executable plan — the controller (or operator) handles them:

- **Push the branch:** `git push` (each task already pushes incrementally if you push after each commit; otherwise this single push at the end works).
- **Open the PR** with `gh pr create --title "Phase 3 — Kubernetes (Minikube) deployment (closes #8)" --body "<...>"`. The body should reference the plan, summarize the deliverables, and include the MCP Inspector smoke-test screenshot from Task 11.10. Use the project's PR template.
- **Confirm all 7 CI checks pass.** If `K8s validate` fails on PR open, debug the rendered manifest output in the GHA logs.
- **Squash-merge the PR** when all checks are green and the reviewer approves. Use the squash merge subject `Phase 3 — Kubernetes deployment (closes #8) (#<PR>)`.
- **Post-merge memory hygiene:** flip the `## Current phase` block one more time (from "Phase 3 active" to "Phase 3 complete; project in maintenance"), and update the README's Phases table status row from `In progress` to `Complete`. Both updates land in a follow-on `docs(memory):`/`docs(readme):` commit on `main` per the no-separate-PR-for-docs rule.
- **Update the Knowledge Graph** with the Phase 3 milestone entity, any new sanctioned patterns (e.g., the `_state` mutable container pattern, the kustomize-namespace-directive-with-explicit-Namespace pattern), and any gotchas discovered during execution.

These steps are documented in the Phase Handoff Protocol referenced in `~/.claude/CLAUDE.md`.
