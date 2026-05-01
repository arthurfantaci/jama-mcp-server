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
