"""tests/test_rag_http_mode.py
Pipeline-level diagnostics for HTTP RAG result classification.

These tests assert on SearchDiagnostics fields NOT covered by
test_pipeline_http_result_kind.py (which asserts on stage_results).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from rag.corpus_identity import CorpusIdentity
from rag.exceptions import RagPipelineError
from rag.models_result import HttpResultKind, ResultSource, SearchDiagnostics
from rag.pipeline import RagPipeline
from rag.pipeline_service import CallRagResult
from rag.types import PipelineRunResult


def _make_pipeline(rag_query_service_url: str = "http://rag.local") -> RagPipeline:
    """Return a RagPipeline with HTTP mode enabled and mocked HTTP client."""
    cfg = MagicMock()
    cfg.rag_query_service_url = rag_query_service_url
    cfg.use_refiner = False
    cfg.use_search = True
    cfg.llm_url = "http://llm.local"
    cfg.embed_url = "http://embed.local"
    http_mock = MagicMock(spec=httpx.AsyncClient)
    pipeline = RagPipeline(http_mock, cfg)
    pipeline.last_fetch_result = None
    pipeline.last_search_diagnostics = SearchDiagnostics()
    return pipeline


# ── HTTP result classification (rag/http_augment.py) ─────────────────────────


@pytest.mark.asyncio
async def test_remote_empty_sets_result_source_remote() -> None:
    """Remote empty result ('') -> last_search_diagnostics.http_result_kind == EMPTY."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(*args, **kwargs):
        return CallRagResult("empty", "", 200, 30.0)

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    assert pipeline.last_search_diagnostics.http_result_kind == HttpResultKind.EMPTY
    sd = pipeline.last_search_diagnostics
    assert sd.result_source == ResultSource.REMOTE
    assert sd.remote_status_code == 200
    assert sd.remote_latency_ms == 30.0
    assert sd.fallback_reason is None


