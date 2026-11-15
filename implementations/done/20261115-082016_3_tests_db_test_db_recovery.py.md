## Goal
- Assert whole-unit reassembly on every restore failure branch and quarantine retention on success, and extend the staging helper tests to the returned records.

## Scope
**Release unit**: whole-unit-rollback-retention (Phase 3 of the plan; lands after `20261115-082016_1` and `20261115-082016_2`; Plan 002's procedures `20261115-080732_1/_2` already landed)

- In scope: `tests/db/test_db_recovery.py` — four new failure-branch tests plus one new helper self-rollback test, three flipped success assertions, one renamed test, extended helper tests (REQ-003, REQ-005), plus a verification row for the cleanup test landed by Plan 002 (Correction 2).
- Cross-plan overlap `tests/db/test_db_recovery.py` (shared with Plan 004): **compatible (sequencing)** — this document edits the quarantine-assertion tests (`:788-835`, `:1024-1063`, `:1438-1459`) and adds whole-unit failure tests; Plan 004's probe-invariance/MISSING tests are disjoint functions.

## Assumptions
- Re-anchored after this procedure landed: `test_restore_with_stale_wal_shm_before_swap` at `:834`, `test_wal_shm_sidecars_land_at_final_locations_after_activation` at `:1076`, `test_os_error_during_the_swap_removes_the_temp_restore_file` (`:1908`), `test_successful_restore_retains_the_quarantine_directory` (`:1942`, the renamed success-path cleanup test), helper tests at `:683`, `:757`, `:777` (new self-rollback test), `:815`.
- Verification correction (this cycle): `test_os_error_during_the_swap_removes_the_temp_restore_file` does NOT stay unchanged — its fixture has no live sidecars, so after `_1`'s mkdir deferral no quarantine directory is created at all (its `:1722` quarantine-kept assert would fail), and after `_2`'s quarantine-back the swap-failure path moves recorded pairs back and removes the emptied directory. The test must gain a live `-wal`/`-shm` fixture and flip `:1722` from "quarantine dir is kept" to whole-unit reassembly assertions (see step 5).
- Verification correction (this cycle): Plan 002's landed `test_activation_failure_after_replace_rolls_back_original` (asserts `not live_wal.exists()`) and `test_partial_activation_removes_moved_sidecars_on_rollback` (asserts both live sidecars absent) break under quarantine-back: the original sidecars are moved back to their live names. They are updated in step 4 to whole-unit byte assertions instead of a duplicated new function. Plan 002's post-activation rollback test (`:933`, no live-sidecar fixture) and its forced-unlink cleanup test stay green; AC-5 needs no new test (Correction 2).
- Live-sidecar fixtures follow `test_restore_with_stale_wal_shm_before_swap` (`:788-835`); backup-sidecar fixtures follow `test_restore_with_backup_wal_shm_sidecars` (`:837+`).

## Design decisions
- Whole-unit assertions use byte comparison (`read_bytes()`) for live main and each sidecar after every failure branch (AC-1), plus a live-directory file-set assertion that no candidate-origin file remains at any live name (AC-2).
- Renamed retention test keeps the original fixture and only inverts the final assertion plus checks `*_corrupt_*` copies inside the retained directory (AC-3).

## Alternatives considered
- One parametrized failure-branch test: rejected — each branch needs a different fault injection (integrity side_effect, logical patch, `shutil.move` patch), and separate functions keep radon baseline (top B(12)) and keep failure diagnosis local.
- Adding a new `_stage_restore` integration test: rejected for this document — `_stage_restore` has no test caller today and the plan's Tests section covers its record change through the `_quarantine_sidecar_files` helper tests; an integration test would duplicate `test_restore_with_backup_wal_shm_sidecars`.

## Implementation
### Target file
`tests/db/test_db_recovery.py`

### Procedure
1. Add `test_preactivation_integrity_failure_restores_whole_unit` (new): live DB with `-wal`/`-shm` fixture; integrity side_effect `[HEALTHY(backup), CORRUPTION(candidate)]`; assert live main plus both original sidecars are byte-identical, the quarantine directory is gone (pairs moved back), and `result.action == "restore_verify_failed"` with `active_db_state="preserved_original"` (AC-1).
2. Add `test_preactivation_logical_failure_restores_whole_unit` (new): same fixture; integrity `[HEALTHY, HEALTHY]`, `patch("db.recovery._run_logical_verification", return_value=(False, "counts mismatch"))`; assert the same whole-unit reassembly and `action == "logical_verify_failed"` (AC-1).
3. Add `test_postactivation_rollback_reassembles_whole_unit` (new): live DB with original `-wal`/`-shm` and backup with its own `-wal`/`-shm`; integrity side_effect `[HEALTHY, HEALTHY, CORRUPTION("post-activation")]`, logical patched `(True, None)`; after rollback assert: live main bytes are the archived original, the original sidecars are present byte-identically at live names (quarantine-back), no candidate sidecar remains at any live name (moved-sidecar removal landed by Plan 002), and the quarantine directory no longer holds those pairs (AC-1, AC-2).
4. Update (not new) Plan 002's two landed activation-failure tests to whole-unit assertions instead of adding a duplicate swap-failure reassembly test (the rejected test_swap_failure_rollback_reassembles_whole_unit — never created): in `test_activation_failure_after_replace_rolls_back_original` replace `assert not live_wal.exists()` with `live_wal.read_text() == "STALE_WAL_CONTENT"` (the quarantined original moved back) plus `assert not list(db_dir.glob("*_sidecar_quarantine_*"))` (moved back and the emptied directory removed); in `test_partial_activation_removes_moved_sidecars_on_rollback` replace the two "sidecar absent" asserts with byte-identity asserts against the stale originals at the live names — the moved candidate `-wal` is removed and the quarantined originals take its place (AC-1, AC-2; builds on Plan 002's holder).
5. Flip `test_restore_with_stale_wal_shm_before_swap` (`:834`) and `test_wal_shm_sidecars_land_at_final_locations_after_activation` (`:1076`) to quarantine retention. Update `test_os_error_during_the_swap_removes_the_temp_restore_file` (`:1908`): add a live `-wal`/`-shm` fixture (distinct content) and change its "quarantine dir is kept" assert to whole-unit reassembly — both sidecars byte-identical at live names and no `*_sidecar_quarantine_*` directory left (swap never completed, quarantine-back ran; see Assumptions correction). Rename the success-path cleanup test to `test_successful_restore_retains_the_quarantine_directory` (`:1942`) and add a live `-wal`/`-shm` fixture to it (without sidecars the deferred `mkdir` creates no directory at all, so the retention assert would have nothing to find), asserting the retained directory exists and contains the `*_corrupt_*` sidecar copies (REQ-003, AC-3).
6. Extend `test_quarantine_sidecar_files` (`:683`) to assert the returned records list (pairs of live name → quarantine path, correct names); `test_quarantine_sidecar_files_raises_on_copy_failure` (`:749`) behavior assertions unchanged (REQ-005).
7. Add `test_restore_without_sidecars_creates_no_quarantine_directory` (new): successful restore with no sidecars anywhere asserts no `*_sidecar_quarantine_*` directory exists (Plan Assumption: deferred `mkdir`).
8. Verify (no new test): Plan 002's landed forced-unlink cleanup test covers AC-5 (Correction 2).
9. Verification correction (landed during testing): add `test_quarantine_sidecar_files_self_rolls_back_mid_failure` (new) — live `-wal`/`-shm` fixture; patch `db.recovery_restore.shutil.copy2` to raise only for destinations containing `-shm_corrupt_` (second sidecar); assert the recorded `-wal` pair moved back byte-identically to its live name, `-shm` stayed in place untouched, and the emptied quarantine directory was removed (covers the self-rollback added to `_quarantine_sidecar_files` per companion `_1` step 4).

