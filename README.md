# Jama MCP Server

A Model Context Protocol (MCP) server providing programmatic access to a hosted [Jama Connect](https://www.jamasoftware.com/) instance via its REST API. Implemented with rigorous typing, professional tooling, and a phased delivery roadmap.

The server is positioned as an **anticipatory placeholder for the official Jama Connect MCP™** vendor product — replicating that product's expected tool surface so the Software Engineer Use Case can be demonstrated end-to-end before Jama Connect MCP™ is generally available.

## Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0     | Repository scaffolding, CI/CD, memory hygiene apparatus | Complete |
| 1     | Functional MVP — six MCP tools demonstrating end-to-end traceability | Complete |
| 2     | Docker containerization | Complete |
| 4.5   | `create_comment` write tool | Complete |
| MVP build | Six new MCP tools across two namespaces (`core/*` + `workflow/*`) | Complete |

The full design is published in [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md).

## Architecture

The project is organized as two top-level Python packages under a single source tree:

- **`jama_client`** — an asynchronous Python library wrapping a curated subset of the Jamacloud REST API. Owns authentication, transport, retry policy, and Pydantic-typed entity models.
- **`jama_mcp_server`** — a [FastMCP](https://github.com/modelcontextprotocol/python-sdk) server that imports `jama_client` and exposes its operations as MCP tools, supporting both `stdio` and `streamable-http` transports.

This split keeps the Jama API integration reusable independently of the MCP server (for a future MCP client agent, a CLI, or a notebook).

## Tool Namespaces

Tools are organized into two namespaces that reflect their architectural role:

### `core/*` — Anticipatory Jama Connect MCP™ placeholders

Tools that mirror functionality expected in the Jama Connect MCP™ vendor product. Each tool maps directly to a Jamacloud REST endpoint. When Jama Connect MCP™ becomes available, these tools can be replaced transparently — the tool names, signatures, and return schemas are designed to be forward-compatible.

### `workflow/*` — AI-consumption macro tools

Tools that compose `core/*` primitives into higher-level operations optimized for agentic AI consumption. These are explicitly **not** expected in Jama Connect MCP™; they represent this project's value-add layer demonstrating the engineering practice of designing MCP tools for agent workflows.

## MCP tool surface (thirteen operational tools)

### `core/*` reads

1. `whoami` — identifies the authenticated user.
2. `list_projects` — enumerates accessible Jama projects.
3. `get_item(item_id)` — retrieves a single Jama item; returns `{"found": false, ...}` on 404.
4. `search_items(project_id, query)` — searches items within a project.
5. `get_downstream_relationships(item_id)` — traces relationships from a requirement toward its tests.
6. `get_test_runs_for_item(item_id)` — retrieves test execution history for a covered item.
7. `list_item_types(project_id)` — enumerates item types configured for a project (e.g. `CODE`, `SUBSR`).
8. `list_relationship_types(project_id)` — enumerates relationship types (e.g. `"Implemented by"`).
9. `list_items_by_type(project_id, item_type, max_items=200)` — lists items of a given type with pagination; returns `{"items": [...], "max_items_reached": bool}`.

### `core/*` writes

10. `create_comment(item_id, project_id, body, comment_type="GENERAL")` — posts a top-level comment. Accepts any of Jama's eight `commentType` enum values; compliance-review workflows should use `ISSUE` for non-compliant findings.
11. `create_item(project_id, item_type, parent, name, fields=None)` — creates a new Jama item of the specified type within a parent Set. Type-specific field keys follow Jama's `<fieldName>$<typeId>` pattern (e.g. `path$114`).
12. `create_relationship(from_item, to_item, relationship_type)` — creates a directed relationship between two items. Validates that neither endpoint is a Set (item type 31) before submission — Sets carry no relationships in Jama.

### `workflow/*`

13. `create_path_a_trace(project_id, source_requirement_key, code_path, code_version, ...)` — high-level workflow: given a requirement document key, a code file path, and a code version, validates the source requirement exists, creates a Code item in the Implementation Code Set, and creates an "Implemented by" relationship from the requirement to the Code item. Optional parameters override type and Set discovery (defaults resolve via `list_item_types` / `list_relationship_types` / `list_items_by_type` with per-session caching).

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

The Inspector lists thirteen tools; invoking `whoami` round-trips through the server to your Jamacloud sandbox and returns the authenticated user.

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
