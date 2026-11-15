## Goal

Remove the 2 direct POST execution routes (`/delete_file`, `/delete_directory`) from `delete_server.py`; keep `/health`, `/v1/tools`, `/v1/call_tool`. (`REQ-002`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The 2 routes call `_service.*` directly and bypass dispatch/idempotency/dedup/audit; removing them removes only the HTTP surface, not tool availability.
- No external deploy/ops/admin/CI/integration caller posts to these routes (`AC-6`).
- Delete tools remain reachable via `/v1/call_tool`.

## Design decisions
- Delete the `@app.post` decorators and handler bodies together; keep `/health`, `/v1/tools`, `/v1/call_tool` untouched.

## Alternatives considered
- Keeping the routes behind the dispatcher: out of scope — this Plan removes the parallel execution contract.

## Implementation
### Target file
`scripts/mcp_servers/file/delete_server.py`

### Procedure
1. Delete the 2 direct POST execution-route handlers and registrations at lines 131-156 (`/delete_file`, `/delete_directory`).
2. Keep `/health` (line 158), `/v1/tools` (line 191), `/v1/call_tool` (line 241) unchanged.
3. Remove now-unused route-specific imports/response-model names if unused elsewhere.

### Method
`grep -n "@app.post" scripts/mcp_servers/file/delete_server.py`; delete each decorator + handler; confirm no `@app.post` execution route remains.

### Details
Removed handlers call `_service.delete_file/delete_directory(req)` directly, never touching `_dispatch_*`, the idempotency/dedup path, or `_emit_call_tool_audit`. Availability is preserved via `/v1/call_tool`.

## Compatibility considerations
Breaking HTTP-surface removal; no backward-compat shim (`tools/check_compat_shims.py`).

## Security considerations
Side-effecting calls now go through the shared audit path.

## Rollback considerations
Revert the commit.

## Validation plan
- Route-inventory test for the file-delete app asserts no execution route remains and `/v1/call_tool` works (`AC-1`, `AC-5`).
- `rg` over deploy/ops/admin/.github/workflows/tests/integration finds no external caller (`AC-6`).

## Completion criteria
- No `@app.post` execution route remains; only `/health`, `/v1/tools`, `/v1/call_tool` remain.
- Delete tools still dispatch via `/v1/call_tool`.

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
- **Requirement ID**: `REQ-002` — remove the direct POST execution routes from the file delete server
- **Source issue**: `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-045455_mcproute001_remove-direct-mcp-routes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084338
- **Related target files**: `scripts/mcp_servers/file/delete_server.py`
