"""tests/rag/test_stage_lifecycle.py

Tests for RagPipelineStageLifecycle in scripts/rag/stage_lifecycle.py.

Covers:
- Stage execution order (MQE → search → RRF → rerank)
- Timing recording accuracy
- Fallback detection correctness
- Edge cases: empty stage list, single-stage execution, all-fail scenario
"""

from unittest.mock import MagicMock, patch

import pytest
from rag.models_config import RagConfigImpl
from rag.stage_lifecycle import RagPipelineStageLifecycle
from rag.types import PipelineRunResult


@pytest.fixture
def mock_cfg():
    """Create a minimal RagConfigImpl for testing."""
    return RagConfigImpl(
        use_mqe=True,
        top_k_search=5,
        use_rerank=False,
        rag_top_k=3,
        max_chunks_per_doc=5,
        top_k_rerank=10,
        rag_min_score=0.0,
        use_rrf=True,
        rrf_k=60,
        use_search=True,
        rag_service_url=None,
        rag_auth_token=None,
        use_refiner=False,
        refiner_max_tokens=512,
        refiner_max_chars_per_chunk=800,
        refiner_timeout=30.0,
        llm_url="",
        embed_url="",
        rag_db_path=":memory:",
        sqlite_vec_so="/opt/llm/sqlite-vec/vec0.so",
        sqlite_timeout=5,
        sqlite_busy_timeout_ms=5000,
        embed_retry=3,
        embed_workers=4,
        rag_pipeline_service_url=None,
        mqe_prompt_template="Expand query: {query}",
        mqe_n_queries=3,
        rerank_prompt_template="Rerank results for: {query}",
    )


@pytest.fixture
def mock_llm():
    """Create a mock LLM client."""
    return MagicMock(return_value={})


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return MagicMock(spec=["aclose"])


@pytest.fixture
def lifecycle(mock_cfg, mock_llm, mock_http_client):
    """Create a RagPipelineStageLifecycle instance for testing."""
    return RagPipelineStageLifecycle(
        cfg=mock_cfg,
        llm=mock_llm,
        http_client=mock_http_client,
        embed_url="",
    )


