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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-only |

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
