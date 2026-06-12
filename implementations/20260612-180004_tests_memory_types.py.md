# Goal

Remove the `MEMORY_TYPES` import and `TestMemoryTypesConstant` test class from
`tests/test_memory_types.py` now that the constant is deleted.

# Scope

- `tests/test_memory_types.py`

# Assumptions

1. `MEMORY_TYPES` is deleted from `types.py` in Step 1.
2. `TestMemoryTypesConstant` tests only the constant itself, not behavior.
   The MemoryType enum coverage is already provided by other tests.
3. The import line `from agent.memory.types import MEMORY_TYPES, ...` must also
   be updated to remove `MEMORY_TYPES`.

# Implementation

## Target file

`tests/test_memory_types.py`

## Procedure

1. Find and update the import line that includes `MEMORY_TYPES`:
   ```python
   # Before (line 11)
   MEMORY_TYPES,

   # After — remove this line from the import
   ```

2. Delete the `TestMemoryTypesConstant` class (lines 162–173):
   ```python
   # Delete:
   # ── MEMORY_TYPES constant ──


   class TestMemoryTypesConstant:
       def test_memory_types_contains_semantic(self):
           assert "semantic" in MEMORY_TYPES

       def test_memory_types_contains_episodic(self):
           assert "episodic" in MEMORY_TYPES

       def test_memory_types_is_frozenset(self):
           assert isinstance(MEMORY_TYPES, frozenset)
   ```

3. Run pytest to confirm remaining tests pass.

## Method

Import line update + class deletion.

# Validation plan

- `grep -n "MEMORY_TYPES" tests/test_memory_types.py` → 0 hits
- `uv run pytest tests/test_memory_types.py -v`
