# Jama MCP Server — Working State

## Current phase

**DX testing phase — In progress.** Phase 0 (design + scaffolding) complete 2026-05-11: design spec, cloud-routine runbook, and PR template addition committed directly to `main` as commit `143d4dd`. Two new Software Requirements (`AF-SUBSS-26` *SWR-MCP-001*, `AF-SUBSS-27` *SWR-MCP-002*) created in Sandbox to ground the testing in real project state, describing this project's own workflow-tool contract and HTTP-error-to-typed-exception mapping respectively. Phase 1 in progress: GitHub [issue #15](https://github.com/arthurfantaci/jama-mcp-server/issues/15) opened; cloud routine **`trig_018rCL9cxSTCMMySaeBsRJZm`** ("DX testing implementation — bundled PR (closes #15)") submitted via `RemoteTrigger` API for the bundled PR scope: truncation regex fix plus new `repo_origin` parameter on `create_path_a_trace` populating Code item `description` with a deep link to tagged code. Routine fires 2026-05-11T16:40:00Z. The MVP build phase remains complete from 2026-05-10 (PR #14 squash-merged as commit `589fbac`; 119 unit/protocol tests pass; all three write tools live-smoked).

Design specs: [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md) (foundation), [`docs/superpowers/specs/2026-05-10-jama-mvp-build-design.md`](docs/superpowers/specs/2026-05-10-jama-mvp-build-design.md) (MVP build), and [`docs/superpowers/specs/2026-05-11-jama-mvp-dx-testing-design.md`](docs/superpowers/specs/2026-05-11-jama-mvp-dx-testing-design.md) (DX testing). Cloud routine conventions: [`docs/runbooks/cloud-routine-config.md`](docs/runbooks/cloud-routine-config.md). Public-first development conventions apply (professional portrayal, gitleaks, validate-docs-placement, Conventional Commits, Issue → Branch → PR for code; docs/memory-only changes commit directly to the working branch per `CLAUDE.md`).

