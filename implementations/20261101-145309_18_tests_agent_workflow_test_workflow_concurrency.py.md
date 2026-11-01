<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "tests/agent/workflow/test_workflow_concurrency.py", "target_kind": "test", "seq": 18} -->

## Goal

Create `tests/agent/workflow/test_workflow_concurrency.py` with two-connection claim and attempt-numbering race tests (REQ-002, REQ-003, REQ-011 / AC-5b).

## Scope

- New file in the existing `tests/agent/workflow/` directory (no multi-connection workflow test exists at HEAD).
- Scenarios: two connections claim the same `pending` task — exactly one wins, the other raises `TaskTransitionError`; two concurrent `begin_stage_if_new` calls for one (task, stage) — one proceeds, the other raises `StageAlreadyRunningError`; `attempt_number` allocation under two connections never duplicates (unique index `idx_attempts_task_stage_number` backstop).

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- Two `sqlite3` connections to one file with short busy timeouts; determinism via ordering assertions rather than wall-clock timing.

## Design decisions

- Race outcomes are asserted as invariant sets (exactly-one-winner, unique numbers), not as specific interleavings — keeps the tests deterministic.

## Alternatives considered

- Threading stress with many iterations: rejected for the regression home — deterministic two-connection cases are the REQ-011 requirement.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_concurrency.py` (new)

### Procedure
1. Create the module with a two-connection fixture.
2. Implement the three race groups.

### Method
New file creation.

### Details
- SQLite write serialization means "simultaneous" means interleaved committed transactions; the tests pin the conditional-update semantics that make the race safe.

## Compatibility considerations

- Depends on rows 03/05/10 for the APIs and index it tests.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Delete the file.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_concurrency.py -v`; red until rows 03/05/10 land.

## Completion criteria

- Claim, concurrent start, and numbering races each have a deterministic test (AC-5b).

## Out of Scope

- Multi-process (spawned) races.

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
- **Workflow phase**: Phase 3 (per the Plan traceability row: Testing Expectations 2-3)
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-011`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `tests/agent/workflow/test_workflow_concurrency.py`, `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/db/schema_sql.py`
