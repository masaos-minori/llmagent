# Goal

Replace `config: dict[str, Any] | None` with `IngesterConfig` DTO, remove three
`except Exception` clauses, change `_read_chunk_json` to return `ChunkRecord`
instead of `dict | None`, and collect parallel processing failures into
`PipelineExecutionResult`.

# Scope

- `scripts/rag/ingestion/ingester.py`

# Assumptions

1. `IngesterConfig`, `ChunkRecord`, `PipelineExecutionResult` from `rag.models`
   (Step 2-3 prerequisite).
2. `read_json_file` now returns `ChunkDocument` and raises on failure (Step 6-1).
3. `except Exception` appears at lines 59, 272, 304 in ingester.py:
   - Line 59: wraps config loading → replace with `(ValueError, FileNotFoundError)`.
   - Line 272: wraps per-chunk processing → replace with `(OSError, sqlite3.OperationalError)`.
   - Line 304: wraps batch insert → replace with `(sqlite3.OperationalError, sqlite3.DatabaseError)`.
4. `_read_chunk_json(path) -> dict[str, Any] | None` → `ChunkRecord` (raises on failure).
   Fields from `data.get("title", "")` etc. → `chunk_doc.title` after Step 6-1.
5. `data.get("title", "")` / `data.get("lang", "en")` etc. → `ChunkRecord` field access.
6. Parallel processing errors collected into `PipelineExecutionResult` instead of
   being silently swallowed.

# Implementation

## Target file

`scripts/rag/ingestion/ingester.py`

## Procedure

1. Import `IngesterConfig`, `ChunkRecord`, `PipelineExecutionResult` from `rag.models`.
2. Change `config: dict[str, Any] | None = None` → `IngesterConfig | None = None`.
3. Replace `except Exception:` (line 59) with `except (ValueError, FileNotFoundError)`.
4. Change `_read_chunk_json(path) -> dict[str, Any] | None` → `ChunkRecord`:
   - Call `read_json_file(path)` which returns `ChunkDocument`.
   - Build `ChunkRecord` from the document.
5. Replace `data.get("title", "")` etc. → `record.title` etc.
6. Replace `except Exception as e:` (line 272) with `except (OSError, sqlite3.OperationalError) as e:`.
7. Replace `except Exception:` (line 304) with `except (sqlite3.OperationalError, sqlite3.DatabaseError)`.
8. Aggregate errors into `PipelineExecutionResult` and return it.
9. Run ruff + mypy.

## Method

Config DTO + exception narrowing + ChunkRecord return type.

# Validation plan

- `grep -n "except Exception\|dict\[str, Any\]" scripts/rag/ingestion/ingester.py` → 0 hits
- `uv run ruff check scripts/rag/ingestion/ingester.py`
- `uv run mypy scripts/rag/ingestion/ingester.py`
- `uv run pytest tests/ -k "ingestion or ingester" --ignore=tests/test_create_schema.py -v`
