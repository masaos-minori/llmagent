## Goal

Update `tests/db/test_session_consistency.py` for the deleted write smoke test: drop the
`write_smoke_test_ok` assertions, replace the now-obsolete cleanup test with a no-mutation
characterization test, and add a spy asserting no INSERT/DELETE executes during
`check_session_consistency()`.

## Scope
**Release unit**: session report contract removal

## Assumptions

- The write smoke test is deleted in `scripts/db/session_consistency.py` (seq 01) and the
  field in `scripts/db/models.py` (seq 02). These test edits must land in the same commit as
  those source edits; otherwise they assert a field that no longer exists.
- The read-only probes remain, so healthy-DB assertions still hold: `session_diagnostics_readable`
  and `read_smoke_test_ok` are still `True` on a healthy DB.
- `_FakeSQLiteHelper` (L18-L30) wraps a real in-memory `sqlite3.Connection`, so a spy can be
  installed on `conn.execute` to observe the SQL text.

## Design decisions

- Replace `test_write_smoke_test_cleans_up` with a whole-path no-mutation test rather than
  deleting it: the plan's Tests section requires a characterization test that snapshots
  `session_diagnostics` row count and contents before/after and asserts equality, plus a spy
  that no INSERT/DELETE executes. This directly covers AC-001/REQ-001.

## Alternatives considered

- Deleting `test_write_smoke_test_cleans_up` versus replacing it with a no-mutation test.
  Chose replacement: the plan explicitly requires a no-mutation characterization test, and
  the old test's intent ("the check leaves no residue") is preserved under the read-only
  contract.

## Implementation
### Target file
`tests/db/test_session_consistency.py`

### Procedure
1. In `test_all_checks_pass_on_healthy_db`: delete the assertion at L124:
   ```python
   assert report.write_smoke_test_ok is True
   ```
   Keep the surrounding healthy-DB assertions (`session_diagnostics_readable is True`,
   `read_smoke_test_ok is True`).
2. Replace `test_write_smoke_test_cleans_up` (current L146-L153) with a no-mutation
   characterization test:
   ```python
   def test_check_consistency_leaves_database_unchanged(self):
       """check_session_consistency() performs no INSERT/UPDATE/DELETE and leaves residue behind."""
       db = _make_session_db()
       before_rows = db.execute(
           "SELECT * FROM session_diagnostics ORDER BY id"
       ).fetchall()
       before_count = db.execute(
           "SELECT COUNT(*) FROM session_diagnostics"
       ).fetchone()[0]

       inserted_or_deleted = []

       original_execute = db.conn.execute

       def _spy_execute(sql, params=()):
           stmt = sql.strip().upper()
           if any(stmt.startswith(kw) for kw in ("INSERT", "DELETE", "UPDATE")):
               inserted_or_deleted.append(sql)
           return original_execute(sql, params)

       db.conn.execute = _spy_execute
       try:
           report = check_session_consistency(db)
       finally:
           db.conn.execute = original_execute

       after_rows = db.execute(
           "SELECT * FROM session_diagnostics ORDER BY id"
       ).fetchall()
       after_count = db.execute(
           "SELECT COUNT(*) FROM session_diagnostics"
       ).fetchone()[0]

       assert report.sessions >= 0
       assert before_count == after_count
       assert before_rows == after_rows
       assert inserted_or_deleted == []
   ```
3. Confirm no other test references `write_smoke_test_ok` or `_check_write_smoke_test`.
4. Grep the file for `write_smoke_test_ok` and confirm zero remaining references.

### Method
Remove two assertions, replace one obsolete test with a no-mutation characterization test
using a spy on the wrapped connection. No new module-level symbol.

### Details
- The spy installs on `db.conn.execute` (the underlying `sqlite3.Connection`), which every
  query in `check_session_consistency()` flows through via `_FakeSQLiteHelper.execute`. Any
  INSERT/UPDATE/DELETE is recorded; a fully read-only path records nothing.
- `before_rows == after_rows` asserts byte-level equality of the diagnostics table, covering
  AC-001's "row-count snapshot before and after ... identical".
- This test must run against the post-seq-01 code where the write probe is gone; on the old
  code it would fail because the spy would record the throwaway INSERT/DELETE.

## Compatibility considerations
Test-only change. The new no-mutation test asserts the read-only contract (AC-001/REQ-001)
and must pass only after seq 01 deletes the write probe. The consumer regression suite
(`tests/agent/`) must stay green.

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_session_consistency.py` — healthy-DB, no-content, missing-table,
  and the new no-mutation/spy tests.
- `uv run pytest tests/db/test_db_recovery.py -k "session"` — remaining trigger semantics (seq 05).
- `uv run lint-imports` (0 broken contracts), `uv run ruff check .`, `uv run mypy scripts/`.

## Completion criteria
- No test asserts `report.write_smoke_test_ok`.
- A no-mutation characterization test asserts identical `session_diagnostics` contents and
  row count before/after `check_session_consistency()`.
- A spy asserts no INSERT/UPDATE/DELETE statement executes during the check.

## Out of Scope
The source removal (`scripts/db/session_consistency.py`, seq 01), the field removal
(`scripts/db/models.py`, seq 02), the recovery trigger tests (seq 05), and the doc wording
(seq 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Assertion removal + no-mutation test. |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document is the test change. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docs only (seq 06). |

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
- **Requirement ID**: `REQ-001` (no mutation), `REQ-004` (read-only probe behavior, no residue)
- **Source issue**: issues/20261104-143443_sessmoke001_atomic-session-smoke-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-230832_sessmoke001_atomic-session-smoke-test.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-161823
- **Related target files**: tests/db/test_session_consistency.py
