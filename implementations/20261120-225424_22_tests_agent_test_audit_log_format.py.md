## Goal

Pin the audit event field contract: approval and exec events carry the logical call id and never raw args (`REQ-008` audit format).

## Scope
**Release unit**: N/A: the row is not cited by any Release-unit phase step; it verifies the row 8 field contract and runs alongside unit auth-intent.

## Assumptions
- The serialized key name stays `idempotency_key` (row 8 decision); only the value shape changes to a uuid7 string.

## Design decisions
- Update the existing `audit_tool_exec`-driven format pins to expect a uuid7-shaped `idempotency_key` value on side-effecting events.
- Add a pin that `args_preview`/masked fields behavior is unchanged (no raw args in any event field).

## Alternatives considered
- N/A: test-only mirror of row 8.

## Implementation
### Target file
`tests/agent/test_audit_log_format.py`

### Procedure
Adjust the event-field expectations; add the uuid7-shape and grant-free assertions.

### Method
Existing fixture-driven assertions only; no new harness.

### Details
- `ToolApprovalEvent` now carries `idempotency_key` (row 8); add its presence to the approval-event pin.

## Compatibility considerations
Old stored audit lines are historical; pins assert newly written events only.

## Security considerations
Reinforces the no-raw-args invariant.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/test_audit_log_format.py`.

## Completion criteria
New approval and exec events are pinned to carry the same logical call id with masked args.

## Out of Scope
Audit raising semantics (row 5 and its companion).

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
- **Requirement ID**: `REQ-008`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `tests/agent/test_audit_log_format.py`
