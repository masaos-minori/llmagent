## Goal

Extend `tests/mcp_servers/test_posture_gate_start_path.py` to assert single execution through the real `run_http()` path (`REQ-001`/`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The Plan's open single-execution mechanism is approach (a) or (b) (mutually exclusive).
- Existing tests in this file patch `MCPServer.run_http`; the extension must use the REAL `run_http()` to observe the gate's re-import.

## Design decisions
- **New parametrized test:** for each server, run `runpy.run_module(<module>, run_name="__main__")` with real `run_http()` (uvicorn.Config stubbed, posture validated) and assert exactly one config load.

## Alternatives considered
- Extending the patched-run_http tests: rejected — a patched `run_http` never reaches the gate, so it cannot observe the double import.

## Implementation
### Target file
`tests/mcp_servers/test_posture_gate_start_path.py`

### Procedure
1. Add a parametrized test over `_SERVERS` that runs the real `run_http()` and asserts a single config load per module (`REQ-001`/`REQ-004`).
2. Keep the existing patched tests unchanged.

### Method
Append a new test function; reuse the `_OK`/`_FAILED` posture namespaces already defined at the top of the file.

### Details
- For each `(module_name, class_name)` in `_SERVERS`, import the module, set its `_security_posture` to `_OK`, stub `uvicorn.Config` so binding is skipped, run `runpy.run_module(module_name, run_name="__main__")`, and assert the served module's config loads exactly once.
- Drive the config-load recording by patching `ConfigLoader.load` within the test and counting calls, mirroring the approach in `test_config_isolation_import.py`.
- On current code the gate re-imports the module and the config loads twice, so the new test fails pre-fix and passes after the fix (`REQ-004`).

## Compatibility considerations
- N/A: test-only; existing tests are untouched.

## Security considerations
- N/A: test-only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_posture_gate_start_path.py` — new and existing tests pass.
- `uv run pytest tests/mcp_servers` — new and existing tests pass.

## Completion criteria
- `REQ-001`/`REQ-004`: the new test exercises the real `run_http()` and asserts a single config load; it fails on current code and passes after the fix.

## Out of Scope
- The `server.py` gate/diagnostic edits and the approach choice — covered by `implementations/20261108-074423_01_scripts_mcp_servers_server.py.md`.
- The config-isolation regression rewrite — covered by `implementations/20261108-074423_13_tests_mcp_servers_test_config_isolation_import.py.md`.

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
- **Requirement ID**: `REQ-001`/`REQ-004` — single execution through the real `run_http()` path
- **Source issue**: `issues/20261107-132004_mcpstartup001_python-m-double-execution.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-213404_mcpstartup001_python-m-double-execution.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-074423
- **Related target files**: `tests/mcp_servers/test_posture_gate_start_path.py`
