## Goal

Extend `TOOL_CALL_STATES` to the full intent vocabulary (`REQ-005` state vocabulary, AC-6).

## Scope
**Release unit**: auth-intent

## Assumptions
- `reconciliation_required` (new) is vocabulary-only in this Plan; its writer arrives with mcpdl004 (UNK-03 plan default).

## Design decisions
- Replace the frozenset at line 20 with: `pending`, `dispatch_starting`, `dispatched`, `response_received`, `completed`, `failed`, `interrupted`, `outcome_unknown` (new), `reconciliation_required` (new).
- `pending` is kept (not renamed to `prepared`) so `classify_stale_pending` and its existing pins stay valid until the new states are exercised (Plan Design).

## Alternatives considered
- N/A: the vocabulary is fixed by REQ-005; this row only mirrors it.

## Implementation
### Target file
`scripts/agent/workflow/models.py`

### Procedure
Edit `TOOL_CALL_STATES` (:20) in the same commit as the canonical DDL `CHECK` change (row 12) — required by the Plan's Unit-2 rule.

### Method
Single-line frozenset replacement.

### Details
- The comment above the frozenset must name the new terminal/non-replayable states (`outcome_unknown` (new)) so readers see AC-6.

### Companion test files
- `tests/agent/workflow/test_workflow_status_vocabulary.py`
  - Procedure: pin the exact nine-state frozenset; assert removal of none of the legacy four.
  - Validation: `uv run pytest tests/agent/workflow/test_workflow_status_vocabulary.py` passes.

## Compatibility considerations
The DDL `CHECK` (row 12) must ship in the same commit; a mismatch is rejected by `tools/check_db_separation.py` and the shape pins.

## Security considerations
N/A: vocabulary-only change.

## Rollback considerations
N/A: revert the commit together with row 12 (DDL and vocabulary land as one unit).

## Validation plan
`uv run pytest tests/agent/workflow/test_workflow_status_vocabulary.py tests/db/test_create_schema.py && uv run python tools/check_db_separation.py`.

## Completion criteria
`TOOL_CALL_STATES` and the canonical DDL `CHECK` accept exactly the same nine states.

## Out of Scope
Transition semantics (row 10); recorder contract (row 6).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs sweep owned by mcpai012 |

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
- **Related target files**: `scripts/agent/workflow/models.py`, `tests/agent/workflow/test_workflow_status_vocabulary.py`
