## Goal

Remove the 4 direct POST execution routes (`/write_file`, `/edit_file`, `/create_directory`, `/move_file`) from `write_server.py`; keep `/health`, `/v1/tools`, `/v1/call_tool`. (`REQ-002`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The 4 routes call `_service.*` directly and bypass dispatch/idempotency/dedup/audit; removing them removes only the HTTP surface, not tool availability.
- No external deploy/ops/admin/CI/integration caller posts to these routes (`AC-6`).
- Write tools remain reachable via `/v1/call_tool`.

## Design decisions
- Delete the `@app.post` decorators and handler bodies together; keep `/health`, `/v1/tools`, `/v1/call_tool` untouched.

## Alternatives considered
- Keeping the routes behind the dispatcher: out of scope — this Plan removes the parallel execution contract.

## Implementation
### Target file
`scripts/mcp_servers/file/write_server.py`

### Procedure
1. Delete the 4 direct POST execution-route handlers and registrations at lines 130-188 (`/write_file`, `/edit_file`, `/create_directory`, `/move_file`).
2. Keep `/health` (line 191), `/v1/tools` (line 224), `/v1/call_tool` (line 276) unchanged.
3. Remove now-unused route-specific imports/response-model names if unused elsewhere.

### Method
`grep -n "@app.post" scripts/mcp_servers/file/write_server.py`; delete each decorator + handler; confirm no `@app.post` execution route remains.

### Details
Removed handlers call `_service.write_file/edit_file/create_directory/move_file(req)` directly, never touching `_dispatch_*`, the idempotency/dedup path, or `_emit_call_tool_audit`. Availability is preserved via `/v1/call_tool`.

## Compatibility considerations
Breaking HTTP-surface removal; no backward-compat shim (`tools/check_compat_shims.py`).

## Security considerations
None beyond the general breaking-surface change; side-effecting calls now go through the shared audit path.

## Rollback considerations
Revert the commit.

## Validation plan
- Route-inventory test for the file-write app asserts no execution route remains and `/v1/call_tool` works (`AC-1`, `AC-5`).
- `rg` over deploy/ops/admin/.github/workflows/tests/integration finds no external caller (`AC-6`).

## Completion criteria
- No `@app.post` execution route remains; only `/health`, `/v1/tools`, `/v1/call_tool` remain.
- Write tools still dispatch via `/v1/call_tool`.

## Out of Scope
- `/v1/call_tool` behavior changes; idempotency-key enforcement; route-specific model deletion (service-layer consumers keep those models).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-111108 | 20261115-111108 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261115-111108 | 20261115-111108 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-111108 | 20261115-111108 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261115-111108 | 20261115-111108 |  |

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
- **Requirement ID**: `REQ-002` — remove the direct POST execution routes from the file write server
- **Source issue**: `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-045455_mcproute001_remove-direct-mcp-routes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084338
- **Related target files**: `scripts/mcp_servers/file/write_server.py`