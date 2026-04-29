# Memory Audit Command

Run the memory-hygiene skill against the project's memory files.

## Instructions

1. Invoke the `memory-hygiene` skill defined at `.claude/skills/memory-hygiene/SKILL.md`.

2. Apply the audit checklist:
   - Check for stale file references in `CLAUDE.md` and `MEMORY.md`.
   - Verify architecture sections match the actual codebase.
   - Update recent decisions/PRs (keep last 5–10).
   - Check line counts against caps (CLAUDE.md ~150, MEMORY.md ~100).
   - Verify patterns are still valid.
   - Verify phase pointer accuracy.

3. Audit BOTH memory tiers:
   - Public (in repo): `CLAUDE.md`, `MEMORY.md`.
   - Private (per-user): `~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/CLAUDE.md` and `~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/memory/MEMORY.md`.

4. Report findings per the skill's "Output" section.

## When to use

Trigger this command after:

- Merging a PR that changes architecture, conventions, or core file paths.
- Completing a development phase.
- Deleting modules or significant code.
- Detecting stale Claude suggestions.
- Approaching memory auto-compaction.

## Related

- `.claude/skills/memory-hygiene/SKILL.md` — the underlying audit checklist.
- `~/.claude/CLAUDE.md` — the author's global Knowledge Graph Memory Protocol and Phase Handoff Protocol.
