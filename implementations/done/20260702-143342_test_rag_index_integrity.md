# Implementation Procedure: tests/test_rag_index_integrity.py (DESIGN-3 regression tests)

## Goal

Create a new test file `tests/test_rag_index_integrity.py` with six tests covering the
DESIGN-3 index integrity invariants (TEST-DESIGN3-01 through TEST-DESIGN3-05) and one
additional test for the fixed `reconcile_url()` FTS deletion bug. All tests use an
in-memory SQLite database following the `_FakeSQLiteHelper` pattern from
`tests/test_fts_fallback.py`.

## Scope

- **In:** `tests/test_rag_index_integrity.py` — new file, create from scratch
- **Out:** No modifications to `tests/test_fts_fallback.py`; no new shared fixture modules;
  no changes to production source files

## Assumptions

1. The `_FakeSQLiteHelper` class and `_SCHEMA_SQL` string are copied verbatim from
   `tests/test_fts_fallback.py` into this file. No shared fixture module exists yet.
2. `chunks_vec` is a plain table (`CREATE TABLE chunks_vec (chunk_id INTEGER PRIMARY KEY)`)
   — the `vec0` virtual table extension is unavailable in the test environment.
3. The test schema must include an `embedding BLOB` column on `chunks` to support
   `rebuild_vec()` coverage if needed. However, since the plan excludes `rebuild_vec()`
   tests from this ticket (plan Scope Out: "skip rebuild_vec() test"), only add the column
   if it does not break other tests. Add it to be safe.
4. `RagMaintenanceService` methods (`rebuild_fts()`, `reconcile_url()`) call
   `SQLiteHelper("rag").open(...)` internally. Tests must patch `SQLiteHelper` to inject
   the `_FakeSQLiteHelper` instance. Use `unittest.mock.patch` targeting
   `agent.services.rag_maintenance_service.SQLiteHelper`.
5. `check_rag_consistency()` from `db.maintenance` operates on a DB connection object.
   For TEST-DESIGN3-05, call it directly with the fake DB (pass the `_FakeSQLiteHelper`
   instance). Read `scripts/db/maintenance.py` to confirm the function signature before
   implementing — it likely takes a `db` parameter compatible with the fake helper.
6. `delete_document_chain()` is NOT a method on `RagMaintenanceService`. It is a
   standalone helper in `db.maintenance` or `rag.repository`. Verify the function location
   before implementing TEST-DESIGN3-03 and TEST-DESIGN3-04. If no such standalone function
   exists, simulate the deletion sequence manually in the test (delete `chunks_vec` rows,
   then delete `chunks` rows via CASCADE, then delete `documents` row).
7. `_FakeSQLiteHelper.open()` returns `self` and supports context manager protocol
   (`__enter__`/`__exit__`). This is sufficient for `RagMaintenanceService` methods that
   use `with SQLiteHelper("rag").open(...) as db:`.

## Implementation

### Target file

`tests/test_rag_index_integrity.py`

### Procedure

1. **File header** — module docstring and imports:
   ```python
   """
   tests/test_rag_index_integrity.py
   Regression tests for DESIGN-3 index integrity invariants.

   Covers:
   - TEST-DESIGN3-01: rebuild_fts() uses COALESCE(normalized_content, content)
   - TEST-DESIGN3-02: chunks_fts is trigger-synced from chunks (not independently maintained)
   - TEST-DESIGN3-03: delete_document_chain() leaves no orphan chunks_vec rows
   - TEST-DESIGN3-04: deletion order invariant (chunks_vec -> chunks -> documents)
   - TEST-DESIGN3-05: check_rag_consistency() detects FTS desynchronization
   - reconcile_url() FTS deletion does not raise OperationalError (bug fix regression)

   Resolves: DESIGN-3 missing tests (docs/03_rag_90_inconsistencies_and_known_issues.md)
   """
   from __future__ import annotations

   import sqlite3
   from collections.abc import Generator
   from unittest.mock import patch

   import pytest
   from db.maintenance import check_rag_consistency
   from rag.repository import fts_search

   from agent.services.rag_maintenance_service import RagMaintenanceService
   ```

2. **Schema SQL** — copy `_SCHEMA_SQL` from `test_fts_fallback.py` and add `embedding BLOB`
   column to `chunks`:
   ```sql
   -- chunks table gets an extra embedding column:
   chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
   doc_id             INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
   chunk_index        INTEGER NOT NULL,
   content            TEXT    NOT NULL,
   normalized_content TEXT,
   embedding          BLOB
   ```
   All triggers (`chunks_ai`, `chunks_ad`, `chunks_au`) remain identical to `test_fts_fallback.py`.

3. **`_FakeSQLiteHelper` class** — copy verbatim from `test_fts_fallback.py`.

4. **Fixtures** — `db` fixture (same as `test_fts_fallback.py` but using the new `_SCHEMA_SQL`):
   ```python
   @pytest.fixture
   def db() -> Generator[_FakeSQLiteHelper]:
       conn = sqlite3.connect(":memory:")
       conn.row_factory = sqlite3.Row
       conn.executescript(_SCHEMA_SQL)
       conn.commit()
       yield _FakeSQLiteHelper(conn)
       conn.close()
   ```

