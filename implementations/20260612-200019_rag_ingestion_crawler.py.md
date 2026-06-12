# Goal

Extract the CLI entry point from `crawler.py` into a dedicated `_main()` function,
remove `Any` type usages, and categorize error handling into HTTP / parse / file /
SQLite error types.

# Scope

- `scripts/rag/ingestion/crawler.py`

# Assumptions

1. `if __name__ == "__main__":` block at line 416 contains CLI argument parsing +
   orchestration. Extract to `def _main() -> None`.
2. `Any` usages in function signatures → replace with concrete types or remove.
3. The two `except Exception` clauses (lines 203, ~300) correspond to:
   - HTTP errors → `except (httpx.RequestError, httpx.HTTPStatusError)`
   - File errors → `except (OSError, FileNotFoundError)`
   - Parse errors → `except (orjson.JSONDecodeError, ValueError)`
4. Use `CrawlTarget` from `rag.models` where URL+lang pairs are passed.

# Implementation

## Target file

`scripts/rag/ingestion/crawler.py`

## Procedure

1. Move `if __name__ == "__main__":` block body to `def _main() -> None`.
2. At file bottom: `if __name__ == "__main__": _main()`.
3. Replace `Any` parameter types with concrete types.
4. Replace `except Exception` (line 203) with specific HTTP/parse exception types.
5. Replace `except Exception` (near line 300) with `(OSError, sqlite3.OperationalError)`.
6. Run ruff + mypy.

## Method

Function extraction + exception narrowing.

# Validation plan

- `grep -n "except Exception\|: Any" scripts/rag/ingestion/crawler.py` → 0 hits
- `uv run ruff check scripts/rag/ingestion/crawler.py`
- `uv run mypy scripts/rag/ingestion/crawler.py`
