# Jama MCP Server — DX Testing Phase Design Specification

**Document type:** Design specification (DX testing phase)
**Date:** 2026-05-11
**Status:** Draft pending author approval
**Author:** Arthur Fantaci
**Foundation spec:** [`2026-04-28-jama-mcp-server-design.md`](2026-04-28-jama-mcp-server-design.md)
**MVP build spec:** [`2026-05-10-jama-mvp-build-design.md`](2026-05-10-jama-mvp-build-design.md)
**Cloud routine runbook:** [`../../runbooks/cloud-routine-config.md`](../../runbooks/cloud-routine-config.md)

This specification governs the developer experience (DX) testing phase initiated on 2026-05-11. The MVP build phase shipped 2026-05-10 via PR #14, landing thirteen operational MCP tools across the `core/*` and `workflow/*` namespaces. This phase tests and refines the end-to-end developer experience when an agentic coding assistant uses those tools to satisfy the Software Engineer use case (Preston Mitchell's persona; see the consulting brief in `docs/internal/briefs/`).

The phase has two pieces, executed in sequence:

1. **A bundled implementation pull request**, delivered by a single autonomous cloud routine. The pull request lands two changes together: the truncation regex fix carried over from the MVP build phase's known issues, and a new repository-origin parameter on `create_path_a_trace` that populates each new Code item's `description` with a deep link to the tagged code. These changes harden the trace artifact so that Jama reviewers can locate referenced code without external knowledge.
2. **A subsequent in-session scenario execution** (separate session, post-merge) that runs seven scenarios via `Agent` subagents against the hardened tool surface, grounded in real project state — two new Software Requirements (`AF-SUBSS-26`, `AF-SUBSS-27`) created in the Sandbox describing this project's own behavior, and code paths drawn from this repository's actual Python modules. A public findings report and private memory layer follow.

Cross-host portability, smaller-model behavior, and System Engineer use-case coverage are explicitly out of scope and enumerated in Section 9.

## 1. Mission

Validate that an agentic coding assistant, encountering the Jama MCP server's thirteen-tool surface cold, can reliably satisfy the Software Engineer use case end-to-end through the tool selections it makes. The primary observable is the **sequence of tool calls the agent emits** in response to natural-language developer prompts. Secondary observables are parameter choices, error-surfacing behavior under failure conditions, and the agent's handling of under-specified prompts.

The use case (verbatim, as received from the engagement sponsor):

> I'm coding in an IDE and I need to lookup a requirement in Jama and tag my code to it. Jama then creates a trace link from that requirement to the software package / library where the code exists. SW engineer never needs to leave IDE but they are create requirement to code trace.

## 2. Failure mode anchoring the session

**Tool selection** is the gateway failure mode. An agent that picks the wrong tool, composes primitives badly, or fails to invoke `create_path_a_trace` when appropriate undermines every downstream property — HITL legibility, completion rate, error UX — before those properties can manifest. Tool selection is also the **most transferable** finding to the anticipatory-placeholder strategy: when Jama Connect MCP™ becomes available and customers swap servers, every customer-deployed agent will still run tool selection against whatever surface is in front of it. Findings about docstring clarity, parameter naming, and namespace mechanics carry forward unchanged.

The session does not anchor on HITL legibility (per-host permission UI) because only one host is in scope, nor on end-to-end completion (which is largely a downstream consequence of tool selection — if selection is right, completion follows for the happy paths).

## 3. Methodology

### 3.1 Execution model

