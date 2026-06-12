# Goal

Replace `str(args.get("db", ""))` and `str(args.get("sql", ""))` in
`sqlite/service.py` with explicit isinstance validation that raises `ValueError`
on non-str input.

# Scope

- `scripts/mcp/sqlite/service.py` — lines 101–102

# Assumptions

1. `args: ToolArgs` is `dict[str, Any]` at the external tool call boundary.
   Both `"db"` and `"sql"` should be `str`; a non-str value indicates a
   malformed tool call that should be rejected with `ValueError`.
2. An absent key (`args.get("db")` returns `None`) → return `""` as default,
   then the subsequent `if db not in self._db_allowlist` check catches empty
   string naturally.
3. No helper function needed — two inline replacements suffice.

# Implementation

## Target file

`scripts/mcp/sqlite/service.py`

## Procedure

```python
# Before
db = str(args.get("db", ""))
sql = str(args.get("sql", ""))

# After
db_raw = args.get("db", "")
if not isinstance(db_raw, str):
    raise ValueError(f"'db' must be str, got {type(db_raw).__name__}")
db = db_raw

sql_raw = args.get("sql", "")
if not isinstance(sql_raw, str):
    raise ValueError(f"'sql' must be str, got {type(sql_raw).__name__}")
sql = sql_raw
```

## Method

Two inline isinstance guards replacing unconditional `str()` coercions.

# Validation plan

- `grep -n "str(args\.get" scripts/mcp/sqlite/service.py` → 0 hits
- `uv run ruff check scripts/mcp/sqlite/service.py`
- `uv run mypy scripts/mcp/sqlite/service.py`
- `uv run pytest tests/ -k "sqlite" --ignore=tests/test_create_schema.py -v`
