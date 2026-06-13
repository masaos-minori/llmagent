# Implementation: db/create_schema.py + agent/document_repo.py — chunking_strategy schema + DB fix

## Goal

Step 0: Fix `document_repo.py` to use `SQLiteHelper("rag")` (bug: was using "session").
Step 1: Add `chunking_strategy TEXT NOT NULL DEFAULT 'text'` to documents DDL in `create_schema.py`.
Step 2: Add `migrate_schema()` to `create_schema.py` for ALTER TABLE on existing DBs.
Update `tests/test_document_repo.py` `_SCHEMA_SQL` to include `chunking_strategy`.

## Scope

- `scripts/agent/document_repo.py` — SQLiteHelper("session") → SQLiteHelper("rag") in list_documents() and delete_document()
- `scripts/db/create_schema.py` — add `chunking_strategy` to `_RAG_SCHEMA_TEMPLATE`; add `migrate_schema()` function
- `tests/test_document_repo.py` — add `chunking_strategy` to `_SCHEMA_SQL`; update key assertions

## Assumptions

- `documents` table is in `rag.sqlite`, not `session.sqlite`
- `SQLiteHelper("rag")` is the correct target for all document CRUD
- `migrate_schema()` uses `ALTER TABLE documents ADD COLUMN chunking_strategy TEXT NOT NULL DEFAULT 'text'` with OperationalError("duplicate column name") suppression
- No existing test checks the SQLiteHelper target string; test uses in-memory mock

## Implementation

### Target file

- `scripts/agent/document_repo.py`
- `scripts/db/create_schema.py`
- `tests/test_document_repo.py`

### Procedure

1. In `document_repo.py`: replace all `SQLiteHelper("session")` with `SQLiteHelper("rag")`
2. In `create_schema.py` `_RAG_SCHEMA_TEMPLATE`: add `chunking_strategy` column to documents DDL
3. In `create_schema.py`: add `migrate_schema()` function after `create_rag_schema()`
4. In `test_document_repo.py`: update `_SCHEMA_SQL` with `chunking_strategy` column

### Method

- Edit tool for each file
- grep to find all SQLiteHelper("session") in document_repo.py before editing

### Details

**`document_repo.py` — replace SQLiteHelper target:**
```python
# Before: SQLiteHelper("session")
# After:  SQLiteHelper("rag")
# Apply replace_all=True since all instances should change
```

**`create_schema.py` — documents DDL:**
```sql
CREATE TABLE IF NOT EXISTS documents (
    doc_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    url                TEXT    NOT NULL UNIQUE,
    title              TEXT,
    lang               TEXT    NOT NULL CHECK (lang IN ('ja', 'en')),
    fetched_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    etag               TEXT,
    last_modified      TEXT,
    chunking_strategy  TEXT    NOT NULL DEFAULT 'text'
);
```

**`create_schema.py` — migrate_schema():**
```python
def migrate_schema(db_name: str = "rag") -> None:
    """Apply incremental schema migrations to an existing DB.

    Safe to run on an already-migrated DB — duplicate column errors are suppressed.
    """
    with SQLiteHelper(db_name).open(write_mode=True) as db:
        try:
            db.execute(
                "ALTER TABLE documents ADD COLUMN"
                " chunking_strategy TEXT NOT NULL DEFAULT 'text'"
            )
            db.commit()
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
```

**`test_document_repo.py` — _SCHEMA_SQL:**
```sql
CREATE TABLE IF NOT EXISTS documents (
    doc_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    url                TEXT    NOT NULL UNIQUE,
    title              TEXT,
    lang               TEXT    NOT NULL DEFAULT 'en',
    fetched_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    etag               TEXT,
    last_modified      TEXT,
    chunking_strategy  TEXT    NOT NULL DEFAULT 'text'
);
```

## Validation plan

- `uv run pytest tests/test_document_repo.py -v` — all pass
- `uv run mypy scripts/db/create_schema.py scripts/agent/document_repo.py` — 0 new errors
- `grep "SQLiteHelper" scripts/agent/document_repo.py` — all instances say "rag"
