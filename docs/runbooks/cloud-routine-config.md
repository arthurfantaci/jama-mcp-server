# Cloud Routine Configuration Runbook

**Purpose:** Standardize the configuration, prompt structure, and operational conventions for cloud routines submitted via `claude.ai/code` to operate on this project. A routine that follows this runbook should run autonomously, produce a single reviewable pull request, and stop-and-escalate cleanly on the failure modes documented below.

**Audience:** the project's author and any future operator preparing to submit a routine against this repository.

**Cross-cutting reference:** the author's global protocols at `~/.claude/CLAUDE.md` define Session Handoff, Phase Handoff, Pre-Compaction, and Knowledge Graph protocols that interact with routine submission. This runbook is project-scoped; the global protocols are not duplicated here.

## 1. When to use a cloud routine

A cloud routine is appropriate for work that:

- **Has a settled design specification** committed to the repository (typically in `docs/superpowers/specs/`). Ambiguous scope is the leading cause of routine escalation.
- **Can complete in one pull request** without interactive clarification. Routines are non-interactive; mid-run questions force escalation to GitHub PR comments and a separate Session to resolve.
- **Does not modify external state** beyond GitHub (commits, branches, pull request creation). Operations against external systems (Jamacloud, Slack, etc.) require Connectors and are higher-risk; prefer to keep them in human-driven sessions until the Connector pattern has been rehearsed for this project.
- **Has a predictable verification path.** For this project that is `uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest -m "not integration"`. Routines that need novel verification logic are higher-risk.

A cloud routine is NOT appropriate for:

- Exploratory or research work — use a local Claude Code session.
- Multi-pull-request sequences — use multiple sequential routines, not one.
- Work whose scope changes mid-flight — revise the design specification, then submit a new routine.
- Work that requires user input during execution — use a local session or an ad-hoc `claude.ai/code` Session.

## 2. Cloud routine vs. ad-hoc Session vs. local Claude Code

| Surface | Use for | Branching behavior | Communication |
|---|---|---|---|
| **Local Claude Code (IDE terminal)** | Interactive design, exploration, debugging, learning the codebase | Operator drives `git checkout -b` | Direct chat |
| **Cloud routine (Trigger)** | Bounded autonomous implementation against a spec | Branch auto-named on initial Trigger fire (e.g., `claude/adjective-noun-XXX`); pull request title is what we control | GitHub pull request and issue comments; `claude.ai/code` run-history transcripts |
| **Ad-hoc Session (`claude.ai/code`)** | Targeted follow-up on a Trigger's branch (e.g., adding a test, fixing CI) | Honors explicit branch directives in prompts | Same as Trigger |

The Trigger vs. Session distinction was characterized empirically during the MVP build routine on 2026-05-10. Sessions respect "work on branch X" directives in prompts; Triggers do not on their initial fire. Branch directives in a Trigger's prompt should be treated as cosmetic guidance rather than as binding instructions.

## 3. Pre-submission checklist

Before submitting a routine, verify in order:

1. **Design specification committed.** The path is referenceable from the routine prompt. The spec is the routine's contract; if the spec is missing or stale, the routine guesses.
2. **GitHub issue opened.** Includes the spec reference and (in the proposed pull request title) a `closes #N` directive. Routines cite the issue number in their pull request.
3. **Working state in `MEMORY.md` reflects the upcoming routine.** A "Recent decisions" row pointing at the spec, the issue, and the planned routine submission.
4. **No conflicting branches or pull requests.** Routines write to a fresh branch, so an existing branch with the same intent is not a blocker, but it creates review noise. Close or delete redundant branches first.
5. **Local verification clean.** Run the four-command verification on `main` locally. If `main` is broken, the routine will likely fail at verification time.
6. **Standard configuration values reviewed** (Section 4).
7. **Prompt drafted from the template** (Section 5).
8. **Stop-and-escalate conditions present in the prompt** (Section 6).

## 4. Standard configuration values

These values apply by default unless the work materially requires deviation:

| Field | Value | Rationale |
|---|---|---|
| **Schedule** | Schedule-once at a near-future timestamp (15–30 minutes out) | Gives the operator time to verify the routine appeared correctly in the dashboard before it fires. Cron-recurring is for maintenance routines, not implementation routines. |
| **Cloud Environment** | Default Cloud Environment | Reproducible; no custom environment setup risk. |
| **Connectors** | Empty | Routines doing code-only work do not need MCP server connectors. Adding connectors increases setup risk and broadens the credential surface. Reserve connector use for routines that have been rehearsed locally first. |
| **Auto-fix pull requests** | OFF | Favors first-run observation over automation. Auto-fix would replay routines on test failures without operator review of the original failure mode. |
| **Allow unrestricted git push** | OFF | Defense-in-depth on `main`. The prompt prohibits push-to-main; this is the platform-level enforcement. |

### 4.1 Note on `mcp_connections` request-vs-response shape

Sending `mcp_connections: []` in the `RemoteTrigger create` request body produces a response that lists the user's globally-enabled connectors (for example, Hugging Face, Slack) with `permitted_tools: []`. The connectors are listed in the response but the routine cannot call them at runtime because `permitted_tools` is empty. This is functionally identical to "no MCP at runtime" — the asymmetry is in the request-versus-response shape, not in the routine's runtime capability. Observed during the DX testing implementation routine submission on 2026-05-11.

## 5. Prompt template

A routine prompt is self-contained and addresses an LLM agent operating without conversation history. The template:

