# Goal

Make `_recency_boost()` fail-fast by raising `MemorySchemaError` instead of
silently logging a warning and returning `0.0` when `created_at` is an invalid
or unparseable ISO-8601 date.

# Scope

- `scripts/agent/memory/retriever.py`

# Assumptions

1. `_recency_boost(created_at: str, recency_days: float) -> float` currently catches
   `(ValueError, OverflowError)` and logs a warning before returning `0.0`.
2. The plan requires raising `MemorySchemaError` instead. This means any memory
   entry with an invalid `created_at` will cause the retriever to raise rather than
   silently scoring it as 0.
3. **Pre-condition check (must be done before implementing):** Verify that
   `created_at` is always stored as valid ISO-8601 (e.g. `"2026-01-01T00:00:00"`)
   in the SQLite DB and JSONL files. Run:
   ```bash
   sqlite3 /opt/llm/data/session.sqlite \
     "SELECT count(*) FROM memories WHERE created_at IS NULL OR created_at = ''"
   ```
   If count > 0, migrate those rows to valid timestamps before implementing this step.
4. `MemorySchemaError` is already defined in `agent/memory/exceptions.py`.
5. The caller `_score_entry()` (or its wrapper) will propagate `MemorySchemaError`
   upward. The retriever's `search()` method should let it propagate.

# Implementation

## Target file

`scripts/agent/memory/retriever.py`

## Procedure

1. Change `_recency_boost`:

```python
# Before
def _recency_boost(created_at: str, recency_days: float = _RECENCY_DAYS) -> float:
    try:
        ...
    except (ValueError, OverflowError) as e:
        logger.warning("_recency_boost: invalid created_at %r: %s", created_at, e)
        return 0.0
```

```python
# After
def _recency_boost(created_at: str, recency_days: float = _RECENCY_DAYS) -> float:
    try:
        ...
    except (ValueError, OverflowError) as e:
        raise MemorySchemaError(
            f"_recency_boost: invalid created_at {created_at!r}: {e}"
        ) from e
```

2. Import `MemorySchemaError` at the top of the file (if not already imported).

3. Run ruff + mypy.

## Method

Change `except` body from `logger.warning + return 0.0` to `raise MemorySchemaError`.
No other logic changes.

# Validation plan

- `grep -n "logger.warning.*recency_boost\|return 0.0" scripts/agent/memory/retriever.py`
  → 0 hits in `_recency_boost`
- `uv run ruff check scripts/agent/memory/retriever.py`
- `uv run mypy scripts/agent/memory/retriever.py`
- `uv run pytest tests/test_memory_retriever.py -v`
- Unit test: call `_recency_boost("NOT_A_DATE")` → verify `MemorySchemaError` raised
  (not `0.0` returned)
