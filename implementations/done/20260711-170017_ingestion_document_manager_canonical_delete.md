# Implementation Procedure: scripts/rag/ingestion/document_manager.py — canonical 2-step deletion

Source plan: `plans/20260711-164446_plan.md` — Phase 1

## Goal

Make `delete_document_chain()` in `scripts/rag/ingestion/document_manager.py` follow the
canonical 2-step deletion contract (`chunks_vec` deleted explicitly, then `documents`
deleted with `ON DELETE CASCADE` removing `chunks`), matching the reference
implementation already used in `scripts/mcp_servers/rag_pipeline/document_manager.py`.
Remove the now-redundant explicit `DELETE FROM chunks` statement and correct the
docstring to describe the 2-step contract instead of the current 3-step wording.

## Scope

**In-Scope:**
- `scripts/rag/ingestion/document_manager.py`: `delete_document_chain()` function body and
  its docstring
- `DocumentManager.delete_existing_document()` docstring, only if it also references the
  3-step order (currently: "chunks_vec removed first because it has no FK constraint to
  chunks" — check whether this needs updating for consistency with the new docstring)

**Out-of-Scope:**
- `scripts/mcp_servers/rag_pipeline/document_manager.py` — already correct, reference only,
  no change
- Any other function in this file (`handle_existing_document`, `_handle_existing_file`,
  `_update_etag`, `check_consistency`, etc.)
- Test files (covered by a separate implementation doc for Phase 2/3)

## Assumptions

1. Current `delete_document_chain()` (lines 17-30) performs 3 explicit statements: `DELETE
   FROM chunks_vec ...`, `DELETE FROM chunks WHERE doc_id = ?`, `DELETE FROM documents
   WHERE doc_id = ?` — confirmed by direct read.
2. `chunks.doc_id` has `ON DELETE CASCADE` to `documents(doc_id)` (per
   `scripts/db/schema_sql.py` RAG schema template) and the only production call path opens
   the DB with `write_mode=True`, which enables `PRAGMA foreign_keys=ON`
   (`scripts/db/helper.py::_apply_connection_pragmas`) — so CASCADE is active and the
   explicit `chunks` delete is redundant.
3. Removing the explicit `chunks` delete is behavior-preserving: the same rows end up
   removed, just via CASCADE instead of an explicit statement. No caller inspects
   intermediate DB state between the two remaining statements.
4. The only caller of `delete_document_chain()` in this file is
   `DocumentManager.delete_existing_document()`, which does not depend on the removed
   statement's side effects beyond final DB state.

## Implementation

### Target file

`scripts/rag/ingestion/document_manager.py`

### Procedure

1. Locate `delete_document_chain()` (currently lines 17-30).
2. Remove the `db.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))` statement.
3. Update the docstring to state the 2-step contract explicitly, mirroring the reference
   implementation's semantics and the plan's Design section:
   - `chunks_vec` has no FK to `chunks` (sqlite-vec limitation) — deleted explicitly first.
   - Deleting `documents` cascades to `chunks` (requires the write-mode connection's
     `PRAGMA foreign_keys=ON`), which in turn fires `chunks_ad` (FTS5 sync) and
     `chunks_vec_ad` (defensive vec cleanup) triggers automatically.
   - `chunks_vec_ad` is a backstop for direct `chunks` deletes that bypass this helper —
     it is not the primary mechanism here.
4. Review `DocumentManager.delete_existing_document()`'s docstring (line 112): update if it
   still implies a 3-step order or otherwise contradicts the corrected 2-step wording.

### Method

Direct in-place edit of the function body (remove one line) and docstring text (rewrite).
No new imports, no signature change, no new symbols.

### Details

Target end-state for `delete_document_chain()` (illustrative signature only, not
production code to copy verbatim — adapt docstring wording as needed):

```
def delete_document_chain(db: SQLiteHelper, doc_id: int) -> None:
    """Delete chunks_vec, then documents; ON DELETE CASCADE removes chunks.

    chunks_vec has no FK to chunks (sqlite-vec limitation), so it is deleted
    explicitly first. Deleting documents cascades to chunks (requires the
    write-mode connection's PRAGMA foreign_keys=ON), which in turn fires the
    chunks_ad (FTS5 sync) and chunks_vec_ad (defensive vec cleanup) triggers
    automatically. chunks_vec_ad is a backstop for direct chunks deletes that
    bypass this helper -- it is not the primary mechanism here.
    """
    # 1. delete chunks_vec rows for this doc's chunks (no FK, must be explicit)
    # 2. delete documents row (CASCADE removes chunks automatically)
```

No change to function signature (`db: SQLiteHelper, doc_id: int) -> None`) or to
`DocumentManager.__init__`/other methods.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/rag/ingestion/document_manager.py` | 0 errors |
| Type check | `uv run mypy scripts/rag/ingestion/document_manager.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no import changes) |
| Regression | `uv run pytest tests/test_rag_pipeline.py tests/test_rag_repository.py -k "delete" -q` | No new failures — confirms behavior-preserving change doesn't break any ingestion-side caller |
| Manual grep | `grep -rn "DELETE FROM chunks WHERE doc_id" scripts/rag/ingestion/document_manager.py` | No matches remain (explicit chunks delete removed) |
