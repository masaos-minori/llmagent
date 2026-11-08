# Implementation procedure: `scripts/agent/workflow/attempt_ops.py` — validate `status` in `finish_attempt`

## Goal
Reject out-of-vocabulary attempt statuses with a typed `ValueError` before any SQL runs (`REQ-002`).

## Scope
**Release unit**: wfaudit005-full

- One validation guard at the top of `finish_attempt` (L81-94) plus the `models.py` import.

## Assumptions
- All current callers pass `completed` or `failed` (verified: `workflow_engine.py` L331-371 failure/completion paths, recovery-adjacent flows) — guard is a no-op for existing behavior (`REQ-005`).
- The direct-SQL attempt writes that bypass this helper (`idempotency_ops.py` INSERT `running` L63-80; recovery UPDATE `status='failed'` in `state_store.py` L225-226) are vocabulary-valid by construction and are covered by the sibling seq 06 consistency test (`REQ-004`), not by this guard.

## Design decisions
- Guard at the writer helper (Plan Design "Validate at the writer"): `finish_attempt` is the single chokepoint for attempt terminal writes through the facade.
- Error message names the table and value: `raise ValueError(f"invalid attempts.status {status!r}")` (`REQ-002`).

## Alternatives considered
- N/A: single-guard change.

## Implementation
### Target file
`scripts/agent/workflow/attempt_ops.py`

### Procedure
1. Import `ATTEMPT_STATUSES` from `agent.workflow.models` (new import).
2. At the top of `finish_attempt`, before `db.execute`, add: `if status not in ATTEMPT_STATUSES: raise ValueError(f"invalid attempts.status {status!r} (allowed: {sorted(ATTEMPT_STATUSES)})")`.
3. Extend the docstring with a `Raises ValueError` line.

### Method
- Guard-first pattern; the UPDATE statement and error-detail parameters are untouched.

### Details
- Current state (verified at HEAD `50b5ac2c6`): `finish_attempt(db, attempt_id, status, error_msg, error_kind, error_detail)` writes any string; no vocabulary check exists.

## Compatibility considerations
- `ValueError` propagates to engine callers already wrapped in stage error handling; no engine behavior change for valid statuses (`REQ-005`).
- Rejection tests are owned by sibling document `20261108-093720_06_tests_agent_workflow_.md`; no companion here.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/workflow/attempt_ops.py` | rejection tests (sibling seq 06 owns them) | `uv run pytest tests/agent/workflow/ -q` | `finish_attempt(id, "done")` raises `ValueError`, row unchanged (`REQ-002`) |
| gates | static | `rules/toolchain.md` sequence incl. lint-imports | clean |

## Completion criteria
- Out-of-vocabulary attempt status raises and writes nothing (`Acceptance Criteria REQ-002`); valid-status behavior unchanged (`REQ-005`).

## Out of Scope
- `begin_stage_if_new` (its `running` insert is DDL-default-valid).
- Recovery reconciliation writes (`wfaudit001`/`wfaudit007`, sequenced after).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocks wfaudit001 and wfaudit007: land this plan's batch first |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | No companion test file: rejection tests owned by sibling seq 06 |

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
- **Requirement ID**: `REQ-002` (attempt-status writer validation)
- **Source issue**: `issues/20261107-203218_wfaudit005_unvalidated-status-writes.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: `plans/20261108-084002_wfaudit005_unvalidated-status-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-093720
- **Related target files**: `scripts/agent/workflow/attempt_ops.py`
