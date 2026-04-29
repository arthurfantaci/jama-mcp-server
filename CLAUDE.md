# Jama MCP Server — Claude Code Instructions

## Project overview

Model Context Protocol server providing access to Jamacloud (Jama Connect SaaS) via its REST API. Two-layer architecture: `jama_client` (async REST client) and `jama_mcp_server` (FastMCP server). Phase 1 MVP exposes six tools demonstrating requirements-to-test-runs traceability.

Full design: [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md).

## Repository visibility

This repository is public on GitHub from inception and is reviewed by potential employers, including Jama Software engineers and their hiring managers. Every committed file must portray the project, the author, and the role of AI-assisted development as serious, professional Agentic AI Application Engineering work.

**Mechanical enforcement:**

- `.claude/hooks/validate-docs-placement.sh` warns on staged docs containing internal markers.
- `gitleaks` (pre-commit) scans every commit for staged credentials.
- `docs/internal/` and `docs/plans/` are gitignored escape hatches for working notes.
- The PR template includes a "Professional Portrayal" checklist.

**Excluded from public surface:** debug `print` statements, commented-out code, AI-collaboration artifacts (e.g., narrative comments referencing the assistant by name), scratch files, half-finished thought experiments.

## Project layout

- `src/jama_client/` — async Jamacloud REST client. Owns auth, transport, models, exceptions.
- `src/jama_mcp_server/` — FastMCP server, tool definitions, transport entry points, lifespan management.
- `tests/{unit,integration}/` — three-tier test suite (unit, integration, MCP-protocol).
- `docs/superpowers/specs/` — design specifications.
- `docs/superpowers/plans/` — implementation plans.

## Conventions

- **Python 3.12**, managed with `uv`. `uv.lock` is committed.
- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `ci:`.
- **Issue → Branch → PR** for all phases after Phase 0.
- **Documentation-only changes do NOT get separate issues, branches, or PRs.** Bundle into the next phase's PR or commit directly to the working branch.
- **Async throughout.** New code in `jama_client` and `jama_mcp_server` is async by default.
- **Type annotations and Google-style docstrings on every public surface.** Enforced by ruff `ANN` and `D` rules.
- **Errors map to typed exceptions** per the two-layer policy in the design spec.

## Tooling rigor

- **Ruff** (21 rule families): E, W, F, I, N, D, UP, ANN, S, B, C4, SIM, TCH, RUF, TRY, EM, PIE, PT, RET, ARG, PL. Google docstring convention. Per-file relaxations for tests.
- **Mypy strict** (blocking CI check): `strict = true`, pydantic plugin, no implicit reexport.
- **Pytest** with `asyncio_mode = "auto"` and `--strict-markers`.
- **Pre-commit**: ruff, mypy, gitleaks, validate-docs-placement, standard hygiene hooks.

## Verification before PR

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -m "not integration"
```

## Memory hygiene

This project maintains two memory tiers:

- **Public** (in repo, version-controlled): `CLAUDE.md` (this file, ~150 lines max), `MEMORY.md` (~100 lines max), `docs/superpowers/{specs,plans}/`.
- **Private** (per-user): `~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/{CLAUDE.md, memory/MEMORY.md}`, plus the Knowledge Graph via the `memory` MCP server.

**Slash commands:**

- `/memory-audit` — invoke the memory-hygiene skill.
- `/pre-compact` — Pre-Compaction Protocol (persist findings, update MEMORY.md).
- `/phase-handoff` — Phase Handoff Protocol (merge PR, clean branches, update memory).

**Triggers** for memory updates: phase completion, new convention codified, non-obvious gotcha discovered, architectural change, approach to auto-compaction, post-PR-merge with path/convention changes.

See [`.claude/skills/memory-hygiene/SKILL.md`](.claude/skills/memory-hygiene/SKILL.md) for the audit checklist.

## Pointers to global protocols

The author's `~/.claude/CLAUDE.md` defines:

- Knowledge Graph Memory Protocol (when to write to KG via `memory` MCP server).
- Context Recovery Protocol (re-establishing state after compaction).
- Phase Handoff Protocol (cross-phase memory hygiene).
- Pre-Compaction Protocol (persist findings before auto-compact).

This project follows those protocols; do not duplicate them here.
