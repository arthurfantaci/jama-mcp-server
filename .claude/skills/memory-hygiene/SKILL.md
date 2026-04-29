---
name: memory-hygiene
description: Audit and update Claude memory files after PRs, milestones, or architectural changes. Use after merging PRs, deleting files, or changing architecture.
allowed-tools: Read, Edit, Write, Glob, Grep
---

# Memory Hygiene

Audit and update Claude's memory files to prevent stale context across sessions.

## Memory file locations

```text
~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/
├── CLAUDE.md        # Author's private session instructions (~150 lines max)
└── memory/
    └── MEMORY.md    # Accumulated session learnings (~100 lines max)
```

```text
<repo-root>/
├── CLAUDE.md        # Project conventions and pointers (~150 lines max)
└── MEMORY.md        # Working state: phase, branch, current task (~100 lines max)
```

## Audit checklist

### 1. Check for stale file references

Extract paths mentioned in memory files and verify each still exists:

```bash
grep -oE '[a-zA-Z_/]+\.(py|md|toml|yml|yaml|json|sh)' CLAUDE.md MEMORY.md
```

Remove references to deleted files. Update paths that have moved.

### 2. Verify architecture sections

Compare the architecture description in `CLAUDE.md` against the actual layout:

```bash
ls -la src/jama_client/
ls -la src/jama_mcp_server/
```

Update the architecture section if module structure has changed.

### 3. Update recent decisions

In `MEMORY.md`, keep only the last 5–10 significant decisions or PRs. Remove older entries.

### 4. Check line counts

- `CLAUDE.md` should be at most ~150 lines.
- `MEMORY.md` should be at most ~100 lines.

```bash
wc -l CLAUDE.md MEMORY.md
wc -l ~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/CLAUDE.md
wc -l ~/.claude/projects/-Users-arthurfantaci-jama-mcp-server/memory/MEMORY.md
```

If over limit, consolidate or archive content.

### 5. Verify patterns are still valid

Review any "Patterns" or "Gotchas" sections. Remove patterns that have been refactored away. Update patterns that have evolved.

### 6. Verify the phase pointer

`MEMORY.md` should accurately reflect:

- The currently active phase (0, 1, 2, 3, or post-3).
- The current working branch.
- The next planned task or PR.

If the phase has just transitioned, run the Phase Handoff Protocol from the author's global `~/.claude/CLAUDE.md`.

## When to run this skill

- After merging a PR that changes architecture, conventions, or core file paths.
- After completing a development phase.
- After deleting modules.
- When session context feels stale or Claude makes outdated suggestions.
- Before approaching memory auto-compaction.
- Monthly hygiene check.

## Output

After running, report:

1. Files audited.
2. Stale references removed.
3. Sections updated.
4. Current line counts versus caps.
5. Any flagged content that may belong in `docs/internal/`.
