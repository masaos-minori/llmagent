# Implementation: tests/test_rag_pipeline_stage.py — per-stage unit tests + latency test

## Goal

Add unit tests for each RAG pipeline stage (MqeStage, SearchStage, FusionStage, RerankStage, AugmentStage) and a test that verifies `RagPipeline.last_timings` is populated after `run()`.

## Scope

- `tests/test_rag_pipeline_stage.py` — add test classes for each stage and latency recording

## Assumptions

1. All stages follow the `PipelineStage` protocol: `async def run(self, ctx: PipelineContext, **kwargs) -> None`.
2. `MqeStage` takes `(cfg: dict, llm: RagLLM)`.
3. `SearchStage` takes `(cfg: dict)` and needs a `db` kwarg with `RagRepository`.
4. `FusionStage` takes `(cfg: dict)`.
5. `RerankStage` takes `(cfg: dict, llm: RagLLM)`.
6. `AugmentStage` takes no args.
7. `RagLLM` methods are async; mock them with `AsyncMock`.
8. `SearchStage` calls `RagRepository` which requires a DB connection; pass a mock `db` object.

## Implementation

### Target file

`tests/test_rag_pipeline_stage.py`

### Procedure

1. Read the current file (retain existing observer tests).
2. Add import statements for stage classes and mocks.
3. Add one test class per stage.
4. Add `TestRagPipelineLastTimings` class.
5. Run `uv run pytest tests/test_rag_pipeline_stage.py -v`.

### Method

New `pytest` test classes using `AsyncMock` and `MagicMock`. Each stage test:
- constructs the stage with minimal config
- builds a `PipelineContext`
- calls `await stage.run(ctx, db=mock_db)`
- asserts that `ctx` fields are updated as expected

### Details

**Imports to add:**
```python
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from rag.stage import PipelineContext
from rag.stages.mqe import MqeStage
from rag.stages.search import SearchStage
from rag.stages.fusion import FusionStage
from rag.stages.rerank import RerankStage
from rag.stages.augment import AugmentStage
```

**TestMqeStage:**
```python
class TestMqeStage:
    @pytest.mark.asyncio
    async def test_mqe_disabled_returns_original_query(self) -> None:
        llm = MagicMock()
        stage = MqeStage({"use_mqe": False}, llm)
        ctx = PipelineContext(query="hello")
        await stage.run(ctx)
        assert ctx.queries == ["hello"]

    @pytest.mark.asyncio
    async def test_mqe_enabled_calls_llm(self) -> None:
        llm = MagicMock()
        llm.expand_queries = AsyncMock(return_value=["hello", "hi there"])
        stage = MqeStage({"use_mqe": True}, llm)
        ctx = PipelineContext(query="hello")
        await stage.run(ctx)
        assert ctx.queries == ["hello", "hi there"]
        llm.expand_queries.assert_called_once_with("hello")

    @pytest.mark.asyncio
    async def test_mqe_falls_back_on_exception(self) -> None:
        llm = MagicMock()
        llm.expand_queries = AsyncMock(side_effect=RuntimeError("fail"))
        stage = MqeStage({"use_mqe": True}, llm)
        ctx = PipelineContext(query="hello")
        await stage.run(ctx)
        assert ctx.queries == ["hello"]
```

**TestFusionStage:**
```python
class TestFusionStage:
    @pytest.mark.asyncio
    async def test_rrf_merge_combines_lists(self) -> None:
        from rag.stages.fusion import FusionStage
        stage = FusionStage({"top_k_rrf": 10})
        ctx = PipelineContext(query="q")
        ctx.search_results = [
            [{"chunk_id": 1, "score": 0.9, "content": "a", "url": "u1"}],
            [{"chunk_id": 2, "score": 0.8, "content": "b", "url": "u2"}],
        ]
        await stage.run(ctx)
        assert len(ctx.merged) >= 1
```

**TestRerankStage:**
```python
class TestRerankStage:
    @pytest.mark.asyncio
    async def test_rerank_disabled_returns_top_k(self) -> None:
        llm = MagicMock()
        cfg = {"use_rerank": False, "rag_top_k": 2, "max_chunks_per_doc": 5}
        stage = RerankStage(cfg, llm)
        hits = [{"chunk_id": i, "score": 0.9, "content": f"c{i}", "url": "u"} for i in range(5)]
        ctx = PipelineContext(query="q")
        ctx.merged = hits
        await stage.run(ctx)
        assert len(ctx.reranked) <= 2
```

**TestAugmentStage:**
```python
class TestAugmentStage:
    @pytest.mark.asyncio
    async def test_augment_sets_result(self) -> None:
        stage = AugmentStage()
        ctx = PipelineContext(query="q")
        ctx.reranked = [{"chunk_id": 1, "content": "text", "url": "http://x.com", "title": "T"}]
        await stage.run(ctx)
        assert ctx.augment_result  # non-empty string
```

**TestRagPipelineLastTimings:**
```python
class TestRagPipelineLastTimings:
    @pytest.mark.asyncio
    async def test_last_timings_populated_after_run(self) -> None:
        """Verify run() populates last_timings with one entry per stage."""
        import httpx
        from unittest.mock import patch, AsyncMock
        from shared.types import RagConfig
        from rag.pipeline import RagPipeline

        cfg = RagConfig(use_search=True, use_mqe=False, use_rerank=False, ...)
        http = MagicMock(spec=httpx.AsyncClient)
        pipeline = RagPipeline(http, cfg)

        mock_db = MagicMock()

        # Patch all stage run() methods to be no-ops
        with patch.object(MqeStage, "run", new_callable=AsyncMock) as m:
            # ... patch each stage
            pass

        # Simpler approach: mock the entire stages list
        with patch("rag.pipeline.MqeStage") as MockMqe, \
             patch("rag.pipeline.SearchStage") as MockSearch, \
             patch("rag.pipeline.FusionStage") as MockFusion, \
             patch("rag.pipeline.RerankStage") as MockRerank, \
             patch("rag.pipeline.AugmentStage") as MockAugment:
            for M in (MockMqe, MockSearch, MockFusion, MockRerank, MockAugment):
                M.return_value.run = AsyncMock()
            await pipeline.run("test query", mock_db)

        assert len(pipeline.last_timings) == 5
        for stage_name in ("MqeStage", "SearchStage", "FusionStage", "RerankStage", "AugmentStage"):
            assert stage_name in pipeline.last_timings
            assert isinstance(pipeline.last_timings[stage_name], float)
            assert pipeline.last_timings[stage_name] >= 0.0
```

Note: Adjust `RagConfig` constructor call based on actual field names (check `shared/types.py`).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_rag_pipeline_stage.py` | 0 errors |
| Type | `uv run mypy tests/test_rag_pipeline_stage.py` | no new errors |
| Unit tests | `uv run pytest tests/test_rag_pipeline_stage.py -v` | all pass |
| Coverage | changed lines covered | ≥ 90% |
