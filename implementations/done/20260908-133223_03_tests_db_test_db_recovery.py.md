## Goal

Add test coverage proving a wrong-domain backup is rejected before the live DB is
touched, returns a distinct `action` value, and leaves the live DB/directory
unchanged; confirm the two named pre-existing tests still pass (REQ-001, REQ-002,
REQ-003, REQ-004).

## Scope

In scope: three new test cases in `tests/db/test_db_recovery.py`, plus running the two
existing tests named by REQ-004 to confirm no regression. Out of scope: any change to
`scripts/db/recovery.py` or `scripts/db/models.py` themselves (tracked in the other two
documents from this same Plan).

## Assumptions

- Existing fixtures `mock_db_cfg` (`tests/db/test_db_recovery.py:10-23`) and
  `mock_sqlite_helper` (lines 26-30) are reused as-is; the new tests follow the same
  `with patch("scripts.db.recovery._run_integrity_check", ...)` plus
  `patch("scripts.db.recovery._verify_domain_identity", ...)` pattern already used by
  `test_recover_corrupt_rag_restores` (lines 44-64) and `test_recover_bad_backup`
  (lines 114-125) for `_run_integrity_check`.
- `_verify_domain_identity` (added in
  `implementations/20260908-133223_01_scripts_db_recovery.py.md`) is mocked directly
  in the new tests rather than exercised against a real SQLite file — consistent with
  every other `_restore_from_backup()` test in this file, all of which mock
  `SQLiteHelper`/the relevant check function rather than hitting a real database.

## Design decisions

Mock `scripts.db.recovery._verify_domain_identity` to return `(False, "...")` for the
rejection tests, and assert `result.action == "backup_wrong_domain"` plus
`result.success is False`. For the "live DB/directory unchanged" test (REQ-003),
assert that `shutil.copy2` and `os.replace` were never called — mirroring how
`test_recover_bad_backup` already proves no restore side effect occurs by never
patching/asserting on those calls happening, but made explicit here via
`mock.assert_not_called()` since REQ-003 specifically requires proving inaction.

## Alternatives considered

- Using a real temporary SQLite file with a different schema instead of mocking
  `_verify_domain_identity` — rejected: every other test in this file mocks at the
  `_run_integrity_check`/`SQLiteHelper` boundary rather than using real files: `pathlib.Path.exists`
  is also patched (e.g. line 53, line 121), so no test in this module touches a real
  filesystem path; introducing a real-file test here would be an inconsistent testing
  style for this file and would require new fixture setup/teardown machinery this file
  does not currently have.

## Implementation
### Target file
`tests/db/test_db_recovery.py`

### Procedure
1. Add `test_recover_wrong_domain_backup_rejected` — asserts `result.success is False`
   and `result.action == "backup_wrong_domain"` when `_run_integrity_check` reports
   healthy for both DB and backup but `_verify_domain_identity` returns `(False,
   "...")`.
