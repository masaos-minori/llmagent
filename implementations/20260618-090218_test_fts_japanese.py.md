# Implementation: tests/test_fts_japanese.py

## Goal

Add Japanese FTS regression tests for the RAG layer: verify `chunks_ai` trigger indexing via `normalized_content`, `_build_fts_query()` tokenization, morphological variant search quality, and trigger lifecycle (update/delete).

## Scope

- **New file only:** `tests/test_fts_japanese.py`
- No changes to `scripts/rag/repository.py`, `scripts/db/schema_sql.py`, or `tests/conftest.py`
- Tests cover 10 cases across 4 test classes

## Assumptions

1. `sudachipy` is available in `.venv/` (confirmed).
2. FTS5 schema and triggers are defined in `scripts/db/schema_sql.py` via `_RAG_SCHEMA_TEMPLATE`; the template contains a `DIMS` placeholder for `chunks_vec` that must be replaced with an integer before execution.
3. `chunks_vec` uses `vec0` virtual table; in-memory tests replace it with a plain stub table (same pattern as `test_document_repo.py`).
4. `_build_fts_tokens_ja()` and `_build_fts_query()` are module-level private functions in `scripts/rag/repository.py` — importable directly.
5. `_SudachiTokenizer` is a module-level singleton (`_sudachi`); patching `_build_fts_tokens_ja` controls tokenizer output in isolation tests without requiring Sudachi at all.
6. The `_FakeSQLiteHelper` pattern from `tests/test_document_repo.py` is the correct abstraction for in-memory SQLite tests.
7. `fts_search()` module-level helper at `rag.repository.fts_search` wraps `RagRepository.fts_search()`.
8. Sudachi dictionary `"core"` is available (confirmed by `import sudachipy` passing).

## Implementation

### Target file

`tests/test_fts_japanese.py`

### Procedure

1. Write test module with in-memory SQLite fixture using real FTS5 schema (without `chunks_vec` vec0).
2. Implement 4 test classes covering trigger indexing, query building, FTS search quality, and trigger lifecycle.
3. Run `uv run ruff format tests/test_fts_japanese.py && uv run ruff check tests/test_fts_japanese.py`.
4. Run `uv run mypy tests/test_fts_japanese.py`.
5. Run `uv run pytest tests/test_fts_japanese.py -v`.
6. Run `uv run pytest tests/ -x -q` for regression check.

### Method

Use `pytest` class-based test organization (4 classes). Use `pytest.fixture` for the in-memory SQLite connection. Patch `rag.repository._build_fts_tokens_ja` where Sudachi output must be controlled precisely. Use the real `_build_fts_query` and real `fts_search` for integration-level tests.

### Details

**Schema fixture:**
```python
import sqlite3
from scripts/db/schema_sql import _RAG_SCHEMA_TEMPLATE

_SCHEMA_SQL = _RAG_SCHEMA_TEMPLATE.replace("DIMS", "4").replace(
    "USING vec0(\n        chunk_id  INTEGER PRIMARY KEY,\n        embedding float[4]\n    )",
    "(chunk_id INTEGER PRIMARY KEY)"
)
```
Actually, since `chunks_vec` is a virtual table with `vec0` which may not be available, replace the entire `CREATE VIRTUAL TABLE chunks_vec` statement with a plain stub. The cleanest approach: define a local `_SCHEMA_SQL` string that mirrors the real schema but with `chunks_vec` as a stub.

The schema SQL for the fixture must include:
- `documents` table (full definition from `_RAG_SCHEMA_TEMPLATE`)
- `chunks` table with `normalized_content` column
- `chunks_fts` FTS5 virtual table with `unicode61` tokenizer
- `chunks_ai`, `chunks_ad`, `chunks_au` triggers using `COALESCE(normalized_content, content)`
- `chunks_vec` as a plain stub table

