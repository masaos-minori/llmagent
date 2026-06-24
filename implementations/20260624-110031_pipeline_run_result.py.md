# Implementation Procedure: scripts/rag/types.py + pipeline.py + mcp/rag_pipeline/service.py

## Goal

`RagPipeline.run()` の戻り値を 4-tuple から `PipelineRunResult` 型付きデータクラスに変更する。

## Scope

**In:**
- `scripts/rag/types.py` — `PipelineRunResult` 定義
- `scripts/rag/pipeline.py` — 戻り値型アノテーション + return 文更新
- `scripts/mcp/rag_pipeline/service.py` — タプル展開から named attribute アクセスに更新
- docs 更新

**Out:** ランキング/取得ロジックの大幅変更

## Assumptions

1. `types.py` に `RawHit`, `RagHit`, `StageResult`, `SearchDiagnostics` が定義済み

## Implementation

### types.py — PipelineRunResult 追加

```python
import dataclasses
from typing import Optional

@dataclasses.dataclass
class PipelineRunResult:
    """Typed result from RagPipeline.run()."""
    queries: list[str]
    search_results: list[list[RawHit]]
    merged: list[RagHit]
    reranked: list[RagHit]
    stage_results: list[StageResult]
    diagnostics: SearchDiagnostics
    result_source: Optional[str] = None
```

### pipeline.py:298 — return 文更新

```python
return PipelineRunResult(
    queries=ctx.queries,
    search_results=ctx.search_results,
    merged=ctx.merged,
    reranked=ctx.reranked,
    stage_results=list(ctx.stage_results),
    diagnostics=ctx.search_diagnostics,
)
```

### service.py — tuple 展開 → named attribute

```python
# Before: queries, search_results, merged, reranked = await self._pipeline.run(...)
# After:
result = await self._pipeline.run(query_text, cfg=cfg)
queries = result.queries
reranked = result.reranked
# etc.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| tuple 展開なし | `grep -rn "pipeline\.run" scripts/` | no positional index access |
| Tests | `uv run pytest tests/ -k "rag_pipeline" -x -q` | all pass |
| 型チェック | `uv run mypy scripts/rag/pipeline.py` | no new errors |
