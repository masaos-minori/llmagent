<!-- workitem: {"kind":"implementation-procedure","batch_id":"20261101-145309","seq":3,"source_plan":"plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md","source_issue":null,"source_review":null,"target_file":"scripts/agent/workflow/task_ops.py","generated_at":"2026-11-01T14:53:09Z","schema_version":"1.0","schema_hash":"488513b688446992"} -->

## Goal

Make task-status writes in `scripts/agent/workflow/task_ops.py` conditional single-row transitions and add the claim entry point used by engine and adapter (REQ-002, REQ-007 / AC-2, AC-6).

## Scope

- Replace the unconditional `update_task_status` (`task_ops.py:21-36`, ignores row count) with `transition_task_status(db, task_id, current, target)` implementing the REQ-001 matrix.
- Add `claim_task_running(db, task_id)` accepting `pending` or `failed` only.
- Zero updated rows: `TaskNotFoundError` when the task row is absent, `TaskTransitionError` otherwise.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- `StateStore.update_task_status` (`state_store.py:63-69`) is an inline duplicate that row 06 converts into a delegate; both call paths land in one unit so no caller sees a half-migrated API.

## Design decisions

- Transition is one statement: `UPDATE tasks SET status=?, updated_at=? WHERE task_id=? AND status=?`; `rowcount` decides the outcome — no read-then-write race window.
- Matrix legality is checked in Python via `can_transition` before the SQL runs, so an illegal edge never reaches the database.
- `claim_task_running` is the single claim surface (REQ-007: `running`, `completed`, `halted` rejected).

## Alternatives considered

- Optimistic version column: rejected — the status column itself is the expected-value guard the REQs define; adding a column widens the migration.

## Implementation
### Target file
`scripts/agent/workflow/task_ops.py`

### Procedure
1. Add `transition_task_status` and `claim_task_running` using `models.TASK_TRANSITIONS`.
2. Rewrite `update_task_status` to delegate to `transition_task_status` for the existing (engine/adapter) call sites, so its signature survives Phase 1 while rows 07/08 migrate callers to explicit transitions.
3. Raise the row-02 errors on the zero-row branches (`SELECT 1 FROM tasks WHERE task_id=?` distinguishes not-found from wrong-status).

### Method
Direct edit; additive functions plus a body rewrite of `update_task_status`.

### Details
- Existing SQL in `task_ops.py` is parameter-bound already (`:30-36`); the only behavioral change is the `AND status=?` clause and the row-count branch.
- Interaction with wftaskapi001 row `implementations/20261101-140834_01_*` (Pending): that procedure renames `idempotency_key` to `task_nonce` and rewords the same docstring region; whichever lands first is the baseline and the other re-applies on top (Plan UNK-05).

## Compatibility considerations

- `tests/agent/test_orchestrator.py` mocks `update_task_status` (`:2758-2896`); row 19 updates those assertions in Phase 4.
- The adapter halted-resume message contract (`RuntimeError` naming `halted`) is preserved via `TaskTransitionError` (row 02 decision).

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.
- No `eval`/string interpolation of statuses; enum-typed parameters only.

## Rollback considerations

- Revert this file plus the row-06 delegate in one commit; no persisted shape changes.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_state_store.py -v` after row 12 adds the invalid-status/zero-row API tests.
- `uv run pytest tests/agent/workflow/test_workflow_concurrency.py -v` (row 18, claim race).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- Every task-status write goes through a conditional single-row update; illegal edges and zero-row outcomes raise typed errors; claim accepts only `pending`/`failed` (AC-2, AC-6).

## Out of Scope

- Attempt transitions (rows 04/05); engine/adapter call-site migration (rows 07/08).

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
- **Workflow phase**: Phase 1 (Vocabulary, errors, and task transitions)
- **Requirement ID**: `REQ-002`, `REQ-007`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/models.py`, `scripts/agent/workflow/errors.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow_engine_adapter.py`

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

