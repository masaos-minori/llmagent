<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "tests/agent/workflow/test_workflow_stage_persistence.py", "target_kind": "test", "seq": 15} -->

## Goal

Replace bypass-path usage and add ledger semantics tests in `tests/agent/workflow/test_workflow_stage_persistence.py` (REQ-003, REQ-004, REQ-011, REQ-012 / AC-3, AC-4, AC-9).

## Scope

- Replace `start_attempt` calls (`:42,61,73`) with the canonical `begin_stage_if_new` path; keep the raw task INSERT fixture (`:29`, `pending` — within the new vocabulary).
- Add ledger tests: a completed stage is skipped on re-run; a stage whose attempt `failed` re-runs and gets the next `attempt_number`; starting while another attempt for the stage is `running` raises `StageAlreadyRunningError`.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- This file is the AC-9 verification home for "no bypass caller": after the change, `rg "start_attempt" tests` returns nothing.

## Design decisions

- Skip assertions key on the ledger row for (task, stage), matching the REQ-004 semantics chosen in row 05.

## Alternatives considered

- Testing skip via attempt status: rejected — the ledger is the contract (Plan UNK-02).

## Implementation
### Target file
`tests/agent/workflow/test_workflow_stage_persistence.py`

### Procedure
1. Swap helper imports/calls.
2. Add `TestLedgerSkip`, `TestNumberingAfterFailure`, `TestConcurrentStageStart` classes.

### Method
Direct edit plus new test classes.

### Details
- Fixture task row (`:29`) uses explicit column list; add `attempt_number` to its attempts inserts once row 10 lands.

## Compatibility considerations

- `test_begin_stage_if_new_idempotent` (ADR INV-08 citation, `:187-188` region of the ADR test table) is re-pointed by row 23 if the test name changes.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Revert with rows 04/05.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_stage_persistence.py -v`; ledger tests fail pre-change.

## Completion criteria

- Stage skip, re-run numbering, and concurrent-start rejection are proven; no test uses the deleted bypass (AC-3, AC-4, AC-9).

## Out of Scope

- Two-connection race tests (row 18).

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
- **Workflow phase**: Phase 3 (Attempt lifecycle, ledger, and recovery)
- **Requirement ID**: `REQ-003`, `REQ-004`, `REQ-011`, `REQ-012`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `tests/agent/workflow/test_workflow_stage_persistence.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/attempt_ops.py`

## Implementation Result (2026-11-03: superseded by upstream)

This wfrecovery001 procedure implemented an attempt-number-based recovery state
machine. Upstream (`origin/master`) superseded this design with a lease-based
stale-attempt recovery (wflease001, AC-2/AC-4/AC-5/AC-7). The batch was
therefore NOT merged into `origin/master`.

- **Decision (2026-11-03):** full supersession. Every one of the ~32 code files
  the batch touched was rewritten or replaced by upstream (lease columns on
  `attempts`, a `disable_foreign_keys` migration-runner rebuild, fail-closed
  tool audit, schema manifest bumped to workflow version 1.4.0). No substantive
  delta survives.
- **Action:** the 3-way merge (`git merge --no-commit backup-batch` onto branch
  `rederive` from `origin/master`) was aborted (`git merge --abort`), returning
  to a clean `origin/master` at `7d6744fd`.
- **Residual:** `attempt_number` / `CHECK` are entangled with upstream's
  lease/local-retry design and cannot be integrated as a clean, bounded
  addition; reintroducing them would fight the lease architecture.
- **Outcome:** divergent code is not integrated. The batch remains on
  `backup-batch` as a superseded historical record. All 26 procedures were
  executed and marked Completed on `backup-batch`; this note records the
  supersession.

