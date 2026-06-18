# Implementation: tests/test_stage_observability.py

## Goal

Verify that `RagPipeline.run()` populates `last_stage_results` correctly,
including fallback detection for disabled stages and success for normal paths.

## Scope

- New file: `tests/test_stage_observability.py`
- No production code changes.

## Assumptions

1. `RagPipeline` is constructed with a `SimpleNamespace` cfg (matches existing test pattern in `test_rag_pipeline.py`).
2. DB is a minimal in-memory SQLite with only `documents` and `chunks` tables (no vec/fts — search returns empty).
3. HTTP client and LLM are mocked (`AsyncMock`) to avoid network calls.
4. `pipeline.run()` is called with the in-memory DB helper.
5. Tests check `pipeline.last_stage_results` after `run()`.
6. Stage name values: "MqeStage", "SearchStage", "FusionStage", "RerankStage", "AugmentStage".

## Implementation

### Target file

`tests/test_stage_observability.py`

### Key helper

```python
def _make_cfg(**overrides):
    defaults = dict(
        use_mqe=True, use_rrf=True, use_rerank=True, use_refiner=False,
        use_search=True, rag_service_url="", rag_auth_token="",
        use_semantic_cache=False, top_k_search=5, top_k_rerank=10,
        rag_top_k=3, rag_min_score=0.0, max_chunks_per_doc=3,
        semantic_cache_max_size=10, semantic_cache_threshold=0.9,
        refiner_max_tokens=512, refiner_max_chars_per_chunk=800,
        refiner_timeout=30.0,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)
```

Minimal in-memory DB helper (reuse `_FakeSQLiteHelper` pattern with row_factory=True):
```python
_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    normalized_content TEXT
);
CREATE TABLE IF NOT EXISTS chunks_vec (chunk_id INTEGER PRIMARY KEY);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content,
    content = 'chunks',
    content_rowid = 'chunk_id',
    tokenize = 'unicode61'
)
"""
```

### Tests

4 tests in one class:

```python
class TestStageObservability:
    @pytest.mark.asyncio
    async def test_mqe_disabled_produces_fallback_status(self) -> None:
        cfg = _make_cfg(use_mqe=False)
        pipeline = _make_pipeline(cfg)
        db = _make_db()
        await pipeline.run("test query", db)
        statuses = {r["stage_name"]: r["status"] for r in pipeline.last_stage_results}
        assert statuses["MqeStage"] == "fallback"
        reasons = {r["stage_name"]: r["fallback_reason"] for r in pipeline.last_stage_results}
        assert reasons["MqeStage"] == "use_mqe=False"

    @pytest.mark.asyncio
    async def test_empty_search_produces_fallback_status(self) -> None:
        cfg = _make_cfg()  # use_mqe=True, but DB has no chunks → empty search results
        pipeline = _make_pipeline(cfg)
        db = _make_db()
        with patch("rag.stages.mqe._run_mqe", new=AsyncMock(return_value=["test query"])):
            await pipeline.run("test query", db)
        statuses = {r["stage_name"]: r["status"] for r in pipeline.last_stage_results}
        assert statuses["SearchStage"] == "fallback"
        reasons = {r["stage_name"]: r["fallback_reason"] for r in pipeline.last_stage_results}
        assert reasons["SearchStage"] == "no search results"

    @pytest.mark.asyncio
    async def test_rerank_disabled_produces_fallback_status(self) -> None:
        cfg = _make_cfg(use_rerank=False)
        pipeline = _make_pipeline(cfg)
        db = _make_db()
        await pipeline.run("test query", db)
        statuses = {r["stage_name"]: r["status"] for r in pipeline.last_stage_results}
        assert statuses["RerankStage"] == "fallback"
        reasons = {r["stage_name"]: r["fallback_reason"] for r in pipeline.last_stage_results}
        assert reasons["RerankStage"] == "use_rerank=False"

    @pytest.mark.asyncio
    async def test_all_stages_recorded_with_elapsed(self) -> None:
        cfg = _make_cfg(use_mqe=False, use_rrf=True, use_rerank=False)
        pipeline = _make_pipeline(cfg)
        db = _make_db()
        await pipeline.run("test query", db)
        names = [r["stage_name"] for r in pipeline.last_stage_results]
        assert "MqeStage" in names
        assert "SearchStage" in names
        assert "FusionStage" in names
        assert "RerankStage" in names
        assert "AugmentStage" in names
        for r in pipeline.last_stage_results:
            assert r["elapsed_seconds"] >= 0.0
```

Helper to create pipeline with mocked HTTP and LLM:
```python
def _make_pipeline(cfg) -> RagPipeline:
    http = AsyncMock()
    http.post = AsyncMock()
    pipeline = RagPipeline(http=http, cfg=cfg)
    # Patch _ModuleConfig to return minimal config
    pipeline._llm = MagicMock()
    pipeline._llm.expand_queries = AsyncMock(return_value=["test query"])
    pipeline._embed_url = ""
    return pipeline
```

The `_make_db()` helper creates an in-memory SQLite with the minimal schema above,
with `row_factory=True` set. Since there are no chunks, search returns empty results.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check tests/test_stage_observability.py` | 0 errors |
| Type check | `uv run mypy tests/test_stage_observability.py` | no new errors |
| Tests | `uv run pytest tests/test_stage_observability.py -v` | 4 passed |
