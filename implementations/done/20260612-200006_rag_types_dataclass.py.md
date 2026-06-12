# Goal

Convert `RawHit`, `MergedHit`, `RankedHit` from `TypedDict` to frozen `dataclass`,
change `PipelineStageResult.stage: str` to `PipelineStageName`, and update all
callers that use dict-style `hit["key"]` access.

# Scope

- `scripts/rag/types.py` — convert TypedDicts to dataclasses
- All files in `scripts/rag/` that access `hit["key"]` on `RawHit`/`MergedHit`/`RankedHit`

# Assumptions

1. `PipelineStageName` enum from `rag.enums` (Step 2-2 prerequisite).
2. `RagHit` alias was removed in Step 1-1.
3. Callers using `hit["chunk_id"]`, `hit["score"]` etc. must be updated to `hit.chunk_id`, `hit.score`.
4. Run `grep -rn 'hit\["' scripts/rag/` to enumerate all affected access patterns before editing.
5. `RawHit(TypedDict, total=False)` → `@dataclass(frozen=True)` with all fields explicitly typed.
   Fields currently `total=False` become `| None` with default `None`.
6. `MergedHit` inherits `RawHit` fields; `RankedHit` inherits `MergedHit` fields.
   Use composition or flat dataclasses (flat is simpler for dataclasses).

# Implementation

## Target file

`scripts/rag/types.py`, then all callers

## Procedure

1. Read current `RawHit`/`MergedHit`/`RankedHit` field definitions.
2. Define new frozen dataclasses (flat, no inheritance):

```python
@dataclass(frozen=True)
class RawHit:
    chunk_id: str
    url: str
    title: str
    content: str
    lang: str
    score: float = 0.0
    distance: float | None = None
    # add any other fields currently in TypedDicts

@dataclass(frozen=True)
class MergedHit:
    chunk_id: str
    url: str
    title: str
    content: str
    lang: str
    score: float = 0.0
    rrf_score: float = 0.0
    distance: float | None = None

@dataclass(frozen=True)
class RankedHit:
    chunk_id: str
    url: str
    title: str
    content: str
    lang: str
    score: float = 0.0
    rrf_score: float = 0.0
    rerank_score: float | None = None
    distance: float | None = None
```

3. Change `PipelineStageResult.stage: str` → `stage: PipelineStageName`.
4. Update all callers: `hit["chunk_id"]` → `hit.chunk_id`, etc.
5. Run ruff + mypy.

## Method

TypedDict → dataclass; then grep-and-replace all dict access in callers.

# Validation plan

- `grep -rn 'hit\["' scripts/rag/` → 0 hits after conversion
- `uv run ruff check scripts/rag/`
- `uv run mypy scripts/rag/types.py`
- `uv run pytest tests/test_rag_pipeline.py tests/test_rag_utils.py -v`
