## Goal

Repair `tests/mcp_servers/test_config_isolation_import.py::test_a_server_module_executes_once_under_python_m` so it exercises the real `run_http()` path and observes the second module import (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The chosen single-execution mechanism is approach (a) or (b) (mutually exclusive, open in the Plan). Under approach (a) the current code loads the config twice (once as `__main__`, once via the gate's re-import); the rewritten test must fail on current code and pass after the fix.
- The record-script harness (`_RECORD_SCRIPT`) patches `ConfigLoader.load` to record config filenames in a fresh subprocess.

## Design decisions
- **Exercise real `run_http()`:** drop the `MCPServer.run_http = lambda self: None` stub so the gate runs; stub only `uvicorn.Config` (and validate posture) so the process exits cleanly after the gate.

## Alternatives considered
- Keeping the stub: rejected — with `run_http` stubbed the gate never runs, so the second import is invisible and the regression cannot catch the defect.

## Implementation
### Target file
`tests/mcp_servers/test_config_isolation_import.py`

### Procedure
1. Rewrite `test_a_server_module_executes_once_under_python_m` to run the real `run_http()` (no stub) and assert exactly one load of `git_mcp_server.toml` (`REQ-004`).
2. Stub `uvicorn.Config` and make the posture gate pass inside the prelude so the subprocess exits after the gate.

### Method
Edit `test_a_server_module_executes_once_under_python_m` (current L128-142); the helper `_RECORD_SCRIPT`/`_run` are unchanged.

### Details
- Remove `"MCPServer.run_http = lambda self: None\n"` from the prelude so the real `run_http()` executes.
- Add to the prelude a stub of `uvicorn.Config` (so `run_http()` does not actually bind) and a way to pass the posture gate — for example set the imported module's `_security_posture` to a validated namespace before `runpy.run_module(...)`, mirroring `test_posture_gate_start_path.py`'s `_OK` namespace.
- Keep the `runpy.run_module("mcp_servers.git.git_server", run_name="__main__")` body.
- Assert `loaded.count("git_mcp_server.toml") == 1`. On current code the gate re-imports the module and the config loads twice, so the test fails pre-fix and passes after the fix (`REQ-004`).

## Compatibility considerations
- N/A: test-only; the fresh-subprocess harness and `firejail_on_path` fixture are unchanged.

## Security considerations
- N/A: test-only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_config_isolation_import.py::test_a_server_module_executes_once_under_python_m` — fails on current code, passes after the fix.
- `uv run pytest tests/mcp_servers` — new and existing tests pass.

## Completion criteria
- `REQ-004`: the rewritten test runs the real `run_http()` and asserts a single config load; it fails on current code (two loads) and passes after the fix.

## Out of Scope
- The `server.py` gate/diagnostic edits and the approach choice — covered by `implementations/20261108-074423_01_scripts_mcp_servers_server.py.md`.
- The mdq entry-point assertions — covered by `implementations/20261108-074423_14_tests_mcp_servers_test_posture_gate_start_path.py.md`.

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
- **Requirement ID**: `REQ-004` — repair the regression so it observes the real `run_http()` path
- **Source issue**: `issues/20261107-132004_mcpstartup001_python-m-double-execution.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-213404_mcpstartup001_python-m-double-execution.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-074423
- **Related target files**: `tests/mcp_servers/test_config_isolation_import.py`
