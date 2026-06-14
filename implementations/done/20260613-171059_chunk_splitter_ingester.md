# Implementation: rag/ingestion/chunk_splitter.py + ingester.py — chunking_strategy propagation

## Goal

Step 3: Move `.md` extension check before `md_index_enable` guard in `_is_markdown_source()`.
         Add `chunking_strategy` field to chunk JSON output.
Step 4: Read `chunking_strategy` from chunk JSON in `ingester.py` and persist to `documents` table.

## Scope

- `scripts/rag/ingestion/chunk_splitter.py` — `_is_markdown_source()` logic reorder; `_build_chunk_list()` / `_write_chunk_files()` add `chunking_strategy`
- `scripts/rag/ingestion/ingester.py` — `ingest_url_group()` reads `chunking_strategy`; `_get_or_create_document()` saves it to DB

## Assumptions

- `_is_markdown_source()` currently guards with `if not self._md_index_enable: return False` before extension check
- `_build_chunk_list()` calls `_is_markdown_source()` and sets `use_markdown` flag
- `_write_chunk_files()` receives individual chunk dicts; `chunking_strategy` needs to be passed to it or embedded in the list returned by `_build_chunk_list()`
- `ingester.py:ingest_url_group()` reads first chunk file to get metadata; uses `first_data.get("chunking_strategy", "text")`
- `_get_or_create_document()` has INSERT statement that needs `chunking_strategy` added
- Tests for `_is_markdown_source()` exist in `test_chunk_splitter.py` (or similar)

## Implementation

### Target file

- `scripts/rag/ingestion/chunk_splitter.py`
- `scripts/rag/ingestion/ingester.py`

### Procedure

1. Read `chunk_splitter.py` to find exact `_is_markdown_source()` and `_build_chunk_list()` signatures
2. Reorder `_is_markdown_source()`: extension check first, then md_index_enable guard
3. Add `chunking_strategy: str` to the chunk dict written by `_write_chunk_files()` (or set it in `_build_chunk_list()`)
4. Read `ingester.py` to find `ingest_url_group()` and `_get_or_create_document()`
5. Add `chunking_strategy` read from first_data to `_get_or_create_document()` call
6. Add `chunking_strategy` parameter to `_get_or_create_document()` and update INSERT

### Method

- Read each file before editing
- Edit tool for targeted changes

### Details

**`chunk_splitter.py` — _is_markdown_source() reorder:**
```python
def _is_markdown_source(self, data: dict[str, Any]) -> bool:
    url = data.get("url", "")
    # .md extension: always heading-based chunking regardless of md_index_enable
    if url.endswith((".md", ".markdown", ".mdx")):
        return True
    # Non-.md: use heuristic only when md_index_enable is set
    if not self._md_index_enable:
        return False
    content = data.get("content", "")
    return (
        len(re.findall(rf"{MARKDOWN_HEADING_RE} .+", content, re.MULTILINE))
        >= MIN_HEADING_LINES_FOR_MARKDOWN
    )
```

**`chunk_splitter.py` — add chunking_strategy to chunk JSON:**
After `use_markdown = self._is_markdown_source(data)`, determine:
```python
chunking_strategy = "heading" if use_markdown else "text"
```
Then include `"chunking_strategy": chunking_strategy` in each chunk dict written to JSON.

**`ingester.py` — ingest_url_group() reads chunking_strategy:**
```python
chunking_strategy = first_data.get("chunking_strategy", "text")
# pass to _get_or_create_document()
```

**`ingester.py` — _get_or_create_document() signature:**
```python
def _get_or_create_document(
    self, db, url, title, lang, fetched_at, etag, last_modified, chunking_strategy="text"
) -> int:
```

**`ingester.py` — INSERT adds chunking_strategy:**
```sql
INSERT OR IGNORE INTO documents (url, title, lang, fetched_at, etag, last_modified, chunking_strategy)
VALUES (?, ?, ?, ?, ?, ?, ?)
```

## Validation plan

- `_is_markdown_source()` with `.md` URL and `md_index_enable=False` → True
- `_is_markdown_source()` with non-`.md` URL and `md_index_enable=False` → False
- chunk JSON contains `chunking_strategy` field
- `uv run mypy scripts/rag/ingestion/chunk_splitter.py scripts/rag/ingestion/ingester.py` — 0 new errors
- `uv run ruff check scripts/rag/ingestion/` — 0 errors
- `uv run pytest tests/test_chunk_splitter.py tests/test_ingester.py -v` — all pass (or no new failures)
