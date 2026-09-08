## Goal

Add a cross-server permission test for the new fail-closed behavior when `own_config_file` is falsy (REQ-003). The test verifies that Config Isolation restriction works correctly across MCP server boundaries.

## Scope

Modify exactly one file: `tests/agent/test_config_permission_cross_server.py`. Add a new test for the falsy `own_config_file` fail-closed path.

## Assumptions

- The existing test patterns in this file use `tmp_path` fixture for temporary config files.
- The `MCPServer` class is importable from `mcp_servers.server`.
- The `ConfigPermissionError` exception is importable from `shared.config_errors`.
- **CORRECTED**: `MCPServer` has NO `__init__` parameters — `http_host`, `http_port`, `own_config_file` are class attributes. A minimal subclass must be created to override them.
- **CORRECTED**: `MCPServer.run_http()` is a **synchronous** method (not async); `asyncio.run()` is unnecessary.

## Design decisions

- Follow the existing test pattern in this file (e.g., `test_cross_server_config_load_raises_config_permission_error`).
- Use `pytest.raises` context manager to assert the expected exception.
- Keep the test focused on the cross-server permission boundary aspect.

## Alternatives considered

- Creating a new integration test with multiple MCP servers: rejected because the existing file's pattern uses isolated tmp_path fixtures which are sufficient for this unit test.
- Using a different exception type: rejected because `ConfigPermissionError` was chosen per REQ-003's design decision.

## Implementation
### Target file
`tests/agent/test_config_permission_cross_server.py`

### Procedure
Add a new test method asserting cross-server permission enforcement for the falsy `own_config_file` fail-closed path.

### Method
1. Open `tests/agent/test_config_permission_cross_server.py`.
2. At the end of the file, add a new test method:
```python
def test_falsy_own_config_file_blocks_cross_server_access(tmp_path) -> None:
    """Cross-server permission test for new fail-closed behavior (REQ-003).
    
    When an MCP server starts with a falsy own_config_file, it should raise
    ConfigPermissionError rather than running unrestricted, preventing
    cross-server Config Isolation bypass.
    """
    from mcp_servers.server import MCPServer
    from shared.config_errors import ConfigPermissionError

    # MCPServer has no __init__ args; use a minimal subclass to override class attrs
    class _TestServer(MCPServer):
        http_host = "127.0.0.1"
        http_port = 8081
        own_config_file = ""  # falsy value
        app_module = "test:test"
        mcp_tools = []

    server = _TestServer()

    # Should raise ConfigPermissionError instead of running unrestricted
    # run_http() is synchronous (not async)
    with pytest.raises(ConfigPermissionError):
        server.run_http()
```

### Details
1. Read the existing test patterns in the file (e.g., `test_cross_server_config_load_raises_config_permission_error`).
2. Use a minimal subclass of `MCPServer` to override class attributes (`http_host`, `http_port`, `own_config_file`, `app_module`, `mcp_tools`).
3. `run_http()` is a **synchronous** method — no `asyncio.run()` needed.
4. Run the test locally before committing: `uv run pytest tests/agent/test_config_permission_cross_server.py::test_falsy_own_config_file_blocks_cross_server_access -xvs`.

## Compatibility considerations

- This adds new tests only; no existing behavior changes.
- The test depends on `MCPServer` being importable from `mcp_servers.server`.

## Security considerations

This test validates a security-relevant behavior: Config Isolation must never be silently bypassed by a falsy `own_config_file`, even in cross-server scenarios where one process might try to access another's restricted resources.

## Rollback considerations

Reverting this change means removing the new test method. No operational impact since this is a test-only change.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_config_permission_cross_server.py` | Unit: verify cross-server permission enforcement | `pytest -xvs tests/agent/test_config_permission_cross_server.py::test_falsy_own_config_file_blocks_cross_server_access` | Test passes |

## Completion criteria

- [ ] New test asserts falsy `own_config_file` raises `ConfigPermissionError` in cross-server context
- [ ] Test uses `asyncio.run()` to execute the async `run_http()` method
- [ ] Test passes: `uv run pytest tests/agent/test_config_permission_cross_server.py -q`

## Out of scope

- Modifying source code files.
- Adding tests for other requirements (covered by separate procedure documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add cross-server permission test for fail-closed behavior | Completed | — | — | |
| 2 | Run the validation sequence (rules/toolchain.md) | Completed | — | — | ruff format/check passed; all 5 tests pass |

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
- **Related target files**: tests/agent/test_config_permission_cross_server.py
