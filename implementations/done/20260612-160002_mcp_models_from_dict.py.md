# Goal

Replace `str(d.get(..., ""))` unconditional conversions in the four `from_dict()`
classmethods with explicit `isinstance` validation that raises `ValueError` on
unexpected types.

# Scope

- `scripts/mcp/cicd/models.py` — 2 occurrences (`auth_token`, `github_token`)
- `scripts/mcp/git/models.py` — 2 occurrences (`auth_token`, `audit_log_path`)
- `scripts/mcp/github/models.py` — 3 occurrences (`allowed_repos_mode`, `audit_log_path`, `llm_url`)


# Assumptions

1. All four files have `from_dict(cls, d: dict[str, Any])` classmethods that
   load from TOML config dicts. TOML strictly types values, so in practice these
   fields are always str. The `str()` cast is a silent fallback for wrong types.
2. Adding `isinstance` validation makes config schema errors fail-fast at load
   time rather than silently using a coerced value.
3. Each file adds a module-level helper `_get_str(d, key, default="")` to avoid
   repetition. The helper is file-local (no shared import needed).
4. `None` values from `d.get(key)` → return `default` (not an error); only
   non-str, non-None values raise.

# Implementation

## Target files

`scripts/mcp/cicd/models.py`, `scripts/mcp/git/models.py`,
`scripts/mcp/github/models.py`

## Procedure

For each file, add a module-level helper before the class definition:

```python
def _get_str(d: dict[str, Any], key: str, default: str = "") -> str:
    """Return d[key] as str, or default if absent/None; raises ValueError on wrong type."""
    v = d.get(key)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ValueError(
            f"Config key {key!r} must be str, got {type(v).__name__}"
        )
    return v
```

Then replace each `str(d.get("key", "default"))` with `_get_str(d, "key", "default")`.

### cicd/models.py changes

```python
auth_token=_get_str(d, "auth_token"),
github_token=_get_str(d, "github_token"),
```

### git/models.py changes

```python
auth_token=_get_str(d, "auth_token"),
audit_log_path=_get_str(d, "audit_log_path"),
```

### github/models.py changes

```python
allowed_repos_mode=_get_str(d, "allowed_repos_mode", "fail_closed"),
audit_log_path=_get_str(d, "audit_log_path"),
llm_url=_get_str(d, "llm_url"),
```

## Method

Add one helper per file + replace str() calls. No logic change.

# Validation plan

- `grep -rn "str(d\.get" scripts/mcp/cicd/models.py scripts/mcp/git/models.py scripts/mcp/github/models.py` → 0 hits
- `uv run ruff check scripts/mcp/cicd/models.py scripts/mcp/git/models.py scripts/mcp/github/models.py`
- `uv run mypy scripts/mcp/cicd/models.py scripts/mcp/git/models.py scripts/mcp/github/models.py`
- `uv run pytest tests/ -k "mcp" --ignore=tests/test_create_schema.py -v`
