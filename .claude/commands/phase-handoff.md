# Phase Handoff Command

Execute the Phase Handoff Protocol when transitioning between development phases.

## Instructions

Execute the Phase Handoff Protocol from the author's global `~/.claude/CLAUDE.md`:

1. **Merge the phase's PR** to `main`.

2. **Clean up branches** for the completed phase:

   ```bash
   git branch --merged main | grep -v 'main' | xargs -n 1 git branch -d
   git remote prune origin
   ```

3. **Verify tests pass** on `main`:

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy src/
   uv run pytest -m "not integration"
   ```

4. **Update `MEMORY.md`** to reflect:
   - The newly completed phase status.
   - The newly active phase.
   - The current working branch (likely `main` after handoff).
   - Recent decisions worth remembering.

5. **Update `CLAUDE.md`** if the completed phase introduced:
   - New conventions worth codifying.
   - New module paths worth referencing.
   - Resolved gotchas no longer needing mention.

6. **Run `/memory-audit`** to audit for stale references introduced by the phase change.

7. **Persist phase-completion observations to the Knowledge Graph** via the `memory` MCP server.

## Output

Report:

1. PR merged.
2. Branches deleted.
3. Test results.
4. MEMORY.md and CLAUDE.md updates summary.
5. Memory audit findings.
6. Knowledge Graph updates.

## Related

- `~/.claude/CLAUDE.md` — Phase Handoff Protocol section.
- `.claude/commands/memory-audit.md` — full hygiene audit.
- `.claude/commands/pre-compact.md` — sibling command for auto-compaction prep.
