# Goal

Change `read_json_file` from returning `dict[str, Any] | None` to returning
`ChunkDocument` (raising on failure), and change `collect_source_files` to
return `SkipInfo` DTOs for skipped files.

# Scope

- `scripts/rag/ingestion/pipeline_utils.py`
- Callers in `chunk_splitter.py` and `ingester.py` that call `read_json_file`
  and handle `None` return

# Assumptions

1. `ChunkDocument`, `SkipInfo` from `rag.models` (Step 2-3 prerequisite).
2. `ChunkFormatError` from `rag.exceptions` (Step 2-1 prerequisite).
3. `read_json_file` currently returns `None` on any error (file not found, JSON
   decode error, missing fields). After this change it raises:
   - `FileNotFoundError` for missing file
   - `orjson.JSONDecodeError` for parse failure
   - `ChunkFormatError` for missing required fields (url, content)
4. Callers (`chunk_splitter._read_source_data`, `ingester._read_chunk_json`) that
   currently check `if data is None:` must be updated to catch the new exceptions.
5. `collect_source_files` currently returns `list[Path]`; after this change it
   returns `tuple[list[Path], list[SkipInfo]]` to expose skip reasons.

# Implementation

## Target file

`scripts/rag/ingestion/pipeline_utils.py`, `chunk_splitter.py`, `ingester.py`

## Procedure

1. Change `read_json_file(path) -> dict[str, Any] | None` →
   `read_json_file(path) -> ChunkDocument`:
   ```python
   def read_json_file(path: Path) -> ChunkDocument:
       try:
           data = orjson.loads(path.read_bytes())
       except FileNotFoundError:
           raise
       except orjson.JSONDecodeError as e:
           raise ChunkFormatError(f"JSON parse error in {path}: {e}") from e
       if not isinstance(data.get("url"), str) or not isinstance(data.get("content"), str):
           raise ChunkFormatError(f"Missing required fields in {path}")
       return ChunkDocument(
           url=data["url"],
           title=data.get("title") or "",
           lang=data.get("lang") or "en",
           content=data["content"],
           code_blocks=list(data.get("code_blocks") or []),
       )
   ```
2. Update `chunk_splitter._read_source_data` to catch `(FileNotFoundError, ChunkFormatError)`.
3. Update `ingester._read_chunk_json` to remove `None` return and catch exceptions.
4. Change `collect_source_files` return type to `tuple[list[Path], list[SkipInfo]]`.
5. Run ruff + mypy.

## Method

Return type change (raise instead of return None) + caller exception handling update.

# Validation plan

- `grep -n "dict\[str, Any\] | None\|return None" scripts/rag/ingestion/pipeline_utils.py` → 0 hits
- `uv run ruff check scripts/rag/ingestion/`
- `uv run mypy scripts/rag/ingestion/pipeline_utils.py`
- `uv run pytest tests/ -k "ingestion or splitter" --ignore=tests/test_create_schema.py -v`