2. Add `test_recover_wrong_domain_backup_distinct_action` — same setup, explicitly
   asserts `result.action not in ("no_backup", "bad_backup")` to make REQ-002's
   "distinct from `no_backup`/`bad_backup`" requirement directly checkable (in addition
   to test 1's positive assertion).
3. Add `test_recover_wrong_domain_backup_leaves_db_untouched` — same setup, additionally
   patches `shutil.copy2` and `os.replace` and asserts both were never called (REQ-003).
4. Run `uv run pytest tests/db/test_db_recovery.py::test_recover_corrupt_rag_restores
   tests/db/test_db_recovery.py::test_recover_bad_backup -v` to confirm no regression
   (REQ-004) — both already mock `SQLiteHelper` via `mock_sqlite_helper`, and neither
   patches `_verify_domain_identity`, so the real (patched-in) helper from Row 1 runs
   against the mocked `SQLiteHelper` instance; confirm during implementation that this
   does not require the two tests to also mock `_verify_domain_identity` explicitly (if
   it does, that is a Plan Gap to flag, not a change made silently — see `Out of scope`
   below).

### Method
```python
def test_recover_wrong_domain_backup_rejected(mock_db_cfg, mock_sqlite_helper):
    with (
        patch(
            "scripts.db.recovery._run_integrity_check",
            return_value=(DbCondition.HEALTHY, None),
        ),
        patch(
            "scripts.db.recovery._verify_domain_identity",
            return_value=(False, "backup missing required table 'sessions'"),
        ),
        patch("pathlib.Path.exists", return_value=True),
    ):
        result = recover_corruption(backup_path="/tmp/backup.db", target="session")

        assert result.success is False
        assert result.action == "backup_wrong_domain"


def test_recover_wrong_domain_backup_distinct_action(mock_db_cfg, mock_sqlite_helper):
    with (
        patch(
            "scripts.db.recovery._run_integrity_check",
            return_value=(DbCondition.HEALTHY, None),
        ),
        patch(
            "scripts.db.recovery._verify_domain_identity",
            return_value=(False, "backup missing required table 'sessions'"),
        ),
        patch("pathlib.Path.exists", return_value=True),
    ):
        result = recover_corruption(backup_path="/tmp/backup.db", target="session")

        assert result.action not in ("no_backup", "bad_backup")


def test_recover_wrong_domain_backup_leaves_db_untouched(mock_db_cfg, mock_sqlite_helper):
    with (
        patch(
            "scripts.db.recovery._run_integrity_check",
            return_value=(DbCondition.HEALTHY, None),
        ),
        patch(
            "scripts.db.recovery._verify_domain_identity",
            return_value=(False, "backup missing required table 'sessions'"),
        ),
        patch("pathlib.Path.exists", return_value=True),
        patch("shutil.copy2") as mock_copy2,
        patch("os.replace") as mock_replace,
    ):
        result = recover_corruption(backup_path="/tmp/backup.db", target="session")

        assert result.success is False
        mock_copy2.assert_not_called()
        mock_replace.assert_not_called()
```

### Details
- Place the three new tests immediately after `test_recover_bad_backup` (currently
  ending at line 125), keeping the file's existing test ordering (grouped by
  `_restore_from_backup()` scenario).
- `target="session"` is used in the example above to exercise a domain other than the
  file's dominant `"rag"` default, since the Plan's motivating scenario is
  `rag.sqlite` being replaced by a `session.sqlite` copy — however, since
  `_verify_domain_identity` is mocked directly (not exercising the real per-domain
  table-name mapping from Row 1), the specific `target` value is not load-bearing for
  these three tests; keep it as `"session"` for readability/traceability to the Plan's
  Reason for change, not because the mock depends on it.
- No new fixtures are needed — `mock_db_cfg` and `mock_sqlite_helper` (both already
  defined in this file) cover setup for all three new tests, matching every other test
  in the file.

## Compatibility considerations

N/A: test-only additions; no production code or public test fixture signature changes.

## Security considerations

N/A: no real filesystem, network, or credential access — all three new tests mock
`_run_integrity_check`, `_verify_domain_identity`, `pathlib.Path.exists`, and (for the
third test) `shutil.copy2`/`os.replace`, consistent with the rest of this file.

## Rollback considerations

Revert is a single-file test revert; no fixture or production code is shared
exclusively with these three tests, so reverting them has no effect beyond removing
their own coverage.

## Validation plan

- `uv run pytest tests/db/test_db_recovery.py -v` — all three new tests pass.
- `uv run pytest tests/db/test_db_recovery.py::test_recover_corrupt_rag_restores
  tests/db/test_db_recovery.py::test_recover_bad_backup -v` — both pass unchanged
  (REQ-004).
- Full validation sequence per `rules/toolchain.md`, including
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` on the
  changed lines across all three implementation-procedure documents from this Plan.

## Completion criteria

- `test_recover_wrong_domain_backup_rejected`,
  `test_recover_wrong_domain_backup_distinct_action`, and
  `test_recover_wrong_domain_backup_leaves_db_untouched` exist and pass.
- `test_recover_corrupt_rag_restores` and `test_recover_bad_backup` pass unchanged.
- No new failures in `uv run pytest tests/db/test_db_recovery.py -v`.

## Out of scope

Any change to `scripts/db/recovery.py` (Row 1) or `scripts/db/models.py` (Row 2)
themselves. If Procedure step 4's regression run reveals that
`test_recover_corrupt_rag_restores`/`test_recover_bad_backup` require an explicit
`_verify_domain_identity` mock to keep passing, that is a Plan Gap to report during
implementation (per `skills/plan-to-implementation-procedure/workflow.md` Step 3c),
not a change to make silently in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-08TXX:XX:XX | 2026-09-08TXX:XX:XX | Tests already applied by upstream |
| 2 | Add or update tests per Validation plan | Completed | — | — | All 3 tests present |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Upstream validated |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | No docs in scope |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260907-124049_h0703_backup_candidate_domain_identity_validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-072325_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-133223
- **Related target files**: tests/db/test_db_recovery.py
