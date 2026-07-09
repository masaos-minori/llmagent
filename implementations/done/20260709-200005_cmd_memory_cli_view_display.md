# Implementation: memory visibility — improve status display and startup banner

## Goal

Improve `/memory status` display with clear mode labels and improve startup banner memory state visibility.

## Scope

- `scripts/agent/commands/cmd_memory.py` — improve status display
- `scripts/agent/cli_view.py` — improve startup banner memory state

## Assumptions

1. Phase 1 fix is complete; `build_memory_status()` no longer returns `None` for embedding-disabled state.
2. `MemoryStatus` fields are populated correctly.

## Implementation

### Target files

1. `scripts/agent/commands/cmd_memory.py`
2. `scripts/agent/cli_view.py`

### Procedure

1. In `cmd_memory.py`, add mode labels based on `MemoryStatus` fields:
   - `memory_layer_enabled=False` → "Memory layer disabled"
   - `memory_layer_enabled=True, embedding_enabled=False` → "Memory enabled, embedding disabled (FTS-only)"
   - `circuit_open=True` → "Degraded mode (circuit open, FTS fallback)"
   - `embedding_enabled=True, circuit_open=False` → "Hybrid mode (semantic + FTS)"
2. In `cli_view.py`, update startup banner to show memory state label instead of generic boolean.

### Details

- Use the same label strings consistently in both files.
- Keep existing output format; add a "Mode" line to `/memory status`.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Memory status display | `uv run pytest tests/test_cmd_memory.py -v` | Pass |
| Startup banner | Manual review | Shows correct mode |
