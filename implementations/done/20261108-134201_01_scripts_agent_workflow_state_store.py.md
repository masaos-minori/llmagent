## Goal
Make `recover_stale_attempts` delete the `processed_events` rows of the attempts it fails (REQ-001: recovered stage is no longer permanently skipped), and add the bounded startup retention purge `purge_finished_workflow_events` (new) (REQ-003: unbounded table growth).

## Scope
**Release unit**: wfaudit001-full

- Covers Plan `plans/20261108-084003_wfaudit001_processed-events-never-pruned.md` row 1 only: `scripts/agent/workflow/state_store.py`.
- The orchestrator wiring call is row 3 (`20261108-134201_03_scripts_agent_orchestrator.py.md`); the comment correction is row 2 (`20261108-134201_02_scripts_agent_workflow_idempotency_ops.py.md`).

## Assumptions
- Pair-scoped deletion is the correct superset: `attempts` has no attempt-number column (verified at HEAD, `scripts/db/schema_sql.py:191-204`), so the event key cannot be rebuilt; resume restarts the stage at attempt 1 and needs the whole (`task_id`, `stage_id`) pair cleared (Plan Design/Assumptions).
- Retention horizon: named module constant `_EVENT_RETENTION_SEC` (new) = 30 * 24 * 3600 (30 days, the Plan `UNK-01` candidate value; the dedup precedent
  `scripts/shared/mcp_dedup.py` models the retention-purge mechanism with a 14-day value, verified 2026-11-09 — the 30-day horizon is the Plan's choice, not dedup's; constants-before-configuration precedent).
- Purge target: `processed_events` rows only; terminal `tasks`/`attempts` rows are not deleted in this plan (Plan `UNK-02` resolved events-only; the `ON DELETE CASCADE` FK path remains available for a future decision).

## Design decisions
- The prune DELETE runs only inside the existing `rowcount == 1` compare-and-swap branch of `recover_stale_attempts`, which already proves the attempt was orphaned; it joins the same transaction as the attempt UPDATE and the single `db.commit()` (begin-immediate discipline preserved).
- The purge is a startup call (not a scheduler), mirroring the recovery convention and the `purge_expired` precedent in `scripts/shared/mcp_dedup.py`; it logs the deleted count like `RecoveryReport` does for recovery.

## Alternatives considered
- Rebuilding `event_id = {task_id}:{stage_id}:{attempt}` from the attempt row: impossible — the attempt counter in `_run_stage_with_retry` is process-local and never persisted (`attempts` DDL has no such column).
- Linking event rows to attempts via a new FK column: rejected — schema change out of plan scope, and pair-scoped deletion already produces the correct resume behavior.

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`

### Procedure
1. In `_classify_running_attempts`, extend the classification SELECT to also return `task_id` and `stage_id`, and carry both into the returned dicts.
2. In `recover_stale_attempts`, in the `cursor.rowcount == 1` branch, execute `DELETE FROM processed_events WHERE task_id=? AND stage_id=?` with the claimed attempt's pair before the existing commit.
3. Add `purge_finished_workflow_events` (new) to `StateStore` and the module constant `_EVENT_RETENTION_SEC` (new).

### Method
1. Change the SELECT to `SELECT attempt_id, task_id, stage_id, started_at, owner_id, lease_expires_at FROM attempts WHERE status='running'` and add `"task_id"`/`"stage_id"` to the `entry` dict so every classification path carries them.
2. After `recovered += 1` bookkeeping in the `rowcount == 1` branch: `db.execute("DELETE FROM processed_events WHERE task_id=? AND stage_id=?", (item["task_id"], item["stage_id"]))`. No separate commit — the existing `if stale: db.commit()` covers it.
3. `purge_finished_workflow_events(self, db: SQLiteHelper) -> int` (new): one `DELETE FROM processed_events WHERE task_id IN (SELECT task_id FROM tasks WHERE status IN ('completed','failed','halted') AND updated_at < ?)` with the horizon computed from `_now()` minus `_EVENT_RETENTION_SEC` (new) in the same ISO-UTC format; log the deleted count (`cursor.rowcount`) at INFO; return the count.

### Details
- Vocabulary `('completed','failed','halted')` is the terminal subset of the `tasks.status` CHECK constraint enforced since wfaudit005; keep it in sync with `TASK_STATUSES` in `scripts/agent/workflow/models.py`.
- `find_stale_running_attempts` reuses `_classify_running_attempts`; the added keys are additive and must not break its existing dict contract (existing tests pin its keys).

## Compatibility considerations
- `find_stale_running_attempts` output gains two keys; existing consumers read by name, so additive keys are safe. No public signature changes.

## Security considerations
- No new inputs; all values come from the attempts table. SQL uses parameter binding only.

## Rollback considerations
- Single revert of the commit; no schema or data migration is involved, so no operator action is required.

## Validation plan
- New tests in `tests/agent/workflow/test_state_store.py` (extend `TestRecoverStaleAttemptsOptimisticLocking` fixtures): recovered attempt's event rows for its pair are gone in the same run; a live-lease attempt's pair is untouched; a different stage's event rows for the same task survive.
- New purge boundary tests (same file): terminal task older than `_EVENT_RETENTION_SEC` (new) → its event rows deleted; recent terminal task and running-task events untouched; deleted count returned/logged.
- Resume re-execution test (REQ-002, Plan Acceptance Criteria): after recovery, `begin_stage_if_new` returns an `AttemptRecord` (not None) for the same (`task_id`, `stage_id`) stage run.
- New tests must fail on HEAD before the change; then `uv run pytest tests/agent/workflow/ -q`, then full `uv run pytest tests/ -q`; lint/type gates per `rules/toolchain.md`.

## Completion criteria
- Recovery deletes the pair's event rows atomically with the attempt failover, live-lease pairs untouched, purge enforces the horizon and reports its count; all new and existing workflow tests pass.

## Out of Scope
- Calling the purge from process initialization (row 3 document).
- Replacing the false comment block (row 2 document).
- Deleting terminal `tasks`/`attempts` rows themselves (`UNK-02` events-only resolution).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-062329 | 20261109-062329 | pair-DELETE in CAS branch + purge_finished_workflow_events() + constants in state_store.py |
| 2 | Add or update tests per Validation plan | Completed | 20261109-062329 | 20261109-062329 | TestRecoveryPrunesProcessedEvents (3 tests) + TestPurgeFinishedWorkflowEvents (3 tests) in tests/agent/workflow/test_state_store.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-062329 | 20261109-062329 | run_validation_gates.py exit 0; targeted suites green |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-062329 | 20261109-062329 | docs rows 4-5 own the doc updates N/A: doc updates owned by procedure docs 04/05 |

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
- **Requirement ID**: `REQ-001` (recovery prunes event rows in-transaction), `REQ-003` (bounded retention purge)
- **Source issue**: `issues/20261107-203214_wfaudit001_processed-events-never-pruned.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084003_wfaudit001_processed-events-never-pruned.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-134201
- **Related target files**: `scripts/agent/workflow/state_store.py`