@pytest.mark.asyncio
async def test_remote_empty_does_not_trigger_in_process(monkeypatch) -> None:
    """remote_empty (status 200, empty result) must NOT fall back to in-process pipeline."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(*args, **kwargs):
        return CallRagResult("empty", "", 200, 5.0)

    run_mock = AsyncMock()
    monkeypatch.setattr(pipeline, "run", run_mock)

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        result = await pipeline.augment("test query")

    assert result == ""
    run_mock.assert_not_called()


# ── In-process fallback behavior (rag/pipeline.py) ─────────────────────────────


@pytest.mark.asyncio
async def test_in_process_fallback_sets_result_source_fallback(monkeypatch) -> None:
    """In-process fallback -> last_search_diagnostics.result_source == FALLBACK."""
    pipeline = _make_pipeline()
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    async def mock_call_rag_service(*args, **kwargs):
        return CallRagResult("transient_failure", None, 503, 100.0)

    monkeypatch.setattr(
        pipeline,
        "run",
        AsyncMock(
            return_value=PipelineRunResult(
                queries=["query"],
                search_results=[],
                merged=[],
                reranked=[],
                stage_results=[],
                diagnostics=SearchDiagnostics(),
            )
        ),
    )
    with (
        patch("rag.http_augment.call_rag_service", mock_call_rag_service),
        patch(
            "rag.pipeline.SQLiteHelper",
            return_value=MagicMock(open=MagicMock(return_value=mock_db)),
        ),
    ):
        await pipeline.augment("query")

    assert pipeline.last_search_diagnostics.result_source == ResultSource.FALLBACK
    sd = pipeline.last_search_diagnostics
    assert sd.http_result_kind == HttpResultKind.ERROR
    assert sd.remote_status_code == 503
    assert sd.remote_latency_ms == 100.0
    assert any(
        r.get("fallback_reason") is not None for r in pipeline.last_stage_results
    )


@pytest.mark.asyncio
async def test_fallback_reason_propagated_to_diagnostics(monkeypatch) -> None:
    """Fallback reason is propagated to diagnostics when in_process_fallback occurs."""
    pipeline = _make_pipeline()
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    async def mock_call_rag_service(*args, **kwargs):
        if kwargs.get("set_fallback_reason"):
            kwargs["set_fallback_reason"]("connection refused")
        return CallRagResult("transient_failure", None, 503, 100.0)

    monkeypatch.setattr(
        pipeline,
        "run",
        AsyncMock(
            return_value=PipelineRunResult(
                queries=["query"],
                search_results=[],
                merged=[],
                reranked=[],
                stage_results=[],
                diagnostics=SearchDiagnostics(),
            )
        ),
    )
    with (
        patch("rag.http_augment.call_rag_service", mock_call_rag_service),
        patch(
            "rag.pipeline.SQLiteHelper",
            return_value=MagicMock(open=MagicMock(return_value=mock_db)),
        ),
    ):
        await pipeline.augment("query")

    assert any(
        r.get("fallback_reason") is not None for r in pipeline.last_stage_results
    )


# ── Fallback identity gate integration (RAGCORPUS001 Phase 3, REQ-003) ─────────

# These tests drive augment() against a REAL temp RAG DB carrying a known
# ``rag_corpus_meta`` row, so the local identity is deterministic, and inject the
# remote identity through a mocked ``call_rag_service``. The gate (identity_gate.py)
# compares the injected remote identity against the seeded local one.

_RAG_META_DDL = """
CREATE TABLE IF NOT EXISTS rag_corpus_meta (
    corpus_id                TEXT    NOT NULL,
    index_generation         INTEGER NOT NULL,
    embedding_model_id       TEXT    NOT NULL,
    normalization_version    TEXT    NOT NULL,
    chunking_policy_version  TEXT    NOT NULL,
    updated_at               TEXT    NOT NULL,
    CHECK (rowid = 1)
);
"""

_LOCAL_CORPUS_ID = "known-cid"
_LOCAL_GENERATION = 5
_LOCAL_EMBED_ID = "emb-x"


def _seed_local_identity(tmp_path) -> str:
    """Create a temp RAG DB with a known meta row; return its path.

    The seeded row yields the local identity used by the gate below.
    """
    from db.helper import SQLiteHelper

    db_path = str(tmp_path / "gate_identity.db")
    db = SQLiteHelper(db_path=db_path, sqlite_vec_so="")
    db.open()
    db.executescript(_RAG_META_DDL)
    db.commit()
    db.execute(
        "INSERT INTO rag_corpus_meta VALUES (?, ?, ?, ?, ?, ?)",
        (_LOCAL_CORPUS_ID, _LOCAL_GENERATION, _LOCAL_EMBED_ID, "1", "1", "now"),
    )
    db.commit()
    db.close()
    return db_path


def _local_identity() -> CorpusIdentity:
    return CorpusIdentity(
        corpus_id=_LOCAL_CORPUS_ID,
        index_generation=_LOCAL_GENERATION,
        schema_version="1",
        embedding_model_id=_LOCAL_EMBED_ID,
        normalization_version="1",
        chunking_policy_version="1",
        verified=True,
    )


def _remote_matching() -> CorpusIdentity:
    """Remote identity identical to the seeded local identity."""
    return _local_identity()


def _remote_mismatching() -> CorpusIdentity:
    """Remote identity differing from the seeded local identity by corpus_id."""
    return CorpusIdentity(
        corpus_id="other-cid",
        index_generation=_LOCAL_GENERATION,
        schema_version="1",
        embedding_model_id=_LOCAL_EMBED_ID,
        normalization_version="1",
        chunking_policy_version="1",
        verified=True,
    )


def _pipeline_with_local_identity(tmp_path, *, policy: str = "reject") -> RagPipeline:
    pipeline = _make_pipeline()
    pipeline._rag_db_path = _seed_local_identity(tmp_path)
    pipeline._cfg.rag_identity_mismatch_policy = policy
    return pipeline


@pytest.mark.asyncio
async def test_identity_match_allows_fallback(tmp_path, monkeypatch) -> None:
    """Remote identity == local -> gate proceeds; fallback runs (result_source FALLBACK)."""
    pipeline = _pipeline_with_local_identity(tmp_path)
    run_mock = AsyncMock(
        return_value=PipelineRunResult(
            queries=["query"],
            search_results=[],
            merged=[],
            reranked=[],
            stage_results=[],
            diagnostics=SearchDiagnostics(),
        )
    )
    monkeypatch.setattr(pipeline, "run", run_mock)

    async def mock_call_rag_service(*args, **kwargs):
        return CallRagResult(
            "transient_failure",
            None,
            503,
            100.0,
            remote_identity=_remote_matching(),
        )

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    assert run_mock.await_count >= 1
    assert pipeline.last_search_diagnostics.result_source == ResultSource.FALLBACK


@pytest.mark.asyncio
async def test_missing_remote_identity_preserves_fallback(
    tmp_path, monkeypatch
) -> None:
    """Legacy payload without identity -> remote is None -> unverifiable -> fallback proceeds.

    The gate (user-approved 2026-10-31 semantics) preserves fallback when either side is
    missing rather than rejecting; the fallback-triggering path always carries
    remote_identity=None.
    """
    pipeline = _pipeline_with_local_identity(tmp_path)
    run_mock = AsyncMock(
        return_value=PipelineRunResult(
            queries=["query"],
            search_results=[],
            merged=[],
            reranked=[],
            stage_results=[],
            diagnostics=SearchDiagnostics(),
        )
    )
    monkeypatch.setattr(pipeline, "run", run_mock)

    async def mock_call_rag_service(*args, **kwargs):
        return CallRagResult("transient_failure", None, 503, 100.0)

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    assert run_mock.await_count >= 1
    assert pipeline.last_search_diagnostics.result_source == ResultSource.FALLBACK


@pytest.mark.asyncio
async def test_identity_mismatch_rejected_by_default(tmp_path, monkeypatch) -> None:
    """Different corpus_id + default 'reject' policy -> hard reject; no local re-execution."""
    pipeline = _pipeline_with_local_identity(tmp_path)
    run_mock = AsyncMock()
    monkeypatch.setattr(pipeline, "run", run_mock)

    async def mock_call_rag_service(*args, **kwargs):
        return CallRagResult(
            "transient_failure",
            None,
            503,
            100.0,
            remote_identity=_remote_mismatching(),
        )

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        result = await pipeline.augment("query")

    assert result == ""
    run_mock.assert_not_called()
    assert any(
        s["stage_name"] == "IdentityGate"
        and s["fallback_reason"] == "identity_mismatch"
        for s in pipeline.last_stage_results
    )


@pytest.mark.asyncio
async def test_identity_mismatch_degraded_policy(tmp_path, monkeypatch) -> None:
    """Different corpus_id + 'degraded' policy -> tolerated; fallback runs, marked degraded."""
    pipeline = _pipeline_with_local_identity(tmp_path, policy="degraded")
    run_mock = AsyncMock(
        return_value=PipelineRunResult(
            queries=["query"],
            search_results=[],
            merged=[],
            reranked=[],
            stage_results=[],
            diagnostics=SearchDiagnostics(),
        )
    )
    monkeypatch.setattr(pipeline, "run", run_mock)

    async def mock_call_rag_service(*args, **kwargs):
        return CallRagResult(
            "transient_failure",
            None,
            503,
            100.0,
            remote_identity=_remote_mismatching(),
        )

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    assert run_mock.await_count >= 1
    assert pipeline.get_diagnostics()["identity_degraded"] is True


@pytest.mark.asyncio
async def test_generation_recorded_on_fallback(tmp_path, monkeypatch) -> None:
    """The recorded corpus_generation on fallback is the local corpus generation (REQ-004)."""
    pipeline = _pipeline_with_local_identity(tmp_path)
    run_mock = AsyncMock(
        return_value=PipelineRunResult(
            queries=["query"],
            search_results=[],
            merged=[],
            reranked=[],
            stage_results=[],
            diagnostics=SearchDiagnostics(),
        )
    )
    monkeypatch.setattr(pipeline, "run", run_mock)

    async def mock_call_rag_service(*args, **kwargs):
        return CallRagResult("transient_failure", None, 503, 100.0)

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    assert pipeline.get_diagnostics()["corpus_generation"] == _LOCAL_GENERATION


@pytest.mark.parametrize("status", [401, 403])
@pytest.mark.asyncio
async def test_auth_error_still_never_falls_back(
    tmp_path, monkeypatch, status: int
) -> None:
    """HTTP 401/403 -> RagPipelineError; the identity gate is never consulted (REQ-009)."""
    pipeline = _pipeline_with_local_identity(tmp_path)
    run_mock = AsyncMock()
    monkeypatch.setattr(pipeline, "run", run_mock)

    async def mock_call_rag_service(*args, **kwargs):
        if kwargs.get("set_fallback_reason"):
            kwargs["set_fallback_reason"](f"http_auth_error: {status}")
        return CallRagResult("auth_error", None, status, 0.0)

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        with pytest.raises(RagPipelineError, match=str(status)):
            await pipeline.augment("query")

    run_mock.assert_not_called()
