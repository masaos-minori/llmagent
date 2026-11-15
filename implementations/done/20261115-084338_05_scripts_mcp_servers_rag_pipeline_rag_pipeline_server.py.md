## Goal

Remove the `/rag_run_pipeline` and `/rag_debug_pipeline` direct POST execution routes from `rag_pipeline_server.py`; keep `/health`, `/v1/tools`, `/v1/call_tool`. (`REQ-002`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Both routes call `_service` directly and bypass dispatch/idempotency/dedup/audit; removing them removes only the HTTP surface, not tool availability.
- No external deploy/ops/admin/CI/integration caller posts to these routes (`AC-6`).

## Design decisions
- Delete both `@app.post` decorators and their handler bodies together; keep `/health`, `/v1/tools`, `/v1/call_tool` untouched.

## Alternatives considered
- Keeping the routes behind the dispatcher: out of scope — this Plan removes the parallel execution contract.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`

### Procedure
1. Delete the `/rag_run_pipeline` handler and registration at line 182 and the `/rag_debug_pipeline` handler at line 199.
2. Keep `/health` (line 245), `/v1/tools` (line 261), `/v1/call_tool` (line 288) unchanged.
3. Remove now-unused route-specific imports/response-model names (`RagRunResponse`, `RagDebugResponse`) if unused elsewhere. NOTE (corrected during Step 3a adversarial verification): after deleting both handlers, `time`, `fmt_kvlog`, and `RagRunRequest` are also imported but no longer used in this module (their only usages were inside the two removed handlers), so all five names are removed together.

### Method
`grep -n "@app.post" scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`; delete both decorators + handlers; confirm no `@app.post` execution route remains.

### Details
Removed handlers call `_service` directly, never touching `_dispatch_*`, the idempotency/dedup path, or `_emit_call_tool_audit`. Availability is preserved via `/v1/call_tool`.

## Compatibility considerations
Breaking HTTP-surface removal; no backward-compat shim (`tools/check_compat_shims.py`).

## Security considerations
Side-effecting calls now go through the shared audit path.

## Rollback considerations
Revert the commit.

## Validation plan
- Route-inventory test for the RAG app asserts no execution route remains and `/v1/call_tool` works (`AC-1`, `AC-5`).
- `rg` over deploy/ops/admin/.github/workflows/tests/integration finds no external caller (`AC-6`).

## Completion criteria
- No `@app.post` execution route remains; only `/health`, `/v1/tools`, `/v1/call_tool` remain.
- RAG tools still dispatch via `/v1/call_tool`.

### Companion test files
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`
  - Procedure: remove the tests that post to the removed routes (`test_service_error_maps_to_503` line 180, `test_success_returns_run_result` line 194, `test_success_returns_debug_result` line 215); keep the `/v1/call_tool` and embed-url probe tests.
  - Validation: targeted pytest on the RAG server-endpoint suite passes; no reference to `/rag_run_pipeline` or `/rag_debug_pipeline` remains.

## Out of Scope
- `/v1/call_tool` behavior changes; idempotency-key enforcement; route-specific model deletion.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-112625 | 20261115-112625 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261115-112625 | 20261115-112625 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-112625 | 20261115-112625 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261115-112625 | 20261115-112625 | STEP:4:N/A no docs/00_index.md task-scope mapping for rag_pipeline_server.py; API reference update is REQ-008 (procedure 19) |

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
- **Requirement ID**: `REQ-002` — remove the direct POST execution routes from the RAG server
- **Source issue**: `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-045455_mcproute001_remove-direct-mcp-routes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084338
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`