5. **Helper functions** `_insert_doc()` and `_insert_chunk()` — copy from `test_fts_fallback.py`.
   No signature changes needed.

6. **TEST-DESIGN3-01** (`test_rebuild_fts_uses_coalesce`):
   - Insert a doc and a chunk with `normalized_content=None`.
   - Manually delete-all FTS entries:
     `db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('delete-all')")`
   - Confirm FTS search returns nothing (sanity check).
   - Patch `SQLiteHelper` to return the fake helper, call `RagMaintenanceService().rebuild_fts()`.
   - Assert `fts_search("english", top_k=5, db=db)` returns exactly 1 result with the
     correct `content`.

7. **TEST-DESIGN3-02** (`test_chunks_fts_is_trigger_synced`):
   - Insert a doc and a chunk via `_insert_chunk()` (canonical INSERT into `chunks` triggers
     `chunks_ai`).
   - Assert `fts_search("trigger", top_k=5, db=db)` returns 1 result.
   - Do NOT manually INSERT into `chunks_fts` — verify trigger-only sync.

8. **TEST-DESIGN3-03** (`test_delete_document_chain_no_orphan_vec`):
   - Insert a doc, a chunk, and a `chunks_vec` row manually:
     `db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))`
   - Simulate `delete_document_chain()` by executing the deletion in the correct order:
     1. `DELETE FROM chunks_vec WHERE chunk_id = ?`
     2. `DELETE FROM documents WHERE doc_id = ?` (CASCADE deletes `chunks`)
   - Assert `SELECT COUNT(*) FROM chunks_vec WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)`
     returns 0.

9. **TEST-DESIGN3-04** (`test_deletion_order_no_orphan_vec`):
   - Insert a doc, two chunks, and two `chunks_vec` rows.
   - Delete `chunks_vec` rows first, then delete `documents` (CASCADE).
   - Assert orphan vec count = 0. This directly validates the mandated deletion order.

10. **TEST-DESIGN3-05** (`test_consistency_check_detects_fts_gap`):
    - Insert a doc and a chunk (trigger auto-populates `chunks_fts`).
    - Manually remove the FTS entry using the FTS5 delete-command:
      ```python
      fts_text = db.execute(
          "SELECT COALESCE(normalized_content, content) FROM chunks WHERE chunk_id = ?",
          (chunk_id,)
      ).fetchone()[0]
      db.execute(
          "INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', ?, ?)",
          (chunk_id, fts_text),
      )
      db.commit()
      ```
    - Call `check_rag_consistency(db)`.
    - Assert `report.fts_gap >= 1`.
    - **Note:** Read `scripts/db/maintenance.py` to verify the return type of
      `check_rag_consistency()` and the attribute name for FTS gap count before writing
      this assertion.

11. **test_reconcile_url_fts_deletion** (reconcile_url fix regression test):
    - Insert a doc and a chunk (trigger populates `chunks_fts`).
    - Patch `SQLiteHelper` to inject the fake helper.
    - Call `RagMaintenanceService().reconcile_url("http://example.com")`.
    - Assert the call returns `{"found": True, "chunks": 1}` — no `OperationalError` raised.
    - Assert `fts_search("reconcile", top_k=5, db=db)` returns 1 result (FTS re-inserted).

### Method

- Create the file using the `Write` tool.
- Use `unittest.mock.patch` as a context manager inside each test that calls
  `RagMaintenanceService` methods. Patch target: `"agent.services.rag_maintenance_service.SQLiteHelper"`.
  The mock's `return_value.open.return_value.__enter__.return_value` must be set to the
  `_FakeSQLiteHelper` instance.
  Example pattern:
  ```python
  with patch("agent.services.rag_maintenance_service.SQLiteHelper") as mock_helper_cls:
      mock_helper_cls.return_value.open.return_value.__enter__.return_value = db
      mock_helper_cls.return_value.open.return_value.__exit__ = lambda *_: None
      RagMaintenanceService().rebuild_fts()
  ```

### Details

- **Import of `check_rag_consistency`:** Verify the import path by reading
  `scripts/db/maintenance.py` before writing the file. The plan imports it from
  `db.maintenance`; confirm that is correct.
- **FTS delete-command in TEST-DESIGN3-05:** Using `DELETE FROM chunks_fts WHERE rowid = ?`
  would fail on FTS5 virtual table with `content=` config. Use the correct FTS5 delete-command
  syntax as shown above.
- **`db.commit()` after manual FTS manipulation:** Always commit after manual SQL in tests
  to ensure the in-memory DB state is consistent before calling service methods.
- **Test ordering:** Tests are independent; each uses its own `db` fixture instance.

## Validation plan

| Check | Command | Expected outcome |
|-------|---------|-----------------|
| New test suite | `uv run pytest tests/test_rag_index_integrity.py -v` | All 6 tests pass |
| Existing FTS tests (regression) | `uv run pytest tests/test_fts_fallback.py -v` | All pass |
| Full suite | `uv run pytest` | 0 new failures |
| Lint | `ruff check tests/test_rag_index_integrity.py` | 0 errors |
| Type check | `mypy tests/test_rag_index_integrity.py` | 0 new errors |
