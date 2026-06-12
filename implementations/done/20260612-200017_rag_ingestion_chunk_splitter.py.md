# Goal

Replace `config: dict[str, Any] | None` with `ChunkSplitterConfig` DTO,
change `data.get("lang", "en")` to `ChunkDocument.lang` attribute access,
and remove `except Exception`.

# Scope

- `scripts/rag/ingestion/chunk_splitter.py`

# Assumptions

1. `ChunkSplitterConfig`, `ChunkDocument` from `rag.models` (Step 2-3 prerequisite).
2. `read_json_file` now returns `ChunkDocument` (Step 6-1 prerequisite).
3. `config: dict[str, Any] | None = None` constructor parameter → `ChunkSplitterConfig | None = None`;
   if `None`, load from TOML using `_build_config_from_toml()` helper.
4. `data.get("lang", "en")` → `chunk_doc.lang` after `ChunkDocument` is the return type.
5. `except Exception: pass` (line 72) wraps a sudachipy import. Replace with
   `except ImportError: ...` since that is the only expected failure.
6. `_is_markdown_source(data: dict[str, Any])` → `(data: ChunkDocument) -> bool`.
7. `_build_chunk_list(data: dict[str, Any])` → `(data: ChunkDocument) -> list[...]`.
8. `_read_source_data(src_path) -> dict[str, Any] | None` → returns `ChunkDocument`
   or raises (after Step 6-1 changes).

# Implementation

## Target file

`scripts/rag/ingestion/chunk_splitter.py`

## Procedure

1. Import `ChunkSplitterConfig`, `ChunkDocument` from `rag.models`.
2. Change constructor `config: dict[str, Any] | None = None` to
   `config: ChunkSplitterConfig | None = None`.
3. Replace `cfg: dict[str, Any] = config or ConfigLoader().load(...)` with
   factory that loads TOML and constructs `ChunkSplitterConfig`.
4. Replace `except Exception: pass` on sudachipy import with `except ImportError: pass`.
5. Update `_is_markdown_source(data: dict[str, Any])` → `(data: ChunkDocument)`.
6. Update `_build_chunk_list(data: dict[str, Any])` → `(data: ChunkDocument)`.
7. Replace `data.get("lang", "en")` → `chunk_doc.lang`.
8. Replace `data.get("url")` / `data.get("content")` → `chunk_doc.url` / `chunk_doc.content`.
9. Run ruff + mypy.

## Method

Constructor config DTO + method signature changes + attribute access.

# Validation plan

- `grep -n "dict\[str, Any\]\|except Exception\|data\.get" scripts/rag/ingestion/chunk_splitter.py` → 0 hits
- `uv run ruff check scripts/rag/ingestion/chunk_splitter.py`
- `uv run mypy scripts/rag/ingestion/chunk_splitter.py`
- `uv run pytest tests/ -k "splitter" --ignore=tests/test_create_schema.py -v`
