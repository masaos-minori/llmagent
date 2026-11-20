## Goal

Pin new-key row writes, the intent transitions, and collision-freedom in the workflow state store (`REQ-005` state store contract).

## Scope
**Release unit**: N/A: the row is not cited by any Release-unit phase step; it verifies rows 10-12 and lands with unit auth-intent.

## Assumptions
- Tests drive `StateStore` against a scratch DB built from the canonical DDL (row 12).

## Design decisions
- Assert rows written with uuid7 logical ids never merge (two calls, identical tool+args+task, distinct ids → two rows).
- Assert `finalize_tool_call` accepts every intermediate intent state and rejects non-vocabulary values (existing ValueError contract).
- Assert `classify_stale_pending` splits: never-dispatched → `interrupted`, dispatch-stage → `outcome_unknown` (row 10 semantics).

## Alternatives considered
- N/A: test-only mirror of rows 10-12.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_state_store.py`

### Procedure
Update existing `tool_call_state` fixtures to logical-id keys; add the transition and split cases.

### Method
Scratch-DB fixtures already used by this file; no new helpers.

### Details
- Keep the `pending_tool_calls` listing pin: dispatch-stage rows stay out of it.

## Compatibility considerations
Existing pending-only cases stay valid; only key values change.

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/workflow/test_workflow_state_store.py`.

## Completion criteria
The store honors the nine-state vocabulary, keys by logical id, and the stale split is pinned end-to-end.

## Out of Scope
Engine replay behavior (row 10's companion); DDL text (row 12's companions).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Rows 10-12 already landed the key/transition/stale-split pins in this file; this row adds the two remaining pins: `test_distinct_logical_ids_never_merge` (identical tool+args+task, distinct uuid7 ids → two rows) and `test_dispatch_stage_rows_stay_out_of_pending` (dispatch_starting/dispatched/response_received stay out of `pending_tool_calls`, row still live). Fixture key values already match the logical-id shape. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | `uv run pytest tests/agent/workflow/test_workflow_state_store.py tests/deploy/test_required_workflow_tables_parity.py`: 57 passed; ruff clean on the changed file. |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 2026-11-21 | N/A: test-only |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `tests/agent/workflow/test_workflow_state_store.py`
