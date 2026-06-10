# Implementation: memory/types.py + mapper.py — MemoryQuery cleanup, EmbeddingErrorKind enum, tags strict

## Goal

1. Add `EmbeddingErrorKind` StrEnum to replace free-string `error_kind` in `EmbeddingResult`.
2. Remove `MemoryQuery.session_id` (unused in SQL queries).
3. Add `MemoryQuery.__post_init__` validation (query non-empty, limit >= 1, valid memory_type).
4. Strict tags handling in `mapper.py`: TypeError on non-list/non-string tags.

## Scope

- `scripts/agent/memory/types.py` — primary
- `scripts/agent/memory/mapper.py` — tags strict mode
- `scripts/agent/memory/injection.py` — remove `session_id=session_id` from MemoryQuery calls
- Tests: `tests/test_memory_layer.py`, `tests/test_memory_retriever.py`

## Assumptions

1. `EmbeddingErrorKind` is a `StrEnum` so `result.error_kind == "disabled"` comparisons continue to work.
2. `MemoryQuery.session_id` callers: only `injection.py:83,94`. After removing the field, remove those kwargs.
3. `mapper.py:row_to_entry` currently does `orjson.loads(tags_raw) if isinstance(tags_raw, str) else list(tags_raw)`.
   The `list(tags_raw)` branch allows non-list types; replace with `TypeError` raise.
4. No existing test passes `session_id` directly to `MemoryQuery`; confirmed by grep.

## Implementation

### types.py changes

```python
from enum import StrEnum

class EmbeddingErrorKind(StrEnum):
    DISABLED         = "disabled"
    CIRCUIT_OPEN     = "circuit_open"
    TIMEOUT          = "timeout"
    HTTP_ERROR       = "http_error"
    INVALID_RESPONSE = "invalid_response"
    UNKNOWN_ERROR    = "unknown_error"

@dataclass
class MemoryQuery:
    query: str
    memory_type: str | None = None
    limit: int = 10

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("MemoryQuery.query must not be empty")
        if self.memory_type is not None and self.memory_type not in ("semantic", "episodic"):
            raise ValueError(f"MemoryQuery.memory_type must be 'semantic', 'episodic', or None; got {self.memory_type!r}")
        if self.limit < 1:
            raise ValueError(f"MemoryQuery.limit must be >= 1, got {self.limit}")

@dataclass
class EmbeddingResult:
    success: bool
    embedding: list[float] | None = None
    error_kind: EmbeddingErrorKind | None = None
```

### mapper.py tags change

```python
# BEFORE
tags: list[str] = (
    orjson.loads(tags_raw) if isinstance(tags_raw, str) else list(tags_raw)
)

# AFTER
if isinstance(tags_raw, str):
    tags: list[str] = orjson.loads(tags_raw)
elif isinstance(tags_raw, list):
    tags = list(tags_raw)
else:
    raise TypeError(f"tags must be a JSON string or list, got {type(tags_raw).__name__}")
```

### injection.py: remove session_id from MemoryQuery

Remove `session_id=session_id,` from both MemoryQuery instantiations.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/memory/types.py scripts/agent/memory/mapper.py scripts/agent/memory/injection.py` | 0 errors |
| Type | `uv run mypy scripts/agent/memory/types.py` | no new errors |
| Tests | `uv run pytest tests/test_memory_*.py -x -q` | all pass |
