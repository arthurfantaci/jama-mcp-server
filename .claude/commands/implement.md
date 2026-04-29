# Implement Command

Implement the feature: $ARGUMENTS

## Instructions

1. Follow Test-Driven Development (TDD):
   - Write failing test first.
   - Implement minimum code to pass.
   - Refactor while keeping tests green.

2. Follow project conventions documented in `CLAUDE.md` and the relevant spec under `docs/superpowers/specs/`.

3. Apply relevant skills:
   - `fastmcp-patterns` for MCP tool definitions.
   - `claude-api` if Anthropic SDK code is involved.

4. After each file, verify:

   ```bash
   uv run ruff check [file]
   uv run mypy [file]
   uv run pytest [test_file]
   ```

## Workflow

```text
write test → run test (fails) → implement → run test (passes) → refactor → commit
```

## Verification checklist

Before marking complete:

- [ ] All new code has type hints (enforced by ruff `ANN` rules).
- [ ] All public functions, classes, and methods have Google-style docstrings (enforced by ruff `D` rules).
- [ ] Tests cover happy path and edge cases.
- [ ] `uv run ruff check src/` passes.
- [ ] `uv run mypy src/` passes.
- [ ] `uv run pytest -m "not integration"` passes.
- [ ] No credentials or secrets committed.
- [ ] No debug `print` statements or commented-out code.

## Output

After implementation, provide:

1. Summary of changes.
2. Test results.
3. Follow-up items, if any.
