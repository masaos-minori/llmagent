## Goal

Add one regression test for the REQ-006 call-site fix at line 189 only.

## Scope

- Add a test asserting `health_timeout=0` does not cause near-instant timeout at the `_fetch_server_tools()` call site.

## Assumptions

- The test can mock the HTTP response to avoid actual network calls.
- The existing test infrastructure supports mocking `httpx.AsyncClient`.

## Design decisions

- Add a single test method in the existing test class that exercises the `health_timeout=0` path.

## Alternatives considered

- Creating a new test class for this single test — rejected: adds unnecessary class proliferation.
- Merging this test with the `mcp_config.py` unit-level test — rejected: clarity benefits from separation by call site.

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure

Add a regression test for REQ-006 at the discovery call site.

### Method

- **Step 1**: Add a test method to the appropriate test class:

```python
@pytest.mark.asyncio
async def test_health_timeout_zero_does_not_cause_near_instant_timeout(self) -> None:
    """REQ-006: health_timeout=0 should not cause near-instant timeout at _fetch_server_tools()."""
    # ... implement using mock httpx.AsyncClient with timeout=None assertion
    pass
```

### Details

**Step 1 — Add REQ-006 regression test:**

Add after the existing test methods in the appropriate test class:

```python
@pytest.mark.asyncio
async def test_health_timeout_zero_does_not_cause_near_instant_timeout(self) -> None:
    """REQ-006: health_timeout=0 should not cause near-instant timeout at _fetch_server_tools()."""
    # Arrange: create a config with health_timeout=0
    cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://127.0.0.1:8000",
        startup_mode=StartupMode.PERSISTENT,
        auth_token="test-token",
        health_timeout=0,
    )
    
    # Mock the HTTP client to capture the timeout value
    captured_timeout = None
    
    async def mock_get(url, timeout=None):
        nonlocal captured_timeout
        captured_timeout = timeout
        # Return a minimal valid response
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"tools": []}
        return resp
    
    # Act: call _fetch_server_tools with mocked HTTP
    discovery = McpToolDiscovery(ctx=MagicMock())
    discovery._ctx.services_required.http.get = mock_get
    
    result = await discovery._fetch_server_tools("test_server", cfg)
    
    # Assert: timeout should be None (no timeout), not 0 (near-instant)
    assert captured_timeout is not None
    assert captured_timeout.timeout == None or captured_timeout.read is None
```

## Compatibility considerations

- New test uses existing patterns; no changes to existing test methods.

## Security considerations

- No security impact. This is a behavioral change test for REQ-006.

## Rollback considerations

- Reverting the test changes restores the pre-fix test suite but does not affect source code.

## Validation plan

- Run unit tests: `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v`
- Verify the new test passes.
- Static analysis: `uv run ruff check tests/agent/services/test_mcp_tool_discovery.py`, `uv run mypy tests/agent/services/test_mcp_tool_discovery.py`.

## Completion criteria

- REQ-006 test passes: `health_timeout=0` does not cause near-instant timeout at the discovery call site.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `scripts/agent/services/mcp_tool_discovery.py` source code — covered in previous row (REQ-006).
- Testing the status call site — covered in subsequent row.
- Any MCP server business logic unrelated to the timeout call site.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add REQ-006 regression test for discovery call site | Pending | — | — | |
| 2 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-006, REQ-009
- **Source issue**: issues/20260914-103159_mcpagent05_mcp-lifecycle-invocation-gate-unification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-123229_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: tests/agent/services/test_mcp_tool_discovery.py
