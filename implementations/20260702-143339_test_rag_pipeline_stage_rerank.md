# Implementation Procedure: Add TestRagPipelineRunStage to tests/test_rag_pipeline_stage.py

## Goal

Add a pipeline-level test class `TestRagPipelineRunStage` that verifies `RagPipeline._run_stage()`
catches `RagRerankError` (as `RuntimeError`), records `StageResult.status="failure"`, and does
not re-raise the exception. This closes the gap between the stage-level test
(`test_rerank_raises_on_error`, which tests `RerankStage.run()` propagation) and the pipeline-level
absorption behavior.

## Scope

- **In scope:** One new test class with one test method, appended to
  `tests/test_rag_pipeline_stage.py`
- **Out of scope:** Modifying existing test classes; adding new fixtures; any change to
  `scripts/rag/pipeline.py` or `scripts/rag/stages/rerank.py`

## Assumptions

1. `RagRerankError` is defined in `scripts/rag/llm_prompts.py:73` as
   `class RagRerankError(RuntimeError)`. It is importable as `from rag.llm_prompts import RagRerankError`.
2. `_run_stage()` signature (pipeline.py line 194):
   ```python
   async def _run_stage(self, stage: PipelineStage, ctx: PipelineContext, db: SQLiteHelper) -> None
   ```
3. After catching an exception, `_run_stage()` appends a `StageResult` to `ctx.stage_results`
   with `status="failure"` (pipeline.py lines 215–226).
4. `RagPipeline.__init__` requires `httpx.AsyncClient` and a `RagConfig`-compatible object.
   The existing `_make_rag_cfg()` helper (line 42 of the test file) returns a `_RagCfg` that
   satisfies the constructor without triggering config file I/O.
5. `SQLiteHelper` passed as `db` argument to `_run_stage()` is never called by the
   `RerankStage.run()` mock, so `MagicMock()` is sufficient.
6. `PipelineContext` is imported from `rag.stage` (already imported in the test file, line 11).
7. No new imports are needed in the test file beyond those already present; `httpx` must be
   imported inside the test method (pattern used in `TestRagPipelineLastTimings`, line 271).

## Implementation

### Target file

`tests/test_rag_pipeline_stage.py`

### Procedure

Append the following class after the last existing class (`TestSemanticCacheDimensionGuard`,
which ends at line 358).

### Method

Use the Edit tool. Insert after the final line of `TestSemanticCacheDimensionGuard`:

```
old_string (anchor — the last two lines of the file):
    def test_lookup_empty_cache_returns_none(self) -> None:
        from rag.cache import SemanticCache

        cache = SemanticCache()
        assert cache.lookup([1.0, 2.0, 3.0]) is None

new_string (original content preserved, new class appended):
    def test_lookup_empty_cache_returns_none(self) -> None:
        from rag.cache import SemanticCache

        cache = SemanticCache()
        assert cache.lookup([1.0, 2.0, 3.0]) is None


# ---------------------------------------------------------------------------
# RagPipeline._run_stage — pipeline-level failure absorption
# ---------------------------------------------------------------------------


class TestRagPipelineRunStage:
    @pytest.mark.asyncio
    async def test_run_stage_records_failure_on_rerank_error(self) -> None:
        """_run_stage() must absorb RagRerankError, record status='failure', not re-raise."""
        import httpx
        from unittest.mock import AsyncMock, MagicMock

        from rag.llm_prompts import RagRerankError
        from rag.pipeline import RagPipeline
        from rag.stage import PipelineContext
        from rag.stages.rerank import RerankStage

        http = MagicMock(spec=httpx.AsyncClient)
        pipeline = RagPipeline(http, _make_rag_cfg(use_rerank=True))

        # Construct a RerankStage whose run() raises RagRerankError
        llm = MagicMock()
        llm.cross_encoder_rerank = AsyncMock(side_effect=RagRerankError("rerank failed"))
        stage = RerankStage(_make_rag_cfg(use_rerank=True), llm)

        ctx = PipelineContext(query="q")

        # Must not raise; _run_stage() absorbs the error
        await pipeline._run_stage(stage, ctx, db=MagicMock())

        assert len(ctx.stage_results) == 1
        assert ctx.stage_results[0]["status"] == "failure"
        assert "rerank failed" in (ctx.stage_results[0]["fallback_reason"] or "")
```

### Details

- The test does **not** patch `MqeStage`, `SearchStage`, etc. — only `_run_stage()` is called
  directly; the full `run()` method is not invoked.
- `ctx.stage_results[0]` accesses the `StageResult` TypedDict appended by `_run_stage()`.
  Verify the key names against `rag/stage.py:StageResult` before writing assertions:
  expected keys are `stage_name`, `status`, `elapsed_seconds`, `fallback_reason`.
- `ctx.reranked` remains `[]` (its default) after the failure; no assertion on it is required
  for this test (the doc fix covers the empty-list behavior, not this test).
- Do not add `from unittest.mock import AsyncMock, MagicMock` at the module level — they are
  already imported at the top of the file (line 8). Remove the redundant local import inside
  the test method when writing the final code; retain only the imports not yet at module scope
  (`httpx`, `RagRerankError`, `RagPipeline`, `PipelineContext`, `RerankStage`).

## Validation plan

| Check | Command | Expected result |
|---|---|---|
| New test passes | `uv run pytest tests/test_rag_pipeline_stage.py::TestRagPipelineRunStage -v` | 1 test PASSED |
| Full test file passes | `uv run pytest tests/test_rag_pipeline_stage.py -v` | All tests PASSED |
| Lint | `ruff check tests/test_rag_pipeline_stage.py` | 0 errors |
| Type check | `mypy tests/test_rag_pipeline_stage.py` | No new errors |
| No duplicate test names | `grep -n "def test_run_stage_records_failure" tests/test_rag_pipeline_stage.py` | Exactly 1 hit |
