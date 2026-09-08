## Goal

Add a new unit test for the falsy `own_config_file` fail-closed path (REQ-003). The test asserts that `MCPServer.run_http()` raises an error when `own_config_file` is falsy instead of silently skipping Config Isolation restriction.

## Scope

Modify exactly one file: `tests/agent/test_startup.py`. Add a new test method for the falsy `own_config_file` scenario.

## Assumptions

- The `MCPServer` class is importable from `mcp_servers.server`.
- The test can use `pytest` fixtures and `unittest.mock` for mocking.
- The existing test patterns in this file (e.g., `TestStartupOrchestratorStartServers`) use async test methods — follow the same pattern.
- **CORRECTED**: `MCPServer` does NOT accept constructor arguments (`http_host`, `http_port`, `own_config_file`). These are class attributes. A minimal subclass must be created to override them.

## Design decisions

- Add a new async test method under an existing test class or create a new class for this specific scenario.
- Mock the uvicorn server startup to avoid actually starting a server during the test.
- Assert that `ConfigPermissionError` is raised (matching the exception type chosen in REQ-003's design decision).

## Alternatives considered

- Creating a new integration test that starts a real MCP server: rejected because it requires network setup and is slower; mocking is sufficient for this unit test.
- Using a different exception type: rejected because `ConfigPermissionError` was chosen per REQ-003's design decision.

## Implementation
### Target file
`tests/agent/test_startup.py`

### Procedure
Add a new test method asserting that falsy `own_config_file` raises `ConfigPermissionError`.

### Method
1. Open `tests/agent/test_startup.py`.
2. At the end of the file, add a new test class:
```python
class TestMCPServerFalsyOwnConfigFile:
    """Tests for MCPServer.fail-closed when own_config_file is falsy."""

    @pytest.mark.asyncio
    async def test_falsy_own_config_file_raises(self) -> None:
        """Assert that MCPServer.run_http() raises when own_config_file is falsy."""
        from mcp_servers.server import MCPServer
        from shared.config_errors import ConfigPermissionError

        # MCPServer has no __init__ args; use a minimal subclass to override class attrs
        class _TestServer(MCPServer):
            http_host = "127.0.0.1"
            http_port = 8080
            own_config_file = ""  # falsy value
            mcp_tools = []

        server = _TestServer()

        # run_http() is synchronous (not async); raises ConfigPermissionError
        with pytest.raises(ConfigPermissionError):
            server.run_http()
```

### Details
1. Read the existing test patterns in the file (e.g., `TestStartupOrchestratorStartServers.test_production_profile_raises_on_start_failure`).
2. `MCPServer` has NO `__init__` parameters — `http_host`, `http_port`, `own_config_file` are class attributes. Use a minimal subclass to override them.
3. Verify that `ConfigPermissionError` is importable from `shared.config_errors`.
4. `MCPServer.run_http()` is a **synchronous** method (not async).
5. Run the test locally before committing: `uv run pytest tests/agent/test_startup.py::TestMCPServerFalsyOwnConfigFile -xvs`.

## Compatibility considerations

- This adds new tests only; no existing behavior changes.
- The test depends on `MCPServer` being importable from `mcp_servers.server`.

## Security considerations

This test validates a security-relevant behavior: Config Isolation must never be silently bypassed by a falsy `own_config_file`.

## Rollback considerations

Reverting this change means removing the new test class. No operational impact since this is a test-only change.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_startup.py` | Unit: verify falsy own_config_file raises | `pytest -xvs tests/agent/test_startup.py::TestMCPServerFalsyOwnConfigFile` | Test passes |

## Completion criteria

- [ ] New test asserts falsy `own_config_file` raises `ConfigPermissionError` at startup
- [ ] Test uses mock to avoid actual uvicorn server startup
- [ ] Test passes: `uv run pytest tests/agent/test_startup.py -q`

## Out of scope

- Modifying source code files.
- Adding tests for other requirements (covered by separate procedure documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add test for falsy own_config_file fail-closed path | Completed | — | — | |
| 2 | Run the validation sequence (rules/toolchain.md) | Completed | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/done/20260902-101452_h02_config_loader_fail_closed_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-203653_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-09-07T23:18:04Z
- **Related target files**: tests/agent/test_startup.py
