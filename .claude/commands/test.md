# Test Command

Write tests for: $ARGUMENTS

## Instructions

1. Create pytest tests following the AAA pattern:
   - **Arrange:** set up test data and mocks.
   - **Act:** call the function under test.
   - **Assert:** verify expected outcomes.

2. Test file location:
   - Unit tests: `tests/unit/<package>/test_<module>.py`.
   - Integration tests: `tests/integration/test_<feature>.py` with `@pytest.mark.integration`.
   - Protocol tests: `tests/unit/jama_mcp_server/test_protocol.py`.

3. Use shared fixtures from `tests/conftest.py`.

4. Mock external dependencies:
   - HTTP calls: `respx` (mocks `httpx.AsyncClient`).
   - `JamaClient` (in MCP tool tests): inject via `lifespan` context.

## Test categories

### Unit tests

```python
async def test_function_happy_path(respx_mock):
    respx_mock.get("https://example.com/api/x").respond(200, json={...})
    result = await function(input)
    assert result == expected


async def test_function_handles_404(respx_mock):
    respx_mock.get("https://example.com/api/x").respond(404)
    with pytest.raises(JamaNotFoundError):
        await function(input)
```

### Integration tests

```python
@pytest.mark.integration
async def test_real_jama_whoami(jama_client):
    user = await jama_client.get_current_user()
    assert user.id > 0
```

## Coverage targets

- `jama_client`: at least 80 percent line coverage.
- `jama_mcp_server`: every error class triggered at least once.

Run with:

```bash
uv run pytest -m "not integration" --cov=src --cov-report=term-missing
```

## Output

After writing tests:

1. List test functions created.
2. Run tests; show results.
3. Show coverage delta if applicable.
