## Goal
Prove the posture gate runs on every launch path: `Class().run_http()` with a FAILED posture exits 1 before binding for all ten servers, a missing gate fails closed, and the mdq `__main__` module is guarded (`REQ-006`).

## Scope
- New test module only; existing tests unchanged.

## Assumptions
- `tests/conftest.py` sets the MCP token variables and patches firejail presence at collection, so all ten server modules import in one process.
- `ConfigLoader.restrict_to` and `uvicorn.Config` can be patched so no real server starts and no process-wide restriction leaks between tests.

## Design decisions
- Use an explicit list of (module, class) pairs for the ten servers instead of `discover_servers()`: the discovery function imports every module in one process and is being changed by the config-isolation plan.
- Replace the module's `_security_posture` with a small stand-in object that has `validated = False` and an empty `checks` list.

## Alternatives considered
- Run each server in a subprocess: rejected, slower and unnecessary because the gate runs before any socket work.

## Implementation
### Target file
`tests/mcp_servers/test_posture_gate_start_path.py` (new)

### Procedure
1. Define the list of ten (module path, class name) pairs matching the `app_module` values.
2. Parametrized test: monkeypatch `<module>._security_posture` to a FAILED stand-in, patch `shared.config_loader.ConfigLoader.restrict_to` and make `uvicorn.Config` raise `AssertionError`; assert `Class().run_http()` raises `SystemExit` with code 1.
3. Test that a validated stand-in reaches `uvicorn.Config` (patched to a sentinel exception) for one server.
4. Test that a fake class with `app_module = "mcp_servers.fake_missing_gate:app"` (module injected into `sys.modules` without the function) makes `run_http()` raise `RuntimeError`.
5. Test that importing `mcp_servers.mdq.__main__` does not call `MCPServer.run_http` (patched to raise), and that `runpy.run_module("mcp_servers.mdq", run_name="__main__")` calls it exactly once.

### Method
- Use `pytest.mark.parametrize` and `monkeypatch`; restore `sys.modules` after the injected-module test.

### Details
- Reference only: `tests/mcp_servers/test_mcp_server_base.py` (`_SimpleServer` pattern and `uvicorn` patching), per-server gates in `*_server.py`.

## Compatibility considerations
- Test-only.

## Security considerations
- No secrets; tokens come from `tests/conftest.py` fake values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_posture_gate_start_path.py`, `uv run pytest tests/mcp_servers`, `uv run ruff check tests/mcp_servers`, `uv run mypy`.

## Completion criteria
- All cases pass with the gate implemented and fail without it (the FAILED-posture case reaches uvicorn on the pre-change code).

## Out of Scope
- Changes to existing test modules
- Agent-side posture tests

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test module per Implementation > Procedure (tests are this row's change) | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (launch-path tests), covering `REQ-001`, `REQ-002`, `REQ-003`
- **Source issue**: issues/20261023-114021_mcpstart002_posture-gate-bypassed-by-launchers-and-mdq-main.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-114842_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123153
- **Related target files**: tests/mcp_servers/test_posture_gate_start_path.py
