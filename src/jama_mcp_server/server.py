"""FastMCP application instance and transport entry points."""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import anyio
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

from jama_client import JamaClient, JamaNetworkError, OAuthCredentials
from jama_mcp_server.config import Settings
from jama_mcp_server.logging_config import configure_logging

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from starlette.requests import Request


@dataclass
class _ServerState:
    """Mutable container for HTTP-server-process state read by Starlette routes.

    The streamable-HTTP route handlers registered via ``server.custom_route``
    cannot reach FastMCP's per-MCP-session ``lifespan_context`` (that context
    is only visible to MCP tools via ``ctx.request_context.lifespan_context``).
    This container bridges the gap: ``main_http`` populates it before Uvicorn
    begins serving so the readiness probe reports 'ready' from the moment the
    Pod accepts connections, regardless of whether any MCP session is open.

    Owned by ``_run_http_with_warm``; written exactly once at HTTP-server
    startup and cleared exactly once at shutdown.
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
    """Construct and tear down a per-MCP-session :class:`JamaClient`.

    FastMCP invokes this lifespan once per MCP session (via the low-level
    ``Server`` class) - NOT at HTTP server startup. The yielded client lands
    in ``ctx.request_context.lifespan_context['jama_client']`` for tools.

    Eagerly warms the OAuth token cache at session start so the first tool
    call does not pay the OAuth round-trip latency, and so credential errors
    surface at session start rather than on the first user-driven tool call.
    """
    factory = client_factory or _default_client_factory
    client = factory(settings)
    async with client:
        await client.warm_token_cache()
        yield {"jama_client": client}


async def _health(_request: Request) -> JSONResponse:
    """Return a static liveness payload for HTTP healthcheck probes.

    The handler is intentionally cheap and stateless: it does not touch
    the JamaClient or any external service. Kubernetes liveness probes
    (Phase 3) and the Phase 2 Docker HEALTHCHECK both target this endpoint.
    For deeper readiness checks (OAuth token freshness), see _readyz.
    """
    return JSONResponse({"status": "ok"})


async def _readyz(_request: Request) -> JSONResponse:
    """Return a deeper readiness payload that drives Kubernetes readiness probes.

    Unlike liveness (``/health``, static), readiness reflects whether the
    Pod should remain in the Service's endpoint pool. For this server that
    means: the HTTP-server-process JamaClient is initialized AND its cached
    OAuth token is fresh (not aged beyond 90 percent of TTL).

    The check is in-memory only (no I/O to Jamacloud) so that K8s probing
    every few seconds does not pressure the upstream OAuth endpoint.
    ``_run_http_with_warm`` populates ``_state.jama_client`` and warms the
    cache before Uvicorn begins serving; subsequent tool calls refresh
    proactively at >=90 percent TTL via ``_ensure_token``. A non-fresh token
    in a busy deployment indicates a real problem; in an idle one it simply
    means the TTL elapsed without a tool call.

    Returns:
        JSONResponse with status_code 200 and body ``{"status": "ready"}``
        when the cached token is fresh; 503 with body ``{"status":
        "not_ready", "reason": "<client_not_initialized |
        token_unavailable>"}`` otherwise.
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
    server.custom_route("/readyz", methods=["GET"])(_readyz)

    # Register tools.
    from jama_mcp_server import tools  # noqa: PLC0415

    tools.register(server)
    return server


async def _run_http_with_warm(
    server: FastMCP,
    settings: Settings,
    client_factory: Callable[[Settings], JamaClient] | None = None,
    *,
    warm_retries: int = 3,
) -> None:
    """Eagerly warm the OAuth cache and populate ``_state`` before Uvicorn serves.

    FastMCP's ``streamable_http_app()`` constructs a Starlette ASGI app
    whose lifespan is fixed to ``session_manager.run()``. The user-supplied
    ``lifespan=`` parameter on ``FastMCP()`` only runs per-MCP-session via
    the low-level Server. To populate ``_state.jama_client`` before the
    first Kubernetes readiness probe lands - and well before any MCP client
    connects - we materialize a long-lived JamaClient here, run
    ``warm_token_cache``, then enter ``run_streamable_http_async``.

    The warm is retried on :class:`JamaNetworkError` to absorb startup-time
    transient errors. The motivating case is the Kubernetes CNI policy
    programming race: when a Pod starts, Calico (or any policy-enforcing
    CNI) takes a moment to materialize the NetworkPolicy rules; egress
    issued during that window fails with ConnectTimeout. A small
    exponential backoff bridges the gap. Other JamaClient exceptions
    (auth, server) are not retried - they are fatal and propagate
    immediately so the Pod crashes with a clear K8s rollout signal.

    Credential errors (HTTP 401 from the OAuth endpoint) raise out of
    ``warm_token_cache`` and crash the Pod at startup, exactly the right
    failure mode for K8s rollout signaling.
    """
    factory = client_factory or _default_client_factory
    client = factory(settings)
    async with client:
        for attempt in range(warm_retries):
            try:
                await client.warm_token_cache()
                break
            except JamaNetworkError:
                if attempt + 1 == warm_retries:
                    raise
                await anyio.sleep(2**attempt)
        _state.jama_client = client
        try:
            await server.run_streamable_http_async()
        finally:
            _state.jama_client = None


def main_stdio() -> None:
    """Run the MCP server using the stdio transport."""
    settings = Settings()
    configure_logging(settings.mcp_transport)
    server = build_server(settings=settings)
    server.run(transport="stdio")


def main_http() -> None:
    """Run the MCP server using the streamable-HTTP transport.

    Wraps ``server.run_streamable_http_async()`` with eager OAuth-token
    cache warming via ``_run_http_with_warm`` so the readiness probe
    reports 'ready' from the moment the Pod accepts connections.
    """
    settings = Settings()
    configure_logging(settings.mcp_transport)
    server = build_server(settings=settings)
    anyio.run(_run_http_with_warm, server, settings)