**Helper insert function:**
```python
def _insert_chunk(conn, doc_id, chunk_index, content, normalized_content=None):
    conn.execute(
        "INSERT INTO chunks (doc_id, chunk_index, content, normalized_content) VALUES (?,?,?,?)",
        (doc_id, chunk_index, content, normalized_content),
    )
    conn.commit()
```

**_FakeSQLiteHelper** (same as `test_document_repo.py`):
- `open(*, write_mode, row_factory)` → sets `conn.row_factory = sqlite3.Row if row_factory else None`
- `execute(sql, params)`, `fetchall(sql, params)`, `commit()`, `close()`, `__enter__`, `__exit__`

**Class 1: `TestChunksAiTrigger`**
- `test_ja_normalized_content_indexed_in_fts`: Insert chunk with `content="食べる料理"`, `normalized_content="食べる 料理"`. Query FTS for `'"食べる"'`. Assert 1 result.
- `test_ja_raw_content_fallback_when_normalized_null`: Insert English chunk with `normalized_content=None`. Query FTS for raw word token. Assert found.
- `test_trigger_uses_coalesce_order`: Insert chunk with both columns. Verify FTS contains normalized form, not raw content (search for a token only in normalized, not in raw).

**Class 2: `TestBuildFtsQuery`**
- `test_build_fts_query_ja_extracts_nouns_verbs_adjectives`: Patch `_build_fts_tokens_ja` to return `["食べ物", "美味しい"]`. Call `_build_fts_query("食べ物は美味しい")`. Assert result is `'"食べ物" "美味しい"'`.
- `test_build_fts_query_en_uses_ascii_extraction`: Call `_build_fts_query("hello world 123")`. Assert result is `'"hello" "world" "123"'`.
- `test_build_fts_query_escapes_fts_metacharacters`: Patch `_build_fts_tokens_ja` to return `['te"st']`. Assert double-quote is stripped from result.

**Class 3: `TestFtsSearchQuality`**
- `test_ja_morphological_variant_returns_same_results`: Insert chunk with `normalized_content="食べ物"`. Patch `_build_fts_tokens_ja` to return `["食べ物"]`. Call `fts_search("食べ物を食べる", top_k=5, db=fake)`. Assert 1 result.
- `test_empty_japanese_query_returns_no_hits`: Patch `_build_fts_tokens_ja` to return `[]`. Insert 1 chunk. Call `fts_search("は", 5, db=fake)`. Assert 0 results.

**Class 4: `TestTriggerLifecycle`**
- `test_update_trigger_reindexes_normalized_content_change`: Insert chunk with `normalized_content="古いトークン"`. UPDATE to `normalized_content="新しいトークン"`. FTS search for `"新しいトークン"` → 1 result; for `"古いトークン"` → 0 results.
- `test_delete_trigger_removes_from_fts`: Insert chunk, verify FTS finds it. DELETE chunk. Verify FTS returns 0 results.

**Import structure:**
```python
from __future__ import annotations

import sqlite3
from collections.abc import Generator
from unittest.mock import patch

import pytest

from rag.repository import RagRepository, _build_fts_query, fts_search
```
Note: `_build_fts_tokens_ja` is not directly importable for patching without the full module path. Use `patch("rag.repository._build_fts_tokens_ja", ...)`.

**PYTHONPATH note:** `AGENTS.md` specifies `scripts/` is the Python root (import-linter uses `PYTHONPATH=scripts`). Tests must be run with `PYTHONPATH=scripts` or via `uv run pytest` which sets it up from `pyproject.toml`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Format | `uv run ruff format tests/test_fts_japanese.py` | clean |
| Lint | `uv run ruff check tests/test_fts_japanese.py` | 0 errors |
| Type check | `uv run mypy tests/test_fts_japanese.py` | no new errors |
| Target tests | `uv run pytest tests/test_fts_japanese.py -v` | all pass |
| Full suite | `uv run pytest tests/ -x -q` | no regressions |
