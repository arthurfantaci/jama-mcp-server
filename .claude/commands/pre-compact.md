# Pre-Compaction Command

Prepare for memory auto-compaction by persisting any unwritten findings.

## Instructions

Execute the Pre-Compaction Protocol from the author's global `~/.claude/CLAUDE.md`:

1. **Persist unwritten findings to the Knowledge Graph.** Review the current session for:
   - Debugging insights that took significant effort.
   - Architectural decisions with rationale.
   - Cross-project patterns or gotchas.
   - User corrections (prefix observation with `Corrected YYYY-MM-DD:`).
   - Dependency relationships.

   For each, call the `memory` MCP server's `create_entities`, `add_observations`, or `create_relations` tools to write the finding into the Neo4j-backed Knowledge Graph.

2. **Update `MEMORY.md`** with the current task state:
   - Active phase.
   - Active branch.
   - Current task or in-progress work.
   - Open questions or decisions awaiting input.

3. **Verify CLAUDE.md and MEMORY.md line counts** are within caps (CLAUDE.md ~150, MEMORY.md ~100). Consolidate if over.

4. **Run `/memory-audit`** to perform the full hygiene checklist.

## Output

Report:

1. Knowledge Graph entities created or updated.
2. MEMORY.md sections updated.
3. CLAUDE.md and MEMORY.md current line counts.
4. Any pending work that should be resumed in the next session.

## Related

- `~/.claude/CLAUDE.md` — Pre-Compaction Protocol section.
- `.claude/commands/memory-audit.md` — full hygiene audit.
