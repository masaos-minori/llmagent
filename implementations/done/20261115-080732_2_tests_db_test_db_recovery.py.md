## Goal
- Cover the in-activation failure paths with fault-injection tests, and move the handler rollback-failure test to the unified vocabulary.

## Scope
**Release unit**: activation-rollback-reporting (Phase 3 of the plan; companion to `20261115-080732_1_scripts_db_recovery.py.md` — the unit red-gates until both land)

- In scope: `tests/db/test_db_recovery.py` — one existing test updated, four new failure tests (REQ-003, REQ-005).
- Cross-plan overlap `tests/db/test_db_recovery.py` (shared with Plans 003/004): **compatible (sequencing)** — this document edits `test_os_error_after_activation_with_failed_rollback_reports_non_serviceable` (`:996-1021`) and appends new functions; Plan 001's generated procedures are add-only functions appended after `test_wal_shm_sidecars_land_at_final_locations_after_activation`; Plan 003's quarantine-flip tests and Plan 004's probe tests are disjoint functions.

## Assumptions
- Baseline recorded this cycle: `uv run pytest tests/db/test_db_recovery.py -q` → 74 passed; `action == "error"` assertions exist at 108, 120, 132, 1020, 1432, 1477 and only the one at 1020 changes (1432 is `os.replace` itself failing: no swap, no rollback — stays `error`).
- Existing failure tests (`:933-963`, `:965-991`, `:1424-1436`) keep passing unchanged: they exercise post-activation re-check failures and replace-failure, whose vocabulary does not change.
- New failure tests patch `db.recovery._run_logical_verification` to `(True, None)` and use the 3×HEALTHY `db.recovery._run_integrity_check` side_effect pattern (the existing WAL-test pattern at `:1044-1052`) so the flow reaches activation.

## Design decisions
- Fault injection at exactly the two in-activation points the Issue's Testing Expectations name: after `os.replace` (via `shutil.move` raising) and after the first sidecar move (via a `shutil.move` side_effect that delegates the first call then raises).
- `_cleanup_staged` failure injection uses a side_effect that raises only for the temp-restore path, so no unrelated `unlink` call in the flow is affected.

