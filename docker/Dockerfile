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

# Layer 2: install the project itself. README.md is required because
# pyproject.toml declares `readme = "README.md"`, which hatchling reads
# during package-metadata validation when uv installs the project.
# Re-runs when src/ or README.md changes.
COPY README.md ./
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
