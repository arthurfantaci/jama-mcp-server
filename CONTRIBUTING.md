# Contributing to the Jama MCP Server

Thanks for considering a contribution. This project is in active development; the contribution surface is intentionally narrow during Phase 0 and Phase 1.

## Quick links

- [Design specification](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md)
- [Project conventions (`CLAUDE.md`)](CLAUDE.md)
- [Working state (`MEMORY.md`)](MEMORY.md)

## Local development setup

```bash
git clone https://github.com/arthurfantaci/jama-mcp-server.git
cd jama-mcp-server
uv sync --extra dev
uv run pre-commit install
cp .env.example .env
# Populate .env with your Jamacloud OAuth credentials.
```

## Branch and PR workflow

- All work after Phase 0 follows an Issue → Branch → PR workflow.
- Branch naming: `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`, `refactor/<short-name>`, `test/<short-name>`, `chore/<short-name>`, `ci/<short-name>`.
- Commits follow the [Conventional Commits](https://www.conventionalcommits.org/) specification with imperative-mood subjects.
- Documentation-only changes (touching only `CLAUDE.md`, `MEMORY.md`, or per-user memory files) do not get separate issues, branches, or PRs; they are bundled into the next phase's PR.

## Pre-commit checks

The following must pass before a commit lands:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -m "not integration"
```

`pre-commit install` enables these as git hooks. Pre-commit also runs `gitleaks` for secret scanning and `validate-docs-placement` for documentation hygiene.

## Coding conventions

- **Python 3.12.** All code targets Python 3.12 syntax and standard library.
- **Full type annotations.** All public functions, classes, and methods have type annotations on parameters and return values. `mypy --strict` is a blocking CI check.
- **Google-style docstrings.** All public functions, classes, and methods have Google-style docstrings. Ruff's `D` rules enforce this.
- **Async throughout.** New code in `jama_client` and `jama_mcp_server` is async by default.
- **Errors map to typed exceptions.** Follow the two-layer error policy in the design specification.

## Testing

- **Unit tests** (`tests/unit/`) — `respx`-mocked, fast, run on every save and in CI.
- **Integration tests** (`tests/integration/`) — opt-in via `pytest -m integration`, hit the real Jamacloud sandbox, never run in CI.
- **Protocol tests** (`tests/unit/jama_mcp_server/test_protocol.py`) — use FastMCP's in-process test client.

New `jama_client` code targets at least 80 percent line coverage. New `jama_mcp_server` code triggers every error class at least once.

## Documentation

- Public docs live in `docs/` root and `docs/superpowers/{specs,plans}/`.
- Working notes, raw plans, and exploratory writing live in `docs/internal/` (gitignored).
- Architectural changes update both the relevant design spec and `CLAUDE.md`.

## Reporting issues

Use the GitHub issue templates. Redact secrets and personally identifying information.

## Security

See [`SECURITY.md`](SECURITY.md) for the security disclosure policy.
