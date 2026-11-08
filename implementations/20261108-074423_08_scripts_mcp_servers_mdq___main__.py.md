## Goal

Confirm `scripts/mcp_servers/mdq/__main__.py` already routes `python -m mcp_servers.mdq` through a single canonical import and needs no `__main__` rewrite; record that any mdq double-execution is fixed by the `server.py` gate guard under approach (a).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The Plan's open single-execution mechanism is mutually exclusive: approach (a) centralized guard in `scripts/mcp_servers/server.py`, or approach (b) per-module `__main__` delegation.
- `__main__.py` already imports `MdqMCPServer` under its real module name at the top of the file.

## Design decisions
- **No rewrite needed:** the current file already delegates through a single canonical import, so approach (b) makes no change here; approach (a) fixes any residual double-import in `server.py`.

## Alternatives considered
- Rewriting the `__main__` block: rejected — it already imports under the real name; a rewrite would be cosmetic only.

## Implementation
### Target file
`scripts/mcp_servers/mdq/__main__.py`

### Procedure
1. Verify the top-of-file import resolves `MdqMCPServer` from `mcp_servers.mdq.mdq_server` (already in `sys.modules` when `run_http()`'s gate looks it up).
2. Record in the Procedure that no edit is required and why.

### Method
Read-only check of the trailing block (current lines 5-8).

### Details
Current file:
```python
from mcp_servers.mdq.mdq_server import MdqMCPServer

if __name__ == "__main__":
    MdqMCPServer().run_http()
```
Under approach (b) this is already correct — no change. Under approach (a) leave it unchanged; the `server.py` gate guard (`implementations/20261108-074423_01_scripts_mcp_servers_server.py.md`) serves the already-imported `MdqMCPServer` instance.

## Compatibility considerations
- N/A: entry-point only; no change is made.

## Security considerations
- N/A: the posture gate still runs via the imported module.

## Rollback considerations
- N/A: revert the commit; no change is made here.

## Validation plan
- `uv run pytest tests/mcp_servers/test_posture_gate_start_path.py::test_running_the_mdq_entry_module_goes_through_run_http` — passes.
- `uv run ruff check scripts/` — clean.

## Completion criteria
- Confirmed `__main__.py` delegates through a single canonical import; no edit required.

## Out of Scope
- The `server.py` gate/diagnostic edits and the approach choice — covered by `plans/20261107-213404_mcpstartup001_python-m-double-execution.md` and implemented by `implementations/20261108-074423_01_scripts_mcp_servers_server.py.md`.
- The `mdq_server.py` `__main__` block — covered by `implementations/20261108-074423_09_scripts_mcp_servers_mdq_mdq_server.py.md`.

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
- **Requirement ID**: `REQ-001` — single execution of the server module on the `python -m` / direct-run launch path
- **Source issue**: `issues/20261107-132004_mcpstartup001_python-m-double-execution.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-213404_mcpstartup001_python-m-double-execution.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-074423
- **Related target files**: `scripts/mcp_servers/mdq/__main__.py`
