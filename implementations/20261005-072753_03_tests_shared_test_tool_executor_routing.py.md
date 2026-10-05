## Goal

Update ~6 `HttpTransport(...)` construction sites in `tests/shared/test_tool_executor_routing.py` that currently omit `cfg` to carry explicit configuration, and rewrite `test_no_cfg_sends_empty_headers` to assert the fail-loud contract instead of the silent-off behavior.

## Scope

- Modify `tests/shared/test_tool_executor_routing.py`: add explicit `cfg` argument to all `HttpTransport` constructions that currently omit it (~6 sites), and rewrite `test_no_cfg_sends_empty_headers` to assert that `cfg=None` raises.

## Assumptions

- Test constructions that omit `cfg` are fixtures for non-auth behaviors (retries, errors, redaction, x-request-id) and can carry a minimal explicit config without changing what they assert.
- The stand-in config needs only `auth_token=""` (empty token, not None) to satisfy the fail-loud guard while preserving the silent-off behavior for these specific tests.
- The Plan undercounted no-cfg sites as "~5"; actual count is 6 (verified via `rg`).

## Design decisions

- Use a minimal `_FakeConfig(auth_token="")` stand-in instead of importing the real `McpServerConfig`. This avoids pulling in production dependencies into test fixtures and keeps the change localized.
- Set `auth_token=""` (empty string, not None) — this satisfies the fail-loud guard (cfg is not None) while preserving the silent-off behavior for these specific tests.
- Rewrite `test_no_cfg_sends_empty_headers` to assert `ValueError` is raised when `cfg=None`, replacing the old assertion that headers were empty.

## Alternatives considered

- Import and use `McpServerConfig` directly: rejected because it pulls in production dependencies and adds unnecessary complexity to test fixtures.
- Keep the original test name but change its assertion: rejected because the test name "sends_empty_headers" describes the old behavior; renaming clarifies the intent.

## Implementation
### Target file
`tests/shared/test_tool_executor_routing.py`

### Procedure
Add explicit `cfg=_FakeConfig(auth_token="")` to all `HttpTransport` constructions that currently omit the `cfg` argument (~6 sites). Rewrite `test_no_cfg_sends_empty_headers` to assert the fail-loud contract.

### Method
1. Define a minimal `_FakeConfig` class near the top of the file (or reuse an existing one if available).
2. For each `HttpTransport(mock_http, base_url, server_key)` call, add `cfg=_FakeConfig(auth_token="")` as the fourth positional argument.
3. Rewrite `test_no_cfg_sends_empty_headers` to expect a `ValueError` when `cfg=None`.

### Details
**Change 1 — Add `_FakeConfig` helper:**

```python
class _FakeConfig:
    """Minimal config stub for test HttpTransport constructions."""
    def __init__(self, auth_token: str = "") -> None:
        self.auth_token = auth_token
```

**Change 2 — Update HttpTransport constructions (example):**

Before:
```python
transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
```

After:
```python
transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc", cfg=_FakeConfig(auth_token=""))
```

Apply this pattern to all 6 sites identified by `rg 'HttpTransport('` in the file (lines 263, 278, 293, 311, 324, 334).

**Change 3 — Rewrite `test_no_cfg_sends_empty_headers`:**

Before:
```python
@pytest.mark.asyncio
async def test_no_cfg_sends_empty_headers(self) -> None:
    """Backward-compat: HttpTransport without cfg arg sends no auth header."""
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.content = b'{"result":"ok","is_error":false}'
    mock_resp.raise_for_status = MagicMock()
    mock_resp.headers = {}
    mock_http.post = AsyncMock(return_value=mock_resp)

    transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
    await transport.call("my_tool", {})

    call_kwargs = mock_http.post.call_args.kwargs
    assert call_kwargs["headers"] == {}
```

After:
```python
@pytest.mark.asyncio
async def test_no_cfg_raises_fail_loud(self) -> None:
    """Fail-loud: HttpTransport without cfg arg raises ValueError."""
    mock_http = AsyncMock(spec=httpx.AsyncClient)

    with pytest.raises(ValueError, match="HttpTransport requires a non-None"):
        HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
```

## Compatibility considerations

- No public API surface is affected; only test fixtures change.
- The `_FakeConfig` class is private (prefixed with `_`) and scoped to this test file.
- Renaming `test_no_cfg_sends_empty_headers` to `test_no_cfg_raises_fail_loud` changes the test name but preserves the same logical coverage (testing the no-cfg path).

## Security considerations

- Using `auth_token=""` on the stand-in config preserves the original silent-off behavior for these specific non-auth test cases. This is intentional — these tests exercise retry/error/redaction paths, not authentication.
- The rewritten `test_no_cfg_raises_fail_loud` explicitly verifies the security improvement (fail-loud behavior).

## Rollback considerations

- Revert the `cfg` additions and remove the `_FakeConfig` class.
- Restore the original `test_no_cfg_sends_empty_headers` test.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/shared/test_tool_executor_routing.py | Unit (behavior lock + rewrite) | `uv run pytest tests/shared/test_tool_executor_routing.py -v` | Passes; rewritten fail-loud case passes |
| Full suite | Regression | `uv run pytest tests/` | No new failures |

## Completion criteria

- [ ] All ~6 `HttpTransport` constructions in `tests/shared/test_tool_executor_routing.py` carry an explicit `cfg` argument.
- [ ] The `_FakeConfig` class provides `auth_token=""` to satisfy the fail-loud guard.
- [ ] `test_no_cfg_raises_fail_loud` asserts `ValueError` is raised when `cfg=None`.
- [ ] All existing test assertions pass (behavior lock).
- [ ] `ruff format` and `ruff check` pass cleanly on the modified file.

## Out of scope

- Changing any test assertions beyond adding the `cfg` argument.
- Modifying `tests/shared/test_tool_executor.py` (separate procedure document).
- Adding an explicit opt-out flag for deliberately unauthenticated transports (deferred follow-up).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Related target files**: tests/shared/test_tool_executor_routing.py
