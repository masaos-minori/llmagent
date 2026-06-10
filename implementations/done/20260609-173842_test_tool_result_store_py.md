# Implementation: tests/test_tool_result_store.py — update schema and kwarg references

## Goal

Update the in-memory schema definition and all keyword argument usages in `test_tool_result_store.py` to use `args_masked` instead of `args_json`.

## Scope

- `tests/test_tool_result_store.py`
  - `_SCHEMA_SQL`: rename `args_json` column → `args_masked`
  - All `store()` call keyword arguments: `args_json=` → `args_masked=`

## Assumptions

1. `ToolResultStore.store()` parameter is already renamed to `args_masked` (see `db_tool_results_py.md`).
2. No test currently reads back `result["args_json"]` from `get()` — if any do, rename those too.

## Implementation

### Target file

`tests/test_tool_result_store.py`

### Procedure

1. Read the file.
2. Replace `args_json` in `_SCHEMA_SQL` (line 19).
3. Replace all `args_json=` in `store()` call sites (lines ~80, 97, 109, 126, 154, 155, 156).
4. Run `uv run pytest tests/test_tool_result_store.py -v`.

### Method

Global replace of `args_json` → `args_masked` within this file. No logic changes.

### Details

**`_SCHEMA_SQL` (line 19):**
```sql
-- BEFORE
    args_json  TEXT,

-- AFTER
    args_masked  TEXT,
```

**All `store()` calls — keyword argument rename:**
```python
# BEFORE
store.store(..., args_json='{"path": "/tmp/x"}', ...)
store.store(..., args_json="{}", ...)

# AFTER
store.store(..., args_masked='{"path": "/tmp/x"}', ...)
store.store(..., args_masked="{}", ...)
```

There are approximately 8 call sites in the test file. Use replace_all=True or edit each occurrence.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_tool_result_store.py` | 0 errors |
| Type | `uv run mypy tests/test_tool_result_store.py` | no new errors |
| Unit tests | `uv run pytest tests/test_tool_result_store.py -v` | all pass |
