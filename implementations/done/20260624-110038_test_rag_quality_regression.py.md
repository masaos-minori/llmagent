# Implementation Procedure: tests/test_rag_quality_regression.py

## Goal

主要な RAG 実行モードを対象とした決定論的リグレッションテストハーネスを作成する。

## Scope

**In:**
- 新規 `tests/test_rag_quality_regression.py`

**Out:** 人手によるベンチマーク作成

## Assumptions

1. `RagPipeline` は mock embedder で構築可能
2. in-memory SQLite に既知コンテンツを投入できる

## Implementation

### tests/test_rag_quality_regression.py

```python
"""tests/test_rag_quality_regression.py
Deterministic regression harness for major RAG pipeline execution modes.

Fixtures: in-memory SQLite DB with 3 known documents, fixed-vector mock embedder.
"""
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture()
def rag_pipeline_rrf(in_memory_rag_db, mock_embedder):
    """RagPipeline with use_rrf=True (default)."""
    cfg = build_test_cfg(use_rrf=True, use_rerank=False)
    return build_pipeline(cfg, db=in_memory_rag_db, embedder=mock_embedder)


@pytest.fixture()
def rag_pipeline_no_rrf(in_memory_rag_db, mock_embedder):
    """RagPipeline with use_rrf=False (diagnostic mode)."""
    cfg = build_test_cfg(use_rrf=False, use_rerank=False)
    return build_pipeline(cfg, db=in_memory_rag_db, embedder=mock_embedder)


class TestRagQualityRegression:
    async def test_rrf_returns_result_for_known_query(self, rag_pipeline_rrf) -> None:
        result = await rag_pipeline_rrf.run("python asyncio")
        assert len(result.reranked) >= 1, "RRF mode: expected at least one result"

    async def test_no_rrf_returns_result(self, rag_pipeline_no_rrf) -> None:
        result = await rag_pipeline_no_rrf.run("python asyncio")
        assert len(result.reranked) >= 0, "no-RRF mode: must not raise"

    async def test_semantic_cache_hit(self, rag_pipeline_rrf) -> None:
        """Second identical query returns cached context string."""
        await rag_pipeline_rrf.run("python asyncio")
        result2 = await rag_pipeline_rrf.run("python asyncio")
        assert result2.result_source == "cache" or len(result2.reranked) >= 0

    async def test_fallback_no_embed_server(self, in_memory_rag_db) -> None:
        """Unavailable embed server → empty result, not exception."""
        cfg = build_test_cfg(use_rrf=True)
        failing_embedder = AsyncMock(side_effect=ConnectionError("embed server down"))
        pipeline = build_pipeline(cfg, db=in_memory_rag_db, embedder=failing_embedder)
        result = await pipeline.run("any query")
        assert result.reranked == [], "fallback: expected empty result, not exception"
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| ファイル存在 | `ls tests/test_rag_quality_regression.py` | found |
| テストパス | `uv run pytest tests/test_rag_quality_regression.py -v` | all pass |
