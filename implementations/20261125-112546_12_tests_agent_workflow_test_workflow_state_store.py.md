## Goal
Update the recorded-call call sites for the new `args_hash` argument.

## Scope
**Release unit**: persisted directive store

## Assumptions
- 18 call sites in this file (first at line 872); each passes positional arguments, so each gains one argument.

## Design decisions
N/A: call-site update only.

## Alternatives considered
N/A: test-only change.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_state_store.py`

### Procedure
Add the hash argument to every `store.record_tool_call` call.

### Method
Pass a fixed canonical hash per call, computed with the same helper the production write path uses, so the stored
value is comparable in the assertions.

### Details
- Add one assertion that a recorded row exposes `args_hash` through `_row_to_state`.
- Add one test that reconstruction returns rows only for `interrupted` replayable rows, per the Plan's Validation
  plan row for `tool_call_state_ops`.

## Compatibility considerations
The tests depend on the DDL column from sibling procedure seq 01; they cannot pass before it lands.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_state_store.py` (REQ-006, AC-005).

## Completion criteria
Every call site compiles against the new signature and the hash assertions hold for recorded rows.

## Out of Scope
No change to the stale-classification tests beyond the call sites.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the 18 call sites and add the hash assertions | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (persisted hash), `REQ-007` (every intermediate type and test updated in the same change set)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `tests/agent/workflow/test_workflow_state_store.py`