**Active branch:** `main` (at `143d4dd`, in sync with origin/main after Phase 0 docs commit + push 2026-05-11)
**Open PR:** the DX testing bundled implementation PR opens upon routine completion against `main` from an auto-named branch (per the runbook's Trigger-vs-Session distinction). Two Dependabot PRs #11 + #12 also open with all CI checks green — routine docker-action bumps awaiting decision.
**Most recent code merge:** [PR #14](https://github.com/arthurfantaci/jama-mcp-server/pull/14) — MVP build phase (squash-merged 2026-05-10, merge commit `589fbac`)
**Open issues:** [issue #15](https://github.com/arthurfantaci/jama-mcp-server/issues/15) — DX testing bundled-PR scope. To be auto-closed by the routine's PR via `closes #15` directive.

## Demo seed data in Sandbox (project 127, as of 2026-05-10 post-merge smoke)

Use these existing artifacts as demo seed data; do NOT recreate or destructively reset them without deliberate intent. The Sandbox accumulates timestamped smoke-test artifacts; manual UI cleanup is expected per Jama's append-only design.

**Original seed (load-bearing for demo flow):**
- **`AF-SUBSS-25`** (item 115100, V3) — Source side of demo trace. *"SWR-OD-001: Module shall detect upstream occlusion within 500 ms."* Type 87 Subsystem Requirement, located at `Software Subsystems → Thermostat OS → Software Requirements` (parent `AF-SET-180`, item 115097). Currently shows description-vs-`req_value$87` inconsistency (description says 300 ms, `req_value$87` says "500") — kept deliberately as Persona 2 (compliance-officer) demo bait.
- **`AF-CODE-1`** (item 115102) — Original Code item for demo trace. *"occlusion_detector.py:detect_upstream_occlusion."* Type 114 Code, located at `Software Subsystems → Implementation Code (for trace)` (parent `AF-SET-212`, item 115094). Carries `path$114 = "src/occlusion_detection/occlusion_detector.py:7-42"`, `code_version$114 = "v1.0.0-rc1"`.
- **Relationship 18505** — `from_item: 115100, to_item: 115102, relationship_type: 19` ("Implemented by"), currently `suspect: true` after the 2026-05-10 verification description-edit.

**DX testing requirements (added 2026-05-11 to ground scenarios in real project state; load-bearing for DX testing scenario set):**
- **`AF-SUBSS-26`** — *SWR-MCP-001: Workflow tool shall create Code item and "Implemented by" relationship in a single call.* Type 87 Subsystem Requirement, parent `AF-SET-180`. Describes the contract of `create_path_a_trace`. Created via Jama UI 2026-05-11 after the local MCP server's OAuth credential returned HTTP 401 on POST `/items` against the Software Requirements Set (writes against the Implementation Code Set succeeded yesterday; suggests Set-level write-permission asymmetry on the dev credential).
- **`AF-SUBSS-27`** — *SWR-MCP-002: Jama client transport layer shall map HTTP error responses to typed exceptions.* Type 87 Subsystem Requirement, parent `AF-SET-180`. Describes the transport-layer behavior in `JamaClient._raise_for_status`. Created via Jama UI 2026-05-11 in the same UI session as `AF-SUBSS-26`.

**Smoke-test artifacts (added 2026-05-10 during MVP write-tool validation; safe to leave or clean via Jama UI):**
- **`AF-CODE-2`** (item 115104) — Created by `test_create_item` live smoke. Name: `integration-smoke-create-item-2026-05-10T23:05:25.991099+00:00`.
- **`AF-CODE-3`** (item 115105) — Created by manual `create_path_a_trace` live smoke. Name: `path_a_smoke_2026-05-10T23` (truncated due to name-derivation bug; see Known issues).
- **Relationship from 115100 → 115104** — Created by `test_create_relationship` live smoke, type 19.
- **Relationship 18507** — Created by manual `create_path_a_trace` live smoke, `from_item: 115100, to_item: 115105, relationship_type: 19`.

## Phase status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Repository scaffolding, CI/CD, memory hygiene apparatus | Complete |
| 1 | Functional MVP — six client operations + six MCP tools, both transports | Complete (PR #5 merged 2026-04-29) |
| 2 | Docker containerization | Complete (PR #7 merged 2026-04-30) |
| 4.5 | `create_comment` write tool — narrow Phase 4.5 carve-out | Complete (PR #10 merged 2026-05-02, merge commit `6e28b9f`) |
| MVP build | Six new MCP tools: `core/*` primitives (`create_item`, `create_relationship`, `list_item_types`, `list_relationship_types`, `list_items_by_type`) + `workflow/*` macro (`create_path_a_trace`); single-PR cloud-routine delivery | Complete (PR #14 squash-merged 2026-05-10, merge commit `589fbac`; all 3 write tools live-smoked against `pm2.jamacloud.com`) |
| DX testing | Validate end-to-end developer experience using the updated MCP server to meet the Software Engineer Use Case. Single-host (Claude Code), tool-selection-anchored, scenario-driven via `Agent` subagents against real Sandbox state (`AF-SUBSS-26`, `AF-SUBSS-27`); preceded by a bundled implementation PR (truncation regex fix + `repo_origin` deep-link description) delivered via cloud routine. | In progress — Phase 0 complete (design + scaffolding committed 2026-05-11 as `143d4dd`); Phase 1 in progress (routine `trig_018rCL9cxSTCMMySaeBsRJZm` submitted, fires 2026-05-11T16:40:00Z) |
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

## MCP tool surface (thirteen operational tools)

**`core/*` reads:** `whoami`, `list_projects`, `get_item`, `search_items`, `get_downstream_relationships`, `get_test_runs_for_item`, `list_item_types`, `list_relationship_types`, `list_items_by_type`. **`core/*` writes:** `create_comment` (Phase 4.5), `create_item`, `create_relationship`. **`workflow/*`:** `create_path_a_trace`. Tools package layout: `src/jama_mcp_server/tools/__init__.py` + `core.py` + `workflow.py`. See [MVP design spec](docs/superpowers/specs/2026-05-10-jama-mvp-build-design.md).

## Known constraints

- **Repository visibility:** public on GitHub; reviewed by potential employers including Jama Software. Every commit must meet professional standards.
- **OAuth credential discipline:** dedicated `jama-mcp-server-dev` credential.
- **Sandbox URL:** `https://pm2.jamacloud.com`.
- **Author identity:** Arthur Fantaci, `arthur.fantaci@mac.com`.

## Known issues (post-MVP-merge; for DX testing or follow-up fix)

- **`create_path_a_trace` name-derivation bug.** When the workflow tool creates a Code item with no explicit `name`, it derives the name from the code path's basename "excluding any trailing `:line-range` suffix" per the docstring. The implementation truncates at the FIRST colon rather than detecting a trailing `:N-M` line-range pattern specifically. Result: code paths containing ISO timestamps (which have colons in the time portion, e.g. `2026-05-10T23:05:25`) get their names truncated early. Verified on `AF-CODE-3` (smoke-created 2026-05-10): expected name `path_a_smoke_2026-05-10T23:05:25.991099+00:00.py`, actual name `path_a_smoke_2026-05-10T23`. The `path$114` field stores the full untruncated path; only the human-readable `name` field is affected. Workaround: callers can pass an explicit `name` parameter to bypass derivation entirely. Fix: change the truncation regex to anchor on `:\d+-\d+$` (trailing line range) instead of the first colon.

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
| 2026-05-11 | **DX testing phase Phase 0 complete; Phase 1 implementation routine submitted via `RemoteTrigger` API.** Phase 0 work (committed as `143d4dd` and pushed to origin/main): design spec at `docs/superpowers/specs/2026-05-11-jama-mvp-dx-testing-design.md`, cloud-routine runbook at `docs/runbooks/cloud-routine-config.md`, PR template addition for routine-driven-work metadata. Two new Software Requirements `AF-SUBSS-26` (SWR-MCP-001) and `AF-SUBSS-27` (SWR-MCP-002) created in Sandbox to ground DX testing scenarios in real project state describing this project's own behavior. Strategic pivot during the session from "test the existing surface and patch one bug" to "harden the surface against Path A (deep-link description population), ground scenarios in real project state, rehearse remote-routine workflow." [GitHub issue #15](https://github.com/arthurfantaci/jama-mcp-server/issues/15) opened. Cloud routine `trig_018rCL9cxSTCMMySaeBsRJZm` ("DX testing implementation — bundled PR (closes #15)") submitted via API for the bundled implementation PR (truncation regex fix + `repo_origin` parameter + deep-link description). Routine fires 2026-05-11T16:40:00Z; monitoring via GitHub commits + PR per the runbook. Operational observations: (a) local Jama MCP server returned HTTP 401 on POST `/items` against `AF-SET-180` Software Requirements Set while `whoami` GET succeeded — Set-level write-permission asymmetry on the `jama-mcp-server-dev` credential worth investigating before next write-tool work (this project's prior writes only exercised `AF-SET-212` Implementation Code Set); (b) submitting with `mcp_connections:[]` in the create body returned a response listing globally-enabled connectors (Hugging Face, Slack) with `permitted_tools:[]` — functionally empty but the runbook wording could be sharpened. | The strategic pivot reflects the user's stated workflow migration toward remote/autonomous execution (routines + emerging frameworks like OpenClaw and Hermes). Bundling truncation fix and Path A in one PR is engineering-yield-maximizing because both changes share the same regex anchoring code path. Grounded scenarios in real project state are more honest than synthetic seed data and produce findings that transfer cleanly to customer engagements. The two Jama-side operational observations are findings for the runbook plus the knowledge graph in the memory-hygiene phase. |
| 2026-05-10 | **MVP build PR #14 squash-merged into main as commit `589fbac`; all three write tools live-smoked against `pm2.jamacloud.com`.** Live smoke results: `create_item` created `AF-CODE-2` (115104); `create_relationship` linked AF-SUBSS-25 → AF-CODE-2 with type 19; `create_path_a_trace` created `AF-CODE-3` (115105) + relationship 18507 in one tool call. A follow-up cloud-routine **Session** added the third integration test (`test_create_path_a_trace_against_live_sandbox`) to the PR branch before merge. Discovered minor `create_path_a_trace` name-derivation bug (truncates at first colon vs. trailing `:line-range`); documented under Known issues. Branch cleanup post-merge: `claude/optimistic-keller-Zyv4j` auto-deleted local+remote by `gh pr merge --delete-branch`; earlier-discovered orphans `claude/optimistic-keller-f6of7` and `feat/create_comment` previously cleaned. KG entity "Cloud Routine Configuration Pattern" extended with the Session-vs-Trigger distinction and the Session-honors-branch-directive finding. | The MVP build phase delivered an authoritative, smoke-verified, host-agnostic foundation. The Session-vs-Trigger API observation is a cross-project routine pattern: monitoring routine progress requires GitHub (not the Trigger API), and ad-hoc Sessions DO honor explicit branch directives in prompts (unlike the auto-naming behavior on initial Trigger fires). |
| 2026-05-10 | **MVP build implemented by cloud routine on branch `claude/optimistic-keller-Zyv4j`.** Six new tools across `core/*` and `workflow/*` namespaces. `tools.py` refactored into `tools/__init__.py` + `core.py` + `workflow.py`. `_type_cache` added to `JamaClient` for per-instance caching of resolved type IDs. `create_path_a_trace` implemented as a `JamaClient` method (accesses `_type_cache` directly) called by the workflow MCP tool. Set validation (type 31) kept at MCP tool layer (`core/create_relationship`) rather than client layer for testability. 119 tests pass. | Clean implementation following all codified patterns. `JamaClient.create_path_a_trace` placement allows cache sharing across multiple tool calls in a single session. |
| 2026-05-10 | **First cloud routine submitted at `claude.ai/code` for MVP implementation.** Routine "Implement Jama MCP Server MVP build phase (closes #13)" configured with: Schedule-once trigger at 18:10 EDT, Default Cloud Environment, empty Connectors, Auto-fix PRs OFF, Allow unrestricted git push OFF. Self-contained prompt includes bypassPermissions directive and four stop-and-escalate conditions (test failures unfixable in one attempt, pre-commit failures, spec ambiguity, new dependency needed). PR opens against `main` from working branch `claude/optimistic-keller-Zyv4j` upon completion; does not auto-merge. Pattern captured in KG entity "Cloud Routine Configuration Pattern (Jama MCP Server)". | First cloud-routine handoff for this project. Configuration favors first-time observation over automation (Auto-fix OFF). Defense-in-depth on `main` (unrestricted-push OFF, prompt prohibits push-to-main). Communication via GitHub PR/issue comments + claude.ai/code run-history transcripts — routines are non-interactive. |
| 2026-05-10 | **MVP build phase scope locked; design spec committed.** Six tools: five `core/*` primitives (`create_item`, `create_relationship`, `list_item_types`, `list_relationship_types`, `list_items_by_type`) anticipating Jama Connect MCP™'s expected surface, plus one `workflow/*` macro (`create_path_a_trace`) demonstrating AI-consumption tool design. **Option 2 chosen**: foundation-first, host-agnostic; VS Code Extension / Skill / Plugin deferred as customer-specific deliverables. Single-PR cloud-routine delivery via Anthropic infrastructure. Brief Section 2 / Section 4 / storyboard captions revised (Section 6 of new spec). See: `docs/superpowers/specs/2026-05-10-jama-mvp-build-design.md`. | The original brief expanded Preston Mitchell's verbatim use case into a four-surfaces architecture. Option 2 walks the expansion back to the foundation while preserving the storyboard as forward-looking customer-deliverable illustration. Foundation-first model is elegant, host-agnostic, extensible — gives Jama's diverse customer base an MCP-server placeholder today plus a clean substrate for customer-specific Skills/Plugins later. |
