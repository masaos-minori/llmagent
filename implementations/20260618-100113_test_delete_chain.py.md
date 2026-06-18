# Implementation: tests/test_delete_chain.py

## Goal

Verify `delete_document_chain()` deletes in correct order and leaves no orphaned rows.
Also verify `DocumentRepository.delete_document()` leaves no orphaned chunks_vec rows.

## Scope

- New file: `tests/test_delete_chain.py`
- Also add one test to `tests/test_document_repo.py` (orphan check)

## Assumptions

1. In-memory SQLite with the same schema as `test_document_repo.py`.
2. `chunks_vec` is a plain table (no vec0) — stub.
3. `delete_document_chain` is importable from `rag.ingestion.ingester`.
4. `_FakeSQLiteHelper` reuses the pattern from `test_document_repo.py`.

## Tests in test_delete_chain.py

4 tests:

1. `test_delete_removes_all_rows` — insert doc+chunks+vec rows, call `delete_document_chain`, assert all 3 tables have 0 rows for that doc_id.

2. `test_delete_chunks_vec_before_chunks` — use a custom `_TrackingSQLiteHelper` that records SQL order; assert `DELETE FROM chunks_vec` appears before `DELETE FROM chunks` and before `DELETE FROM documents`.

3. `test_delete_idempotent` — call `delete_document_chain` twice on same doc_id; no error, tables still empty.

4. `test_delete_does_not_remove_other_docs` — insert 2 docs, delete 1, assert the other doc's rows are intact.

## Test in test_document_repo.py

Add to `TestDeleteDocument`:

`test_no_orphaned_chunks_vec_after_delete` — insert doc + chunk + chunks_vec row, call `delete_document()`, assert `chunks_vec` has 0 rows.
