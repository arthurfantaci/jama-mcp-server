# Jama MCP Server

A Model Context Protocol (MCP) server providing programmatic access to a hosted [Jama Connect](https://www.jamasoftware.com/) instance via its REST API. Implemented with rigorous typing, professional tooling, and a phased delivery roadmap.

## Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0     | Repository scaffolding, CI/CD, memory hygiene apparatus | Complete |
| 1     | Functional MVP — six MCP tools demonstrating end-to-end traceability | Complete |
| 2     | Docker containerization | Planned |
| 3     | Kubernetes deployment (Minikube) | Planned |

The full design is published in [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md).

## Architecture

The project is organized as two top-level Python packages under a single source tree:

- **`jama_client`** — an asynchronous Python library wrapping a curated subset of the Jamacloud REST API. Owns authentication, transport, retry policy, and Pydantic-typed entity models.
- **`jama_mcp_server`** — a [FastMCP](https://github.com/modelcontextprotocol/python-sdk) server that imports `jama_client` and exposes its operations as MCP tools, supporting both `stdio` and `streamable-http` transports.

This split keeps the Jama API integration reusable independently of the MCP server (for a future MCP client agent, a CLI, or a notebook).

## Phase 1 tool surface

The Phase 1 MVP exposes six MCP tools demonstrating Jama Connect's signature requirements-to-test-runs traceability workflow:

1. `whoami` — identifies the authenticated user.
2. `list_projects` — enumerates accessible Jama projects.
3. `get_item(item_id)` — retrieves a single Jama item.
4. `search_items(project_id, query)` — searches items within a project.
5. `get_downstream_relationships(item_id)` — traces relationships from a requirement toward its tests.
6. `get_test_runs_for_item(item_id)` — retrieves test execution history for a covered item.

## Quick start

```bash
git clone https://github.com/arthurfantaci/jama-mcp-server.git
cd jama-mcp-server
uv sync --extra dev
cp .env.example .env
# Populate .env with your Jamacloud OAuth credentials.
uv run jama-mcp-stdio
```

Smoke-test the server with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run jama-mcp-stdio
```

The Inspector lists six tools; invoking `whoami` round-trips through the server to your Jamacloud sandbox and returns the authenticated user.

## Tool reference

| Tool | Arguments | Returns |
|------|-----------|---------|
| `whoami` | none | The authenticated user. |
| `list_projects` | none | Accessible Jama projects (first page). |
| `get_item` | `item_id: int` | The item, or `{"found": false, ...}` on 404. |
| `search_items` | `project_id: int`, `query: str` | Items within the project matching the query. |
| `get_downstream_relationships` | `item_id: int` | Downstream relationships from the item. |
| `get_test_runs_for_item` | `item_id: int` | Test runs that exercise the item. |

## Configuration

The server reads its configuration from environment variables (or a `.env` file). See [`.env.example`](.env.example) for the full list. The required variables are:

| Variable | Purpose |
|----------|---------|
| `JAMA_BASE_URL` | Jamacloud REST API base URL (e.g., `https://pm2.jamacloud.com`) |
| `JAMA_OAUTH_CLIENT_ID` | OAuth 2.0 client ID provisioned in Jama Connect |
| `JAMA_OAUTH_CLIENT_SECRET` | OAuth 2.0 client secret |
| `MCP_TRANSPORT` | `stdio` or `streamable-http` |

## Development

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -m "not integration"
```

Pre-commit hooks (ruff, mypy, gitleaks, validate-docs-placement) install via:

```bash
uv run pre-commit install
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full contribution workflow.

## Documentation

- [`docs/superpowers/specs/`](docs/superpowers/specs/) — design specifications.
- [`docs/superpowers/plans/`](docs/superpowers/plans/) — implementation plans.
- [`docs/setup.md`](docs/setup.md) — local setup instructions.
- [`CLAUDE.md`](CLAUDE.md) — Claude Code project conventions.
- [`MEMORY.md`](MEMORY.md) — project working state.

## Security

See [`SECURITY.md`](SECURITY.md) for the security disclosure policy.

## License

Apache License 2.0. See [`LICENSE`](LICENSE) for the full text.
