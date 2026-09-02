## Goal
Satisfy `REQ-001`/`REQ-005`: add a unit test proving `DbCondition.UNKNOWN` does not
trigger `_restore_from_backup()` and returns `action="unknown_preserved"`.

## Scope
Add exactly one new test method to `TestRecoverCorruption` (line 487) in
`tests/db/test_db_maintenance.py`. No existing test in this file is modified.

## Assumptions
- `db.recovery._run_integrity_check` can be mocked directly to return
  `(DbCondition.UNKNOWN, "some detail")`, matching Plan `T-001`'s specified
  approach — simpler than driving an actual exception through `_classify_error()`.

## Design decisions
Mock `_run_integrity_check` directly rather than simulating a real exception
through `SQLiteHelper` — isolates this test to `recover_corruption()`'s branch
logic (the row under test), not `_classify_error()`'s exception-mapping logic
(explicitly out of scope per Plan Scope Out-of-Scope: "Changing `_classify_error()`
logic").

## Alternatives considered
Simulating an unrecognized exception type through the real `_run_integrity_check` /
`_classify_error` path (e.g., a mock raising a bare `Exception`) — rejected as more
indirect than needed; mocking `_run_integrity_check`'s return value directly tests
`recover_corruption()`'s own branch, which is this row's actual target.

## Implementation
### Target file
tests/db/test_db_maintenance.py

### Procedure
Add `test_unknown_condition_preserves_db_and_does_not_restore` to
`TestRecoverCorruption`.

### Method
1. Locate `class TestRecoverCorruption:` (line 487) and its existing
   `test_dry_run_returns_recovery_result` method (line 512) as the pattern to
   follow (same `_patch_build_db_config` autouse fixture already applies).
2. Add, after `test_restore_from_backup` (line 626-654) or any convenient point in
   the class body:
   ```python
       def test_unknown_condition_preserves_db_and_does_not_restore(
           self, monkeypatch: pytest.MonkeyPatch
       ) -> None:
           """UNKNOWN classification is preserved, not treated as CORRUPTION."""
           from unittest.mock import patch

           with patch(
               "db.recovery._run_integrity_check",
               return_value=(DbCondition.UNKNOWN, "unrecognized failure"),
           ):
               with patch("db.recovery._restore_from_backup") as mock_restore:
                   result = recover_corruption(target="rag")

           mock_restore.assert_not_called()
           assert result.success is False
           assert result.action == "unknown_preserved"
   ```
3. Confirm `DbCondition` is already imported in this test file (used elsewhere in
   the same class per Plan evidence) — if not, add
   `from db.recovery import DbCondition` alongside the existing `recover_corruption`
   import.

### Details
This test does not need the `tmp_path`/`db_file` setup used by
`test_restore_from_backup`, since `_run_integrity_check` is mocked directly and
`_restore_from_backup` is also mocked (never actually called) — no real file I/O
occurs.

## Compatibility considerations
Test-only change; no production code behavior affected by this row.

## Security considerations
N/A: test file, no production code path.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py -k unknown` — passes after seq 01 lands (this test's `action == "unknown_preserved"` assertion depends on seq 01's new branch).
- `uv run pytest tests/db/test_db_maintenance.py` — full file passes, no new failures.

## Completion criteria
The new test passes and asserts both that `_restore_from_backup` is never called
and that the result communicates `action="unknown_preserved"`.

## Out of scope
`scripts/db/recovery.py` (seq 01), `tests/integration/test_session_recovery.py`
(seq 03), and `docs/adr/ADR-008-sqlite-4db-separation.md` (seq 04) — each covered by
its own implementation procedure document for this same Plan. This row must land
after seq 01.

## Documentation
Not a `docs/*.md` file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_unknown_condition_preserves_db_and_does_not_restore` per Method | Pending | — | — | Depends on seq 01 landing first |
| 2 | Run validation sequence | Pending | — | — | |
| 3 | N/A: no further test needed (this row is itself the test) | Pending | — | — | N/A |
| 4 | Documentation update | Pending | — | — | N/A: test file |

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
- **Requirement ID**: REQ-001, REQ-005 (unit test for UNKNOWN classification)
- **Source issue**: `issues/20260831-181721_adr008_01_recover_corruption_unknown_classification_gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-111916_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-141419
- **Related target files**: `tests/db/test_db_maintenance.py`
