<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "tests/agent/workflow/test_workflow_engine.py", "target_kind": "test", "seq": 14} -->

## Goal

Update `tests/agent/workflow/test_workflow_engine.py` so engine tests cover persisted attempt numbering, claim rejection, and the restart-spanning retry budget (REQ-007, REQ-009, REQ-011 / AC-6, AC-8).

## Scope

- Existing idempotency/retry classes (`test_workflow_engine.py:111-161`, `:186-206`) currently assume the in-memory `attempt = 0` numbering (`workflow_engine.py:202`); align them with the persisted number.
- Add: resume of a `failed` task after N attempts continues at N+1; claim rejection for `running`/`completed`/`halted`; `max_attempts` enforced across simulated restarts.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- Fixture helpers in this file build a real workflow database via the schema — fixtures gain `attempt_number` when rows 10/15 land.

## Design decisions

- Restart simulation: close the engine/store and re-run against the same database file, asserting persisted state drives behavior.

## Alternatives considered

- Mock-only engine tests: rejected — persisted numbering is the behavior under test.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_engine.py`

### Procedure
1. Fix helper inserts for the new columns.
2. Adjust retry-budget assertions to count persisted attempts.
3. Add `TestClaimRejection` and `TestPersistedAttemptBudget` classes.

### Method
Direct edit plus new test classes.

### Details
- `TestRunStageWithRetryGeneralization` (cited by the ADR test table for INV-03) keeps its scenario; only the numbering expectations change.

## Compatibility considerations

- ADR citation (row 23) unchanged for INV-03.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Revert with rows 05/07.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py -v`; new classes fail pre-change.

## Completion criteria

- Engine claims correctly, numbering and budget persist across restarts, and attempt number is exposed (AC-6, AC-8).

## Out of Scope

- Adapter guard tests (row 19).

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
- **Workflow phase**: Phase 4 (Engine, adapter, and audit correlation)
- **Requirement ID**: `REQ-007`, `REQ-009`, `REQ-011`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `tests/agent/workflow/test_workflow_engine.py`, `scripts/agent/workflow/workflow_engine.py`, `tests/agent/workflow/test_workflow_recovery.py`

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

