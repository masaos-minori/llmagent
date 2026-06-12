# Goal

Remove the `d.get("memory_type", "")` silent fallback in `_entry_from_dict()` and
replace it with direct key access that raises `JsonlFormatError` on missing or
invalid `memory_type`.

# Scope

- `scripts/agent/memory/jsonl_store.py`

# Assumptions

1. `_entry_from_dict(d: dict)` currently uses `d.get("memory_type", "")` which
   returns `""` for a missing key. An empty string is not a valid `MemoryType`,
   so the subsequent `if memory_type not in MEMORY_TYPES` check catches it, but
   the error message says `Invalid memory_type=""` rather than "field missing".
2. The fix: use `d["memory_type"]` with a KeyError → `JsonlFormatError` conversion.
3. `read_all()` already raises `JsonlFormatError` on any parse error (no `strict=False`
   path exists anymore). Verify and confirm.
4. `asdict(entry)` in `write()` is fine as-is (dataclasses.asdict is correct for
   serialization). No change needed here.
5. `_entry_from_dict` parameter type `d: dict` → tighten to `d: dict[str, Any]`.

# Implementation

## Target file

`scripts/agent/memory/jsonl_store.py`

## Procedure

1. Replace the `_entry_from_dict` body:

```python
# Before
def _entry_from_dict(d: dict) -> MemoryEntry:
    memory_type = d.get("memory_type", "")
    if memory_type not in MEMORY_TYPES:
        raise JsonlFormatError(f"Invalid memory_type={memory_type!r}")
    return row_to_entry(d)
```

```python
# After
def _entry_from_dict(d: dict[str, Any]) -> MemoryEntry:
    """Deserialise one JSONL dict to MemoryEntry; raises JsonlFormatError on error."""
    if "memory_type" not in d:
        raise JsonlFormatError("Missing required field: 'memory_type'")
    memory_type = d["memory_type"]
    if not isinstance(memory_type, str):
        raise JsonlFormatError(
            f"'memory_type' must be a str, got {type(memory_type).__name__}"
        )
    if memory_type not in MEMORY_TYPES:
        raise JsonlFormatError(f"Invalid memory_type={memory_type!r}")
    return row_to_entry(d)
```

2. Add `from typing import Any` if not already imported (check existing imports).

3. Run ruff + mypy.

## Method

Direct key access with explicit `KeyError` check, plus type validation before the
membership check.

# Validation plan

- `grep -n '\.get("memory_type"' scripts/agent/memory/jsonl_store.py` → 0 hits
- `uv run ruff check scripts/agent/memory/jsonl_store.py`
- `uv run mypy scripts/agent/memory/jsonl_store.py`
- `uv run pytest tests/test_memory_jsonl.py tests/test_jsonl_store.py -v`
- Regression: write a JSONL line with no `memory_type` key → verify `JsonlFormatError`
  with message "Missing required field: 'memory_type'" is raised by `read_all()`
