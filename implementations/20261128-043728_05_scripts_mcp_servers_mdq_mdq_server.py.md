## Goal

Pass `dry_run` from the call arguments into the two MDQ write request models in the handlers, so a
`dry_run=True` call reaches the decision-only path instead of performing a real write.

## Scope
**Release unit**: preview path

- `_handle_index_paths()` (line 253) and `_handle_refresh_index()` (line 261): the request
  construction only.

## Assumptions

- The dispatcher already resolves `execution_mode` as `preview` from the declared capability and the
  `dry_run` argument (`scripts/shared/execution_mode.py` `resolve_execution_mode()`, 27-54); the
  handler change is what makes the mdq side agree with that resolution.
- `dry_run` is optional in the schema, so the handler reads it with a `False` default, matching the
  existing `force` handling.

## Design decisions

- The handler does not decide the mode itself: it only forwards the argument, keeping the mode
  decision in the shared contract and the path selection in the service layer.

## Alternatives considered

- N/A: the handler change is a single argument pass-through with no design choice.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_server.py`

### Procedure
1. In `_handle_index_paths()`, build `IndexPathsRequest` with `dry_run=args.get("dry_run", False)`.
2. In `_handle_refresh_index()`, pass the same value alongside `paths` and `force`.

### Method

- No other handler changes: the metadata ContextVar and the audit detail builder keep reading the
  metadata mapping the service returns.

### Details

- The two handlers are the only mdq handlers that build write requests, so the pass-through is the
  complete handler-side change.

## Compatibility considerations

- For a preview call the metadata is the planned model, so `_build_call_tool_audit_detail()` (line 350)
  reads executed keys (`indexed_count`, `skipped_count`, `deleted_count`, `failed_count`) that are
  absent from the planned model and reports zeros through its existing `.get(..., 0)` defaults. The
  audit payload shape is not changed by this Plan (UNK-03), and the preview is identified by
  `execution_mode="preview"` with `side_effect_applied=False` in the shared record.
- `tests/mcp_servers/mdq/test_mdq_metadata_consistency.py` is the guard for the metadata key contract.
- Cross-plan overlap: this file is also a target of mdqmcp001, which changes the availability check and
  the audit boundary; this document changes only the two handlers' argument pass-through.
- `tests/mcp_servers/conftest.py` (66-94) emulates the preview-capability bootstrap seam that the
  endpoint test relies on to resolve `dry_run` as `preview`.

## Security considerations

- Without this pass-through a declared dry-run capability would still write, which is the exact
  condition the fail-closed preview contract is meant to prevent.

## Rollback considerations

- Revert the commit; no persisted state depends on the pass-through.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_dry_run.py tests/mcp_servers/mdq/test_mdq_routing.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- A `dry_run=True` call is resolved as `preview` and never writes (AC-2).

## Out of Scope

- The capability declaration and the schema property: row 1.
- The decision-only path: row 3.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | New dry-run tests are row 10 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs row 16 records the contract |

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
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `scripts/mcp_servers/mdq/mdq_server.py`
