# Jama MCP Server — MVP Build Phase Design Specification

**Document type:** Design specification (MVP build phase)
**Date:** 2026-05-10
**Status:** Draft pending author approval
**Author:** Arthur Fantaci
**Foundation spec:** [`2026-04-28-jama-mcp-server-design.md`](2026-04-28-jama-mcp-server-design.md)

This specification governs the MVP build phase initiated on 2026-05-10. It builds on the foundation specification (2026-04-28), which governs Phases 0 through 4.5 (initialization, functional MVP, Docker containerization, `create_comment` write tool). Architecture, layering, conventions, tooling rigor, and memory hygiene defined there carry forward unchanged. This document specifies what is new: a strategic reframe, an expanded MCP tool surface across two namespaces, a delivery plan, and revisions to companion consulting artifacts.

## 1. Project Context and Continuity

The Jama MCP Server has shipped four phases:

- **Phase 0** (initialization, repository scaffolding, CI/CD, memory hygiene apparatus). Status: complete.
- **Phase 1** (functional MVP — six MCP tools across stdio and streamable-HTTP transports). Shipped via [PR #5](https://github.com/arthurfantaci/jama-mcp-server/pull/5), merged 2026-04-29.
- **Phase 2** (Docker containerization, multi-stage build, healthcheck, non-root runtime). Shipped via [PR #7](https://github.com/arthurfantaci/jama-mcp-server/pull/7), merged 2026-04-30.
- **Phase 4.5** (`create_comment` write tool, narrow carve-out introducing the write surface). Shipped via [PR #10](https://github.com/arthurfantaci/jama-mcp-server/pull/10), merged 2026-05-02.

The repository is public, CI passes across six checks (Lint, Mypy strict, Test, Dependency Review, codecov, Docker build), 91 unit/protocol tests pass on `main`, and the OAuth + transport + Pydantic-modeling + two-layer error policy architecture is settled.

The foundation specification's Section 10 named Phases 5 and 6 (write tools and read-tool expansion). Both were cancelled 2026-05-04 following Jama Software's general availability announcement of Jama Connect MCP™, on the grounds that the vendor's own write surface would make this project's write tools redundant. They were un-cancelled 2026-05-10 after the customer's Jama Connect MCP™ access was delayed indefinitely. This specification governs that resumed work.

## 2. Strategic Reframe — Anticipatory Placeholder for Jama Connect MCP™

The MCP server's role is reframed for the MVP build phase. Rather than being a portfolio piece demonstrating Agentic AI engineering capability with no fixed external reference, it is positioned as **an anticipatory placeholder for the official Jama Connect MCP™ server**, replicating that vendor product's expected functional surface so the engagement's Software Engineer Use Case can be demonstrated end-to-end before Jama Connect MCP™ becomes accessible to the customer.

### Implications of the reframe

**Tool design discipline.** Every read/write tool added to the `core/*` namespace must pass the test of plausibly being a tool Jama Software would ship in Jama Connect MCP™. Tool design that prioritizes this project's convenience over vendor-likely surface area is excluded from `core/*`.

**Separation of value-add tooling.** Tools whose justification is specifically AI-consumption design — workflow tools, macro tools that compose primitives — live in a distinct `workflow/*` namespace and are explicitly labeled in their docstrings and in the README as this project's value-add layer, NOT placeholders for Jama Connect MCP™.

**Host-agnosticism as a foundation property.** Any MCP-compliant host (Claude Code, Cursor, GitHub Copilot Chat, Continue, Claude Desktop) can drive the Software Engineer Use Case workflow by calling this project's tools through standard MCP protocol semantics. The engagement's IDE-side experience (custom VS Code extension, host-specific Skills, distribution Plugins) is positioned as a separate, customer-specific deliverable, NOT a runtime requirement of the foundation.

**Consulting-narrative implications.** The original Software Engineer Workflow Brief expanded Preston Mitchell's verbatim use case into a four-surfaces architecture (VS Code Extension, Claude Code Skills, configured IG2200 project, documentation). This MVP build phase walks that expansion back to a foundation-first model that meets Preston's verbatim use case while positioning the extension/Skills/Plugins as customer-specific deliverables built on top of the foundation. The brief is revised accordingly during this MVP build phase (see Section 6).

## 3. MVP Scope — Six MCP Tools Across Two Namespaces

### `core/*` — read/write primitives anticipating Jama Connect MCP™

Five tools that mirror functionality Jama Connect MCP™ is expected to expose, modeled after the underlying Jama REST API. Tool naming follows Jama's conceptual model rather than this project's use case.

| Tool | Type | Purpose |
|---|---|---|
| `create_item` | write | Create a new Jama item of a specified type within a specified parent (typically a Set), with arbitrary type-specific field values. POSTs to `/items`; follows the Phase 4.5 meta-only response envelope pattern. |
| `create_relationship` | write | Create a directed relationship between two existing Jama items with a specified relationship type. POSTs to `/relationships`. Validates that neither endpoint is a Set type (Jama gotcha codified in the project memory: Sets carry no relationships). |
| `list_item_types` | read | Enumerate all item types configured for a project. Required for the agent to discover correct type IDs ahead of `create_item`. GETs `/projects/{id}/itemtypes` (or equivalent). |
| `list_relationship_types` | read | Enumerate all relationship types configured for a project. Required for the agent to discover the correct relationship type ID (e.g., "Implemented by") ahead of `create_relationship`. GETs `/relationshiptypes` scoped by project. |
| `list_items_by_type` | read | List all items in a project matching a given item type, with pagination. Supports the workflow's "show me the project's software requirements" entry point. GETs `/abstractitems?project={id}&itemType={typeId}`. |

### `workflow/*` — AI-consumption macro tool

One tool whose role is to demonstrate the engineering practice of designing MCP tools for agentic AI consumption. Explicitly NOT a placeholder for Jama Connect MCP™.

| Tool | Type | Purpose |
|---|---|---|
| `create_path_a_trace` | write | High-level workflow tool composing the primitives: given a source requirement key, a code file path, and a code version, validates the source requirement exists, locates or accepts the "Implemented by" relationship type, locates or accepts the Implementation Code Set, creates a Code item (name derived from the code path's basename unless an explicit `name` parameter overrides) with the file-path and code-version fields populated, creates the relationship from source to the new Code item, and returns both new item IDs and the relationship ID. |

### Namespace mechanics

The `core/*` vs `workflow/*` distinction is surfaced at three levels:

- **In tool docstrings.** `core/*` tools' docstrings cite the corresponding Jama REST endpoint and frame the tool as anticipating Jama Connect MCP™. `workflow/*` tools' docstrings open with a "Workflow tool — composes core primitives; NOT expected in Jama Connect MCP™" header.
- **In the README.** A new "Tool Namespaces" subsection distinguishes the two and explains the strategic rationale.
- **In Python module layout.** The existing `src/jama_mcp_server/tools.py` is refactored into `src/jama_mcp_server/tools/__init__.py` + `core.py` + `workflow.py`. The refactor is justified by the namespace distinction and is in scope for the MVP work.

### MCP tool surface after MVP

Six new tools plus seven existing tools yields **thirteen operational MCP tools** at MVP completion: `whoami`, `list_projects`, `get_item`, `search_items`, `get_downstream_relationships`, `get_test_runs_for_item`, `create_comment` (existing), plus the six new tools above.

## 4. Out of Scope (with Reasons)

| Excluded | Reason |
|---|---|
| **Phase 7 — Tier 2 VS Code Extension** | Deferred. Per the Option 2 decision (2026-05-10), the IDE-native experience is positioned as a customer-specific deliverable, not foundation. Reinstatable as a follow-on engagement scope. |
| **Claude Code Skill packaging** | Deferred to stretch. The MCP server alone enables the Software Engineer Use Case workflow via any agentic host's chat surface; a Skill is opinionated host-specific polish that is most valuable after the foundation is proven on real demo material. |
| **Claude Code Plugin distribution bundle** | Deferred to stretch. Plugin packaging assumes the Skill exists. |
| **Additional `workflow/*` tools** (e.g., `create_implementation_code`, `link_implementation_to_requirement`) | Deferred. `create_path_a_trace` is sufficient to demonstrate AI-consumption tool-design judgment. Additional workflow tools can be added post-MVP if customer engagements pull for them. |
| **IG2200 project creation** | Replaced by Sandbox-as-demo-target (project 127, "Arthur Sandbox" on `pm2.jamacloud.com`). The brief's IG2200 references are revised in Section 6 below. |
| **`get_item_children`, `get_picklist_options`, `get_upstream_relationships`, `list_relationship_rules`, `get_comments`** | Originally part of the Phase 6 plan. Cut from this MVP because the 2026-05-10 workflow analysis showed they are not required for the Software Engineer Use Case end-to-end. They may return in a post-MVP Phase 6b if the System Engineer persona or other workflows require them. |
| **`JAMA_READONLY` environment gate / per-tool confirmation hooks** | Per Phase 4.5 conventions: HITL is the orchestrating skill's responsibility, not the MCP server's. The server stays stateless; HITL is provided by the MCP host's permission UI. |
| **`create_path_a_trace` exposing every code-item field** | The workflow tool accepts the demo-critical fields (file path, code version) and uses sensible defaults for other Code-item fields. Callers needing arbitrary field control use `core/create_item` directly. |

## 5. Delivery Plan — One Cloud Routine, One Branch, One PR

### Topology

The MVP work is delivered as **one GitHub issue, one working branch, one pull request** opened by a single autonomous cloud routine running on Anthropic infrastructure. The cloud routine may internally parallelize work via sub-agents where the implementation surface permits, but produces one bundled PR for human review.

The decision to bundle rather than split into multiple PRs reflects:

- The engagement sponsor's stated review preference (a single PR-review interaction at completion)
- The MVP's tight scope (six tools, all following codified patterns from Phases 1 and 4.5)
- The cohesion of the work (the six tools form a deliberate set; reviewing them together surfaces design coherence that splits would obscure)
- Cloud-routine reliability (a single routine producing one PR is simpler to author, run, and debug than a routine orchestrating multiple PRs)

### Recommended internal sequencing for the cloud routine

The routine prompt recommends but does not mandate the following stages:

**Stage 1 — `core/*` reads (no inter-tool conflicts; parallelizable internally if the routine chooses):**

- `list_item_types`
- `list_relationship_types`
- `list_items_by_type`

These three reads add new Pydantic models (`ItemType`, `RelationshipType`) and three new endpoint accessors to `client.py`. The new models do not conflict with each other; the client methods are independent; the test fixtures do not conflict.

**Stage 2 — `core/*` writes (follow the Phase 4.5 meta-only POST envelope pattern):**

- `create_item`
- `create_relationship`

Both follow the Phase 4.5 meta-only POST envelope handling pattern codified in `_parse_envelope`. The two writes share `_request` write-path conventions.

**Stage 3 — `workflow/*` (depends on Stages 1 and 2):**

- `create_path_a_trace`

Composes the primitives. Implemented after Stages 1 and 2 because it depends on them being functional and tested.

**Stage 4 — Integration and final verification:**

- Refactor `tools.py` into the two-module namespace layout
- Update `README.md` to document new tools and the namespace distinction
- Update `MEMORY.md` to reflect MVP completion state
- Update `CLAUDE.md` to codify any new conventions discovered during implementation
- Update consulting artifacts in `docs/internal/` per Section 6 below
- Run full verification: `uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest -m "not integration"`
- Push the branch and open the pull request

### Per-stage testing

Each stage adds:

- **Unit tests for `client.py` methods** following the synthetic-response pattern in `tests/unit/jama_client/`
- **MCP-protocol tests** for each new tool in `tests/unit/jama_mcp_server/test_protocol.py`, using the `mock_jama_client` fixture and synthetic `RequestContext` pattern codified in Phase 1
- **Integration tests for write tools** following the Phase 4.5 `JAMA_INTEGRATION_*` env-var gating pattern: skip-by-default, leave timestamped Sandbox artifacts that the author cleans up via the Jama UI

Total expected test count after MVP: approximately 91 (current) + 25-30 (new) = 115-120 unit/protocol tests.

### Conflict-prone shared files

The routine should expect to edit (or refactor) the following:

- `src/jama_client/client.py` — six new client methods
- `src/jama_client/models.py` — new `ItemType`, `RelationshipType` Pydantic models following the `_JamaModel` base
- `src/jama_mcp_server/tools/` — refactor `tools.py` into `core.py` + `workflow.py` plus an `__init__.py` that registers all tools; preserve existing tools' module-level `Context` import idiom and `_Context = Context[Any, Any, Any]` alias pattern
- `src/jama_mcp_server/server.py` — update tool-registration imports/calls to reflect the two-module layout; preserve the `server.custom_route("/health", ...)` registration order (must precede tool registration per Phase 2 conventions)
- `tests/conftest.py` — possibly add shared mock-response fixtures for new endpoints
- `README.md` — namespace subsection, updated tool inventory, possibly an "Anticipatory placeholder for Jama Connect MCP™" framing paragraph
- `MEMORY.md` — reflect MVP completion in phase table and recent decisions
- `CLAUDE.md` — codify any new conventions discovered during implementation (e.g., paginated-read patterns, workflow-tool composition patterns)
- `docs/internal/briefs/InfusionGuard 2200 - Software Engineer Workflow Brief.md` — Section 2 operational interpretation revision, Section 4 architecture revision, IG2200 → Sandbox-as-demo language updates, storyboard frame captions (Section 6 below)
- `docs/internal/specs/InfusionGuard 2200 - Project Configuration Specification.md` — IG2200 → Sandbox-as-demo language updates

These shared-file edits happen inside the single working branch; no inter-branch merge friction.

### Branch and PR naming

- **Branch:** `mvp/foundation-tools` (descriptive of the deliverable, not the issue number)
- **Issue title:** "MVP build phase — `core/*` primitives + `create_path_a_trace` workflow tool"
- **PR title:** "MVP build phase — anticipatory Jama Connect MCP™ placeholder, six new tools"

## 6. Brief Revision Plan

The consulting artifacts in `docs/internal/` (gitignored — author's working copies; never enter the public repository) are revised as part of the MVP build phase. The revisions reflect the author's strategic shift to Option 2 (foundation-first, host-agnostic, customer-specific extension layer as separate deliverable).

### Section 2 — Operational interpretation revision

Current text requires VS Code's native UI primitives: *"Lookup, selection, and trace-link creation happen via VS Code's native UI primitives (command palette, QuickPick) backed by Jama Connect MCP™."*

Revised text broadens this to allow agentic-coding-assistant-native UI as a valid expression of "without leaving the IDE": *"Lookup, selection, and trace-link creation happen via the developer's chosen agentic coding assistant's native UI primitives — its chat interface, command palette, or custom extensions where available — backed by Jama Connect MCP™."* The revision is accompanied by an explicit acknowledgment that customer engagements may add a VS Code Extension or host-specific Skill polish on top of the foundation, but those polish layers are customer-specific deliverables, not foundation requirements.

### Section 4 — Architecture revision

The four-surfaces architecture table is restructured to a **foundation-plus-experience-layers** model:

- **Foundation (universal):** Jama Connect MCP™ + the developer's agentic coding assistant
- **Experience layers (customer-specific):** optional VS Code Extension; optional Claude Code, Cursor, Continue, or GitHub Copilot Skills; optional Plugins; configured demo project

The `jama-mcp-server` row in the table is retained and amended: it is now cited as both proof-of-execution credibility AND an explicit "anticipatory placeholder for Jama Connect MCP™" — the vehicle by which the engagement can demonstrate the Software Engineer Use Case before the customer has Jama Connect MCP™ procured.

### Brief Section 3 — Storyboard handling (option ii)

Per the author's 2026-05-10 decision, the six storyboard frames in the brief's Section 3 are retained as forward-looking illustrations of what a customer-specific VS Code Extension could deliver. Each frame's caption is amended to note: *"This frame illustrates a customer-specific VS Code Extension deliverable, not the foundation engagement scope. The foundation engagement delivers the underlying MCP tool surface; UI affordances are added per customer need."* The illustrations preserve the visual asset of the brief while honoring Option 2's foundation-first scope.

### IG2200 → Sandbox-as-demo language

References to "the configured `IG2200` project" as engagement scope are revised to "the Sandbox demo project (project 127 on `pm2.jamacloud.com`, configured per the companion specification)". The companion specification (`InfusionGuard 2200 - Project Configuration Specification.md`) is similarly revised, with its content reframed to describe the Sandbox's current state plus an "additional configuration that customer engagements may apply" appendix capturing the original IG2200-specific guidance.

### Commit and PR-description treatment

The brief and configuration-spec revisions are committed as part of the MVP working branch (per CLAUDE.md's bundling rule for docs-only changes alongside relevant phase work). Since `docs/internal/` is gitignored, the revisions are local-only and do not appear in the PR's diff. They are listed in the PR description under a "Companion artifact revisions completed alongside MCP changes" section so a reviewer can see the work was done.

## 7. Sandbox-as-Demo Seed Data

Project 127 ("Arthur Sandbox") on `pm2.jamacloud.com` is the demo target for this MVP and for downstream engagement work until a customer-specific Jama tenant is provisioned. Current state, validated 2026-05-10:

- **`AF-SUBSS-25`** (item 115100, V3) — *"SWR-OD-001: Module shall detect upstream occlusion within 500 ms."* Type 87 Subsystem Requirement. Located at `Software Subsystems → Thermostat OS → Software Requirements` (parent `AF-SET-180`). Carries a deliberate description-vs-`req_value$87` inconsistency (description says 300 ms; `req_value$87` says "500") preserved as Persona 2 (compliance-officer) demo bait — **do NOT reconcile during MVP work**.
- **`AF-CODE-1`** (item 115102) — *"occlusion_detector.py:detect_upstream_occlusion."* Type 114 Code. Located at `Software Subsystems → Implementation Code (for trace)` (parent `AF-SET-212`). Carries `path$114 = "src/occlusion_detection/occlusion_detector.py:7-42"`, `code_version$114 = "v1.0.0-rc1"`.
- **Relationship 18505** — from `115100` (AF-SUBSS-25) to `115102` (AF-CODE-1), type `19` ("Implemented by"). Currently `suspect: true` after a 2026-05-10 description-edit verification — **leave as-is**.

The MVP work may extend the Sandbox with additional requirements (further `AF-SUBSS-*` items) or additional Code items (`AF-CODE-2…N`) to broaden demo coverage. New artifacts should be added cleanly (correct types, correct parent Sets, populated field values). Integration tests that create artifacts during execution leave timestamped comments and items in the Sandbox per the Phase 4.5 pattern; manual cleanup via the Jama UI is expected. Jama exposes no REST endpoint for comment deletion; items can be deleted via the UI.

The Sandbox's `pm2.jamacloud.com` OAuth credentials are configured in the author's local `.env`. The cloud routine running the MVP work does NOT need Jama OAuth, because integration tests are skip-by-default (`JAMA_INTEGRATION_*` environment variables unset in the routine's environment). The routine's verification step runs `uv run pytest -m "not integration"`, which excludes all integration tests.

## 8. Open Decisions Resolvable by the Cloud Routine

The cloud routine will encounter the following decisions during implementation. The spec gives the recommended resolution; the routine defaults to the spec but may escalate via PR description if circumstances diverge.

1. **`list_items_by_type` pagination strategy.** Jama's REST API paginates `/abstractitems` queries. **Recommendation:** aggregate across pages internally with a `max_items` parameter defaulting to 200. The Sandbox project has approximately 60 items; 200 is generous headroom. A `max_items_reached` boolean is included in the response so callers can detect when the cap was hit.

2. **`create_path_a_trace` source-existence validation.** The workflow tool must validate that the source requirement exists before creating the Code item, to avoid orphaned Code items when the requirement key is wrong. **Recommendation:** call `get_item` internally; raise `JamaNotFoundError` (existing exception type) if 404, before any write occurs.

3. **`core/*` vs `workflow/*` namespace mechanics.** Two reasonable implementations: (a) Python module split (`tools/core.py` + `tools/workflow.py`), (b) tool naming prefix (`core_create_item` vs `workflow_create_path_a_trace`). **Recommendation:** module split (option a). Cleaner imports, matches existing project layout conventions, supports the namespace distinction structurally rather than relying on naming hygiene.

4. **Code item naming convention in `create_path_a_trace`.** When the workflow tool creates a Code item, what should the item's `name` field be? **Recommendation:** derive from the code path's basename plus optionally a function/symbol name when provided (e.g., `occlusion_detector.py:detect_upstream_occlusion` for a file/function pair, or `occlusion_detector.py` for a file-only reference). Accept an optional `name` parameter that overrides the derivation.

5. **Item-type and relationship-type ID resolution.** `create_path_a_trace` needs the Code item type ID and the "Implemented by" relationship type ID. **Recommendation:** accept them as optional parameters that, when omitted, are looked up via `list_item_types` and `list_relationship_types` on first use and cached for the `JamaClient` instance's lifetime. Cache invalidation is not implemented (instances are short-lived).

6. **Existing `Item` model reuse for `list_items_by_type` results.** The new read tool returns items matching the existing `Item` Pydantic model. **Recommendation:** reuse `Item` directly; do not introduce a `BriefItem` or similar slimmer model. The full `Item` payload is what Jama returns and what callers will want.

7. **`JamaClient` cache for type lookups.** The recommendation in (5) creates instance-level cache state. **Recommendation:** add a private `_type_cache: dict[str, Any]` to `JamaClient.__init__` with explicit keys (`item_types_<project_id>`, `relationship_types_<project_id>`, `code_set_<project_id>`). Document in the class docstring that the cache is per-instance and not invalidated.

8. **Implementation Code Set discovery in `create_path_a_trace`.** The workflow tool must place the new Code item in a Set; the demo Sandbox's Set is `AF-SET-212` ("Implementation Code (for trace)"). The tool needs to find this Set without hardcoding the Sandbox-specific ID. **Recommendation:** accept `code_set_id` as an optional parameter. When omitted, query `list_items_by_type(project, type=31)` (Sets) and pick the Set whose `name` contains "Implementation Code" (case-insensitive substring match). Cache the result in `_type_cache` per decision 7. Raise `JamaNotFoundError` with an explicit message if no matching Set is found or if multiple matches are found without an explicit `code_set_id` parameter.

## 9. References

- **Foundation design spec:** [`docs/superpowers/specs/2026-04-28-jama-mcp-server-design.md`](2026-04-28-jama-mcp-server-design.md)
- **Phase 1 plan:** [`docs/superpowers/plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md`](../plans/2026-04-29-jama-mcp-server-phase-1-functional-mvp.md)
- **Phase 2 plan:** [`docs/superpowers/plans/2026-04-30-jama-mcp-server-phase-2-docker.md`](../plans/2026-04-30-jama-mcp-server-phase-2-docker.md)
- **Phase 4.5 conventions (codified):** [`CLAUDE.md`](../../../CLAUDE.md) — see the "Phase 4.5 conventions codified" section
- **Project conventions and tooling rigor:** [`CLAUDE.md`](../../../CLAUDE.md)
- **Working state and recent decisions:** [`MEMORY.md`](../../../MEMORY.md)
- **Consulting artifacts (gitignored, author's working copies):** `docs/internal/briefs/InfusionGuard 2200 - Software Engineer Workflow Brief.md`; `docs/internal/specs/InfusionGuard 2200 - Project Configuration Specification.md`
- **Author's global protocols:** `~/.claude/CLAUDE.md`

---

*End of specification.*
