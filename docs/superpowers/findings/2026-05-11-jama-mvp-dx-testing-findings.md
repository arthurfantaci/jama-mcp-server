# Jama MCP Server — DX Testing Findings

**Date:** 2026-05-11
**Status:** Final
**Author:** Arthur Fantaci
**Design spec:** [`../specs/2026-05-11-jama-mvp-dx-testing-design.md`](../specs/2026-05-11-jama-mvp-dx-testing-design.md)
**Bundled implementation PR:** [#16](https://github.com/arthurfantaci/jama-mcp-server/pull/16) — `feat: populate Code item description with deep link; fix name truncation` (squash-merged 2026-05-11 as commit `57db8a2`)
**Closing issue:** [#15](https://github.com/arthurfantaci/jama-mcp-server/issues/15) — auto-closed by merge

## 1. Context

The DX testing phase validates the developer experience of the Jama MCP server's thirteen-tool surface for the Software Engineer use case (Preston Mitchell persona; see the consulting brief). The phase had two sequential pieces:

1. **Bundled implementation pull request** (PR #16): two changes to `JamaClient.create_path_a_trace` and the MCP workflow wrapper, delivered by a single autonomous cloud routine. Change A fixed the name-derivation truncation regex (anchored on `:\d+-\d+$` instead of first-colon split); Change B added a new `repo_origin` parameter that, when supplied, populates the new Code item's `description` field with a four-line GitHub-style deep link.
2. **Seven scenarios** (this report): general-purpose `Agent` subagents invoked the post-merge tool surface cold, each receiving a developer-style prompt grounded in real project state — `AF-SUBSS-26` and `AF-SUBSS-27` (Software Requirements describing this project's own behavior), and code paths drawn from this repository's `src/jama_client/client.py` and `src/jama_mcp_server/tools/workflow.py`.

The primary observable is **the sequence of tool calls the agent emits** in response to natural-language prompts. Secondary observables are parameter choices (especially defaults for `code_version` and `repo_origin`), error-surfacing behavior, and the agent's handling of under-specified prompts.

## 2. Methodology

Each scenario was executed by a `general-purpose` subagent spawned via the `Agent` tool with the exact prompt template specified in Section 3.1 of the design specification. Subagents inherit MCP server connections (including the Jama MCP server's thirteen tools) but **not** the parent session's conversation history, `CLAUDE.md` content, `MEMORY.md` content, spec content, or knowledge-graph entries. Each agent therefore encounters the tool surface cold.

All seven subagents were dispatched in parallel in a single message. Parallel dispatch isolates each agent's tool-selection observation from cross-scenario influence on the agent's reasoning, though Jama-side state inevitably accumulates across the run (relationships, Code items, comments). One transient side-effect of parallel execution surfaced in Scenario 1 and is documented in Section 4.7.

The "do not ask clarifying questions — choose sensible defaults" instruction in the template is deliberate: it biases the subagent toward emitting tool calls (the data the session needs) rather than producing a low-information clarification turn.

## 3. Per-scenario results

Each subsection lists the developer prompt verbatim, the observed tool sequence, the deviation (if any) from the spec's ideal sequence, and the takeaway.

### 3.1 Scenario 1 — Macro target

**Prompt:** "I just wrote the create_path_a_trace MCP wrapper at src/jama_mcp_server/tools/workflow.py:36-99. The corresponding Jama requirement is AF-SUBSS-26 in project 127. Create the trace link from that requirement to this code."

**Ideal sequence:** Single `create_path_a_trace` call.

**Observed sequence:**

1. `create_path_a_trace(project_id=127, source_requirement_key="AF-SUBSS-26", code_path="src/jama_mcp_server/tools/workflow.py:36-99", code_version="main")` — agent reports HTTP 409 returned.
2. `search_items` (resolved AF-SUBSS-26 → 115106).
3. `get_downstream_relationships(115106)` — surfaced two existing "Implemented by" traces to Code items 115110 and 115111 (created by Scenarios 7 and 5, respectively, running concurrently).
4. `create_item(item_type=114, parent=115094, name="workflow.py:create_path_a_trace", fields={path$114, code_version$114})` → produced Code item 115112.
5. `create_relationship(from_item=115106, to_item=115112, relationship_type=19)` → produced relationship 18511.

**Deviation:** The agent reached for the macro first (correct), then fell back to composing primitives after a transient failure. Its rationale for composing rather than retrying was sound: it inspected existing traces, observed the developer's prompt was more specific than the existing artifacts (lines 36-99 vs. whole-file at `HEAD`), and created a precise new pointer.

**`repo_origin`:** Not supplied. `code_version` defaulted to `"main"` (branch name).

**Takeaway:** Macro selection is correct on the happy path. The agent's recovery from the transient failure showed sophisticated tool composition — but smaller models would more plausibly retry blindly or surface the raw error.

### 3.2 Scenario 2 — Search-first framing

**Prompt:** "Find the requirement in Jama project 127 about mapping HTTP errors to typed exceptions, then link my code at src/jama_client/client.py to it."

**Ideal sequence:** `search_items` → `get_item` → `create_path_a_trace`.

**Observed sequence:**

1. `search_items(project_id=127, query="HTTP errors typed exceptions")` and two retries with re-worded queries — all three returned empty.
2. `list_item_types(project_id=127)` — surfaced Subsystem Requirement = type 87.
3. `list_items_by_type(project_id=127, item_type=87, max_items=200)` — returned 12 items including `AF-SUBSS-27` whose description specified the HTTP-error mapping.
4. `create_path_a_trace(source_requirement_key="AF-SUBSS-27", code_path="src/jama_client/client.py", code_version="main")` → produced Code item 115113 and relationship 18512.

**Deviation:** The agent pivoted from free-text search to type-based enumeration when `search_items` failed to surface results — sound, but slow (12-item scan rather than direct lookup). The pivot itself confirms the agent understood the constraint: it didn't give up and didn't blindly retry the same query.

**`repo_origin`:** Not supplied. `code_version` defaulted to `"main"`.

**Takeaway:** `search_items` quality is a real constraint (no stemming, no semantic match, exact-phrase only). The agent's pivot is the correct DX recovery but produces a low-signal first turn for the developer. The `list_items_by_type` fallback works but is order-N rather than order-1.

### 3.3 Scenario 3 — Explicit primitive composition

**Prompt:** "Show me all subsystem requirements in Jama project 127. I want to pick one before we wire anything up."

**Ideal sequence:** `list_items_by_type(item_type=87)` and halt.

**Observed sequence:**

1. `list_item_types(project_id=127)` — confirmed Subsystem Requirement = type 87.
2. `list_items_by_type(project_id=127, item_type=87, max_items=500)` — returned 12 items, `max_items_reached=False`.

The agent then formatted the 12 results by parent set and surfaced them to the developer. **No write tools were invoked.**

**Deviation:** None. The agent invoked an additional `list_item_types` discovery call before `list_items_by_type` to resolve type 87 — defensible (it cannot rely on knowing the project-specific type ID a priori) but adds a turn.

**Takeaway:** The "halt and surface" outcome is the correct response to stepwise developer framing. Tool-selection discipline held cleanly; the agent did not jump ahead into write tools despite having them available.

### 3.4 Scenario 4 — Wrong-fit trap

**Prompt:** "Add a note to Jama requirement AF-SUBSS-26 saying that the workflow tool implementation at src/jama_mcp_server/tools/workflow.py now exists."

**Ideal sequence:** Key resolution → `create_comment`.

**Observed sequence:**

1. `list_projects()` — returned project 127 (Arthur Sandbox).
2. `search_items(project_id=127, query="AF-SUBSS-26")` → item 115106.
3. `create_comment(item_id=115106, project_id=127, body=<implementation note>, comment_type="GENERAL")` → comment ID 551 created on AF-SUBSS-26.

**Deviation:** The agent invoked `list_projects` despite the prompt explicitly stating project context ("Jama requirement AF-SUBSS-26"). Minor inefficiency — one redundant discovery call. The trap was avoided: the agent did not reach for `create_relationship` or `create_path_a_trace`, both of which would have been semantically wrong for "add a note."

**Takeaway:** The "note vs trace" semantic distinction is clear enough in the tool docstrings that Opus 4.7 selected correctly. The `list_projects` redundancy suggests an agent default of "discover the project before doing anything," which could be tightened by documenting in `create_comment`'s docstring that `project_id` is required as a parameter (already true) and skipping the discovery turn when the prompt provides project context.

### 3.5 Scenario 5 — Idempotency under repeated tagging

**Prompt:** "I already tagged src/jama_client/client.py:\_raise\_for\_status to AF-SUBSS-27 in project 127 — that's the HTTP-error-to-typed-exception mapping requirement. We've also decided this same code section implements AF-SUBSS-26 because it sits in the same workflow path as create_path_a_trace's error handling. Tag it to that one too."

**Ideal sequence (duplication-avoiding):** `search_items` → `list_items_by_type(item_type=114)` to find existing Code item → `create_relationship`.

**Observed sequence:**

1. `create_path_a_trace(project_id=127, source_requirement_key="AF-SUBSS-26", code_path="src/jama_client/client.py:_raise_for_status", code_version="v1.0.0-rc1")` → produced Code item 115111 and relationship 18509.

**Deviation:** The agent invoked the macro and created a new Code item rather than searching for the existing one. **However, the agent proactively flagged the idempotency gap in its summary:**

> Note: this creates a second, distinct Code item rather than reusing the one already tagged to AF-SUBSS-27 — the `create_path_a_trace` workflow always creates a fresh Code item, so `_raise_for_status` now has two separate Code-item representations in Jama, one linked to each requirement. If you'd wanted both requirements pointing at a single shared Code item, that would require calling `create_relationship` directly against the existing code_item_id from the AF-SUBSS-27 trace instead.

**Path handling:** The `:_raise_for_status` member-style suffix was passed verbatim. The truncation regex (anchored on `:\d+-\d+$`) correctly did not strip it; the derived name became `client.py:_raise_for_status`. **`code_version` choice:** the agent picked `"v1.0.0-rc1"` — explicitly stated as "matching the prior AF-SUBSS-27 tag." That suggests the agent assumed seed data from the prompt and chose a coherent default rather than `HEAD` or `main`.

**`repo_origin`:** Not supplied.

**Takeaway:** This is the most informative scenario. Opus 4.7 understood the docstring well enough to articulate the idempotency limitation in plain prose, but the tool surface does not enforce reuse. **Three findings flow from this:**

1. The macro's docstring already implies non-idempotent semantics ("creates a Code item") clearly enough for a sophisticated agent to articulate, but the implication is not strong enough to redirect tool choice.
2. Smaller models (Haiku, GPT-4o, Gemini Flash) would less plausibly produce the explanatory note — the duplicate would be silent.
3. A `reuse_existing_code_item_id` parameter on `create_path_a_trace`, or a separate `tag_existing_code` workflow tool, would close the gap.

### 3.6 Scenario 6 — Bad-key error recovery

**Prompt:** "Tag my code at src/jama_mcp_server/tools/workflow.py to requirement AF-SUBSS-NOPE in project 127."

**Ideal sequence:** `create_path_a_trace(...)` → fail-fast on key resolution → surface error.

**Observed sequence:**

1. `create_path_a_trace(project_id=127, source_requirement_key="AF-SUBSS-NOPE", code_path="src/jama_mcp_server/tools/workflow.py", code_version="HEAD")` → tool surfaced an error indicating the document key could not be resolved.

The agent then framed the failure cleanly for the developer: "The requirement key AF-SUBSS-NOPE doesn't exist in project 127 — please double-check the key (it looks like a placeholder/typo); you can find the correct key in the Jama UI on the requirement page, or I can search_items in project 127 if you give me a few words from the requirement title."

**Deviation:** None. The fail-fast contract held: no Code item was created, no relationship was attempted, Jama state was unchanged.

**`code_version`:** Defaulted to `"HEAD"` (third variant observed across the run).

**Takeaway:** The pre-validation step in `create_path_a_trace` (validating the source requirement before any write) works as documented and produces a clean recovery surface for the agent.

### 3.7 Scenario 7 — Novice phrasing

**Prompt:** "i wrote some code and now i need to put it in jama so we know it implements the spec. file is src/jama_mcp_server/tools/workflow.py. spec is AF-SUBSS-26. project is 127."

**Ideal sequence:** Same as Scenario 1, without the line range.

**Observed sequence:**

1. `create_path_a_trace(project_id=127, source_requirement_key="AF-SUBSS-26", code_path="src/jama_mcp_server/tools/workflow.py", code_version="HEAD")` → produced Code item 115110 (`AF-CODE-5`, `name="workflow.py"`) and relationship 18510.

**Deviation:** None. The informal phrasing did not degrade tool selection. The agent reached for the macro directly.

**`code_version`:** Defaulted to `"HEAD"`. **`repo_origin`:** Not supplied.

**Takeaway:** Under-specified, informal prompts recover cleanly to the macro target. The agent's robustness to phrasing is a positive finding for customer-facing deployment, where natural-language IDE prompts rarely look like the structured form in Scenario 1.

## 4. Surfaced issues

### 4.1 `repo_origin` was not used by any of the seven agents

**Severity:** High. **The new `repo_origin` parameter — the centerpiece of PR #16's hardening — was never supplied across the five scenarios that created Code items.** Verification: `get_item` on Code items 115110 (Scenario 7) and 115113 (Scenario 2) both returned `fields` dicts with no `description` key. Scenarios 1, 5, and 6 also created Code items (or attempted to) without `repo_origin`.

**Root cause:** The agent has no signal that `repo_origin` matters. None of the seven prompts mention repository context, and none of the agents proactively inspected `git remote -v` or hard-coded a `github.com/<owner>/<repo>` value. The tool docstring documents the parameter and its effect, but the parameter is optional with a `None` default, so omission is silent.

**Impact:** The Code items created during DX testing carry only `path$114` and `code_version$114` — no deep link to the source. Jama reviewers cannot navigate from the Code item to the tagged code without external knowledge, defeating the design goal of PR #16's Change B.

**Recommendation:** see Section 5.1.

### 4.2 Idempotency gap not enforced; recognition depends on model strength

**Severity:** Medium. Scenario 5 demonstrated that `create_path_a_trace` cannot be re-used to tag an already-tagged code section to a second requirement without producing a duplicate Code item. Opus 4.7 articulated this limitation in its response but still executed the macro, producing the duplicate.

**Recommendation:** see Section 5.2.

### 4.3 Concurrent `create_path_a_trace` calls produced a transient error in Scenario 1

**Severity:** Low to medium. With three subagents (Scenarios 1, 5, 7) calling `create_path_a_trace` against `AF-SUBSS-26` concurrently, Scenario 1's agent reported "HTTP 409" from its macro call and fell back to composing primitives. The exact failure mode is not preserved in the agent's transcript (only the agent's narrative gloss), and the test environment does not log raw Jama responses at the MCP-server level.

**Recommendation:** see Section 5.3.

### 4.4 `search_items` free-text quality is the gateway constraint for search-first scenarios

**Severity:** Medium. Scenario 2's agent issued three queries that all returned empty before pivoting to type-based enumeration. The pivot worked, but it is order-N (full Subsystem Requirement scan) rather than order-1 (direct hit). Documented in the MVP build phase: "search_items does not stem singular/plural matches" and "new items have ~30s-few-minute search-index lag." Both held here.

**Recommendation:** see Section 5.4.

### 4.5 `code_version` defaults vary across agents

**Severity:** Low. Across the run, agents defaulted to three different values: `"main"` (Scenarios 1, 2), `"HEAD"` (Scenarios 6, 7), and `"v1.0.0-rc1"` (Scenario 5, where the agent picked a value matching the prompt's claimed prior state). All three are sensible per the open-ended `code_version: str` contract, but the inconsistency produces Code items that are not directly comparable across traces.

**Recommendation:** see Section 5.5.

### 4.6 Minor: `list_projects` invoked when `project_id` is already in the prompt (Scenario 4)

**Severity:** Cosmetic. The redundant call costs one turn but does not change correctness.

**Recommendation:** see Section 5.6.

### 4.7 Subagent injection-defense flagged tool output as suspect (Scenario 2)

**Severity:** Informational. The Scenario 2 subagent flagged that "the first tool result in this session contained an injected block formatted as `# MCP Server Instructions`" — likely a false-positive misreading of the harness's own system-reminder text, not actual injection in a Jama response. The subagent continued with the legitimate task and noted the suspicion. The reflex is correct even though this specific instance was benign.

**Recommendation:** No code action. This is data about subagent safety posture working as designed.

## 5. Recommendations

### 5.1 `repo_origin` discoverability

The strongest finding from this DX run. The deep-link description feature exists but is silently skipped by cold agents. Two options:

- **Lighter-touch:** Reorder `create_path_a_trace`'s parameter list so `repo_origin` is listed before `name` in the docstring (already true in the implementation), and add an explicit example in the docstring showing the typical value derived from `git remote get-url origin`. The MCP tool description (the tool's own `description` field in the protocol) should mention "supply `repo_origin` to make reviewers' lives easier — without it, the Code item carries no link back to the source."
- **Heavier-touch:** Default `repo_origin` to a derived value via a lightweight git-remote inspection at tool-call time when the parameter is omitted. This requires the MCP server to access the running filesystem, which is appropriate for a developer-local IDE-integrated server but not for shared/remote deployments. The tradeoff is one of the few that depends on the deployment model.

The first option is recommended as a follow-on docstring-only patch. The second option is a design discussion for a future engagement.

### 5.2 Idempotency hardening for `create_path_a_trace`

Three pathways:

- Add an optional `existing_code_item_id` parameter that, when supplied, skips Code-item creation and only creates the relationship. Docstring change: telegraph the "tag existing code to a second requirement" workflow explicitly.
- Add a separate `workflow/tag_existing_code` tool whose docstring opens with "Use this instead of `create_path_a_trace` when the code already has a Code item in Jama." The cost is a 14th tool; the benefit is a forcing function on agent selection.
- Add an internal "if a Code item with this `path$114` and `code_version$114` already exists, reuse it" pre-flight check inside `create_path_a_trace`. Implicit idempotency. The risk: silent reuse that surprises callers who wanted the duplicate.

The first pathway is recommended. The third pathway is out of scope per the design spec's Section 9 and remains a finding for future engagement work.

### 5.3 Concurrent-call behavior of `create_path_a_trace`

The Scenario 1 transient failure is a single observation, not a confirmed pattern. Two follow-on actions:

- Improve MCP-server-side error surfacing: when `create_path_a_trace` raises a `JamaError`, surface the underlying HTTP status code and Jama envelope verbatim in the tool's error response, not just the typed-exception class name. This would let future testing distinguish "Jama returned 409" from "client raised JamaValidationError for an unknown reason."
- Reproduce the failure deterministically: run two `create_path_a_trace` calls concurrently against the same source requirement in a controlled test and verify whether Jama returns 409 on relationship creation. If yes, document the constraint in the docstring; if no, attribute Scenario 1's failure to a transient and remove the concern.

### 5.4 `search_items` documentation

The MVP build phase already codified `search_items` constraints in `MEMORY.md` (no stemming, ~30s-few-minute index lag). Promote these constraints to the MCP tool docstring so cold agents see them at tool-discovery time, with a one-line recommendation: "If `search_items` returns empty, consider `list_items_by_type` as a fallback when the item type is known."

### 5.5 `code_version` defaulting

Document the recommended convention in the docstring. Options: "use the most recent release tag" or "use the current HEAD SHA" — pick one and articulate it. Both are valid; consistency matters more than the choice. Suggest in the docstring that branch names (`"main"`) are weaker defaults than tags or SHAs because the resolved code can shift later.

### 5.6 `list_projects` redundancy

Lower priority. Could be addressed by adding an explicit note to the `create_comment` and `create_path_a_trace` docstrings: "When `project_id` is provided by the caller, no prior `list_projects` discovery turn is needed." The cost of the redundant call is small enough that this is a polish item, not a blocker.

## 6. Limitations

The findings in this report are subject to four constraints:

1. **Opus 4.7 ceiling.** Findings represent the strongest agent runtime available. Customer-deployed agents on smaller models (Haiku, GPT-4o, Gemini Flash) may degrade in ways this session does not surface — most notably on Scenarios 1 (transient-failure recovery) and 5 (idempotency-gap articulation). The `repo_origin` finding (Section 4.1) likely worsens on smaller models, where docstring-driven discovery is weaker.
2. **Single-host scope.** Only Claude Code was exercised. The architectural claim that tool-selection findings transfer cleanly across hosts (Cursor, Continue, Copilot Chat) holds in principle but is not evidenced by this session.
3. **General-purpose system prompt.** Subagents retain Claude Code's default system prompt and globally-loaded skills. Behaviors observed here may diverge in third-party hosts with different tool-call orchestration logic.
4. **Single-session, concurrent execution.** All seven scenarios were dispatched in parallel in a single calendar minute. Scenario 1's transient failure may be an artifact of that concurrency rather than a deployment-realistic condition. A sequential rerun is recommended if Section 4.3's mitigation is pursued.

Recommended future DX-testing sessions:

- **Smaller-model session.** Same scenario set, executed against a Haiku or third-party-model subagent to establish a "weakest model" floor.
- **Cross-host session.** Replicate Scenario 1, 4, and 5 in Cursor and Continue to evidence-back the host-agnostic claim.
- **System Engineer use-case session.** Distinct scenario set focused on `whoami`, `list_projects`, `get_test_runs_for_item`, `get_downstream_relationships`, `list_relationship_types`, `list_item_types` — none of which were load-bearing for the Software Engineer use case and therefore not exercised here.

## 7. References

- **MVP build spec:** [`../specs/2026-05-10-jama-mvp-build-design.md`](../specs/2026-05-10-jama-mvp-build-design.md)
- **Foundation design spec:** [`../specs/2026-04-28-jama-mcp-server-design.md`](../specs/2026-04-28-jama-mcp-server-design.md)
- **DX testing design spec:** [`../specs/2026-05-11-jama-mvp-dx-testing-design.md`](../specs/2026-05-11-jama-mvp-dx-testing-design.md)
- **Cloud routine runbook:** [`../../runbooks/cloud-routine-config.md`](../../runbooks/cloud-routine-config.md)
- **Project conventions:** [`../../../CLAUDE.md`](../../../CLAUDE.md)
- **Working state:** [`../../../MEMORY.md`](../../../MEMORY.md)
- **Bundled implementation pull request:** [#16](https://github.com/arthurfantaci/jama-mcp-server/pull/16)
- **Closing issue:** [#15](https://github.com/arthurfantaci/jama-mcp-server/issues/15)

---

*End of findings.*
