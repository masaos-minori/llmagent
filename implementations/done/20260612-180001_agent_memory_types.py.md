# Goal

Delete the `MEMORY_TYPES` backward-compatibility constant from
`scripts/agent/memory/types.py`.

# Scope

- `scripts/agent/memory/types.py` — delete 2 lines (comment + constant)

# Assumptions

1. `MEMORY_TYPES` is only used in `jsonl_store.py` (confirmed by grep).
   That file is updated in Step 2.
2. `test_memory_types.py` imports and tests `MEMORY_TYPES` — updated in Step 4.
3. No other file imports `MEMORY_TYPES` from `types.py`.

# Implementation

## Target file

`scripts/agent/memory/types.py`

## Procedure

Delete lines 16–17:
```python
# Derived from MemoryType enum for backward compatibility
MEMORY_TYPES: frozenset[str] = frozenset(m.value for m in MemoryType)
```

## Method

Two-line deletion. No logic change.

# Validation plan

- `grep -n "MEMORY_TYPES" scripts/agent/memory/types.py` → 0 hits
- `uv run ruff check scripts/agent/memory/types.py`
- `uv run mypy scripts/agent/memory/types.py`