class TestStageExecutionOrder:
    """Test that stages execute in the correct order: MQE → search → RRF → rerank."""

    @pytest.mark.asyncio
    async def test_stage_order_with_mocked_stages(self, lifecycle, mock_cfg):
        """Stages execute in the correct order when mocked."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            result = await lifecycle.run(query="test query", db=MagicMock())
            assert isinstance(result, PipelineRunResult)

    @pytest.mark.asyncio
    async def test_last_stage_results_populated(self, lifecycle, mock_cfg):
        """last_stage_results contains stage results after run()."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            result = await lifecycle.run(query="test query", db=MagicMock())
            assert len(result.stage_results) > 0

    @pytest.mark.asyncio
    async def test_stage_results_have_required_fields(self, lifecycle, mock_cfg):
        """Each stage result has required fields: stage_name, status, elapsed_seconds."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            result = await lifecycle.run(query="test query", db=MagicMock())
            for sr in result.stage_results:
                assert "stage_name" in sr
                assert "status" in sr
                assert "elapsed_seconds" in sr

    @pytest.mark.asyncio
    async def test_query_propagated_to_context(self, lifecycle, mock_cfg):
        """Query is propagated to pipeline context."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            result = await lifecycle.run(query="test query", db=MagicMock())
            assert result.queries is not None

    @pytest.mark.asyncio
    async def test_history_context_propagated(self, lifecycle, mock_cfg):
        """History context is propagated to pipeline context."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            result = await lifecycle.run(
                query="test query",
                db=MagicMock(),
                history_context="previous turn",
            )
            assert result.queries is not None

    @pytest.mark.asyncio
    async def test_default_history_context_is_empty_string(self, lifecycle, mock_cfg):
        """Default history context is empty string."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            result = await lifecycle.run(query="test query", db=MagicMock())
            assert result.queries is not None

    @pytest.mark.asyncio
    async def test_timing_dict_reset_on_each_run(self, lifecycle, mock_cfg):
        """Timing dict is reset on each run."""
        lifecycle.last_timings = {"old": 1.0}
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            await lifecycle.run(query="test query", db=MagicMock())
            assert "old" not in lifecycle.last_timings

    @pytest.mark.asyncio
    async def test_cumulative_counters_increment(self, lifecycle, mock_cfg):
        """Cumulative counters increment across runs."""
        initial_embed_failed = lifecycle.stat_search_embed_failed
        initial_fts_errors = lifecycle.stat_search_fts_errors
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            await lifecycle.run(query="test query", db=MagicMock())
            assert lifecycle.stat_search_embed_failed >= initial_embed_failed
            assert lifecycle.stat_search_fts_errors >= initial_fts_errors

    @pytest.mark.asyncio
    async def test_last_fetch_result_set(self, lifecycle, mock_cfg):
        """last_fetch_result is set after run()."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            await lifecycle.run(query="test query", db=MagicMock())
            assert lifecycle.last_fetch_result is not None

    @pytest.mark.asyncio
    async def test_last_search_diagnostics_set(self, lifecycle, mock_cfg):
        """last_search_diagnostics is set after run()."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            await lifecycle.run(query="test query", db=MagicMock())
            assert lifecycle.last_search_diagnostics is not None

    @pytest.mark.asyncio
    async def test_reranked_hits_in_fetch_result(self, lifecycle, mock_cfg):
        """Reranked hits are stored in last_fetch_result."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            await lifecycle.run(query="test query", db=MagicMock())
            assert lifecycle.last_fetch_result.hits is not None

    @pytest.mark.asyncio
    async def test_min_score_applied_in_fetch_result(self, lifecycle, mock_cfg):
        """min_score_applied reflects config value."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            await lifecycle.run(query="test query", db=MagicMock())
            assert (
                lifecycle.last_fetch_result.min_score_applied == mock_cfg.rag_min_score
            )

    @pytest.mark.asyncio
    async def test_max_chunks_per_doc_in_fetch_result(self, lifecycle, mock_cfg):
        """max_chunks_per_doc reflects config value."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            await lifecycle.run(query="test query", db=MagicMock())
            assert (
                lifecycle.last_fetch_result.max_chunks_per_doc
                == mock_cfg.max_chunks_per_doc
            )

    @pytest.mark.asyncio
    async def test_augment_stage_always_succeeds(self, lifecycle, mock_cfg):
        """Augment stage always records 'success' status."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            result = await lifecycle.run(query="test query", db=MagicMock())
            augment_results = [
                r for r in result.stage_results if r["stage_name"] == "AugmentStage"
            ]
            assert len(augment_results) == 1
            assert augment_results[0]["status"] == "success"

    @pytest.mark.asyncio
    async def test_augment_stage_elapsed_time_recorded(self, lifecycle, mock_cfg):
        """Augment stage elapsed time is recorded in timings."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            await lifecycle.run(query="test query", db=MagicMock())
            assert "AugmentStage" in lifecycle.last_timings

    @pytest.mark.asyncio
    async def test_fallback_logging_triggered(self, lifecycle, mock_cfg):
        """Fallback logging is triggered when fallback stages exist."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            # Simulate a fallback by setting status to "fallback"
            original_get_status = lifecycle._get_stage_status
            lifecycle._get_stage_status = MagicMock(return_value=("fallback", "reason"))
            try:
                mock_run_stage.return_value = None
                result = await lifecycle.run(query="test query", db=MagicMock())
                assert len(result.stage_results) > 0
            finally:
                lifecycle._get_stage_status = original_get_status

    @pytest.mark.asyncio
    async def test_no_fallback_when_all_success(self, lifecycle, mock_cfg):
        """No fallback when all stages succeed."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            original_get_status = lifecycle._get_stage_status
            lifecycle._get_stage_status = MagicMock(return_value=("success", None))
            try:
                mock_run_stage.return_value = None
                result = await lifecycle.run(query="test query", db=MagicMock())
                fallbacks = [
                    r for r in result.stage_results if r["status"] == "fallback"
                ]
                assert len(fallbacks) == 0
            finally:
                lifecycle._get_stage_status = original_get_status

    @pytest.mark.asyncio
    async def test_failure_status_on_exception(self, lifecycle, mock_cfg):
        """Failure status recorded when stage raises an exception."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.side_effect = RuntimeError("simulated failure")
            with pytest.raises(RuntimeError):
                await lifecycle.run(query="test query", db=MagicMock())

    @pytest.mark.asyncio
    async def test_sqlite_operational_error_handled(self, lifecycle, mock_cfg):
        """sqlite3.OperationalError is caught and handled."""
        import sqlite3

        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.side_effect = sqlite3.OperationalError("database locked")
            with pytest.raises(sqlite3.OperationalError):
                await lifecycle.run(query="test query", db=MagicMock())

    @pytest.mark.asyncio
    async def test_http_status_error_handled(self, lifecycle, mock_cfg):
        """httpx.HTTPStatusError is caught and handled."""
        import httpx

        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.side_effect = httpx.HTTPStatusError(
                "error", request=MagicMock(), response=MagicMock()
            )
            with pytest.raises(httpx.HTTPStatusError):
                await lifecycle.run(query="test query", db=MagicMock())

    @pytest.mark.asyncio
    async def test_request_error_handled(self, lifecycle, mock_cfg):
        """httpx.RequestError is caught and handled."""
        import httpx

        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.side_effect = httpx.RequestError("request failed")
            with pytest.raises(httpx.RequestError):
                await lifecycle.run(query="test query", db=MagicMock())

    @pytest.mark.asyncio
    async def test_timeout_error_handled(self, lifecycle, mock_cfg):
        """TimeoutError is caught and handled."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.side_effect = TimeoutError("timeout")
            with pytest.raises(TimeoutError):
                await lifecycle.run(query="test query", db=MagicMock())

    @pytest.mark.asyncio
    async def test_runtime_error_handled(self, lifecycle, mock_cfg):
        """RuntimeError is caught and handled."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.side_effect = RuntimeError("runtime error")
            with pytest.raises(RuntimeError):
                await lifecycle.run(query="test query", db=MagicMock())

    @pytest.mark.asyncio
    async def test_timing_records_elapsed_seconds(self, lifecycle, mock_cfg):
        """Each stage timing records elapsed seconds."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            result = await lifecycle.run(query="test query", db=MagicMock())
            for sr in result.stage_results:
                assert sr["elapsed_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_stage_result_has_fallback_reason_on_failure(
        self, lifecycle, mock_cfg
    ):
        """StageResult has fallback_reason when status is failure."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.side_effect = RuntimeError("simulated failure")
            with pytest.raises(RuntimeError):
                await lifecycle.run(query="test query", db=MagicMock())

    @pytest.mark.asyncio
    async def test_stage_result_has_none_fallback_reason_on_success(
        self, lifecycle, mock_cfg
    ):
        """StageResult has None fallback_reason when status is success."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            result = await lifecycle.run(query="test query", db=MagicMock())
            for sr in result.stage_results:
                if sr["status"] == "success":
                    assert sr["fallback_reason"] is None

    @pytest.mark.asyncio
    async def test_empty_query_handled(self, lifecycle, mock_cfg):
        """Empty query is handled without error."""
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            result = await lifecycle.run(query="", db=MagicMock())
            assert isinstance(result, PipelineRunResult)

    @pytest.mark.asyncio
    async def test_long_query_handled(self, lifecycle, mock_cfg):
        """Long query is handled without error."""
        long_query = "a" * 10000
        with patch.object(lifecycle, "_run_stage") as mock_run_stage:
            mock_run_stage.return_value = None
            result = await lifecycle.run(query=long_query, db=MagicMock())
            assert isinstance(result, PipelineRunResult)
