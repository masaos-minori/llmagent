# Goal

Add a non-dict type check to `_load_single()` and delete the `get_config()`
convenience wrapper (confirmed 0 callers).

# Scope

- `scripts/shared/config_loader.py`

# Assumptions

1. `get_config()` has 0 callers (confirmed by grep). Deletion is safe.
2. TOML and JSON files always produce a `dict` at the top level for valid configs.
   If `orjson.loads()` returns a non-dict (e.g. a list), it should raise `ValueError`
   immediately rather than propagating an `Any` that silently fails downstream.
3. The `_filter_meta_keys()` internal method accepts `dict[str, Any]` — no change needed.

# Implementation

## Target file

`scripts/shared/config_loader.py`

## Procedure

1. In `_load_single()`, after parsing, add dict check:
   ```python
   # For JSON files (already done for TOML via tomllib):
   parsed = orjson.loads(path.read_bytes())
   if not isinstance(parsed, dict):
       raise ValueError(
           f"Config file {path} must be a JSON/TOML object, "
           f"got {type(parsed).__name__}"
       )
   return parsed
   ```
   For TOML files, `tomllib.loads()` always returns `dict[str, Any]` by spec — no
   check needed. Only the JSON path requires the guard.

2. Delete the `get_config()` function and its docstring entirely.

3. Run ruff + mypy.

## Method

Delete one function; add 4-line isinstance guard in one branch.

## Details

After deleting `get_config()`, verify with:
```bash
grep -rn "get_config" scripts/
```
Expected: 0 hits (callers confirmed zero before implementation).

# Validation plan

- `grep -n "def get_config" scripts/shared/config_loader.py` → 0 hits
- `grep -rn "get_config" scripts/` → 0 hits
- `uv run ruff check scripts/shared/config_loader.py`
- `uv run mypy scripts/shared/config_loader.py`
- `uv run pytest tests/test_config_loader.py -v`
