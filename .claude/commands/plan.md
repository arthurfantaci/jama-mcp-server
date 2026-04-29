# Plan Command

Create a comprehensive implementation plan for: $ARGUMENTS

## Instructions

1. **Do not write any code yet** — this is planning only.
2. Explore the codebase to understand current structure and conventions.
3. Read the relevant design specification under `docs/superpowers/specs/`.
4. Identify all files that need to be created or modified, with exact paths.
5. List implementation steps in logical order.
6. Define success criteria and verification commands.
7. Identify potential risks or blockers.
8. **Wait for approval before implementing.**

## Output format

```markdown
## Implementation Plan: [Feature Name]

### Overview
[Brief description.]

### Files to Create
- `exact/path/to/new_file.py` — purpose

### Files to Modify
- `exact/path/to/existing.py:line-range` — what changes

### Implementation Steps
1. [Step with details and verification.]

### Dependencies
- [Any new packages needed.]

### Success Criteria
- [ ] [Testable criterion.]

### Risks
- [Potential issue and mitigation.]
```

## Important

- Be thorough; do not gloss over file paths or content.
- Consider edge cases.
- Specify the testing strategy.
- Do not start implementing until the plan is approved.
- For non-trivial plans, prefer the `superpowers:writing-plans` skill.
