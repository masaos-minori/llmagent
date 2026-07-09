# Implementation: tests — memory visibility tests

## Goal

Add/update tests for the new memory status mode labels and embedding-disabled handling.

## Scope

- `tests/test_cmd_memory.py` — update if display behavior changed
- `tests/test_memory_status.py` — add tests for embedding-disabled state

## Assumptions

1. Phase 1 and Phase 2 changes are complete.

## Implementation

### Target files

1. `tests/test_memory_status.py`
2. `tests/test_cmd_memory.py`

### Procedure

1. In `test_memory_status.py`: add test cases for:
   - `build_memory_status()` with `embed_client=None` returns status (not None) with `embedding_enabled=False`
   - Mode label matches expected value for each state
2. In `test_cmd_memory.py`: update tests if display output format changed.

### Details

- Use existing test fixtures.
- Verify mode labels are exactly as documented.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Memory status tests | `uv run pytest tests/test_memory_status.py -v` | Pass |
| Cmd memory tests | `uv run pytest tests/test_cmd_memory.py -v` | Pass |
