# Implementation Procedure: reconcile_url() FTS Deletion Bug Fix

## Goal

Fix the FTS5 deletion bug in `RagMaintenanceService.reconcile_url()` at line 102–105 of
`scripts/agent/services/rag_maintenance_service.py`. The current code uses
`DELETE FROM chunks_fts WHERE chunk_id IN (...)`, which is invalid on an FTS5 content table
because `chunk_id` is not a filterable column on the virtual table. Replace it with the
correct per-row FTS5 delete-command syntax.

## Scope

- **In:** `scripts/agent/services/rag_maintenance_service.py` — modify `reconcile_url()` only
- **Out:** No schema changes, no changes to `rebuild_fts()`, no changes to `scripts/rag/maintenance.py`

## Assumptions

1. `chunks_fts` is an FTS5 virtual table declared with `content='chunks'` and
   `content_rowid='chunk_id'`. In this mode, the only way to delete entries is the
   FTS5 delete-command: `INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', ?, ?)`.
2. `SQLiteHelper.open(write_mode=True)` used as a context manager opens a connection and
   closes it on `__exit__`; it does NOT auto-commit. Callers must call `db.commit()` explicitly
   (confirmed by reading `scripts/db/helper.py`: `commit()` delegates to `conn.commit()`).
   `reconcile_url()` currently does not call `db.commit()` explicitly — the `sqlite3` module
   in Python uses implicit transactions for DML, so the connection's `__exit__` closes but
   does not commit. **Action:** add `db.commit()` before the `with` block exits, or verify that
   sqlite3 autocommit covers it. The existing code has no explicit commit; preserve the same
   commit behavior (do not add or remove `db.commit()` calls) — only change the FTS delete logic.
3. The per-row FTS delete must read `normalized_content` or `content` from `chunks` BEFORE
   deleting the row — the current code deletes `chunks_vec` entries first (line 99), then
   deletes FTS (lines 101–105), then re-reads `chunks` for re-insertion (lines 106–117).
   The `chunks` rows themselves are NOT deleted in `reconcile_url()`, so reading from `chunks`
   after the FTS delete but before re-insertion is safe.

## Implementation

### Target file

`scripts/agent/services/rag_maintenance_service.py`

### Procedure

1. Locate the block at lines 100–105:
   ```python
   if chunk_ids:
       placeholders = ",".join("?" * len(chunk_ids))
       db.execute(
           f"DELETE FROM chunks_fts WHERE chunk_id IN ({placeholders})",
           tuple(chunk_ids),
       )
   ```
2. Replace the entire block with a per-row FTS5 delete-command loop:
   ```python
   for cid in chunk_ids:
       row_fts = db.execute(
           "SELECT content, normalized_content FROM chunks WHERE chunk_id = ?",
           (cid,),
       ).fetchone()
       if row_fts:
           fts_text = row_fts["normalized_content"] or row_fts["content"]
           db.execute(
               "INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', ?, ?)",
               (cid, fts_text),
           )
   ```
3. Remove the now-unused `placeholders` variable (it was defined inside the `if chunk_ids:` guard).
4. The re-insertion loop at lines 106–117 (the second `for cid in chunk_ids:` loop) is
   unchanged; leave it exactly as-is.

### Method

- Direct `Edit` tool replacement on the exact old string.
- No new imports required — the fix uses only existing `db.execute()` calls.

### Details

- **Why per-row?** The FTS5 delete-command requires the exact indexed text (the value that was
  originally inserted into `chunks_fts`). Since `reconcile_url()` is scoped to a single URL,
  the number of chunks per URL is small (typically < 100), so per-row lookup is acceptable.
- **Row factory:** The `open(write_mode=True)` call at line 85 does NOT pass `row_factory=True`,
  so `db.execute(...).fetchone()` returns a `sqlite3.Row` only if `conn.row_factory` is set.
  Looking at the existing code at line 107–111, it accesses `row["content"]` and
  `row["normalized_content"]` by name — this works because the second `for cid` loop uses the
  same `db` object. The same named-column access applies to `row_fts` in the new loop.
  **Verify:** `_FakeSQLiteHelper` in tests sets `conn.row_factory = sqlite3.Row` on fixture
  construction. The production `open(write_mode=True)` does NOT set `row_factory=True` but the
  existing production code (line 107–111) already relies on named access. Either the production
  DB was initialized with row_factory elsewhere, or `_FakeSQLiteHelper.open()` sets it for tests.
  Do not change row_factory behavior; use the same access pattern as lines 107–111.

## Validation plan

| Check | Command | Expected outcome |
|-------|---------|-----------------|
| Unit test (new) | `uv run pytest tests/test_rag_index_integrity.py::test_reconcile_url_fts_deletion -v` | Pass — no `OperationalError` |
| Existing FTS tests | `uv run pytest tests/test_fts_fallback.py -v` | All pass — no regressions |
| Lint | `ruff check scripts/agent/services/rag_maintenance_service.py` | 0 errors |
| Type check | `mypy scripts/agent/services/rag_maintenance_service.py` | 0 new errors |
| Full suite | `uv run pytest` | 0 new failures |
