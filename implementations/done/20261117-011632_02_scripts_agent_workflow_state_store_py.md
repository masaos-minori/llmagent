## Goal

Make `lease_duration_sec` a required `int` in `StateStore.begin_stage_if_new()` and forward it to `idempotency_ops.begin_stage_if_new()` without a default, so no public production API can create a running attempt without a lease (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-001` (seq 01) makes `idempotency_ops.begin_stage_if_new()` require a positive `lease_duration_sec`; the facade must pass a value through or it cannot satisfy REQ-002.
- `WorkflowEngine` (reference file) already passes `timeout + _LEASE_MARGIN_SEC` (a positive int), so the required-argument change does not alter its call convention.

## Design decisions
- **Mirror the writer's signature.** The facade's parameter becomes `lease_duration_sec: int` (required, no default) and is forwarded positionally/by-keyword to `idempotency_ops.begin_stage_if_new()`. No new validation here — the writer owns it (seq 01).

## Alternatives considered
- **Keeping the optional facade param and relying on the writer's error:** would let the facade accept `None` and defer the failure, but then a public production API could be *called* without a lease (violating AC1 "no public production API can create a running attempt without a lease"). Rejected; the facade mirrors the required argument.

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`
### Procedure
1. Change the parameter annotation from `lease_duration_sec: int | None = None` to `lease_duration_sec: int` (required). Reorder so `lease_duration_sec` precedes the defaulted `workflow_id: str | None = None` (Python forbids a non-default parameter after a defaulted one); both are always called by keyword, so the swap is safe.
2. Forward `lease_duration_sec` to `idempotency_ops.begin_stage_if_new()` in the existing delegation.
### Method
Two edits: the annotation line and the delegation call.
### Details
- Line 118: change
  `        lease_duration_sec: int | None = None,`
  to
  `        lease_duration_sec: int,`
  (required, no default).
- Lines 127-131 (delegation): ensure `lease_duration_sec` is passed through. The current delegation forwards `workflow_id=` by keyword; add `lease_duration_sec=lease_duration_sec` to the same call so the value reaches the writer. Verify the final call reads all four forwarded args (`event_id`, `task_id`, `stage_id`, `workflow_id=...`, `lease_duration_sec=...`).

## Compatibility considerations
Breaking on the facade surface: callers of `StateStore.begin_stage_if_new()` must now supply a positive lease. On this host the only production caller is `WorkflowEngine` (already supplies `timeout + 30`). Test callers that omit it are updated in seq 05/08.

## Security considerations
N/A: no auth/permission changes.

## Rollback considerations
Revert the commit; the change is two edits in one file.

## Validation plan
- Unit: call the facade without a lease → expect `TypeError`; with a positive int → expect success and a stamped attempt.
- Command: `uv run pytest tests/agent/workflow/test_state_store.py` (facade-surface test in seq 08).

## Completion criteria
- `StateStore.begin_stage_if_new()` requires a `lease_duration_sec: int` and forwards it to the writer.

## Out of Scope
The writer's validator/stamping (seq 01); the model field addition (seq 03); the schema DDL (seq 04); caller/test updates (seq 05-10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-130103 | 20261117-130103 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261117-130103 | 20261117-130103 |  |

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
- **Requirement ID**: `REQ-002` (facade requires + forwards lease)
- **Source issue**: `issues/20261116-114834_compat002_mandatory-attempt-leases.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-221315_compat002_mandatory-attempt-leases.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-011632
- **Related target files**: `scripts/agent/workflow/state_store.py`