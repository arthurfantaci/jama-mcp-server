# Jama MCP Server — Working State

## Current phase

**MVP build phase initiated 2026-05-10.** Phase 5 (write tools) un-cancelled. New sibling public repo for VS Code Extension committed. Strategic pivot: shift from "create new IG2200 project" demo dependency to **Sandbox-as-demo-target** (evolve project 127 / "Arthur Sandbox" in place; modify and enhance current data and structures as needed). Path A trace flow validated end-to-end against `pm2.jamacloud.com` 2026-05-10; SUSPECT auto-flag empirically verified.

The fresh session begins MVP planning under the Superpowers plugin (start with `superpowers:brainstorming` to settle scope, then `superpowers:writing-plans`, then `superpowers:executing-plans`). Public-first development conventions apply (professional portrayal, gitleaks, validate-docs-placement, Conventional Commits, Issue → Branch → PR for code; docs/memory-only changes commit directly to the working branch per `CLAUDE.md`).

**Active branch:** `main`
**Open PR:** none
**Local commits ahead of origin:** 3 (docs/memory)
**Most recent code merge:** [PR #10](https://github.com/arthurfantaci/jama-mcp-server/pull/10) — Phase 4.5 `create_comment` (squash-merged 2026-05-02, merge commit `6e28b9f`)

## Demo seed data in Sandbox (project 127, 2026-05-10)

Use these existing artifacts as the MVP's seed data; do NOT recreate or destructively reset them without deliberate intent. Modify and enhance freely as the MVP needs more breadth (additional Software Requirements, additional Code items, etc.).

- **`AF-SUBSS-25`** (item 115100, V3) — Source side of demo trace. *"SWR-OD-001: Module shall detect upstream occlusion within 500 ms."* Type 87 Subsystem Requirement, located at `Software Subsystems → Thermostat OS → Software Requirements` (parent `AF-SET-180`). Currently shows description-vs-`req_value$87` inconsistency (description says 300 ms, `req_value$87` says "500") — kept deliberately as Persona 2 (compliance-officer) demo bait.
- **`AF-CODE-1`** (item 115102) — Target side of demo trace. *"occlusion_detector.py:detect_upstream_occlusion."* Type 114 Code, located at `Software Subsystems → Implementation Code (for trace)` (parent `AF-SET-212`). Carries `path$114 = "src/occlusion_detection/occlusion_detector.py:7-42"`, `code_version$114 = "v1.0.0-rc1"`.
- **Relationship 18505** — `from_item: 115100, to_item: 115102, relationship_type: 19` (UI label "Implemented by"), currently `suspect: true` after the verification description-edit.

## Phase status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Repository scaffolding, CI/CD, memory hygiene apparatus | Complete |
| 1 | Functional MVP — six client operations + six MCP tools, both transports | Complete (PR #5 merged 2026-04-29) |
| 2 | Docker containerization | Complete (PR #7 merged 2026-04-30) |
| 4.5 | `create_comment` write tool — narrow Phase 4.5 carve-out | Complete (PR #10 merged 2026-05-02, merge commit `6e28b9f`) |
| 5 | Write tools: `create_relationship`, `create_item` | Planned — un-cancelled 2026-05-10; MVP scope |
| 6 | Read tool expansion: `get_item_children`, `list_item_types`, `list_relationship_rules`, `list_relationship_types`, `get_picklist_options`, `get_upstream_relationships`, optionally `get_comments` | Planned — un-cancelled 2026-05-10; MVP scope |
| 7 | VS Code Extension Tier 2: command palette + QuickPick + HITL gate + editor insertion + status bar | Planned — new sibling public repo; MVP scope |

## What's validated as of 2026-05-10

End-to-end Path A trace flow proven on real Jamacloud data using only the existing seven MCP tools:

```text
search_items(127, "AF-SUBSS-25") → AF-SUBSS-25 (Subsystem Requirement)
get_downstream_relationships(115100) → relationship 18505 → to_item 115102
get_item(115102) → AF-CODE-1 (Code item with path$114, code_version$114)
```

- `Subsystem Requirement → Code, "Implemented by"` rule pre-existed on the tenant's default project type — no admin work needed.
- `path$114` (file path) and `code_version$114` (version) populated and readable via API.
- Trace appears in Jama's native Relationships viewer (Frame 6 of the brief).
- SUSPECT auto-flag fires when source `description` edited — commercial centerpiece confirmed on real data.
- "Implemented by" semantic close to the brief's "Implemented in code at" wording.

## Key Sandbox structural facts

- Project 127 ("Arthur Sandbox") uses Smart Thermostat sample data, renamed/re-keyed to `AF-` prefix.
- Item types in use: 22 (Attachment), 24 (Requirement, generic), 30 (Component, system), 31 (Set, system), 33 (Text), 86 (System Requirement, typeKey `EM_SR`, "Redwire" package), 87 (Subsystem Requirement, typeKey `SUBSR`, "Redwire"), 114 (Code, typeKey `CODE`, "Aero" package).
- Type 86 carries `safety_classification$86` field with infotip "IEC 62304" — medical-device readiness signal worth citing in the IG2200 narrative.
- **Type 31 (Set) has NO `RELATIONSHIPS` widget** — Sets cannot be source/target of relationships; trace edges terminate only on content items inside Sets. Critical Jama gotcha.
- `search_items` does not stem singular/plural matches (e.g., "Software Requirement" misses items in a Set named "Software Requirements"); new items have ~30s-few-minute search-index lag.
- Default project type permits `Subsystem Requirement → Code, "Implemented by"` without explicit rule addition.

## MCP tool surface (seven operational tools)

**Read:** `whoami`, `list_projects`, `get_item`, `search_items`, `get_downstream_relationships`, `get_test_runs_for_item`. **Write:** `create_comment` (Phase 4.5). Phases 5+6 will expand this surface materially.

## Known constraints

- **Repository visibility:** public on GitHub; reviewed by potential employers including Jama Software. Every commit must meet professional standards.
- **OAuth credential discipline:** dedicated `jama-mcp-server-dev` credential.
- **Sandbox URL:** `https://pm2.jamacloud.com`.
- **Author identity:** Arthur Fantaci, `arthur.fantaci@mac.com`.

## References

- Design spec: [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md)
- Phase 1 plan: [`docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md`](docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md)
- Phase 2 plan: [`docs/superpowers/plans/2026-04-30-jama-mcp-server-phase-2-docker.md`](docs/superpowers/plans/2026-04-30-jama-mcp-server-phase-2-docker.md)
- Conventions: [`CLAUDE.md`](CLAUDE.md)
- Author's global protocols: `~/.claude/CLAUDE.md`
- Strategic positioning (gitignored): `docs/internal/jama-poc-strategic-positioning.md`
- Consulting artifacts (gitignored, finalized 2026-05-06; need updates to reflect 2026-05-10 Sandbox-as-demo pivot): `docs/internal/specs/InfusionGuard 2200 - Project Configuration Specification.md` and `docs/internal/briefs/InfusionGuard 2200 - Software Engineer Workflow Brief.md`

## Recent decisions (last 5)

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-10 | **Phase 5 un-cancelled, MVP build phase initiated.** Add `create_relationship` + `create_item` write tools to the public MCP server. Add priority read tools (`get_item_children`, `list_item_types`, `list_relationship_rules`, `list_relationship_types`, `get_picklist_options`, `get_upstream_relationships`). Build Tier 2 VS Code Extension in a new sibling public repo (TypeScript stack). Pivot to **Sandbox-as-demo-target**: evolve project 127 in place rather than creating a new IG2200 project. Same public-first conventions throughout. Consulting artifacts will need updates to reflect this pivot (bundle into the MVP's documentation work, not a separate docs PR). | Preston's Jama Connect MCP™ access and Sandbox project-creation rights both delayed indefinitely. "Fully-operational MVP" requires a write surface somewhere; pivoting to evolve-the-Sandbox eliminates the project-creation dependency and uses the already-validated AF-SUBSS-25 / AF-CODE-1 / relationship 18505 as seed data. |
| 2026-05-10 | **Path A trace flow validated end-to-end on real Jamacloud.** Read-side smoke test demonstrable today via the existing seven MCP tools. SUSPECT auto-flag verified working. Default project type already permits `Subsystem Requirement → Code "Implemented by"` (no admin work needed). | Commercial centerpiece of the consulting proposal proven on real data; turns the proposal from forward-looking spec into evidence of execution. |
| 2026-05-06 | Software Engineer consulting-proposal artifacts finalized and renamed to buyer-facing filenames. Path A elevated to recommended primary trace mechanism (spec Section 5 / brief Frame 6). Frame 6 redrawn from real Jama UI screenshot to remove fabricated affordances. | Both documents commercial-quality and internally coherent; SUSPECT auto-flag is the regulatory-hygiene differentiator that Path A alone unlocks. |
| 2026-05-04 | Jama Software announced GA of Jama Connect MCP™. Phases 5 and 6 of our MCP server were definitively cancelled at that point. **Reversed by 2026-05-10 decision above** due to access delay. | Vendor's own write surface was supposed to make our write tools redundant. |
| 2026-05-02 | Phase 4.5 PR #10 squash-merged. `create_comment` shipped. Three undocumented Jama API behaviors codified in `CLAUDE.md` (inReplyTo NPE, meta-only POST envelope, eight commentType enum values). | Phase 4.5 closed. |
