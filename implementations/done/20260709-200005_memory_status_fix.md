# Implementation: memory visibility — fix build_memory_status() for embedding-disabled state

## Goal

Fix `build_memory_status()` in `memory_status.py` to handle the `embed_client is None` case without returning `None`, emitting a `MemoryStatus` with `embedding_enabled=False` and `last_retrieval_mode="fts_only"`.

## Scope

- `scripts/agent/commands/memory_status.py`

## Assumptions

1. `build_memory_status()` currently returns `None` when `embed_client is None` (line 70).
2. `MemoryStatus` already has `memory_layer_enabled`, `embedding_enabled`, `circuit_open`, `last_retrieval_mode` fields.

## Implementation

### Target file

`scripts/agent/commands/memory_status.py`

### Procedure

1. In `build_memory_status()`, change the `embed_client is None` branch to return a `MemoryStatus` instead of `None`:
   - `memory_layer_enabled=True`
   - `embedding_enabled=False`
   - `circuit_open=False` (no embedder to have circuit issues)
   - `last_retrieval_mode="fts_only"`
2. Ensure all existing callers of `build_memory_status()` handle the new return value (no longer `None`).

### Method

```python
def build_memory_status(
    embed_client: EmbeddingClient | None,
    store: MemoryStore,
    retriever: MemoryRetriever,
) -> MemoryStatus | None:
    if embed_client is None:
        # Return a status instead of None
        return MemoryStatus(
            memory_layer_enabled=True,
            embedding_enabled=False,
            circuit_open=False,
            last_retrieval_mode="fts_only",
        )
    # ... existing logic
```

### Details

- Update any caller that checks `build_memory_status() is None` to handle the new `embedding_enabled=False` status.
- Return type can stay `MemoryStatus | None` for backward compatibility, or change to `MemoryStatus` if `None` is no longer returned.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Memory status tests | `uv run pytest tests/test_memory_status.py -v` | Pass |
| Type check | `uv run mypy scripts/` | No new errors |
