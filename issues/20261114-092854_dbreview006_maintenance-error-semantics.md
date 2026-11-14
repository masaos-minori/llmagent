# Maintenance operations break their STRICT/BEST_EFFORT contract and leave partial deletes uncommitted

## Priority
Medium

## Summary
`db.maintenance` documents that BEST_EFFORT mode returns `MaintenanceResult(success=False)` instead of raising. Several error types escape, and `purge_old_sessions` runs two deletions without a transaction or rollback, so a failure leaves partial work pending on the connection.

## Background
Found by an adversarial review of `scripts/db` at commit 0fe68d3 (Review finding F-006). Evidence label: `Explicit in code`, confidence High (code reading; not reproduced).

## Problem
- `purge_old_sessions` executes the age delete and the count delete, then commits. If the second statement raises `sqlite3.Error`, STRICT re-raises and BEST_EFFORT returns `success=False`, but the first delete stays in the open implicit transaction. Any later `commit()` on the same helper persists it, and the result reports `age_deleted=N` for rows that are not committed. `extra_data["kept_active_session"]` also reports the requested id, not the computed one.
- `vacuum_db` catches only `OperationalError` and `RuntimeError`; a `sqlite3.DatabaseError` (corrupt file) escapes in BEST_EFFORT mode.
- `RetentionConfig.from_config`, `CorruptArchiveRetentionConfig.from_config`, `build_db_config` and `checkpoint_wal` run before or outside the `try` blocks, so config errors (`ValueError`, load failures) raise even in BEST_EFFORT.
- `_handle_maintenance_error` uses a bare `raise`, which only works while called from inside an `except` block; a future caller outside one raises `RuntimeError: No active exception`.
- `prune_old_memories` collects the ids in `collect_prunable_ids` outside the transaction that `delete_memories_before` later opens, so the returned `pruned_ids` can differ from the rows actually deleted.

## Reason for Change
Callers such as `agent.services.db_maintenance_service` rely on the documented contract to keep maintenance from crashing the agent, and on the result to describe what changed.

## Implementation Intent
Wrap multi-statement maintenance work in one transaction with rollback on error, make the exception handling match the documented modes, and derive reported counts and ids from the transaction that performed the change.

## Target Files or Areas
- `scripts/db/maintenance.py` (`purge_old_sessions`, `vacuum_db`, `_handle_maintenance_error`, `prune_old_memories`)
- `scripts/db/store_impl.py` (`SQLiteMemoryDeleteStore`)
- `scripts/db/helper.py` (`begin_immediate`)
- `tests/db/test_db_maintenance.py`

## Required Changes
- Run the session purge inside `begin_immediate()` so both deletes commit or roll back together.
- Catch `sqlite3.Error` (not only OperationalError) in `vacuum_db`; decide and document how config-load errors behave per mode.
- Pass the exception explicitly to the error handler or re-raise it from the caller.
- Return the deleted ids from the delete transaction instead of a separate pre-query.

## Constraints
- STRICT remains the default and must keep raising.
- Return types stay `MaintenanceResult`.

## Acceptance Criteria
- A forced failure of the second delete leaves the sessions table unchanged and the result states zero committed deletions.
- BEST_EFFORT never raises for `sqlite3.Error` subclasses or config errors, or the docstrings state the exception.
- `pruned_ids` equals the ids actually deleted under a concurrent update.

## Testing Expectations
Unit tests in `tests/db/test_db_maintenance.py` with fault injection per statement; run both modes.

## Documentation Impact
Update the maintenance mode description only if the config-error behavior is changed.

## Out of Scope
- Retention parameter validation (`issues/20261114-092855_dbreview007_retention-input-validation.md`).
- Archive retention (`issues/20261114-092857_dbreview008_artifact-retention-gaps.md`).

## Dependencies
N/A: none

## Unresolved Questions
- Should config-load failure be absorbed in BEST_EFFORT mode? Needs a maintainer decision.

## AI Implementation Instruction
Follow `skills/python-implementation/SKILL.md`. Keep public function signatures. English comments and logs.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261114-092854
- **Related target files**: scripts/db/maintenance.py, scripts/db/store_impl.py, scripts/db/helper.py, tests/db/test_db_maintenance.py
