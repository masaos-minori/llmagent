# Implementation: rag/models.py + shared/types.py — DTO and Protocol additions

## Goal

Add `TwoStageFetchResult` frozen dataclass to `rag/models.py`, add `history_context` field to `CacheEntry`, and add `use_semantic_cache: bool` to the `RagConfig` Protocol in `shared/types.py`.

## Scope

- `scripts/rag/models.py` — add `TwoStageFetchResult` dataclass; add `history_context: str = ""` to `CacheEntry`
- `scripts/shared/types.py` — add `use_semantic_cache: bool` to `RagConfig` Protocol
- No test changes required for this step alone

## Assumptions

- `RagHit` is already defined in `rag/models.py` and importable
- `CacheEntry` is a `frozen=True` dataclass with `embedding: list[float]` and `context_str: str`
- `RagConfig` Protocol is at `shared/types.py:42`; it currently lacks `use_semantic_cache`
- HTTP mode stores `list[dict]` in `last_reranked`; `TwoStageFetchResult.hits` must accept both `list[RagHit]` and `list[dict]`, hence `list[Any]`

## Implementation

### Target file

- `scripts/rag/models.py`
- `scripts/shared/types.py`

### Procedure

1. Open `scripts/rag/models.py`
2. Add `TwoStageFetchResult` frozen dataclass after the existing `CacheEntry` class
3. Add `history_context: str = ""` field to `CacheEntry`
4. Open `scripts/shared/types.py`
5. Add `use_semantic_cache: bool` field to the `RagConfig` Protocol class body

### Method

- Direct `Edit` tool on each file
- No new imports needed in `rag/models.py` (uses `dataclass`, `field`, `Any` already imported or add `Any` from `typing`)
- `shared/types.py` requires no new import

### Details

**`scripts/rag/models.py` — `CacheEntry` change:**

```python
# Before
@dataclass(frozen=True)
class CacheEntry:
    embedding: list[float]
    context_str: str

# After
@dataclass(frozen=True)
class CacheEntry:
    embedding: list[float]
    context_str: str
    history_context: str = ""
```

**`scripts/rag/models.py` — `TwoStageFetchResult` new class (add after `CacheEntry`):**

```python
@dataclass(frozen=True)
class TwoStageFetchResult:
    """Typed result capturing reranked hits with applied filter/dedup parameters."""

    hits: list[Any]           # list[RagHit] in-process; list[dict] HTTP mode
    min_score_applied: float  # rag_min_score used (0.0 = no score filter)
    max_chunks_per_doc: int   # per-doc dedup limit applied
```

- `Any` must be imported: `from typing import Any` (check if already present; add if missing)

**`scripts/shared/types.py` — `RagConfig` Protocol:**

```python
class RagConfig(Protocol):
    ...
    use_semantic_cache: bool   # add this line
```

## Validation plan

- `uv run mypy scripts/rag/models.py scripts/shared/types.py` — 0 errors
- `uv run ruff check scripts/rag/models.py scripts/shared/types.py` — 0 errors
- `grep -n "TwoStageFetchResult" scripts/rag/models.py` — matches the new class definition
- `grep -n "history_context" scripts/rag/models.py` — matches `CacheEntry.history_context`
- `grep -n "use_semantic_cache" scripts/shared/types.py` — matches the Protocol field