For each of the seven scenarios, a `general-purpose` subagent is spawned via the `Agent` tool with a tight, customer-naive prompt. The subagent inherits MCP server connections (including the Jama MCP server's thirteen tools) but **not** the parent session's conversation history, `CLAUDE.md` content, `MEMORY.md` content, design-spec content, or knowledge-graph entries. Each subagent thus encounters the tool surface cold.

The subagent prompt template:

```
You are a developer's coding assistant integrated with their IDE. Your developer has just asked you:
---
[scenario verbatim]
---
You have access to a Jama Connect MCP server (tool names start with `mcp__jama-mcp-server__`). Use those tools to do what the developer asked. Do not ask clarifying questions — choose sensible defaults if anything is under-specified. When you're done, summarize in one paragraph: which tools you called (in order), what parameters you used (the meaningful ones), and the result. If something failed, describe how you would surface the failure to the developer.
```

The "do not ask clarifying questions" instruction is deliberate. A subagent that responds with "what's your code version?" instead of choosing a default produces a low-information transcript. The instruction biases the subagent toward emitting tool calls, which is the data the session needs.

### 3.2 Validity caveats

Two limits constrain inference from these transcripts:

1. **Opus 4.7 ceiling.** Findings represent the strongest agent runtime available. Customer-deployed agents using smaller models (Haiku, GPT-4o, Gemini Flash) may struggle in ways this session does not surface.
2. **General-purpose system prompt.** Subagents retain Claude Code's default system prompt and globally-loaded skills. Customer-deployed agents in third-party hosts (Cursor, Continue, Copilot Chat) operate under different system prompts and different tool-call orchestration logic. Behaviors that hold here may diverge there.

Both limits are recorded in the findings report under "Limitations" and motivate future-DX-testing recommendations.

### 3.3 Single-host scope

Only Claude Code is exercised. This trades cross-host portability validation against depth on a single runtime. The reasoning: tool-selection findings transferring cleanly across hosts is an architectural claim the MVP build phase has already made, not one this session is structured to evidence-back. Cross-host DX testing is recommended as a future session.

### 3.4 Tool-input asymmetry to note during analysis

`create_path_a_trace` accepts a **document key** for `source_requirement_key` (e.g., `AF-SUBSS-26`) and absorbs the key-to-numeric-ID resolution internally. By contrast, `create_comment`, `create_relationship`, and `get_item` accept **numeric item IDs** only. Scenarios that route through the macro therefore skip an explicit `search_items` resolution step; scenarios that route through `create_comment` or compose primitives directly must include it. This asymmetry is the macro's stated value proposition, but it places a docstring-clarity demand on the primitive tools' parameter descriptions that the analysis phase should evaluate.

### 3.5 Grounded scenario data

The scenarios reference real project state rather than synthetic data:

- **Two new Software Requirements** were created in the Sandbox (project 127) on 2026-05-11 under the existing `AF-SET-180` parent Set, alongside `AF-SUBSS-25`:
  - **`AF-SUBSS-26`** — *SWR-MCP-001: Workflow tool shall create Code item and "Implemented by" relationship in a single call.* Describes the contract of `create_path_a_trace`.
  - **`AF-SUBSS-27`** — *SWR-MCP-002: Jama client transport layer shall map HTTP error responses to typed exceptions.* Describes the transport-layer behavior in `JamaClient._raise_for_status`.
- **Code paths** are drawn from this repository's actual Python modules — primarily `src/jama_client/client.py` (transport layer, retry policy, type cache, the `create_path_a_trace` method) and `src/jama_mcp_server/tools/workflow.py` (the MCP wrapper for `create_path_a_trace`). The self-referential framing is honest about what the code we are tagging actually does.

## 4. Scenario set

Seven scenarios exercise tool selection across the dimensions of macro-vs-primitive choice, search-first framing, adversarial trap, idempotency under repeated tagging, error recovery, and informal phrasing. Each scenario's verbatim prompt is what the subagent receives.

| # | Designed to test | Subagent prompt (verbatim) | Ideal tool sequence |
|---|---|---|---|
| 1 | Macro target — does the agent reach for the workflow tool when the use case is straightforward and parameters are present? | `I just wrote the create_path_a_trace MCP wrapper at src/jama_mcp_server/tools/workflow.py:78-130. The corresponding Jama requirement is AF-SUBSS-26 in project 127. Create the trace link from that requirement to this code.` | `create_path_a_trace(project_id=127, source_requirement_key="AF-SUBSS-26", code_path="src/jama_mcp_server/tools/workflow.py:78-130", code_version=<sensible default>, repo_origin=<sensible default for this repo>)` — single call. |
| 2 | Search-first framing — does the agent know to find the requirement before tagging? | `Find the requirement in Jama project 127 about mapping HTTP errors to typed exceptions, then link my code at src/jama_client/client.py to it.` | `search_items(project_id=127, query="HTTP errors typed exceptions")` → `get_item(<resolved item_id>)` to confirm → `create_path_a_trace(source_requirement_key="AF-SUBSS-27", ...)`. |
| 3 | Explicit primitive composition — does the agent honor the developer's stepwise framing instead of jumping ahead? | `Show me all subsystem requirements in Jama project 127. I want to pick one before we wire anything up.` | `list_items_by_type(project_id=127, item_type=87)` — halts and surfaces results to the developer rather than reaching into write tools. |
| 4 | Wrong-fit trap — does the agent distinguish "add a note" from "create a trace"? | `Add a note to Jama requirement AF-SUBSS-26 saying that the workflow tool implementation at src/jama_mcp_server/tools/workflow.py now exists.` | `search_items(project_id=127, query="AF-SUBSS-26")` or equivalent resolution → `create_comment(item_id=<resolved>, project_id=127, body=...)` — **NOT** `create_relationship` or `create_path_a_trace`. |
| 5 | Idempotency under repeated tagging — does the agent recognize that "tag this code to a second requirement" should reuse the existing Code item rather than create a duplicate? | `I already tagged src/jama_client/client.py:_raise_for_status to AF-SUBSS-27 in project 127 — that's the HTTP-error-to-typed-exception mapping requirement. We've also decided this same code section implements AF-SUBSS-26 because it sits in the same workflow path as create_path_a_trace's error handling. Tag it to that one too.` | Ideal (duplication-avoiding): `search_items` to resolve both keys → `list_items_by_type(project_id=127, item_type=114)` to find existing Code item matching `path$114` → `create_relationship(from_item=<AF-SUBSS-26 item_id>, to_item=<existing Code item_id>, relationship_type=19)`. **Actual MVP behavior**: the agent likely invokes `create_path_a_trace`, which creates a fresh Code item — surfacing the idempotency gap. Both outcomes are findings. |
| 6 | Bad-key error recovery — does the agent surface failures cleanly when the requirement does not exist? | `Tag my code at src/jama_mcp_server/tools/workflow.py to requirement AF-SUBSS-NOPE in project 127.` | `create_path_a_trace(...)` → `JamaNotFoundError` → subagent describes how it would surface the failure to the developer. |
| 7 | Novice phrasing — does the agent recover intent from informal, under-specified prompts? | `i wrote some code and now i need to put it in jama so we know it implements the spec. file is src/jama_mcp_server/tools/workflow.py. spec is AF-SUBSS-26. project is 127.` | Functionally equivalent to scenario 1's ideal. |

### 4.1 Line-range and version resolution at execution time

Scenarios 1, 5, and 7 reference specific files. Exact line ranges (`:N-M` suffixes) are resolved at scenario-execution time by reading the relevant modules in this repository — this keeps the spec stable across code-change churn between now and execution. `code_version` for the agent's defaults is resolved similarly (use the most recent release tag or the current `HEAD` SHA at execution time, whichever the agent chooses; the choice itself is a finding).

### 4.2 Outcome analysis for scenario 5

Scenario 5 has three plausible outcomes, each of which is a useful finding:

1. **Agent invokes `create_path_a_trace`.** A duplicate Code item is created. Finding: the macro tool's docstring does not telegraph its non-idempotent semantics strongly enough; downstream Jama state has duplicate `path$114` values.
2. **Agent composes primitives with find-and-reuse.** No duplication. Finding: Opus 4.7 is sophisticated enough to navigate the gap, but smaller models likely will not — recommendation: harden the macro's docstring or add a `reuse_existing_code_item` parameter.
3. **Agent recognizes ambiguity and would normally ask but per instructions does not.** The default choice depends on the prompt's framing. Finding: documented in the report with the agent's emitted reasoning.

### 4.3 Tools deliberately not exercised

`whoami`, `list_projects`, `get_test_runs_for_item`, `get_downstream_relationships`, `list_relationship_types`, `list_item_types` are not load-bearing for the Software Engineer use case. They are out of scope here and are recommended for coverage in a future System Engineer-use-case DX testing session.

## 5. Session phases and order

The phase has seven sub-phases plus this design-spec commit.

| Phase | Description | Approx. effort | Surface |
|---|---|---|---|
| 0 | Commit this design specification, the cloud-routine runbook, and the PR template addition directly to `main` (docs-only direct commit per `CLAUDE.md`). | 10–15 min | Local session |
| 1 | Open the GitHub issue describing the bundled implementation pull request's scope. Submit the implementation routine via the `RemoteTrigger` API per the runbook. | 15–20 min | Local session + claude.ai/code |
| 2 | Cloud routine implements the bundled changes, opens the pull request. CI runs. Operator reviews and squash-merges. | 60–120 min (mostly routine + CI runtime; operator review interleaved) | Cloud routine + GitHub |
| 3 | Pre-flight in a fresh local session: confirm `AF-SUBSS-26` / `AF-SUBSS-27` keys, resolve scenario line ranges by reading the (now-merged) modules. | 10 min | Local session |
| 4 | Run the seven scenarios via `Agent` subagents and capture transcripts. | 35–90 min | Local session |
| 5 | Analyze transcripts. Write the findings report to `docs/superpowers/findings/2026-05-11-jama-mvp-dx-testing-findings.md`. Commit directly to `main` (docs-only direct commit). | 60–90 min | Local session |
| 6 | Persist private layer: one to two knowledge-graph entities capturing non-obvious findings; `MEMORY.md` "Recent decisions" row pointing at the report. | 15 min | Local session |

Phases 0 and 1 land in the same calendar session. Phases 2 and 3 may be split across calendar sessions depending on routine runtime. Phases 4–6 cluster into one local session post-merge.

## 6. Bundled implementation pull request (Phase 2)

The cloud routine delivers two changes together. They are bundled because they touch the same module (`JamaClient.create_path_a_trace`), share a regex-anchoring code path, and form a coherent hardening unit.

### 6.1 Change A — Name-derivation truncation regex fix

Per `MEMORY.md` "Known issues" — `create_path_a_trace` derives the new Code item's `name` from the code path's basename "excluding any trailing `:line-range` suffix." The implementation truncates at the **first** colon rather than detecting a trailing `:N-M` line-range specifically. Code paths containing non-line-range colons (ISO timestamps, embedded annotations, Windows-style paths) get truncated early.

**Code change:** locate the derivation in `src/jama_client/client.py` on `JamaClient.create_path_a_trace`; replace first-colon truncation with a regex anchored on `:\d+-\d+$`, stripping only trailing line-ranges.

### 6.2 Change B — Repository origin + deep-link description population

New behavior: when `create_path_a_trace` creates a Code item, it populates the item's `description` field with a human-readable deep link to the tagged code. This addresses the "reviewer cannot locate code from Jama without external knowledge" gap surfaced during the DX testing design discussion.

**New parameter:** `repo_origin: str` on both `JamaClient.create_path_a_trace` and the MCP workflow tool wrapper. Expected value: a `<host>/<owner>/<repo>` identifier, for example `github.com/arthurfantaci/jama-mcp-server`. No leading scheme; the tool prepends `https://` when constructing the deep link.

**Description-text format** (populated on item creation):

```
Repository: <repo_origin>
Version: <code_version>
Path: <path-without-line-range> (lines N-M)   [when a trailing line-range is present]
Path: <path-without-line-range>               [when no line-range is present]
Link: https://<repo_origin>/blob/<code_version>/<path-without-line-range>#L<N>-L<M>
```

The "Link" line is rendered as a clickable URL by Jama's UI when the tenant's link-detection is enabled (most are by default).

**URL flavor:** GitHub-style only in this iteration. The path-segment ordering (`blob/<ref>/`) and line-range fragment syntax (`#L<n>-L<m>`) are GitHub conventions. GitLab and Bitbucket support is a future enhancement scoped to a separate pull request when a customer engagement requires it.

**Line-range parsing dependency:** the same regex anchored on `:\d+-\d+$` used by Change A is reused to split the path's basename from its line-range when constructing the URL. Change A is therefore a prerequisite for Change B's correctness on edge-case paths; bundling the two ensures they ship together with consistent behavior.

### 6.3 Pull request shape

- **Issue title:** `feat: populate Code item description with deep link; fix name truncation`
- **PR title (verbatim, set by routine prompt):** `feat: populate Code item description with deep link; fix name truncation`
- **PR base:** `main`
- **Branch:** auto-generated by the platform on Trigger fire (e.g., `claude/<adjective>-<noun>-<suffix>`); cosmetic per the runbook's note on initial Trigger behavior.

### 6.4 Tests added

- **Truncation regex:** one unit test in `tests/unit/jama_client/` asserting basename preservation on a path containing non-line-range colons (e.g., `events:custom-handler.py`); one regression test asserting line-range strip on a `:7-42` suffix.
- **Description population:** one unit test asserting the constructed description matches the format in Section 6.2 for a representative path with a line range; one test for the same path without a line range; one test verifying the URL field is constructed correctly.
- **`repo_origin` propagation:** one unit test asserting the parameter is passed correctly through `JamaClient.create_path_a_trace` to the request payload.

All tests follow the synthetic-response pattern in `tests/unit/jama_client/` and the MCP-protocol pattern in `tests/unit/jama_mcp_server/test_protocol.py` per `CLAUDE.md` conventions.

### 6.5 Docstring updates

Both layers (`JamaClient.create_path_a_trace` method, MCP workflow tool wrapper) have docstrings updated to:

- Reflect the new `repo_origin` parameter (purpose, format, examples).
- Reflect the description-population behavior at item creation.
- Continue to note the asymmetry that `source_requirement_key` accepts a document key while other write tools expect numeric IDs.

### 6.6 Verification before push

The routine runs all four convention-mandated commands; all four must pass before push:

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src/`
- `uv run pytest -m "not integration"`

Integration tests are not run by the routine (Jama OAuth is not configured in the routine environment).

## 7. Findings report structure (Phase 5)

`docs/superpowers/findings/2026-05-11-jama-mvp-dx-testing-findings.md` will contain:

1. **Context** — what was tested, why (DX testing phase per `MEMORY.md`), what is out of scope.
2. **Methodology** — subagent execution model, scenario set rationale, validity caveats.
3. **Per-scenario results** — subsection per scenario: prompt verbatim, observed tool sequence, deviation from ideal (if any), takeaway.
4. **Surfaced issues** — truncation regex fix (with reference to the closing pull request), Path A description-population (also closed by the same pull request), idempotency gap from scenario 5, any docstring or parameter-naming weaknesses surfaced during analysis.
5. **Recommendations** — actionable items for tool docstrings, parameter naming, namespace mechanics, future testing.
6. **Limitations** — Opus-only, single-host, single-vendor, single-session; recommended future DX-testing sessions.
7. **References** — MVP build spec, foundation spec, bundled pull request, cloud-routine runbook, `CLAUDE.md` conventions, `MEMORY.md` current state.

## 8. Stop conditions

- **If the cloud routine cannot complete the bundled pull request cleanly** (test failures unfixable in one attempt, spec ambiguity, new dependency needed, pre-commit failures): the routine escalates per the runbook; the operator resolves via follow-up Session or revises the spec. Phase 2 is paused; Phases 3–6 do not begin until Phase 2 resolves.
- **If Phase 4 scenarios surface a second bug worth fixing**: log it in the findings report; do not chain a second fix-PR within this session. One bundled implementation pull request per DX testing phase is the cap to prevent sprawl.
- **If findings beyond the two changes already in the bundled PR are thin**: the findings report stays short, and the "Limitations" section explicitly calls out test-set insufficiency rather than padding the content.

## 9. Out of scope (explicit)

- **Cross-host testing** (Claude Desktop, Cursor, Continue, Copilot Chat). Recommended for a future session; the architectural argument for host-agnosticism stands without evidence-backing from this session.
- **Smaller-model testing** (Haiku, Sonnet, third-party models). Recommended for a future session.
- **System Engineer use-case scenarios.** Scoped as a separate engagement deliverable per the consulting brief.
- **End-to-end UX validation including HITL permission UI.** Single-host single-runtime means HITL legibility is constant across the session; no comparison data to analyze.
- **Performance characterization** (latency, token usage per scenario). Not part of the failure-mode anchoring; ignored.
- **Brief revision** beyond what Section 6 of the MVP build spec already specifies. Further brief changes require their own intent.
- **Idempotency hardening of `create_path_a_trace`.** The gap surfaced by scenario 5 is recorded as a finding and design decision for future work; not addressed in this phase's bundled pull request.
- **Multi-host repo-origin support** (GitLab, Bitbucket flavors of URL construction). GitHub-style only in this iteration. Addable in a separate pull request when a customer engagement requires it.

## 10. References

- **Foundation design spec:** [`2026-04-28-jama-mcp-server-design.md`](2026-04-28-jama-mcp-server-design.md)
- **MVP build spec:** [`2026-05-10-jama-mvp-build-design.md`](2026-05-10-jama-mvp-build-design.md)
- **Cloud routine runbook:** [`../../runbooks/cloud-routine-config.md`](../../runbooks/cloud-routine-config.md)
- **Project conventions:** [`../../../CLAUDE.md`](../../../CLAUDE.md)
- **Working state and known issues:** [`../../../MEMORY.md`](../../../MEMORY.md)
- **Author's global protocols:** `~/.claude/CLAUDE.md`
- **Consulting brief (gitignored):** `docs/internal/briefs/InfusionGuard 2200 - Software Engineer Workflow Brief.md`

---

*End of specification.*
