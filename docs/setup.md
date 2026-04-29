# Local Setup Guide

This document supplements the README's quick-start section with detailed setup instructions for new contributors.

## Prerequisites

- **Python 3.12** — installed via your preferred Python version manager. `uv` will install it automatically if missing.
- **`uv`** — the dependency manager. Install via `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux) or `winget install --id=astral-sh.uv` (Windows).
- **`git`** — version 2.30 or newer.
- **A Jamacloud account** — with a NAMED Creator license (required for REST API access) and OAuth 2.0 client credentials.

## Step 1: Clone the repository

```bash
git clone https://github.com/arthurfantaci/jama-mcp-server.git
cd jama-mcp-server
```

## Step 2: Install dependencies

```bash
uv sync --extra dev
```

This creates a `.venv/` directory, installs all runtime and development dependencies, and pins versions per `uv.lock`.

## Step 3: Install pre-commit hooks

```bash
uv run pre-commit install
```

The hooks run on every commit and enforce ruff lint/format, mypy strict, gitleaks secret scanning, and the `validate-docs-placement` documentation hygiene check.

## Step 4: Provision OAuth credentials

Open Jama Connect, navigate to **My Profile → Set API Credentials using OAuth 2.0**, and create a new credential named `jama-mcp-server-dev` (or similar). Copy the client ID and secret.

## Step 5: Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and populate:

```text
JAMA_BASE_URL=https://pm2.jamacloud.com
JAMA_OAUTH_CLIENT_ID=<your-client-id>
JAMA_OAUTH_CLIENT_SECRET=<your-client-secret>
MCP_TRANSPORT=stdio
```

`.env` is gitignored; it never enters the repository.

## Step 6: Verify the install

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -m "not integration"
```

All four commands should exit with status 0.

## Step 7: Run the integration smoke tests (optional)

```bash
uv run pytest -m integration
```

The integration suite hits the real Jamacloud sandbox and is skipped automatically when `JAMA_OAUTH_CLIENT_ID` or `JAMA_OAUTH_CLIENT_SECRET` are unset.

## Step 8: Run the MCP server (stdio transport)

```bash
uv run jama-mcp-stdio
```

The server reads `MCP_TRANSPORT=stdio` from `.env` (or defaults to stdio if unset) and waits on stdin for JSON-RPC requests. Press `Ctrl-C` to stop.

## Step 9: Run the MCP server (streamable-HTTP transport)

```bash
MCP_TRANSPORT=streamable-http uv run jama-mcp-http
```

The server binds to `MCP_HTTP_HOST:MCP_HTTP_PORT` (default `127.0.0.1:8765`) and exposes the streamable-HTTP transport at `/mcp`. Logs go to stdout in this mode (the convention for container deployments).

## Step 10: Connect via MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run jama-mcp-stdio
```

The Inspector launches the server as a subprocess, lists the six registered tools, and lets you invoke each one interactively. Invoking `whoami` is the fastest end-to-end smoke test — it round-trips through the server, authenticates against Jamacloud, and returns your authenticated user.

## Phase status

Setup guide reflects Phase 1 (functional MVP, complete). Phase 2 (Docker containerization) and Phase 3 (Kubernetes / Minikube) will extend this document. See [`docs/superpowers/specs/`](superpowers/specs/) for the full design.
