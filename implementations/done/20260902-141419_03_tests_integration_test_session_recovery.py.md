## Goal
Satisfy `REQ-001`/`REQ-005`: add an integration test proving an `UNKNOWN`
classification on the `session` target preserves the session DB file unmodified and
does not invoke `_restore_from_backup()`.

## Scope
Add exactly one new test function to `tests/integration/test_session_recovery.py`,
alongside the existing `test_e01`..`test_e05` functions. No existing test function
in this file is modified.

## Assumptions
- **Noted 2026-09-02** (Plan Note, added during `plan-to-implementation-procedure`):
  this file has 3 pre-existing, unrelated failing tests (`test_e02`, `test_e03`,
  `test_e04`) documenting a different, already-fixed bug's stale assertions. This
  row's new test is added independently and does not depend on or interact with
  those three.
- Genuinely triggering `DbCondition.UNKNOWN` via a real, physically-corrupted SQLite
  file is impractical (real corruption classifies as `CORRUPTION`, as `test_e01`-
  `test_e04` already demonstrate) — this test uses a real session DB file (via
  `_patch_db_config`, matching this file's established integration-test style) but
  mocks `db.recovery._run_integrity_check`'s return value to force `UNKNOWN`,
  isolating the assertion to "does the file survive untouched", which is the
  file-level, integration-relevant behavior this row is meant to verify (unlike
  seq 02's unit test, which verifies the branch logic itself).

## Design decisions
Use a real file on disk (read its bytes before and after) rather than mocking
`_restore_from_backup` only — proves the file is untouched at the filesystem level,
which is the specific integration-level guarantee REQ-001 makes for `session`.

## Alternatives considered
Mocking `_restore_from_backup` and asserting `assert_not_called()` only (same
approach as seq 02's unit test) — rejected as redundant with seq 02; this file's own
stated purpose (module docstring: "real, byte-truncated SQLite file rather than a
MagicMock connection") calls for a real-file-level assertion instead.

## Implementation
### Target file
tests/integration/test_session_recovery.py

### Procedure
Add `test_e06_recover_corruption_unknown_preserves_session_db`.

### Method
1. Locate the end of the existing `test_e05_concurrent_session_start_under_exclusive_lock`
   function (or any point after `test_e01`-`test_e05`).
2. Add:
   ```python
   def test_e06_recover_corruption_unknown_preserves_session_db(
       monkeypatch: pytest.MonkeyPatch, tmp_path: Path
   ) -> None:
       """UNKNOWN classification preserves the session DB file untouched."""
       from unittest.mock import patch

       from db.recovery import DbCondition, recover_corruption

       session_db = tmp_path / "session.sqlite"
       original_bytes = b"not a real sqlite file, but presence/content is what matters"
       session_db.write_bytes(original_bytes)
       _patch_db_config(monkeypatch, tmp_path, str(session_db))

       with patch(
           "db.recovery._run_integrity_check",
           return_value=(DbCondition.UNKNOWN, "simulated unclassifiable failure"),
       ):
           with patch("db.recovery._restore_from_backup") as mock_restore:
               result = recover_corruption(target="session")

       mock_restore.assert_not_called()
       assert result.success is False
       assert result.action == "unknown_preserved"
       assert session_db.read_bytes() == original_bytes
   ```

### Details
`_patch_db_config` (module-level helper, line 32) is reused unchanged — it already
points both `db.helper.build_db_config` and `db.recovery.build_db_config` at a
`DbConfig` built from `tmp_path`, matching this file's established pattern for
`test_e01`-`test_e05`.

## Compatibility considerations
Test-only change; no production code behavior affected by this row.

## Security considerations
N/A: test file, no production code path.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- `uv run pytest tests/integration/test_session_recovery.py -k e06` — passes after seq 01 lands.
- `uv run pytest tests/integration/test_session_recovery.py` — no *new* failures (the 3 pre-existing `test_e02`/`test_e03`/`test_e04` failures are baseline, unrelated to this row — see Plan Note).

## Completion criteria
The new test passes, confirming the session DB file's bytes are unchanged and
`_restore_from_backup` was never invoked for an `UNKNOWN` classification.

## Out of scope
`scripts/db/recovery.py` (seq 01), `tests/db/test_db_maintenance.py` (seq 02), and
`docs/adr/ADR-008-sqlite-4db-separation.md` (seq 04) — each covered by its own
implementation procedure document for this same Plan. Fixing `test_e02`/`test_e03`/
`test_e04`'s pre-existing, unrelated stale assertions — recommended as a separate
follow-up issue (see Plan Note), not this row's scope. This row must land after
seq 01.

## Documentation
Not a `docs/*.md` file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_e06_recover_corruption_unknown_preserves_session_db` per Method | Pending | — | — | Depends on seq 01 landing first |
| 2 | Run validation sequence | Pending | — | — | 3 pre-existing unrelated failures expected (Plan Note) |
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
- **Requirement ID**: REQ-001, REQ-005 (integration test for UNKNOWN on session DB)
- **Source issue**: `issues/20260831-181721_adr008_01_recover_corruption_unknown_classification_gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-111916_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-141419
- **Related target files**: `tests/integration/test_session_recovery.py`
