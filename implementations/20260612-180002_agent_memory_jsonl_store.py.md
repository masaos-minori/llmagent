# Goal

Replace the `MEMORY_TYPES` frozenset membership check with a direct `MemoryType`
enum constructor call so the validation uses the enum itself.

# Scope

- `scripts/agent/memory/jsonl_store.py` — lines 21, 35–36

# Assumptions

1. `MEMORY_TYPES` is deleted from `types.py` in Step 1 (prerequisite).
2. `MemoryType` is defined in `agent.memory.enums` (already imported via mapper
   transitively, but must be imported explicitly here).
3. `MemoryType(memory_type)` raises `ValueError` when `memory_type` is not a valid
   enum value — catch and re-raise as `JsonlFormatError`.

# Implementation

## Target file

`scripts/agent/memory/jsonl_store.py`

## Procedure

1. Change import line 21:
   ```python
   # Before
   from agent.memory.types import MEMORY_TYPES, MemoryEntry

   # After
   from agent.memory.enums import MemoryType
   from agent.memory.types import MemoryEntry
   ```

2. Change lines 35–36:
   ```python
   # Before
   if memory_type not in MEMORY_TYPES:
       raise JsonlFormatError(f"Invalid memory_type={memory_type!r}")

   # After
   try:
       MemoryType(memory_type)
   except ValueError:
       raise JsonlFormatError(f"Invalid memory_type={memory_type!r}") from None
   ```

3. Run ruff + mypy.

## Method

Import change + 2-line validation replacement.

# Validation plan

- `grep -n "MEMORY_TYPES" scripts/agent/memory/jsonl_store.py` → 0 hits
- `uv run ruff check scripts/agent/memory/jsonl_store.py`
- `uv run mypy scripts/agent/memory/jsonl_store.py`
- `uv run pytest tests/test_memory_jsonl.py tests/test_jsonl_store.py -v`
