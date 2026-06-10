# Implementation: mapper.py / jsonl_store.py — unify MemoryEntry reconstruction

## Goal

Eliminate duplicate `MemoryEntry` reconstruction logic:
- `mapper.py:row_to_entry()` is the canonical converter (SQLite row / dict → MemoryEntry).
- `jsonl_store.py:_entry_from_dict()` duplicates the same field mapping.

After this change, `_entry_from_dict` handles JSONL-specific pre-validation
(check `memory_type` in `MEMORY_TYPES`, return `None` on invalid), then delegates
the actual `MemoryEntry` construction to `row_to_entry(d)`.

## Scope

- **Target files**: `scripts/agent/memory/jsonl_store.py`, `scripts/agent/memory/mapper.py`
- `mapper.py` itself does not change — it is already correct.
- Only `jsonl_store.py:_entry_from_dict` changes.

## Assumptions

1. `row_to_entry` accepts `dict[str, Any]` (already supports this via `dict(row)`).
2. `row_to_entry` raises `ValueError` via `MemoryEntry.__post_init__` on invalid field values.
   `_entry_from_dict` wraps this in a `try/except Exception` and returns `None` — preserving behavior.
3. The JSONL-specific validation (`memory_type not in MEMORY_TYPES → return None`) must run
   before calling `row_to_entry` because `MemoryEntry.__post_init__` raises `ValueError`
   for invalid `memory_type`, which would be caught by the outer except and counted as malformed.
   Keeping the pre-check makes the failure mode explicit.
4. `_entry_from_dict` is a private function; no external callers to update.

## Implementation

### Target file

`scripts/agent/memory/jsonl_store.py`

### Procedure

1. Add import: `from agent.memory.mapper import row_to_entry`.
2. In `_entry_from_dict(d)`:
   - Keep the `memory_type` pre-check (lines 26-29).
   - Replace the explicit `MemoryEntry(...)` construction block with `return row_to_entry(d)`.
   - Keep the outer `try/except Exception` to catch `ValueError` from `row_to_entry`.

### Method

Direct textual edit.

### Details

```python
from agent.memory.mapper import row_to_entry  # add to imports

def _entry_from_dict(d: dict) -> MemoryEntry | None:
    """Deserialise one JSONL dict to MemoryEntry; return None on validation error."""
    try:
        memory_type = d.get("memory_type", "")
        if memory_type not in MEMORY_TYPES:
            logger.warning(f"Skipping JSONL entry: invalid memory_type={memory_type!r}")
            return None
        return row_to_entry(d)
    except Exception as e:
        logger.warning(f"Skipping malformed JSONL entry: {e}")
        return None
```

Remove the `source_type`, `session_id`, `turn_id`, `project`, `repo`, `branch`, `content`,
`summary`, `tags`, `importance`, `pinned`, `created_at`, `updated_at` explicit mapping lines.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/memory/jsonl_store.py` | 0 errors |
| Type | `uv run mypy scripts/agent/memory/jsonl_store.py` | no new errors |
| Tests | `uv run pytest tests/test_memory_jsonl.py tests/test_memory_store.py -x -q` | all pass |
