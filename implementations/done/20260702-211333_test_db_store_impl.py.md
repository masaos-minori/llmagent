# Implementation: tests/test_db_store_impl.py

## Goal

Update existing `chunk_insert` test calls to remain compatible with the new extended signature, and add a new test `test_chunk_insert_with_metadata` that verifies `chunk_type` and `source_file` are persisted to the database.

## Scope

- Target: `tests/test_db_store_impl.py`
- Existing `chunk_insert` calls continue to work unchanged (defaults applied automatically)
- Add `test_chunk_insert_with_metadata` — insert with `chunk_type="text"` and `source_file="foo.json"`, query the row, assert both fields

## Assumptions

1. Tests use an in-memory or temporary SQLite DB created via a fixture (e.g., `tmp_path` or `:memory:`).
2. `SQLiteDocumentStore` is instantiated by the existing fixture; the same fixture can be reused for the new test.
3. The `chunks` table has `chunk_type TEXT` and `source_file TEXT` columns in the test schema — same schema as production.
4. The new test can query the row directly via `store._db.fetchone()` or `store._db.fetchall()` using the returned `chunk_id`.

## Implementation

### Target file

`tests/test_db_store_impl.py`

### Procedure

1. Review existing `chunk_insert` calls — no changes required (the new params have defaults).
2. Add the new test function `test_chunk_insert_with_metadata` after the existing chunk_insert tests.

### Method

```python
def test_chunk_insert_with_metadata(store: SQLiteDocumentStore) -> None:
    """chunk_insert persists chunk_type and source_file to the chunks table."""
    doc_id = store.doc_insert(
        url="https://example.com/meta",
        title="Meta Doc",
        content_hash="abc123",
        fetched_at="2026-01-01T00:00:00",
    )
    chunk_id = store.chunk_insert(
        doc_id=doc_id,
        chunk_index=0,
        content="hello world",
        normalized="hello world",
        chunk_type="text",
        source_file="foo.json",
    )
    row = store._db.fetchone(
        "SELECT chunk_type, source_file FROM chunks WHERE chunk_id = ?",
        (chunk_id,),
    )
    assert row is not None
    assert row[0] == "text"
    assert row[1] == "foo.json"
```

### Details

- Use `store._db.fetchone()` (or equivalent) to query the row by `chunk_id`. Adjust the access method to match the pattern already used in the existing test file.
- The `store` fixture name must match the existing fixture name in the test file.
- If `doc_insert` has a different signature in the test file, replicate the same call pattern used by adjacent tests.
- Do not modify existing test functions.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `ruff check tests/test_db_store_impl.py` | 0 errors |
| Type | `mypy tests/test_db_store_impl.py` | no new errors |
| Unit tests | `uv run pytest tests/test_db_store_impl.py -v` | All pass, including `test_chunk_insert_with_metadata` |
| Integration | `uv run pytest tests/test_rag_ingester.py -v` | No regressions |
| Full suite | `uv run pytest` | All pass |
| Pre-commit | `pre-commit run --all-files` | Pass |
