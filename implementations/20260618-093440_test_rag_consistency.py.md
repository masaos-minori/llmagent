# Implementation: tests/test_rag_consistency.py

## Goal

Create regression tests that verify `check_rag_consistency()` correctly detects
sync failures between `chunks`, `chunks_fts`, and `chunks_vec` tables.

## Scope

- New file: `tests/test_rag_consistency.py`
- No production code changes.

## Assumptions

1. Tests use in-memory SQLite with `sqlite3.connect(":memory:")` (no filesystem dependency).
2. The RAG DB schema (`schema_sql.py`) must be applied to create triggers.
3. `chunks_fts` FTS5 with `content_rowid = 'chunk_id'` — deletion uses the special
   `INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ...)` command.
4. `chunks_vec` is a sqlite-vec virtual table (`vec0`). In tests, we simulate it with a regular
   table having `chunk_id INTEGER PRIMARY KEY` so no extension is needed.
5. `_FakeSQLiteHelper` pattern (used in `test_fts_japanese.py`): wrap an in-memory sqlite3
   connection with a helper that exposes `fetchone()`, `fetchall()`, `execute()`, `commit()`.
6. FTS5 is available in standard Python 3.13 SQLite build (confirmed in prior tests).
7. `chunks_vec` is simulated with `CREATE TABLE chunks_vec (chunk_id INTEGER PRIMARY KEY)`
   because `vec0` extension is not loaded in unit tests. The `check_rag_consistency()` queries
   only use standard SQL (`COUNT(*)`, `NOT IN`) — no vec0-specific functions.

## Implementation

### Target file

`tests/test_rag_consistency.py`

### Procedure

1. Create `_FakeSQLiteHelper` that wraps `sqlite3.connect(":memory:")`.
2. Create `_make_rag_db()` fixture that applies the RAG schema with `chunks_vec` replaced
   by a plain table (so no sqlite-vec extension needed).
3. Write 5 test functions in a single class.

### Method

Direct in-memory SQLite; no mocking of production code. Tests verify observable behavior
(row counts) after known DB operations.

### Details

**Schema note:** `chunks_vec` is a virtual table using the `vec0` extension. Since the
extension is not available in test environments, replace with:
```sql
CREATE TABLE IF NOT EXISTS chunks_vec (chunk_id INTEGER PRIMARY KEY)
```
The consistency check functions only use `COUNT(*)` and `NOT IN` — these work on a plain table.

**`_FakeSQLiteHelper`:**
```python
class _FakeSQLiteHelper:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def fetchone(self, sql: str, params: tuple = ()) -> sqlite3.Row:
        return self.conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def commit(self) -> None:
        self.conn.commit()
```

**`_make_rag_db()` helper (not a pytest fixture — just a plain function):**
```python
RAG_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    url       TEXT NOT NULL UNIQUE,
    title     TEXT,
    lang      TEXT,
    fetched_at TEXT,
    etag      TEXT,
    last_modified TEXT,
    chunking_strategy TEXT
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id             INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    content            TEXT NOT NULL,
    normalized_content TEXT,
    chunk_index        INTEGER,
    chunk_type         TEXT
);
CREATE TABLE IF NOT EXISTS chunks_vec (
    chunk_id INTEGER PRIMARY KEY
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content,
    content_rowid = 'chunk_id'
);
CREATE TRIGGER IF NOT EXISTS chunks_ai
AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts (rowid, content)
    VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad
AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts (chunks_fts, rowid, content)
    VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
END;
CREATE TRIGGER IF NOT EXISTS chunks_au
AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts (chunks_fts, rowid, content)
    VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
    INSERT INTO chunks_fts (rowid, content)
    VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
END;
"""

def _make_rag_db() -> _FakeSQLiteHelper:
    conn = sqlite3.connect(":memory:")
    for stmt in RAG_SCHEMA.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(stmt)
    conn.commit()
    return _FakeSQLiteHelper(conn)

def _insert_doc(db: _FakeSQLiteHelper) -> int:
    cur = db.execute(
        "INSERT INTO documents (url, title) VALUES (?, ?)",
        ("https://example.com/doc", "Test Doc"),
    )
    db.commit()
    return cur.lastrowid

def _insert_chunk(db: _FakeSQLiteHelper, doc_id: int, content: str) -> int:
    cur = db.execute(
        "INSERT INTO chunks (doc_id, content) VALUES (?, ?)",
        (doc_id, content),
    )
    db.commit()
    return cur.lastrowid
```

**5 test functions:**

```python
class TestRagConsistency:
    def test_consistency_report_counts_match(self) -> None:
        """All tables agree after clean inserts."""
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "hello world")
        db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
        db.commit()
        report = check_rag_consistency(db)
        assert report.chunks == 1
        assert report.fts == 1
        assert report.vec == 1
        assert report.orphan_vec_count == 0
        assert report.fts_gap == 0
        assert is_consistent(report)
        assert summarize_issues(report) == []

    def test_orphan_vec_detected(self) -> None:
        """Orphan in chunks_vec (no matching chunk) is detected."""
        db = _make_rag_db()
        db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (99999)", ())
        db.commit()
        report = check_rag_consistency(db)
        assert report.orphan_vec_count == 1
        assert not is_consistent(report)
        issues = summarize_issues(report)
        assert any("Orphan vec" in i for i in issues)

    def test_fts_gap_after_clean_delete(self) -> None:
        """After a clean delete (trigger fires), gap is 0."""
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "text to delete")
        db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
        db.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))
        db.execute("DELETE FROM chunks_vec WHERE chunk_id = ?", (chunk_id,))
        db.commit()
        report = check_rag_consistency(db)
        assert report.chunks == 0
        assert report.fts == 0
        assert report.fts_gap == 0
        assert is_consistent(report)

    def test_fts_gap_detected_after_broken_delete(self) -> None:
        """If FTS row is removed but chunks row remains, gap > 0."""
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "orphaned fts row")
        # Simulate broken trigger: remove FTS row manually without touching chunks
        db.execute(
            "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
            (chunk_id, "orphaned fts row"),
        )
        db.commit()
        report = check_rag_consistency(db)
        assert report.chunks == 1
        assert report.fts == 0
        assert report.fts_gap == 1
        assert not is_consistent(report)
        issues = summarize_issues(report)
        assert any("FTS gap" in i for i in issues)

    def test_consistency_after_force_reinsert(self) -> None:
        """Consistency is restored after full force-reinsert cycle."""
        db = _make_rag_db()
        doc_id = _insert_doc(db)
        chunk_id = _insert_chunk(db, doc_id, "reinsert content")
        db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
        db.commit()
        # Force-reinsert: delete order is vec → chunks → documents, then re-insert
        db.execute("DELETE FROM chunks_vec WHERE chunk_id = ?", (chunk_id,))
        db.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        db.commit()
        # Re-insert
        doc_id2 = _insert_doc(db)
        chunk_id2 = _insert_chunk(db, doc_id2, "reinsert content")
        db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id2,))
        db.commit()
        report = check_rag_consistency(db)
        assert report.chunks == 1
        assert report.fts == 1
        assert report.vec == 1
        assert is_consistent(report)
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check tests/test_rag_consistency.py` | 0 errors |
| Type check | `uv run mypy tests/test_rag_consistency.py` | no new errors |
| Tests | `uv run pytest tests/test_rag_consistency.py -v` | 5 passed |
| Full suite | `uv run pytest tests/ -x -q` | no new failures |
