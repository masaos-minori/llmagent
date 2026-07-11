# Implementation Procedure: tests/test_rag_index_integrity.py — cascade/backstop test updates and additions

Source plan: `plans/20260711-164446_plan.md` — Phase 3

## Goal

Update the existing deletion tests in `tests/test_rag_index_integrity.py` to assert that
`ON DELETE CASCADE` actually removes `chunks` rows (not just that `chunks_vec` has no
orphans), rename one test to match the corrected 2-step contract, and add a new test
proving the `chunks_vec_ad` trigger works as a defensive backstop for direct `chunks`
deletes. Depends on Phase 2's fixture changes (`PRAGMA foreign_keys=ON` +
`chunks_vec_ad` trigger) already being in place.

## Scope

**In-Scope:**
- `test_delete_document_chain_no_orphan_vec` (currently lines 192-212): update
  docstring/comment wording; add a cascade assertion
- `test_deletion_order_no_orphan_vec` (currently lines 218-242): rename to
  `test_canonical_deletion_leaves_no_orphans_and_cascades_chunks`; update
  docstring/comment wording; add a cascade assertion
- New test: `test_chunks_vec_ad_trigger_cleans_up_direct_chunks_delete`

**Out-of-Scope:**
- `test_rebuild_fts_uses_coalesce`, `test_chunks_fts_is_trigger_synced`,
  `test_consistency_check_detects_fts_gap` — unrelated to the deletion contract, already
  correct, preserved unmodified
- The `db` fixture and `_SCHEMA_SQL` themselves — already updated by the Phase 2
  implementation doc
- Any production source file

## Assumptions

1. Phase 2's fixture changes are already applied: `db` fixture executes `PRAGMA
   foreign_keys=ON`, and `_SCHEMA_SQL` includes the `chunks_vec_ad` trigger. Without these,
   the new cascade assertions in this phase would fail (CASCADE would be a no-op) and the
   new trigger test would have no trigger to exercise.
2. `test_delete_document_chain_no_orphan_vec`'s current body (lines 192-212) manually runs
   `DELETE FROM chunks_vec WHERE chunk_id = ?` then `DELETE FROM documents WHERE doc_id =
   ?`, then asserts only that no orphan `chunks_vec` rows remain — it never asserts `chunks`
   rows were actually removed by CASCADE (confirmed by direct read).
3. `test_deletion_order_no_orphan_vec`'s current body (lines 218-242) does the same for the
   2-chunk case; it keeps the same manual delete pattern and orphan-only assertion.
4. Renaming `test_deletion_order_no_orphan_vec` does not require i.e. changes elsewhere in
   the file (no other test references it by name).

## Implementation

### Target file

`tests/test_rag_index_integrity.py`

### Procedure

1. **`test_delete_document_chain_no_orphan_vec`** (keep name — still accurate):
   - Update the docstring/inline comment from the current 3-step-adjacent phrasing to:
     "delete chunks_vec, then documents (CASCADE removes chunks)".
   - After the existing orphan-count assertion, add:
     ```python
     assert db.execute(
         "SELECT COUNT(*) FROM chunks WHERE doc_id = ?", (doc_id,)
     ).fetchone()[0] == 0
     ```
     This proves CASCADE actually fired, not just that `chunks_vec` was manually cleaned.

2. **Rename `test_deletion_order_no_orphan_vec` →
   `test_canonical_deletion_leaves_no_orphans_and_cascades_chunks`**:
   - Rename the function.
   - Apply the same docstring/comment treatment as step 1.
   - Add the same `chunks` cascade assertion as step 1, extended to check both `chunk_id1`
     and `chunk_id2` are gone (the test already covers the 2-chunk case), e.g.:
     ```python
     assert db.execute(
         "SELECT COUNT(*) FROM chunks WHERE doc_id = ?", (doc_id,)
     ).fetchone()[0] == 0
     ```

3. **New test: `test_chunks_vec_ad_trigger_cleans_up_direct_chunks_delete`**:
   - Insert a document, a chunk, and a corresponding `chunks_vec` row (same helper pattern
     as the existing tests: `_insert_doc`, `_insert_chunk`, then `INSERT INTO chunks_vec
     (chunk_id) VALUES (?)`).
   - Delete the `chunks` row **directly** (bypassing `delete_document_chain()` entirely) —
     e.g. `conn.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))`, simulating an
     ad-hoc/manual delete.
   - Assert the `chunks_vec_ad` trigger alone removed the corresponding `chunks_vec` row:
     ```python
     assert db.execute(
         "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id = ?", (chunk_id,)
     ).fetchone()[0] == 0
     ```
   - This directly proves the "defensive backstop" claim from the plan's Design section.

### Method

Direct in-place edits to two existing test function bodies (docstring + one added
assertion each), one function rename, and one new test function appended near the other
DESIGN3-04-adjacent tests (after
`test_canonical_deletion_leaves_no_orphans_and_cascades_chunks`).

### Details

Illustrative shape of the new test (pseudocode, adapt to existing helper conventions in
the file):

```python
def test_chunks_vec_ad_trigger_cleans_up_direct_chunks_delete(db: _FakeSQLiteHelper) -> None:
    """chunks_vec_ad must clean up chunks_vec when chunks is deleted directly (bypassing
    delete_document_chain()), proving the defensive-backstop claim."""
    conn = db._conn
    doc_id = _insert_doc(conn, url="http://direct-delete.example.com")
    chunk_id = _insert_chunk(conn, doc_id, "direct delete test", None)
    conn.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
    conn.commit()

    # Bypass delete_document_chain(): delete chunks directly
    conn.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))
    conn.commit()

    # chunks_vec_ad trigger should have removed the orphaned vec row
    assert db.execute(
        "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id = ?", (chunk_id,)
    ).fetchone()[0] == 0
```

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_rag_index_integrity.py` | 0 errors |
| Tests | `uv run pytest tests/test_rag_index_integrity.py -v` | All pass, including the 1 new test; the 2 renamed/extended tests pass with their new cascade assertions (proving `PRAGMA foreign_keys=ON` is now actually active) |
| Regression | `uv run pytest tests/test_rag_pipeline.py tests/test_rag_repository.py -k "delete" -q` | No new failures |