### Method
- Direct edit; reuse existing fixtures and tmp-dir patterns; write only under `tmp_path`.

### Details
- Byte-identity fixtures must write distinct content per sidecar so a cross-wired move-back is detectable.

## Compatibility considerations
- The three flipped assertions and one rename are the plan's documented assertion flips; every other test function in the file is untouched.
- Plan 001's appended vec tests and Plan 002's appended failure tests run unaffected (disjoint functions).

## Security considerations
- Test-only; production-DB guard in conftest stays active.

## Rollback considerations
- Test-only file: checkout revert. These tests fail loudly if `_1`/`_2` code is reverted (intended regression alarm).

## Validation plan
- Targeted: `uv run pytest tests/db/test_db_recovery.py -v` → green only with `_1`+`_2` landed (release unit gate).
- Regression: `uv run pytest tests/db -v`, then full suite `uv run pytest -n auto`; documented flips are the only expected assertion changes (plan Validation plan row).
- Static: `uv run radon cc tests/db/test_db_recovery.py -s` (baseline top B(12)), `uv run bandit -r tests/db/test_db_recovery.py` (no new HIGH).

## Completion criteria
- AC-1, AC-2, AC-3 asserted; helper tests extended; AC-5 confirmed via Plan 002's landed test.

## Out of Scope
- Retention lifetime/cleanup scheduling (Plan 008).
- The `_cleanup_staged` implementation (landed by Plan 002).
- Docs text (companions `_4`, `_5`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-104412 | 20261115-104412 | 5 tests landed (whole-unit x2 pre-activation, post-activation reassembly, renamed retention test, no-quarantine-dir test); 2 existing tests updated correction landed: self-rollback test added (step 9); stale tokens cleared; anchors re-anchored post-landing |
| 2 | Add or update tests per Validation plan | Completed | 20261115-104412 | 20261115-104412 | 84 passed test_db_recovery.py; tests/db 407 passed (full suite N/A: not run per user instruction) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-104412 | 20261115-104412 | changed tests all rank B or better; pre-existing C(13)/C(14) test functions untouched |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261115-104412 | 20261115-104412 | N/A for this file: docs handled by companion procedures _4/_5 |

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
- **Requirement ID**: REQ-003, REQ-005 (and REQ-004 verification per Correction 2)
- **Source issue**: issues/done/20261114-092850_dbreview003_restore-sidecar-handling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-041125_dbreview003_restore-sidecar-handling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-082016
- **Related target files**: tests/db/test_db_recovery.py