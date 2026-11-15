## Goal
- Assert whole-unit reassembly on every restore failure branch and quarantine retention on success, and extend the staging helper tests to the returned records.

## Scope
**Release unit**: whole-unit-rollback-retention (Phase 3 of the plan; lands after `20261115-082016_1` and `20261115-082016_2`; Plan 002's procedures `20261115-080732_1/_2` already landed)

- In scope: `tests/db/test_db_recovery.py` — four new failure-branch tests, three flipped success assertions, one renamed test, extended helper tests (REQ-003, REQ-005), plus a verification row for the cleanup test landed by Plan 002 (Correction 2).
- Cross-plan overlap `tests/db/test_db_recovery.py` (shared with Plan 004): **compatible (sequencing)** — this document edits the quarantine-assertion tests (`:788-835`, `:1024-1063`, `:1438-1459`) and adds whole-unit failure tests; Plan 004's probe-invariance/MISSING tests are disjoint functions.

## Assumptions
- Baseline this cycle: `test_restore_with_stale_wal_shm_before_swap` assert at `:834` (`assert len(quarantine_dirs) == 0`), `test_wal_shm_sidecars_land_at_final_locations_after_activation` assert at `:1063` (`assert not list(db_dir.glob("*_sidecar_quarantine_*"))`), `test_os_error_during_the_swap_removes_the_temp_restore_file` keeps the quarantine at `:1436` (stays unchanged — OSError path already retains it), `test_successful_restore_removes_the_quarantine_directory` (`:1438`, assert at `:1459`) (all checked this cycle).
- Plan 002's landed tests (its post-activation rollback test etc.) and its forced-unlink cleanup test remain green; AC-5 needs no new test (Correction 2).
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
4. Add `test_swap_failure_rollback_reassembles_whole_unit` (new): reuse Plan 002's pattern (`shutil.move` side_effect delegates first move, raises on second) with live-sidecar fixture; assert whole-unit reassembly and `active_db_state="preserved_original"` (AC-1, AC-2; builds on Plan 002's holder).
5. Flip `test_restore_with_stale_wal_shm_before_swap` (`:834`), `test_wal_shm_sidecars_land_at_final_locations_after_activation` (`:1063`), and rename `test_successful_restore_removes_the_quarantine_directory` (`:1438`) to `test_successful_restore_retains_the_quarantine_directory` (new), asserting the retained directory exists and contains the `*_corrupt_*` sidecar copies (REQ-003, AC-3). `test_os_error_during_the_swap_removes_the_temp_restore_file` (`:1436`) stays unchanged.
6. Extend `test_quarantine_sidecar_files` (`:683`) to assert the returned records list (pairs of live name → quarantine path, correct names); `test_quarantine_sidecar_files_raises_on_copy_failure` (`:749`) behavior assertions unchanged (REQ-005).
7. Add `test_restore_without_sidecars_creates_no_quarantine_directory` (new): successful restore with no sidecars anywhere asserts no `*_sidecar_quarantine_*` directory exists (Plan Assumption: deferred `mkdir`).
8. Verify (no new test): Plan 002's landed forced-unlink cleanup test covers AC-5 (Correction 2).

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
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-005 (and REQ-004 verification per Correction 2)
- **Source issue**: issues/done/20261114-092850_dbreview003_restore-sidecar-handling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-041125_dbreview003_restore-sidecar-handling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-082016
- **Related target files**: tests/db/test_db_recovery.py
