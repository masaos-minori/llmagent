## Goal

Update ~20 `HttpTransport(...)` construction sites in `tests/shared/test_tool_executor.py` that currently omit `cfg` to carry explicit configuration, preserving their existing non-auth assertions.

## Scope

- Modify `tests/shared/test_tool_executor.py`: add explicit `cfg` argument to all `HttpTransport` constructions that currently omit it (~20 sites), using a minimal stand-in config object.

## Assumptions

- Test constructions that omit `cfg` are fixtures for non-auth behaviors (retries, errors, redaction, x-request-id) and can carry a minimal explicit config without changing what they assert.
- The stand-in config needs only `auth_token=""` (empty token, not None) to satisfy the fail-loud guard while preserving the silent-off behavior for these specific tests.

## Design decisions

- Use a minimal `_FakeConfig(auth_token="")` stand-in instead of importing the real `McpServerConfig`. This avoids pulling in production dependencies into test fixtures and keeps the change localized.
- Set `auth_token=""` (empty string, not None) — this satisfies the fail-loud guard (cfg is not None) while preserving the original silent-off behavior for these non-auth test cases.

## Alternatives considered

- Import and use `McpServerConfig` directly: rejected because it pulls in production dependencies and adds unnecessary complexity to test fixtures.
- Use a mock `MagicMock(spec=McpServerConfig)` with `auth_token=""`: rejected because it obscures the intent (explicit empty token vs. missing config) and could mask future changes to the config class.

## Implementation
### Target file
`tests/shared/test_tool_executor.py`

### Procedure
Add explicit `cfg=_FakeConfig(auth_token="")` to all `HttpTransport` constructions that currently omit the `cfg` argument. Each test's existing assertions remain unchanged.

### Method
1. Define a minimal `_FakeConfig` class near the top of the file (or reuse an existing one if available).
2. For each `HttpTransport(mock_http, base_url, server_key)` call, add `cfg=_FakeConfig(auth_token="")` as the fourth positional argument.

### Details
**Change — Add `_FakeConfig` helper:**

```python
class _FakeConfig:
    """Minimal config stub for test HttpTransport constructions."""
    def __init__(self, auth_token: str = "") -> None:
        self.auth_token = auth_token
```

**Change — Update HttpTransport constructions (example):**

Before:
```python
transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "test")
```

After:
```python
transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "test", cfg=_FakeConfig(auth_token=""))
```

Apply this pattern to all ~20 sites identified by `rg -c 'server_key='` in the file.

## Compatibility considerations

- No public API surface is affected; only test fixtures change.
- The `_FakeConfig` class is private (prefixed with `_`) and scoped to this test file.

## Security considerations

- Using `auth_token=""` on the stand-in config preserves the original silent-off behavior for these specific non-auth test cases. This is intentional — these tests exercise retry/error/redaction paths, not authentication.

## Rollback considerations

- Revert the `cfg` additions and remove the `_FakeConfig` class.
- If a test depends on the silent-off behavior being preserved, keep `auth_token=""` on the stand-in config.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/shared/test_tool_executor.py | Unit (behavior lock + cfg additions) | `uv run pytest tests/shared/test_tool_executor.py -v` | Passes before and after; new fail-loud case present |
| Full suite | Regression | `uv run pytest tests/` | No new failures |

## Completion criteria

- [ ] All ~20 `HttpTransport` constructions in `tests/shared/test_tool_executor.py` carry an explicit `cfg` argument.
- [ ] The `_FakeConfig` class provides `auth_token=""` to satisfy the fail-loud guard.
- [ ] All existing test assertions pass (behavior lock).
- [ ] `ruff format` and `ruff check` pass cleanly on the modified file.

## Out of scope

- Changing any test assertions beyond adding the `cfg` argument.
- Modifying `tests/shared/test_tool_executor_routing.py` (separate procedure document).
- Adding new tests for the fail-loud contract (covered in REQ-001 procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — |  |
| 2 | Add or update tests per Validation plan | Completed | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261004-065813_mcp004_httptransport-silently-sends-unauthenticated-calls-when-constructed-with-cfg-none.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-094856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-072753
- **Related target files**: tests/shared/test_tool_executor.py