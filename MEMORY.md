# Jama MCP Server — Working State

## Current phase

**MVP build phase — cloud routine submitted 2026-05-10.** Scope locked at five `core/*` primitives (`create_item`, `create_relationship`, `list_item_types`, `list_relationship_types`, `list_items_by_type`) plus one `workflow/*` macro tool (`create_path_a_trace`). Strategic frame: anticipatory placeholder for Jama Connect MCP™; host-agnostic foundation; VS Code Extension / Skill / Plugin deferred as customer-specific deliverables per **Option 2**. Delivery: single GitHub [issue #13](https://github.com/arthurfantaci/jama-mcp-server/issues/13) → single working branch (`mvp/foundation-tools`, to be created by the routine) → single PR opened by an autonomous cloud routine running on Anthropic infrastructure. Sandbox-as-demo-target (project 127) confirmed. Path A trace flow validated 2026-05-10 against `pm2.jamacloud.com`; SUSPECT auto-flag empirically verified.

**Cloud routine status (2026-05-10):** First cloud routine for this project submitted at `claude.ai/code`. Schedule trigger: once at 2026-05-10 18:10 EDT. Repository: `arthurfantaci/jama-mcp-server`. Connectors: empty. Behavior → Auto-fix pull requests: OFF. Permissions → Allow unrestricted git push: OFF (defense-in-depth). Routine prompt was at `/tmp/claude/cloud_routine_prompt.md` locally (ephemeral). Expected runtime: 1–3 hours. **Next interaction with this project is the PR review on GitHub.**

Design spec: [`docs/superpowers/specs/2026-05-10-jama-mvp-build-design.md`](docs/superpowers/specs/2026-05-10-jama-mvp-build-design.md). Public-first development conventions apply (professional portrayal, gitleaks, validate-docs-placement, Conventional Commits, Issue → Branch → PR for code; docs/memory-only changes commit directly to the working branch per `CLAUDE.md`).

**Active branch:** `main` (working branch `mvp/foundation-tools` created by cloud routine during its run)
**Open PR:** none yet (cloud routine will open one against `main` upon completion; expected ~1–3 hours after 18:10 EDT)
**Local commits ahead of origin:** updated per session (was 0 after the push that preceded routine submission)
**Most recent code merge:** [PR #10](https://github.com/arthurfantaci/jama-mcp-server/pull/10) — Phase 4.5 `create_comment` (squash-merged 2026-05-02, merge commit `6e28b9f`)
**Open issues:** [#13](https://github.com/arthurfantaci/jama-mcp-server/issues/13) — MVP build phase (cloud routine in flight)

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
| MVP build | Six new MCP tools: `core/*` primitives (`create_item`, `create_relationship`, `list_item_types`, `list_relationship_types`, `list_items_by_type`) + `workflow/*` macro (`create_path_a_trace`); single-PR cloud-routine delivery | Planned — design spec committed 2026-05-10 |
| 7 | VS Code Extension Tier 2 | Deferred — customer-specific deliverable per Option 2 (2026-05-10); reinstatable as follow-on engagement scope |

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

**Read:** `whoami`, `list_projects`, `get_item`, `search_items`, `get_downstream_relationships`, `get_test_runs_for_item`. **Write:** `create_comment` (Phase 4.5). MVP build phase will expand this to thirteen tools across `core/*` and `workflow/*` namespaces — see [MVP design spec](docs/superpowers/specs/2026-05-10-jama-mvp-build-design.md).

## Known constraints

- **Repository visibility:** public on GitHub; reviewed by potential employers including Jama Software. Every commit must meet professional standards.
- **OAuth credential discipline:** dedicated `jama-mcp-server-dev` credential.
- **Sandbox URL:** `https://pm2.jamacloud.com`.
- **Author identity:** Arthur Fantaci, `arthur.fantaci@mac.com`.

## References

- Foundation design spec: [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md)
- MVP build spec: [`docs/superpowers/specs/2026-05-10-jama-mvp-build-design.md`](docs/superpowers/specs/2026-05-10-jama-mvp-build-design.md)
- Phase 1 plan: [`docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md`](docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md)
- Phase 2 plan: [`docs/superpowers/plans/2026-04-30-jama-mcp-server-phase-2-docker.md`](docs/superpowers/plans/2026-04-30-jama-mcp-server-phase-2-docker.md)
- Conventions: [`CLAUDE.md`](CLAUDE.md)
- Author's global protocols: `~/.claude/CLAUDE.md`
- Strategic positioning (gitignored): `docs/internal/jama-poc-strategic-positioning.md`
- Consulting artifacts (gitignored; brief revisions in scope of MVP build per spec Section 6): `docs/internal/specs/InfusionGuard 2200 - Project Configuration Specification.md` and `docs/internal/briefs/InfusionGuard 2200 - Software Engineer Workflow Brief.md`

## Recent decisions (last 5)

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-10 | **First cloud routine submitted at `claude.ai/code` for MVP implementation.** Routine "Implement Jama MCP Server MVP build phase (closes #13)" configured with: Schedule-once trigger at 18:10 EDT, Default Cloud Environment, empty Connectors, Auto-fix PRs OFF, Allow unrestricted git push OFF. Self-contained prompt includes bypassPermissions directive and four stop-and-escalate conditions (test failures unfixable in one attempt, pre-commit failures, spec ambiguity, new dependency needed). PR opens against `main` from working branch `mvp/foundation-tools` upon completion; does not auto-merge. Pattern captured in KG entity "Cloud Routine Configuration Pattern (Jama MCP Server)". | First cloud-routine handoff for this project. Configuration favors first-time observation over automation (Auto-fix OFF). Defense-in-depth on `main` (unrestricted-push OFF, prompt prohibits push-to-main). Communication via GitHub PR/issue comments + claude.ai/code run-history transcripts — routines are non-interactive. |
| 2026-05-10 | **MVP build phase scope locked; design spec committed.** Six tools: five `core/*` primitives (`create_item`, `create_relationship`, `list_item_types`, `list_relationship_types`, `list_items_by_type`) anticipating Jama Connect MCP™'s expected surface, plus one `workflow/*` macro (`create_path_a_trace`) demonstrating AI-consumption tool design. **Option 2 chosen**: foundation-first, host-agnostic; VS Code Extension / Skill / Plugin deferred as customer-specific deliverables. Single-PR cloud-routine delivery via Anthropic infrastructure. Brief Section 2 / Section 4 / storyboard captions revised (Section 6 of new spec). See: `docs/superpowers/specs/2026-05-10-jama-mvp-build-design.md`. | The original brief expanded Preston Mitchell's verbatim use case into a four-surfaces architecture. Option 2 walks the expansion back to the foundation while preserving the storyboard as forward-looking customer-deliverable illustration. Foundation-first model is elegant, host-agnostic, extensible — gives Jama's diverse customer base an MCP-server placeholder today plus a clean substrate for customer-specific Skills/Plugins later. |
| 2026-05-10 | **Phase 5 un-cancelled, MVP build phase initiated.** Add write tools to the public MCP server. Pivot to **Sandbox-as-demo-target**: evolve project 127 in place rather than creating a new IG2200 project. (Superseded by the scope-lock-in entry above for tool list and delivery topology.) | Preston's Jama Connect MCP™ access and Sandbox project-creation rights both delayed indefinitely. "Fully-operational MVP" requires a write surface somewhere; pivoting to evolve-the-Sandbox eliminates the project-creation dependency and uses the already-validated AF-SUBSS-25 / AF-CODE-1 / relationship 18505 as seed data. |
| 2026-05-10 | **Path A trace flow validated end-to-end on real Jamacloud.** Read-side smoke test demonstrable today via the existing seven MCP tools. SUSPECT auto-flag verified working. Default project type already permits `Subsystem Requirement → Code "Implemented by"` (no admin work needed). | Commercial centerpiece of the consulting proposal proven on real data; turns the proposal from forward-looking spec into evidence of execution. |
| 2026-05-06 | Software Engineer consulting-proposal artifacts finalized and renamed to buyer-facing filenames. Path A elevated to recommended primary trace mechanism (spec Section 5 / brief Frame 6). Frame 6 redrawn from real Jama UI screenshot to remove fabricated affordances. | Both documents commercial-quality and internally coherent; SUSPECT auto-flag is the regulatory-hygiene differentiator that Path A alone unlocks. |
