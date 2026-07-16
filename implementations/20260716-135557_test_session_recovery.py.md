# Implementation: tests/integration/test_session_recovery.py (new — real DB corruption + `recover_corruption()` integration tests, E01–E05)

Source plan: `plans/20260716-135105_plan.md`

## Goal

Add integration tests exercising `scripts/db/recovery.py::recover_corruption()`
against a real, physically-corrupted SQLite file (not `unittest.mock.MagicMock`,
which is all `tests/test_db_maintenance.py::TestRecoverCorruption` uses
today), plus a real `AgentSession` instance's behavior against both a
corrupted file and a real `BEGIN EXCLUSIVE` lock contention scenario.

## Scope

**In:**
- Create `tests/integration/test_session_recovery.py` with 5 test
  functions (E01–E05, per the source plan's Design §2 table):
  1. `test_e01_session_start_on_corrupted_db_raises` — `AgentSession(db_path=corrupt_wal_db).start()`
     raises `sqlite3.DatabaseError`/`OperationalError`, not a silent
     `session_id=None`.
  2. `test_e02_recover_corruption_restores_from_backup` — `recover_corruption(target=...)`
     against the corrupted file with a valid backup present; restored DB
     passes `PRAGMA integrity_check`; `AgentSession.start()` succeeds
     afterward.
  3. `test_e03_recover_corruption_no_backup_returns_no_backup_action` —
     same corrupted file, no backup available; returns
     `action="no_backup"`; does not raise; does not fabricate a fresh DB.
  4. `test_e04_recover_corruption_dry_run_does_not_mutate` — `dry_run=True`
     leaves the corrupted file's mtime/hash unchanged; still reports the
     correct integrity-check outcome.
  5. `test_e05_concurrent_session_start_under_exclusive_lock` — extends
     the existing TC-B02 pattern (`hold_write_lock`), but driven through
     `AgentSession.start()` itself rather than raw SQL, confirming the
     documented "no try/except, propagates" behavior is the actual
     behavior when exercised through the real class.

**Out:**
- Any modification to `tests/integration/test_session_sqlite.py` (TC-B01–B08)
  — read-only reference for patterns (`hold_write_lock`,
  `_build_session_memory_db`), not edited.
- Any modification to `scripts/db/recovery.py` or `scripts/agent/session.py`
  — this plan is test-only; if E01–E04 reveal a latent bug in
  `recover_corruption()`, per the source plan's Risk R-2, document the
  finding rather than fixing it in this test-only change.
- Any change to `tests/test_db_maintenance.py`'s existing mock-based
  `TestRecoverCorruption` tests — those remain as unit-level coverage;
  this new file adds integration-level coverage alongside them, not a
  replacement.

## Assumptions

1. `scripts/db/recovery.py::recover_corruption()` (93-125 lines, per the
   Explore sub-agent report used during planning) takes at minimum a
   `target` parameter (`"rag"` or `"session"`) and a `dry_run` flag —
   verify the exact function signature (parameter names, whether
   `backup_path` is a separate argument or resolved internally from
   config) by direct read of `scripts/db/recovery.py` before writing E02–E04;
   the source plan's Design section describes behavior but implementation
   must confirm exact call syntax.
2. `AgentSession`'s constructor accepts a `db_path` override — verify the
   exact signature by direct read of `scripts/agent/session.py` before
   writing E01/E05 (the source plan's Implementation Step 4 explicitly
   flags this as needing direct confirmation, since the Explore report
   read `AgentSession`'s methods but not its exact `__init__` signature).
3. The `corrupt_wal_db` fixture (companion doc,
   `implementations/20260716-135556_integration_conftest_new_fixtures.py.md`)
   must land first — this file's E01–E04 depend on it directly as a
   pytest fixture parameter.
4. For E02 ("valid backup present"), the exact backup-path convention
   `recover_corruption()` expects must be determined by direct read
   (e.g. a sibling file with a fixed suffix, or a path passed explicitly)
   — construct the test's backup file to match whatever convention the
   real function actually implements, not an assumed one.
5. `hold_write_lock()` (existing `conftest.py` fixture/helper, unchanged
   per Scope/Out) is reused as-is for E05 — no modification needed to that
   helper.

## Implementation

### Target file

`tests/integration/test_session_recovery.py` (new file)

### Procedure

1. Before writing any test, read `scripts/db/recovery.py` and
   `scripts/agent/session.py` in full to confirm:
   - `recover_corruption()`'s exact parameter list and return value shape
     (per the source plan's Explore findings: `action="no_backup"` is one
     known return field name; confirm the full return type, e.g. a
     dataclass or dict).
   - `AgentSession.__init__`'s exact parameters (confirm `db_path` is
     accepted, or determine the correct override mechanism — e.g. a
     module-level config patch, if the class does not take `db_path`
     directly).
2. Create the file with a module docstring:
   ```python
   """tests/integration/test_session_recovery.py

   Integration tests: Agent Session <-> SQLite, real corruption + recovery
   (TC-E01 through TC-E05).

   Companion to test_session_sqlite.py (TC-B01-B08, which covers WAL/busy
   -lock/FK/rollback but not physical corruption or recover_corruption()).
   Uses the corrupt_wal_db fixture (tests/integration/conftest.py) for a
   real, byte-truncated SQLite file rather than a MagicMock connection
   (see tests/test_db_maintenance.py::TestRecoverCorruption for the
   existing mock-based unit coverage this file complements).
   """

   from __future__ import annotations

   import shutil
   import sqlite3
   from pathlib import Path

   import pytest
   ```
3. Add `test_e01_session_start_on_corrupted_db_raises`:
   ```python
   def test_e01_session_start_on_corrupted_db_raises(corrupt_wal_db: str) -> None:
       from agent.session import AgentSession  # confirm exact import path

       session = AgentSession(db_path=corrupt_wal_db)  # confirm exact ctor signature
       with pytest.raises((sqlite3.DatabaseError, sqlite3.OperationalError)):
           session.start()
   ```
   (Adjust the constructor call per Assumption 2's confirmation step.)
4. Add `test_e02_recover_corruption_restores_from_backup`:
   ```python
   def test_e02_recover_corruption_restores_from_backup(
       corrupt_wal_db: str, tmp_path: Path
   ) -> None:
       from db.recovery import recover_corruption

       backup_path = str(tmp_path / "backup.sqlite")
       # Build a known-good backup using the same schema-building approach
       # as corrupt_wal_db's pre-corruption state (see conftest.py fixture).
       # (Exact construction depends on recover_corruption()'s expected
       # backup-path convention -- confirm via direct read, per Assumption 4.)
       good_conn = sqlite3.connect(backup_path)
       good_conn.execute("PRAGMA journal_mode=WAL")
       good_conn.commit()
       good_conn.close()

       result = recover_corruption(target="session", db_path=corrupt_wal_db, backup_path=backup_path)

       assert result.success or result.action != "no_backup"
       restored = sqlite3.connect(corrupt_wal_db)
       check = restored.execute("PRAGMA integrity_check").fetchone()
       assert check[0] == "ok"
       restored.close()
   ```
   (This skeleton's exact call signature and result-field names must be
   corrected against the real function per Assumption 1 before this test
   can pass — treat the above as a structural starting point, not a final
   implementation.)
5. Add `test_e03_recover_corruption_no_backup_returns_no_backup_action`:
   ```python
   def test_e03_recover_corruption_no_backup_returns_no_backup_action(
       corrupt_wal_db: str,
   ) -> None:
       from db.recovery import recover_corruption

       result = recover_corruption(target="session", db_path=corrupt_wal_db, backup_path=None)

       assert result.action == "no_backup"
   ```
6. Add `test_e04_recover_corruption_dry_run_does_not_mutate`:
   ```python
   def test_e04_recover_corruption_dry_run_does_not_mutate(
       corrupt_wal_db: str,
   ) -> None:
       from db.recovery import recover_corruption

       before_mtime = Path(corrupt_wal_db).stat().st_mtime
       before_size = Path(corrupt_wal_db).stat().st_size

       recover_corruption(target="session", db_path=corrupt_wal_db, dry_run=True)

       after_mtime = Path(corrupt_wal_db).stat().st_mtime
       after_size = Path(corrupt_wal_db).stat().st_size
       assert before_mtime == after_mtime
       assert before_size == after_size
   ```
7. Add `test_e05_concurrent_session_start_under_exclusive_lock`:
   ```python
   def test_e05_concurrent_session_start_under_exclusive_lock(
       tmp_path: Path,
   ) -> None:
       from tests.integration.conftest import hold_write_lock
       from agent.session import AgentSession

       db_path = str(tmp_path / "e05.sqlite")
       # Build a valid session schema first (see corrupt_wal_db fixture's
       # pre-corruption construction for the exact schema-building call).
       conn = sqlite3.connect(db_path)
       conn.execute("PRAGMA journal_mode=WAL")
       conn.commit()
       conn.close()

       lock_t = hold_write_lock(db_path, 1.0)
       try:
           session = AgentSession(db_path=db_path)
           with pytest.raises(sqlite3.OperationalError):
               session.start()
       finally:
           lock_t.join(timeout=3.0)
   ```

### Method

Five test functions, four consuming the new `corrupt_wal_db` fixture
(companion `conftest.py` doc) and one (`E05`) reusing the existing
`hold_write_lock` helper — all against real `sqlite3`/`AgentSession`
instances, no mocking, matching `test_session_sqlite.py`'s existing
"real connections" architecture.

### Details

- Every test skeleton above contains explicit "confirm exact signature"
  notes — resolve these against the actual source files
  (`scripts/db/recovery.py`, `scripts/agent/session.py`) before considering
  any test complete; do not guess at parameter names.
- If `AgentSession` does not accept a `db_path` constructor override at
  all (contrary to Assumption 2), fall back to whatever DB-path
  configuration mechanism the class actually uses (e.g. a module-level
  `SQLiteHelper` patch via `monkeypatch`, matching
  `test_session_sqlite.py`'s module docstring note about patching
  `SQLiteHelper._db_path` for its own TC-B04/B07/B08 tests) — adapt the
  test setup accordingly rather than forcing an incorrect constructor call.
- Per the source plan's Risk R-2: if any of E01–E04 reveals a genuine bug
  in `recover_corruption()` (e.g. it raises instead of returning
  `action="no_backup"`, or `dry_run=True` still mutates the file), do not
  silently adjust the test to match the buggy behavior — mark the test
  with a clear comment describing the discrepancy and flag it in the
  implementation's commit message / PR description as a follow-up
  candidate, per the source plan's explicit scope boundary (test-only,
  no production-code fixes in this change).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New tests pass | `uv run pytest tests/integration/test_session_recovery.py -v` | 5 passed (or documented findings per Details, if a real bug is discovered) |
| Real corruption confirmed | manual: inspect `corrupt_wal_db` fixture output during E01 | `sqlite3.connect()` succeeds, `integrity_check` fails (per companion conftest doc) |
| No leftover locked/corrupted files affect later tests | `uv run pytest tests/integration/ -v` (full directory, order-independence check) | all tests pass regardless of execution order (via `tmp_path` isolation) |
| Flakiness check | `for i in {1..5}; do uv run pytest tests/integration/test_session_recovery.py -v --timeout=30; done` | 5/5 clean runs |
| Lint | `uv run ruff check tests/integration/test_session_recovery.py` | 0 errors |
| Type check | `uv run mypy tests/integration/test_session_recovery.py` | no new errors |
| Existing suite unaffected | `uv run pytest tests/integration/test_session_sqlite.py tests/test_db_maintenance.py -v` | all existing tests still pass unchanged |