```
You are implementing the work described in the design specification at `<path/to/design.md>`. Follow that specification precisely. This prompt configures your runtime constraints.

## Bypass permissions

bypassPermissions: yes — you are operating in a cloud routine environment with appropriate sandboxing. Run shell commands, edit files, run tests, and commit, push, and open pull requests without per-action confirmation.

## Scope

<one-paragraph summary of the work; cite the issue number and the design spec path>

## Branching and pull request

- Branch off `main`
- Target pull request base: `main`
- Pull request title (verbatim): `<title>`
- Pull request description: include `Closes #<N>`, summarize the work in two to three sentences, list verification steps performed, and embed this routine prompt verbatim in a collapsed `<details>` block for reproducibility

## Verification before push

Run all four commands in sequence; all four must pass before push:

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src/`
- `uv run pytest -m "not integration"`

## Stop-and-escalate conditions

Stop work and post a comment on the pull request (or open a draft pull request with a comment) under any of these conditions:

1. Test failures cannot be diagnosed and fixed in a single attempt
2. Pre-commit hook failures cannot be resolved by re-staging
3. The design specification is ambiguous on a load-bearing decision
4. The work requires a new project dependency

Do NOT:

- Push to `main` directly
- Skip pre-commit hooks (`--no-verify`, `--no-gpg-sign`)
- Squash-merge the pull request (the operator merges)
- Modify files outside the spec's stated scope
- Run integration tests (they require Jama OAuth which is not configured in the routine environment)
```

Replace `<...>` placeholders with concrete values per submission.

## 6. Stop-and-escalate condition library

Use these as a starting library. The four canonical conditions apply to every routine; additional cases apply when relevant.

**Canonical (include in every routine):**

1. **Test failures unfixable in one attempt** — protects against compounding bad diffs.
2. **Pre-commit failures** — gitleaks, validate-docs-placement, or ruff and mypy errors that re-staging does not resolve.
3. **Specification ambiguity** — when the spec does not dictate a load-bearing decision.
4. **New dependency needed** — adding to `pyproject.toml` requires human judgment on supply-chain risk.

**Optional (add when relevant):**

5. **MCP tool surface change requires regeneration** — if the routine modifies a tool's signature in a way that affects downstream agentic callers.
6. **Test fixture data conflict with Sandbox state** — relevant when integration tests assume specific Sandbox state.
7. **External service unavailability** — if Jamacloud, GitHub, or PyPI returns persistent 5xx responses during the run.

## 7. Monitoring conventions

After submission:

- **Primary monitor: GitHub.** Watch for the working branch to appear, then for the pull request. Watch CI checks (Lint, Mypy strict, Test, Dependency Review, codecov, Docker build).
- **Secondary monitor: `claude.ai/code` run history.** The routine's transcript is here. Useful for diagnosing escalations.
- **Do not poll the Trigger API for status.** The Trigger API surfaces routine configuration, not progress. GitHub is the source of truth.
- **Routine escalations** appear as pull request comments (or as a draft pull request with a comment if the routine never pushed to a non-draft state). Reply with operator decisions; the routine does not auto-resume on its own — a follow-up Session is the typical resolution path.

## 8. RemoteTrigger API submission

For routines submitted via the `RemoteTrigger` tool rather than via the `claude.ai/code` UI, the API body shape follows the observed pattern from the MVP build routine submission on 2026-05-10. Verify against current API documentation if anomalies appear during submission.

The API returns a trigger ID and a routine URL. Both are recorded in the next `MEMORY.md` "Recent decisions" row for downstream reference.

## 9. Branch and pull request conventions specific to routine-driven work

- **Branch name** is auto-generated by the platform on Trigger fire. The prompt's branch directive is ignored on the initial Trigger fire; ad-hoc Sessions on the resulting branch do honor directives.
- **Pull request title** is controlled by the prompt. Follow Conventional Commits — `feat:`, `fix:`, `docs:`, etc.
- **Pull request description body** should include the full routine prompt in a collapsed `<details>` block for reproducibility. This makes the pull request a complete record of what was asked of the routine.
- **Squash-merge** to `main` after CI is green. The operator performs the merge; routines do not self-merge.

## 10. Routine exemplars in this repository

Reference these as concrete examples of routine submissions:

- **MVP build routine (2026-05-10):** first routine in this project. Submitted via the `claude.ai/code` UI. Produced PR #14, squash-merged as commit `589fbac`. See `MEMORY.md` "Recent decisions" 2026-05-10 entries and the knowledge graph entity *Cloud Routine Configuration Pattern (Jama MCP Server)*.
- **DX testing routine (2026-05-11):** this runbook's first cited use. Submitted via the `RemoteTrigger` API. Implements the truncation regex fix plus Path A deep-link description population in a single bundled pull request. See [`docs/superpowers/specs/2026-05-11-jama-mvp-dx-testing-design.md`](../superpowers/specs/2026-05-11-jama-mvp-dx-testing-design.md).

## 11. Maintenance

This runbook is project-scoped and version-controlled. Revise it when:

- A new operational pattern is discovered (for example, a new failure mode worth adding to Section 6).
- Configuration defaults change (for example, when the platform releases new routine configuration options).
- A routine exemplar's link rots or the exemplar becomes obsolete.

Routine-pattern findings of broader applicability across projects belong in the user's knowledge graph (under the *Cloud Routine Configuration Pattern* entity), not in this project-scoped runbook.

---

*End of runbook.*
