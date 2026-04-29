# Jama MCP Server — Working State

## Current phase

**Phase 0 — Initialization (complete)**

**Active branch:** `main`

**Next task:** transition to Phase 1 — Functional MVP per the design spec.

## Phase status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Repository scaffolding, CI/CD, memory hygiene apparatus | Complete |
| 1 | Functional MVP — six MCP tools, both transports | Active (planned) |
| 2 | Docker containerization | Planned |
| 3 | Kubernetes deployment (Minikube) | Planned |

## Recent decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-28 | Approach 1 (two-layer split) approved | Clean separation; client lib reusable later |
| 2026-04-28 | Python 3.12 (not 3.13) | Broader compatibility for clone-and-play audience |
| 2026-04-28 | mypy strict (blocking), not ty | Maturity signal — mypy is the widely-recognized lingua franca |
| 2026-04-28 | Apache 2.0 license | Patent grant; contributor-friendly |
| 2026-04-28 | Public GitHub from Day 1 | Public engineering deliverable from inception |
| 2026-04-28 | FastMCP both transports (stdio + streamable-http) | Same module supports both |
| 2026-04-28 | Three-phase deployment plan (P1 code, P2 Docker, P3 K8s) | Clean troubleshooting boundaries |
| 2026-04-28 | Professional portrayal constraint binding via `validate-docs-placement.sh` hook | Mechanical enforcement |
| 2026-04-28 | Phase 0 inception commit pushed to public GitHub | Repository scaffolded; CI green; ready for Phase 1 |

## Known constraints

- **Repository visibility:** public on GitHub; reviewed by potential employers including Jama Software. Every commit must meet professional standards.
- **OAuth credential discipline:** create a dedicated `jama-mcp-server-dev` credential rather than reusing existing ones; revocable independently.
- **Sandbox URL:** `https://pm2.jamacloud.com` (Jama Software-provisioned sandbox).
- **Author identity:** Arthur Fantaci, `arthur.fantaci@mac.com`.

## Open items deferred to Phase 1

- Provision the `jama-mcp-server-dev` OAuth credential in Jama Connect.
- Populate `.env` locally with the new credential.
- Implement `jama_client.auth` and `jama_client.client`.
- Implement the six MCP tools.
- Author hand-crafted JSON fixtures under `tests/fixtures/jama_responses/`.

## References

- Design spec: [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md)
- Phase 0 plan: [`docs/superpowers/plans/2026-04-28-jama-mcp-server-phase-0-initialization.md`](docs/superpowers/plans/2026-04-28-jama-mcp-server-phase-0-initialization.md)
- Conventions: [`CLAUDE.md`](CLAUDE.md)
- Author's global Claude Code protocols: `~/.claude/CLAUDE.md`
