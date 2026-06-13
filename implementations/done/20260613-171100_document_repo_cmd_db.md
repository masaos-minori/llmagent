# Implementation: agent/document_repo.py + agent/commands/cmd_db.py — chunking_strategy in list + display

## Goal

Step 5: Add `chunking_strategy` to `list_documents()` SELECT and return value.
Step 6: Add `Strategy` column to `/db urls` table display in `cmd_db.py`.
Step 7: Update `config/rag_pipeline.toml` comment for `md_index_enable`.

## Scope

- `scripts/agent/document_repo.py` — `list_documents()` SELECT: add `d.chunking_strategy`
- `scripts/agent/commands/cmd_db.py` — `_db_list_urls()`: add Strategy column to write_table
- `config/rag_pipeline.toml` — update `md_index_enable` comment

## Assumptions

- `list_documents()` currently selects `d.url, d.title, d.lang, d.fetched_at` and chunk counts
- `cmd_db.py:_db_list_urls()` uses `write_table` with headers
- `chunking_strategy` defaults to `'text'` — display as-is or abbreviate ("heading"/"text")

## Implementation

### Target file

- `scripts/agent/document_repo.py`
- `scripts/agent/commands/cmd_db.py`
- `config/rag_pipeline.toml`

### Procedure

1. Read `document_repo.py:list_documents()` — add `d.chunking_strategy` to SELECT and return dict
2. Read `cmd_db.py:_db_list_urls()` — add `Strategy` header and row value
3. Read `config/rag_pipeline.toml` — update `md_index_enable` comment

### Method

- Edit tool for each file

### Details

**`document_repo.py` — list_documents() SELECT:**
```python
"SELECT d.url, d.title, d.lang, d.fetched_at, d.chunking_strategy,"
```
Return dict includes `"chunking_strategy": row["chunking_strategy"]`.

**`cmd_db.py` — _db_list_urls() table:**
```python
# Headers: add "Strategy"
["URL", "Title", "Lang", "Fetched", "Strategy", "Chunks"]

# Row: add chunking_strategy
[
    doc["url"],
    doc["title"] or "",
    doc["lang"],
    doc["fetched_at"][:10],
    doc.get("chunking_strategy", "text"),
    str(doc["chunk_count"]),
]
```

**`config/rag_pipeline.toml` — comment:**
```toml
# md_index_enable: enables heading-based chunking for non-.md files using heuristic detection.
# Note: .md / .markdown / .mdx files always use heading-based chunking regardless of this flag.
md_index_enable = false
```

## Validation plan

- `uv run pytest tests/test_document_repo.py tests/test_cmd_db.py -v` — all pass (or no new failures)
- `uv run mypy scripts/agent/document_repo.py scripts/agent/commands/cmd_db.py` — 0 new errors
- `uv run ruff check scripts/agent/document_repo.py scripts/agent/commands/cmd_db.py` — 0 errors
