## Goal

Add the tests that lock the new retention behavior: `ArtifactRetentionConfig` value semantics, the four-sweep matrix in `purge_archive_artifacts`, the `resolve_unique_path` unit cases, and the rotation same-second collision fix (REQ-006; AC-1..AC-6).

## Scope
**Release unit**: retention-sweeps-and-drill-lifecycle

- In scope: new test cases added to the existing `tests/db/test_db_maintenance.py` (1596 lines).
- Out of scope: drill lifecycle tests (companion of row 6); recovery naming re-runs live in `test_db_recovery.py` (not a plan row).

## Assumptions
- Anchors re-verified 2026-11-16. `test_db_maintenance.py` already exercises `_archive_db_file` and the corrupt-retention/config layer; it has no retention-sweep tests for archives/drills/quarantine (grep this cycle). The symbols under test — `ArtifactRetentionConfig`, `purge_archive_artifacts`, `_STALE_WORK_FILE_MAX_AGE_SECONDS` (row 1) and `resolve_unique_path` (row 2) — are created by earlier-`seq` siblings.
- Tests use tmp directories seeded with synthetic files (and `os.utime` to age them); no production DB or archive path is touched.

## Design decisions
- Test the sweep contract, not internals: seed N files/dirs per class with controlled `mtime`, run the sweep, assert survivors by the age-then-count rule with the most-recent-per-source-DB protected.
- Boundary tests mirror the landed 007 semantics (`0` disables a single limit, negative → `ValueError`, bool rejected) so the new config behaves like `CorruptArchiveRetentionConfig`.

## Alternatives considered
- Testing the private sweep helpers directly — rejected: assert through the `purge_archive_artifacts` entry point so the contract is what is protected.

## Implementation
### Target file
`tests/db/test_db_maintenance.py`

### Procedure
1. Config-boundary tests for `ArtifactRetentionConfig.from_config`: defaults when keys absent; `0` disables only the matching limit; negative → `ValueError`; bool → rejected (AC-1).
2. `resolve_unique_path` unit tests: free name unchanged; first collision → `_2`, next → `_3`; a directory path handled the same; cap → `RuntimeError` (AC-6).
3. Four-sweep matrix on seeded tmp dirs:
   - archives (`sqlite_archive_dir`): 15 seeded archives per domain → age 30d then count 14, newest per source DB never deleted; a `{stem}_corrupt_*` file and a non-matching name are never touched (AC-2).
   - drill JSON (`<archive>/drills`): `{domain}_{ts}.json` per domain bounded by age 30d then count 14 (AC-3).
   - quarantine dirs (`{stem}_sidecar_quarantine_*` in a DB dir): age 90d then count 10, newest per DB kept; a non-matching directory and stray live files are untouched (AC-4).
   - stale work leftovers: a `{stem}.tmp_*{suffix}` file and a `*_restored{suffix}` file older than `_STALE_WORK_FILE_MAX_AGE_SECONDS` are removed; younger ones kept (AC-5).
4. Rotation same-second collision test: two `_archive_db_file` calls forced to the same second yield two distinct archive files (AC-6).

### Method
- Seed files with `os.utime` to control age; assert survivors and deletion counts via the `MaintenanceResult.data` counts and directory contents.

### Details
- Use `MaintenanceMode.STRICT` for the ValueError-propagation cases and `BEST_EFFORT` for the partial-count case, matching the 006 mode contract in row 1.

## Compatibility considerations
- Additive tests only; existing assertions in the file are unchanged. Re-read landed 006/007 test patterns before appending to avoid fixture clashes.

## Security considerations
- Include the AC-4 assertions that a non-matching directory and live files survive the quarantine sweep — the recursive-delete safety guard is exercised here.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py -v`; then `uv run pytest tests/db tests/agent -v`; `uv run ruff check` on the test file; diff-cover ≥ 90% on the branch diff.

## Completion criteria
- Every AC-1..AC-6 behavior above has a passing test, including never-delete-most-recent, `_corrupt_`/non-matching exclusion, `0`/negative/bool config boundaries, and the two-archive collision outcome.

## Out of Scope
- Drill `_restored` lifecycle tests (companion, row 6).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add config-boundary, uniquifier, four-sweep, and rotation-collision tests | Completed | 20261116-195234 | — |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) incl. diff-cover | Completed | 20261116-195856 | 20261116-195856 | tests/db + tests/agent + full suite green; diff-cover 97% >= 90 |

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
- **Requirement ID**: REQ-006 (tests for retention config, four sweeps, and collision-safe naming)
- **Source issue**: issues/20261114-092857_dbreview008_artifact-retention-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-054021_dbreview008_artifact-retention-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-144812
- **Related target files**: `tests/db/test_db_maintenance.py`