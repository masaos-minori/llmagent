## Goal

Remove the `/shell_run` direct POST execution route from `shell_server.py`; keep `/health`, `/v1/tools`, `/v1/call_tool`. (`REQ-002`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `/shell_run` calls `_service` directly and bypasses dispatch/idempotency/dedup/audit; removing it removes only the HTTP surface, not tool availability.
- `ShellRunRequest`/`ShellRunResponse` live in `shell/shell_models.py` and are consumed by `shell_service.py`, so they stay.
- No external deploy/ops/admin/CI/integration caller posts to `/shell_run` (`AC-6`).

## Design decisions
- Delete the `@app.post("/shell_run")` decorator and its handler together; keep `/health`, `/v1/tools`, `/v1/call_tool` untouched.

## Alternatives considered
- Keeping the route behind the dispatcher: out of scope — this Plan removes the parallel execution contract.

## Implementation
### Target file
`scripts/mcp_servers/shell/shell_server.py`

### Procedure
1. Delete the `/shell_run` direct POST execution-route handler and registration at line 143 (`@app.post("/shell_run", response_model=ShellRunResponse)` + handler).
2. Keep `/health` (line 162), `/v1/tools` (line 192), `/v1/call_tool` (line 210) unchanged.
3. Leave `ShellRunRequest`/`ShellRunResponse` imports if `shell_service.py` still needs them (it does); remove only if unused after step 1.

### Method
`grep -n "@app.post" scripts/mcp_servers/shell/shell_server.py`; delete the `/shell_run` decorator + handler; confirm no `@app.post` execution route remains.

### Details
The handler calls `_service.run_command(req)` directly, never touching `_dispatch_*`, the idempotency/dedup path, or `_emit_call_tool_audit`. Availability is preserved via `/v1/call_tool`.

## Compatibility considerations
Breaking HTTP-surface removal; no backward-compat shim (`tools/check_compat_shims.py`).

## Security considerations
Side-effecting calls now go through the shared audit path.

## Rollback considerations
Revert the commit.

## Validation plan
- Route-inventory test for the shell app asserts no execution route remains and `/v1/call_tool` works (`AC-1`, `AC-5`).
- `rg` over deploy/ops/admin/.github/workflows/tests/integration finds no external caller (`AC-6`).

## Completion criteria
- No `@app.post` execution route remains; only `/health`, `/v1/tools`, `/v1/call_tool` remain.
- Shell tool still dispatches via `/v1/call_tool`.

### Companion test files
- `tests/mcp_servers/shell/test_shell_server_endpoints.py`
  - Procedure: remove the three tests that post to the removed `/shell_run` route (`test_success_returns_run_result` line 73, `test_authorization_error_maps_to_403` line 86, `test_validation_error_maps_to_422` line 94); keep the `/v1/call_tool` tests.
  - Validation: targeted pytest on the shell server-endpoint suite passes; no reference to `/shell_run` remains.

## Out of Scope
- `/v1/call_tool` behavior changes; idempotency-key enforcement; route-specific model deletion.

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
- **Requirement ID**: `REQ-002` — remove the direct POST execution route from the shell server
- **Source issue**: `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-045455_mcproute001_remove-direct-mcp-routes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084338
- **Related target files**: `scripts/mcp_servers/shell/shell_server.py`, `tests/mcp_servers/shell/test_shell_server_endpoints.py`
