## Goal

Add regression tests that a write to a temporary stand-in "production" directory is detected, that an unchanged and an absent directory pass, and that an opt-out test's own changes are not attributed to the session (`REQ-005`: regression tests; `REQ-002`: skip and opt-out).

## Scope

- Add tests to `tests/test_production_isolation.py` only; the existing guard tests stay unchanged.
- The helpers and fixture under test are created by procedure 01.

## Assumptions

- Plan overlaps: `tools/check_plan_target_overlaps.py` (2026-11-02) names no overlap for this Plan; no sibling Plan targets this file: compatible.
- Verified 2026-11-02: the file already imports `subprocess`, `sys`, `Path`, `pytest`, and imports `_cleanup_isolated_root` and `_production_file_handlers` lazily from `tests.conftest` inside tests; `test_opt_out_marker_skips_guard` and `test_conftest_imports_on_host_without_production_db_dir` (a child-process pattern) exist.
- The names `_PRODUCTION_DB_DIR`, `_fingerprint_directory`, `_changed_files`, `_refresh_db_baseline`, `_assert_production_db_unchanged`, and `_db_baseline` are created by procedure 01 (earlier `seq`) and exist when this row executes.
- The child-process test runs pytest with `-p tests.conftest` so the plugin hooks and fixtures load without the repository's own conftest discovery; this is untested today (Needs confirmation, non-blocking). If it proves impractical, keep the unit-level tests and record in the step Notes that the end-to-end teardown report (UNK-01) and the opt-out wiring were verified by the AC-6 full-suite run only.
- UNK-01 is resolved or confirmed open by the child-process test output.

## Design decisions

- Unit tests monkeypatch `tests.conftest._PRODUCTION_DB_DIR` and `_db_baseline` (`monkeypatch.setattr` restores both), so the real session baseline is never disturbed and nothing under `/opt/llm` is read.
- One child-process test per outcome covers the real fixture end to end: failure naming the file, and pass under the opt-out marker.

## Alternatives considered

- Driving the session fixture directly through its wrapped function: rejected, depends on pytest internals that differ by version.
- Using `pytester`: rejected, it is not enabled in the repository's conftest and would require a plugin entry.

## Implementation
### Target file
`tests/test_production_isolation.py`

### Procedure
1. Add helper `_stand_in(tmp_path, monkeypatch)` (new): create `tmp_path / "db"` with `a.sqlite` and `a.sqlite-wal`, monkeypatch `_PRODUCTION_DB_DIR` to it, call `_refresh_db_baseline()`, return the directory.
2. Add unit tests, each using the helper:
   - `test_unchanged_directory_passes` (new): `_assert_production_db_unchanged()` returns.
   - `test_changed_file_is_reported` (new): rewrite `a.sqlite`; `pytest.raises(pytest.fail.Exception, match="a.sqlite")`.
   - `test_sidecar_only_change_is_reported` (new): change only `a.sqlite-wal`; match `a.sqlite-wal`.
   - `test_added_file_is_reported` (new) and `test_removed_file_is_reported` (new).
   - `test_absent_directory_is_skipped` (new): monkeypatch the constant to a missing path, refresh (baseline `None`), assert no failure.
   - `test_refresh_accepts_prior_change` (new): change a file, call `_refresh_db_baseline()`, assert no failure (opt-out semantics).
   - `test_fingerprint_does_not_create_sidecars` (new): fingerprint a real SQLite file in the stand-in and assert the directory listing is unchanged afterwards.
3. Add child-process tests `test_session_fails_when_standin_changes` (new) and `test_opt_out_marker_does_not_fail_session` (new): write a small test module in `tmp_path` that imports `tests.conftest`, sets `_PRODUCTION_DB_DIR` to a stand-in at import time, and changes a file inside a test (unmarked in the first, `@pytest.mark.production_paths_allowed` in the second); run `sys.executable -m pytest -p tests.conftest -p no:cacheprovider` with `cwd` the repository root and `PYTHONPATH` set to it; assert a nonzero exit and the file name in the output for the first, exit 0 for the second.

### Method
- Reuse the module's existing `subprocess.run(..., capture_output=True, text=True, timeout=120, check=False)` shape from `test_conftest_imports_on_host_without_production_db_dir`.
- Import helpers lazily inside tests (`from tests import conftest as conftest_module`), as the file already does for `_cleanup_isolated_root`.

### Details
- Use only stand-in directories under `tmp_path`; never create files under `/opt/llm`.
- The child run changes a file only inside the stand-in, so it cannot touch production.

## Compatibility considerations

- N/A: new tests only; they restore all patched state through `monkeypatch`.

## Security considerations

- N/A: tests read and write only `tmp_path`; the child process uses the isolation root created by `tests.conftest`.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/test_production_isolation.py -v` (all pass), plus `-p no:randomly` once to check order independence.
- `uv run ruff format`, `uv run ruff check`, and `uv run mypy` on the file per `rules/toolchain.md`.

## Completion criteria

- Changed, added, removed, sidecar-only, unchanged, absent, and opt-out cases are covered and pass; the child-process outcomes match, or the Notes record why they were dropped.

## Out of Scope

- Cleaning contaminated rows; tests of non-database production paths; changes to the existing guard tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the stand-in helper and the unit tests | Completed | 20261102-093554 | 20261102-093618 | 3a: no correction. Changed: tests/test_production_isolation.py |
| 2 | Add the two child-process end-to-end tests (or record the fallback) | Completed | 20261102-093618 | 20261102-093618 | Child-process tests work with -p tests.conftest; UNK-01 resolved: teardown failure prints the message naming the file, exit nonzero |
| 3 | Run the test file and the validation sequence (`rules/toolchain.md`) | Completed | 20261102-093618 | 20261102-093618 | 20 passed (also randomized); ruff, bandit (low-only) clean; mypy only the pre-existing tests/conftest.py:339 error; full suite deferred to plan end |

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
- **Requirement ID**: `REQ-005` (regression tests for detection), `REQ-002` (skip when absent, opt-out)
- **Source issue**: issues/20261030-191351_flowimp006_suite-production-guard.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-075648_flowimp006_suite-production-guard.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-084616
- **Related target files**: `tests/test_production_isolation.py`