## Alternatives considered
- Patching `db.recovery._activate_candidate` wholesale (the Issue's ad hoc reproduction style): rejected for regression value — it would not exercise the holder wiring inside the real function; used only as an extra guard test is unnecessary since the real fault points are reachable through `shutil.move`/`os.replace` patches.
- Global `pathlib.Path.unlink` patch with unconditional raise: rejected — it also hits `_quarantine_sidecar_files`'s unlink when sidecars exist and obscures which guard was tested.

## Implementation
### Target file
`tests/db/test_db_recovery.py`

### Procedure
1. Update `test_os_error_after_activation_with_failed_rollback_reports_non_serviceable` (`:996-1021`): assertion at 1020 changes from `result.action == "error"` to `result.action == "rollback_failed"`; `active_db_state == "non_serviceable"` unchanged (REQ-003, AC-2).
2. Add `test_activation_failure_after_replace_rolls_back_original` (new): tmp dir, corrupt live DB + valid backup carrying a `-wal` sidecar (fixture pattern of `test_restore_with_backup_wal_shm_sidecars` `:837+`), integrity `[HEALTHY(backup), HEALTHY(candidate), HEALTHY(post)]`, logical patched `(True, None)`, `shutil.move` patched with a **destination-selecting** side_effect that raises `OSError` only when the destination is the live-name sidecar and delegates every other call to the real `shutil.move` — the staged sidecar guarantees a real call after the completed `os.replace`, exercising the holder flip; assert `result.success is False`, `result.action == "error"`, `result.active_db_state == "preserved_original"`, live bytes equal the archived original content, and the corrupt archive glob `*_corrupt_*` is empty (the rollback consumes the archive via `os.replace(corrupt_archive, db_path)`, matching `test_post_activation_failure_rolls_back_the_original` `:962`) (AC-1).
   Verification correction (this cycle): the draft's `patch("shutil.move", side_effect=OSError(...))` is unworkable — `_stage_restore` itself calls `shutil.move` (`recovery_restore.py:110`) to stage the backup sidecars, so an unconditional global raise fails during staging, before activation. Destination-selecting side_effect is required. The draft's "corrupt archive remains" is also wrong for a *successful* rollback: the helper moves the archive onto the live name, so the archive name disappears and its content is the live database.
3. Add `test_partial_activation_removes_moved_sidecars_on_rollback` (new): backup carries both `-wal` and `-shm` sidecars; `shutil.move` side_effect delegates staging-destination calls to the real function, performs the first live-name move, and raises `OSError` on the second live-name move; assert after rollback: no candidate sidecar exists at live names (`Path(str(db_path) + "-wal")` and `-shm` absent), live main bytes are the archived original, and the corrupt archive glob `*_corrupt_*` is empty (consumed by the rollback replace) (AC-4, REQ-002).
4. The rollback verification of step 2 is covered by its live-bytes assertion inside step 2's assertions (live bytes) — no separate function (keeps function count small; radon baseline top B(12)).
5. Add `test_cleanup_staged_unlink_failure_does_not_escape` (new): backup carries a `-wal` sidecar (so `staged` is non-empty and "the other staged paths removed" is a real assertion), integrity `[HEALTHY(backup), CORRUPTION(candidate)]` so the flow fails at candidate verification and calls `_cleanup_staged`; patch `pathlib.Path.unlink` with a small helper side_effect that raises `OSError` only for the staged temp file name and delegates every other call to the real unlink; assert `_restore_from_backup` returns a `RecoveryResult` (`action == "restore_verify_failed"`) instead of raising, and the blocked file still exists while the other staged paths are removed (AC-3, REQ-004).
6. Append new tests after `test_wal_shm_sidecars_land_at_final_locations_after_activation` region, keeping existing fixtures/helpers reused; no changes to any other test function.

### Method
- Direct edit; reuse existing module fixtures (`mock_db_cfg`, `mock_sqlite_helper`) and tmp-dir patterns already in the file.

### Details
- Step 2/3 must not patch `os.replace` globally where the real rollback replace must run; only `shutil.move` is faulted there (the holder flip runs inside the real `_activate_candidate`).
- `shutil.move` side_effect is call-destination-keyed, not call-ordinal-keyed: staging (`recovery_restore.py:110`) performs real moves to staged names first, so a call-ordinal side_effect would fault the wrong call. Helper: capture `shutil_move_real = shutil.move` before patching; raise `OSError` only for destinations equal to a live-name sidecar (`str(db_path) + suffix`), delegate otherwise. Step 3 additionally counts live-name calls and raises on the second one.

## Compatibility considerations
- Only one existing assertion line changes (1020); all other `action == "error"` assertions belong to non-rollback paths (verified line list above).
- `tests/db/test_db_maintenance.py` imports `recover_corruption` and asserts action values; expected unchanged (Plan Reference Files).

## Security considerations
- Test-only; writes confined to pytest `tmp_path`; production-DB guard in conftest stays active.

## Rollback considerations
- Test-only file: revert by checkout. If the code document is reverted while these tests remain, steps 1-3 fail loudly (`action`/`active_db_state` mismatches) — the intended regression alarm.

## Validation plan
- Targeted: `uv run pytest tests/db/test_db_recovery.py -v` → all green only when the companion code document has landed (release unit gate).
- Regression: `uv run pytest tests/db -v` then full suite `uv run pytest -n auto`.
- Static: `uv run radon cc tests/db/test_db_recovery.py -s` (baseline top B(12); added functions stay small), `uv run bandit -r tests/db/test_db_recovery.py` (no new HIGH).

## Completion criteria
- AC-1, AC-2, AC-3, AC-4 of the plan are asserted by the new/updated tests; `tests/db` fully green with the companion document landed.

## Out of Scope
- Quarantine-record fixtures and whole-unit reassembly assertions (Plan 003 procedures, which reuse these fault-injection patterns and land after).
- The vec0 e2e tests added by Plan 001's procedure `20261115-075008_2_tests_db_test_db_recovery.py.md`.
- Any production-code change (companion document `_1`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-100836 | 20261115-100836 | 1 existing assertion updated (error->rollback_failed), 3 new failure tests appended |
| 2 | Add or update tests per Validation plan | Completed | 20261115-100836 | 20261115-100836 | AC-1..AC-4 covered; targeted run 80 passed; shutil.move destination-keyed correction applied during verification |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-100836 | 20261115-100836 | tests/db regression 403 passed; radon top C(13) pre-existing (test_restore_with_backup_wal_shm_sidecars), new funcs B(8); bandit test file 33 Medium (B101) unchanged, no new High; full suite N/A: not run per user instruction |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261115-100836 | 20261115-100836 | N/A: docs edits land in companion 20261115-080732_3 |

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
- **Requirement ID**: REQ-003, REQ-005
- **Source issue**: issues/done/20261114-092849_dbreview002_partial-activation-rollback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-035004_dbreview002_partial-activation-rollback.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-080732
- **Related target files**: tests/db/test_db_recovery.py