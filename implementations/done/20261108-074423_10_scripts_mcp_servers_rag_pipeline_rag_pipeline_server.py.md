## Goal

Route this server's `python -m` / direct-run entry point through a single canonical import so the server module body executes exactly once and `_enforce_startup_posture_gate()` resolves the running instance (`REQ-001`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The Plan's open single-execution mechanism is mutually exclusive: approach (a) centralized guard in `scripts/mcp_servers/server.py`, or approach (b) per-module `__main__` delegation. This document covers the entry-file side of whichever is chosen.
- Under approach (a) this file needs no change — the gate reads posture from the already-imported instance; only `server.py` changes.

## Design decisions
- **Approach (b) delegation:** replace the trailing `if __name__ == "__main__":` block with a top-of-file import of `RagPipelineMCPServer` under its real module name, then instantiate once, so `run_http()`'s gate resolves the instance already present in `sys.modules`.

## Alternatives considered
- Leaving the block unchanged: rejected under approach (b) — under `python -m` the module body runs as both `__main__` and its real name, and `run_http()` re-imports it a second time.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`

### Procedure
1. Under approach (b), rewrite the entry block to delegate via a single canonical import (`REQ-001`).
2. Under approach (a), make no change here and record in the Procedure that the fix lives in `server.py`.

### Method
Edit the trailing block of the file (current last lines shown below).

### Details
Current block:
```python
if __name__ == "__main__":
    _enforce_posture_gate()
    server = RagPipelineMCPServer()
    server.run_http()
```
Under approach (b), rewrite to import `RagPipelineMCPServer` under its real name and run it once:
```python
from mcp_servers.rag_pipeline.rag_pipeline_server import RagPipelineMCPServer  # noqa: E402

if __name__ == "__main__":
    RagPipelineMCPServer().run_http()
```
Keep `_enforce_posture_gate()` reachable through the imported module so the posture gate still runs on this launch path. Under approach (a), leave this block untouched.

## Compatibility considerations
- N/A: entry-point only; exit codes and startup ordering are unchanged.

## Security considerations
- N/A: the posture gate still runs via the imported module under both approaches.

## Rollback considerations
- N/A: revert the commit; the change is entry-point delegation only.

## Validation plan
- `uv run pytest tests/mcp_servers/test_config_isolation_import.py::test_a_server_module_executes_once_under_python_m` — passes after the fix (fails on current code under approach (b)).
- `uv run pytest tests/mcp_servers` — new and existing tests pass.
- `uv run ruff check scripts/` — clean.

## Completion criteria
- `REQ-001`: under approach (b) the module body runs once via the canonical import; under approach (a) this file is unchanged and the gate serves the running instance.

## Out of Scope
- The `server.py` gate/diagnostic edits and the approach choice — covered by `plans/20261107-213404_mcpstartup001_python-m-double-execution.md` and implemented by `implementations/20261108-074423_01_scripts_mcp_servers_server.py.md`.

## Verification

- **Approach (a): no change to this entry file.** The single-execution fix lives entirely in `scripts/mcp_servers/server.py` (the gate resolves the already-running instance via `sys.modules.get(module_name)`); the eleven entry files were left untouched by design.
- **Single execution verified for this module.** `test_a_server_module_executes_once_under_python_m[mcp_servers.rag_pipeline.rag_pipeline_server]` runs the real `run_http()` and asserts `second_imports==0` (executes once) plus a single config load; passes on the fixed `server.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261108-130640 | 20261108-130640 | Approach (a): no change to this entry file; fix lives in server.py. Single execution verified (second_imports==0). See Verification section. |
| 2 | Add or update tests per Validation plan | Completed | 20261108-130640 | 20261108-130640 | Approach (a): no change to this entry file; fix lives in server.py. Single execution verified (second_imports==0). See Verification section. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261108-130640 | 20261108-130640 | Approach (a): no change to this entry file; fix lives in server.py. Single execution verified (second_imports==0). See Verification section. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261108-130640 | 20261108-130640 | Approach (a): no change to this entry file; fix lives in server.py. Single execution verified (second_imports==0). See Verification section. |

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
- **Requirement ID**: `REQ-001` — single execution of the server module on the `python -m` / direct-run launch path
- **Source issue**: `issues/20261107-132004_mcpstartup001_python-m-double-execution.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-213404_mcpstartup001_python-m-double-execution.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-074423
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
