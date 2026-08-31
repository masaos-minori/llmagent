# `recover_corruption()` treats Unknown classification identically to Corruption, violating ADR-008 INV-17

## Priority
High

## Summary
ADR-008 (post ADR-011 merge, 2026-08-31) INV-17 requires that Unknown or unclassifiable
integrity-check failures preserve the target database and require operator intervention rather
than triggering automatic restoration. `recover_corruption()` in `scripts/db/recovery.py`
currently treats `DbCondition.UNKNOWN` identically to `DbCondition.CORRUPTION`, so an
unclassifiable failure on `rag.sqlite`/`session.sqlite` still triggers an automatic
backup-restore attempt. This gap is recorded in ADR-008's Known Deviations but not yet fixed.

## Background
Confirmed during the ADR-011 → ADR-008 merge by reading `scripts/db/recovery.py` in full:
`_classify_error()` returns `DbCondition.UNKNOWN` for exceptions that are neither
`sqlite3.OperationalError` (lock/permission) nor `sqlite3.DatabaseError`/`ValueError`
(corruption), but `recover_corruption()`'s branch
`if condition in (LOCK_CONTENTION, PERMISSION_FAILURE, INVALID_FORMAT)` does not include
`UNKNOWN`, so execution falls through to the "CORRUPTION or UNKNOWN" comment and attempts
`_restore_from_backup()` for `rag`/`session` targets exactly as it would for confirmed
corruption.

## Problem
(Evidence: Explicit in code, `scripts/db/recovery.py::recover_corruption()`) An Unknown or
unclassifiable integrity-check failure on `rag.sqlite` or `session.sqlite` is not distinguished
from confirmed corruption and can trigger an automatic backup restore, contradicting ADR-008
INV-17.

## Reason for Change
The ADR-008 invariant exists specifically because an automatic action taken on a failure of
unknown cause is riskier than requiring operator judgment — an ambiguous failure (e.g., a
transient I/O error the classifier does not recognize) should not silently trigger a backup
restore that could discard legitimate current data.

## Implementation Intent
Add an explicit `UNKNOWN` branch in `recover_corruption()` that returns a result equivalent to
`no_recovery_allowed` — preserving the target database and reporting that operator intervention
is required — mirroring the behavior already implemented for `workflow`/`eventbus` targets,
without changing the existing (already-decided) `CORRUPTION` branch's restore behavior for
`rag`/`session`.

## Target Files or Areas
- `scripts/db/recovery.py` (`recover_corruption()`)
- `tests/db/test_db_maintenance.py`
- `tests/integration/test_session_recovery.py`
- `docs/adr/ADR-008-sqlite-4db-separation.md` (Known Deviations entry, once fixed)

## Required Changes
- Split the `condition in (LOCK_CONTENTION, PERMISSION_FAILURE, INVALID_FORMAT)` check (or add a
  parallel check) so `DbCondition.UNKNOWN` returns a result that preserves the target database
  and reports that operator intervention is required, instead of falling into the
  corruption/restore path.
- Update `recover_corruption()`'s docstring `action` value list to reflect the new outcome for
  Unknown.
- Update ADR-008's Known Deviations entry for this gap once fixed (mark resolved or remove).

## Constraints
- Do not change the `CORRUPTION` branch's existing restore behavior for `rag`/`session` — that
  is an already-accepted ADR-008 decision.
- Do not change the `workflow`/`eventbus` `no_recovery_allowed` path.

## Acceptance Criteria
- A `DbCondition.UNKNOWN` integrity-check result on `rag`/`session` no longer triggers
  `_restore_from_backup()`.
- `recover_corruption()` returns a result whose `action` clearly communicates "preserved,
  operator intervention required" for Unknown outcomes.
- ADR-008's Known Deviations entry for this gap is updated to reflect the fix.
- `uv run pytest tests/db/test_db_maintenance.py tests/integration/test_session_recovery.py` passes.

## Testing Expectations
Add or update a unit test asserting that an Unknown classification does not call
`_restore_from_backup()` and leaves the target database unmodified. Run the full
`uv run pytest` suite once and compare against baseline. Apply the standard validation sequence
in `rules/toolchain.md` (format → lint → type → arch → security → test → coverage).

## Documentation Impact
Update ADR-008's Known Deviations section to mark this gap resolved once implemented.

## Out of Scope
- Changing the classification logic in `_classify_error()` itself.
- Changing behavior for `CORRUPTION`, `LOCK_CONTENTION`, `PERMISSION_FAILURE`, or `INVALID_FORMAT`.

## Dependencies
Follows the 2026-08-31 ADR-011 → ADR-008 consolidation (INV-17, Known Deviations entry).

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `scripts/db/recovery.py` in full before editing. Change only the `UNKNOWN`-handling branch;
do not restructure the function. Update the ADR-008 Known Deviations entry in the same change
once the fix lands.
