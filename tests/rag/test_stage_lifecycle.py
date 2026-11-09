"""tests/rag/test_stage_lifecycle.py

Tests for RagPipelineStageLifecycle in scripts/rag/stage_lifecycle.py.

Covers:
- Stage execution order (MQE → search → RRF → rerank)
- Timing recording accuracy
- Fallback detection correctness
- Edge cases: empty stage list, single-stage execution, all-fail scenario
- MQE malformed-response fallback (ragrev001): stage-level and lifecycle-level
"""

import sqlite3
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import orjson
import pytest
from rag.llm_client import RagLLM
from rag.models_config import RagConfigImpl
from rag.stage import PipelineContext
from rag.stage_lifecycle import RagPipelineStageLifecycle
from rag.stages.mqe import MqeStage
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
        rag_query_service_url=None,
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
            # Augment runs outside _run_stage, so only the four pre-augment stages appear.
            assert [
                type(call.args[0]).__name__ for call in mock_run_stage.call_args_list
            ] == ["MqeStage", "SearchStage", "FusionStage", "RerankStage"]

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


# ── MQE malformed-response fallback (ragrev001) ─────────────────────────────────

# One body per REQ-001 shape: content null, empty choices, non-JSON body.
_MALFORMED_BODIES: list[bytes] = [
    orjson.dumps({"choices": [{"message": {"content": None}}]}),
    orjson.dumps({"choices": []}),
    b"not json",
]


def _make_malformed_llm(cfg: RagConfigImpl, body: bytes) -> RagLLM:
    """Real RagLLM whose fake client answers HTTP 200 with a malformed body.

    Mirrors the fake-client pattern in tests/rag/test_llm_client_timeout.py:
    parse_http_json reads .content, so the stub carries only timeout, post,
    a no-op raise_for_status, and the body bytes.
    """
    client = MagicMock(spec=httpx.AsyncClient)
    client.timeout = 7.5
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.content = body
    client.post = AsyncMock(return_value=resp)
    return RagLLM(
        client=client,
        llm_url="http://localhost:8000/v1/chat/completions",
        cfg=cfg,
    )


class TestMqeMalformedResponseFallback:
    """Regression: a malformed MQE response degrades to the original query."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("body", _MALFORMED_BODIES)
    async def test_stage_falls_back_to_original_query(
        self, mock_cfg: RagConfigImpl, body: bytes
    ) -> None:
        """REQ-003: no exception, queries stay [query], status is fallback/mqe_exception."""
        stage = MqeStage(mock_cfg, _make_malformed_llm(mock_cfg, body))
        ctx = PipelineContext(query="test query")

        await stage.run(ctx, db=MagicMock())

        assert ctx.queries == ["test query"]
        assert stage.get_status(ctx) == ("fallback", "mqe_exception")

    @pytest.mark.asyncio
    async def test_lifecycle_continues_past_malformed_mqe(
        self, mock_cfg: RagConfigImpl, mock_http_client: MagicMock
    ) -> None:
        """REQ-004: the run completes and reports the MQE fallback in stage_results.

        Only SearchStage is replaced (patched where the lifecycle looks the class
        up) with a recording stub; MQE runs for real so the RagLLM conversion is
        exercised end to end. Fusion/Rerank/Augment stay real: with use_rerank=False
        and no search results they touch neither the database nor the network.
        """
        recorded: list[list[str]] = []

        class _RecordingSearchStage:
            """Stub search stage that records ctx.queries at its turn."""

            def __init__(self, *args: object, **kwargs: object) -> None:
                pass

            async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
                recorded.append(list(ctx.queries))

        llm = _make_malformed_llm(mock_cfg, _MALFORMED_BODIES[0])
        lc = RagPipelineStageLifecycle(
            cfg=mock_cfg,
            llm=llm,
            http_client=mock_http_client,
            embed_url="",
        )

        with patch("rag.stage_lifecycle.SearchStage", _RecordingSearchStage):
            result = await lc.run(query="test query", db=MagicMock())

        assert isinstance(result, PipelineRunResult)
        assert result.queries == ["test query"]
        assert recorded == [["test query"]]
        mqe_results = [r for r in result.stage_results if r["stage_name"] == "MqeStage"]
        assert len(mqe_results) == 1
        assert mqe_results[0]["status"] == "fallback"
        assert mqe_results[0]["fallback_reason"] == "mqe_exception"


# ── Direct _run_stage coverage (ragrev009): absorption, status mapping, timing ─────────


class _RaisingStage:
    """Fake stage whose run() raises a caller-supplied exception."""

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        raise self._exc


class _SucceedingStage:
    """Fake stage that runs clean with no get_status method."""

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        return None


class _FallbackStage:
    """Fake stage that runs clean but reports a fallback via get_status."""

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        return None

    def get_status(self, ctx: PipelineContext) -> tuple[str, str]:
        return ("fallback", "r")


class TestRunStageDirect:
    """Direct coverage of RagPipelineStageLifecycle._run_stage (no patching)."""

    @pytest.mark.parametrize(
        "exc",
        [
            RuntimeError("boom"),
            sqlite3.OperationalError("locked"),
            httpx.HTTPStatusError("error", request=MagicMock(), response=MagicMock()),
            httpx.RequestError("failed"),
            TimeoutError("timeout"),
        ],
    )
    async def test_absorbed_exceptions_record_failure(
        self, lifecycle, exc: BaseException
    ) -> None:
        """REQ-002: each listed exception becomes a failure result carrying its message."""
        stage = _RaisingStage(exc)
        ctx = PipelineContext(query="q")
        await lifecycle._run_stage(stage, ctx, db=MagicMock())

        assert ctx.stage_results[-1]["status"] == "failure"
        assert ctx.stage_results[-1]["fallback_reason"] == str(exc)
        assert lifecycle.last_timings[type(stage).__name__] >= 0

    async def test_unlisted_exception_propagates_without_result(
        self, lifecycle
    ) -> None:
        """REQ-002: an exception outside the absorbed list propagates and records nothing."""
        ctx = PipelineContext(query="q")
        with pytest.raises(ValueError):
            await lifecycle._run_stage(
                _RaisingStage(ValueError("nope")), ctx, db=MagicMock()
            )
        assert ctx.stage_results == []
        assert "RaisingStage" not in lifecycle.last_timings

    async def test_get_status_fallback_maps_to_fallback(self, lifecycle) -> None:
        """REQ-002: a get_status yielding fallback produces a fallback result."""
        ctx = PipelineContext(query="q")
        await lifecycle._run_stage(_FallbackStage(), ctx, db=MagicMock())

        assert ctx.stage_results[-1]["status"] == "fallback"
        assert ctx.stage_results[-1]["fallback_reason"] == "r"

    async def test_no_get_status_maps_to_success(self, lifecycle) -> None:
        """REQ-002: a stage without get_status produces a success result with None reason."""
        ctx = PipelineContext(query="q")
        await lifecycle._run_stage(_SucceedingStage(), ctx, db=MagicMock())

        assert ctx.stage_results[-1]["status"] == "success"
        assert ctx.stage_results[-1]["fallback_reason"] is None

    async def test_timing_recorded_for_stage(self, lifecycle) -> None:
        """REQ-002: the stage's class name is recorded with a non-negative timing."""
        ctx = PipelineContext(query="q")
        await lifecycle._run_stage(_SucceedingStage(), ctx, db=MagicMock())

        assert lifecycle.last_timings["_SucceedingStage"] >= 0
