# Review Command

Review the code: $ARGUMENTS

## Instructions

If a `code-reviewer` agent is available, delegate to it. Otherwise, perform the review inline.

If no specific files are mentioned, review recently modified files:

```bash
git diff --name-only HEAD~1
```

## Review scope

1. **Code Quality**
   - Type hints (ruff `ANN` rules).
   - Google-style docstrings (ruff `D` rules).
   - Error handling matches the project's two-layer policy.
   - Code organization aligns with module responsibilities in `CLAUDE.md`.

2. **MCP patterns**
   - Tool definitions use `@mcp.tool()` decorators with full type annotations.
   - Tools retrieve dependencies via `lifespan_context`, not module-level globals.
   - Tools shape responses for AI consumption (trimmed fields, structured "not found").

3. **Jama client patterns**
   - Operations are async methods on `JamaClient`.
   - Errors mapped to typed `Jama*Error` exceptions.
   - Retry policy applied only where specified.
   - Pydantic models with `extra="allow"` for forward compatibility.

4. **Security**
   - No credentials in code.
   - No injection vulnerabilities.
   - Logging redacts secrets.
   - Token cache values never logged.

5. **Testing**
   - Unit tests use `respx` for HTTP mocking.
   - Integration tests are gated by `pytest -m integration`.
   - Test names describe behavior, not implementation.

## Output format

```markdown
## Code Review: [file/feature]

### Assessment: [APPROVED / NEEDS CHANGES]

### Issues Found

| Severity | Location | Issue | Fix |
|----------|----------|-------|-----|
| Critical | file:line | description | fix |

### Recommendations

- [Optional improvements.]
```
