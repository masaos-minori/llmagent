# Goal

Replace `except Exception` in `chunk_splitter.py` with specific exception types
that cover the actual failure modes of `process_file()`.

# Scope

- `scripts/rag/ingestion/chunk_splitter.py`

# Assumptions

1. `process_file()` can raise:
   - `OSError` — file I/O failures (read, write, rename)
   - `RuntimeError` — tokenization failures (Sudachi)
   - `ValueError` — invalid chunk data or config validation
   - `orjson.JSONDecodeError` — malformed JSON source file (subclass of `ValueError`)
   Other exceptions are unexpected and should propagate.

2. `logger.exception()` is kept to preserve the full traceback.

3. The variable `e` should be added to the except clause to include the exception
   message in the log for easier diagnosis.

# Implementation

## Target file

`scripts/rag/ingestion/chunk_splitter.py`

## Procedure

1. Change line 72 from:
   ```python
   except Exception:
       logger.exception(f"process_file failed: {path}")
   ```
   to:
   ```python
   except (OSError, RuntimeError, ValueError) as e:
       logger.exception(f"process_file failed: {path}: {e}")
   ```

2. Run ruff + mypy.

## Method

One-line exception narrowing. No logic change.

# Validation plan

- `grep -n "except Exception" scripts/rag/ingestion/chunk_splitter.py` → 0 hits
- `uv run ruff check scripts/rag/ingestion/chunk_splitter.py`
- `uv run mypy scripts/rag/ingestion/chunk_splitter.py`
