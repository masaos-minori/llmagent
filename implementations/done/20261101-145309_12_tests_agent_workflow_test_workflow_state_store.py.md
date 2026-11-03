<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "tests/agent/workflow/test_workflow_state_store.py", "target_kind": "test", "seq": 12} -->

## Goal

Update `tests/agent/workflow/test_workflow_state_store.py` for the canonical attempt path and atomic recovery, and add the transition, error, and raw-SQL invalid-status tests (REQ-002, REQ-003, REQ-005, REQ-006, REQ-011 / AC-2, AC-3, AC-5, AC-7).

## Scope

- Replace `start_attempt` helper use (`:140,147-148,153,162,232-234`) with the canonical `begin_stage_if_new` path.
- Recovery tests (`:449-542` region): assert the owning task moves `running -> failed` and repeats are no-ops.
- Raw INSERT fixtures (`:106,265,269,417,431,435,467,481,510,524`) gain `attempt_number` and stay within the new `CHECK` vocabularies.
- Add invalid-status raw-SQL tests (`IntegrityError`) and zero-row API transition tests (typed errors).

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- The file's `create_task` fixture (`:106` region) keeps its parameter-bound inserts (Plan UNK-06 re-check satisfied at HEAD: raw seeds use only `pending`/`running`).

## Design decisions

- New tests are written to fail against the current code first (Plan REQ-011), committed with the Phase-3 implementation.

## Alternatives considered

- Rewriting the file from scratch: rejected — the existing 542-line fixture suite pins current behavior the Plan wants preserved for aggregates/diagnostics.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_state_store.py`

### Procedure
1. Swap helper import/call sites to the canonical start.
2. Extend recovery-class tests with task-status assertions.
3. Add `TestTaskTransitionErrors` (API level) and `TestRawSqlStatusConstraints` (raw-SQL level) classes.

### Method
Direct edit of the existing test module plus new test classes.

### Details
- Recovery fixture pattern: `workflow_db` factory (`:449-476` region) already inserts tasks/attempts via raw SQL — extend the attempt inserts with `attempt_number`.

## Compatibility considerations

- This file is cited by the ADR test table (row 23 updates the citation rows).

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Test revert pairs with the row-03/04/05/06 revert.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_state_store.py -v`.
- Pre-change run: new transition/recovery tests fail against HEAD; post-change: green (REQ-011 ordering).

## Completion criteria

- Transition, ledger, recovery, and constraint behaviors each have at least one test at API and raw-SQL level (AC-2, AC-3, AC-5, AC-7).

## Out of Scope

- Concurrency tests (row 18); crash-scenario tests (row 17).

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
- **Workflow phase**: Phases 1 and 3 (tests land with their implementation phase)
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-005`, `REQ-006`, `REQ-011`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `tests/agent/workflow/test_workflow_state_store.py`, `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py`, `tests/agent/workflow/test_workflow_recovery.py`

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

