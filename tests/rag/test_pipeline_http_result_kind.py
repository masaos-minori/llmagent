"""tests/test_pipeline_http_result_kind.py
Verifies HTTP RAG result classification in augment() and get_diagnostics().
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from db.helper import SQLiteHelper
from rag.exceptions import RagPipelineError
from rag.models_result import HttpResultKind, ResultSource
from rag.pipeline import RagPipeline, SearchDiagnostics
from rag.pipeline_service import CallRagResult
from rag.types import PipelineRunResult

_META_DDL = """
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


def _seed_local_db(tmp_path, *, generation) -> str:
    """Create a temp RAG DB with one ``rag_corpus_meta`` row at ``generation``.

    Returns the DB path wired into a pipeline via ``pipeline._rag_db_path``.
    """
    db_path = str(tmp_path / "generation.db")
    db = SQLiteHelper(db_path=db_path, sqlite_vec_so="")
    db.open()
    db.executescript(_META_DDL)
    db.commit()
    db.execute(
        "INSERT INTO rag_corpus_meta VALUES (?, ?, ?, ?, ?, ?)",
        ("known-cid", generation, "emb-x", "1", "1", "now"),
    )
    db.commit()
    db.close()
    return db_path


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


@pytest.mark.asyncio
async def test_remote_nonempty(monkeypatch) -> None:
    """Non-empty remote result -> http_result_kind='remote_nonempty'."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(
        http,
        rag_url,
        query,
        history_context,
        *,
        auth_token="",
        set_fetch_result=None,
        set_fallback_reason=None,
    ):
        return CallRagResult("success", "context text", 200, 50.0)

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == HttpResultKind.SUCCESS
    # Remote-served results return before the fallback identity gate runs, so no
    # local corpus generation is recorded (REQ-004 records generation only on the
    # fallback path). This is the real contract, not the assumed "records remote".
    assert diag["corpus_generation"] is None
    sd = pipeline.last_search_diagnostics
    assert sd.result_source == ResultSource.REMOTE
    assert sd.remote_status_code == 200
    assert sd.remote_latency_ms == 50.0
    assert sd.fallback_reason is None
    http_sr = next(
        r for r in pipeline.last_stage_results if r["stage_name"] == "HttpAugment"
    )
    assert http_sr["status"] == "success"
    assert http_sr["fallback_reason"] is None


@pytest.mark.asyncio
async def test_remote_empty(monkeypatch) -> None:
    """Empty remote result ('') -> http_result_kind='remote_empty', fallback_reason=None."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(
        http,
        rag_url,
        query,
        history_context,
        *,
        auth_token="",
        set_fetch_result=None,
        set_fallback_reason=None,
    ):
        return CallRagResult("empty", "", 200, 30.0)

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        with patch("rag.pipeline.SQLiteHelper.open") as mock_open:
            await pipeline.augment("query")

    # remote_empty must NOT trigger in-process pipeline
    mock_open.assert_not_called()

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == HttpResultKind.EMPTY
    # remote_empty also returns before the gate; no local generation recorded.
    assert diag["corpus_generation"] is None
    sd = pipeline.last_search_diagnostics
    assert sd.result_source == ResultSource.REMOTE
    assert sd.http_result_kind == HttpResultKind.EMPTY
    assert sd.remote_status_code == 200
    assert sd.remote_latency_ms == 30.0
    assert sd.fallback_reason is None
    http_sr = next(
        r for r in pipeline.last_stage_results if r["stage_name"] == "HttpAugment"
    )
    assert http_sr["status"] == "success"
    assert http_sr["fallback_reason"] is None


@pytest.mark.asyncio
async def test_in_process_fallback(monkeypatch) -> None:
    """None remote result -> http_result_kind='in_process_fallback'."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(
        http,
        rag_url,
        query,
        history_context,
        *,
        auth_token="",
        set_fetch_result=None,
        set_fallback_reason=None,
    ):
        if set_fallback_reason:
            set_fallback_reason("connection error")
        return CallRagResult("transient_failure", None, 503, 100.0)

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        with patch("rag.pipeline.SQLiteHelper.open"):
            # Also mock the in-process pipeline steps to avoid real execution
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
            await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == HttpResultKind.ERROR
    # This test mocks SQLiteHelper.open, so the local corpus is unverified and no
    # generation is recorded. The verified-local generation path is covered by
    # test_generation_records_local_on_verified_fallback with a seeded DB.
    assert diag["corpus_generation"] is None
    sd = pipeline.last_search_diagnostics
    assert sd.result_source == ResultSource.FALLBACK
    assert sd.http_result_kind == HttpResultKind.ERROR
    assert sd.remote_status_code == 503
    assert sd.remote_latency_ms == 100.0
    http_sr = next(
        r for r in pipeline.last_stage_results if r["stage_name"] == "HttpAugment"
    )
    assert http_sr["status"] == "fallback"
    assert http_sr.get("fallback_reason") is not None


@pytest.mark.asyncio
async def test_no_http_mode(monkeypatch) -> None:
    """No rag_query_service_url -> http_result_kind=None."""
    pipeline = _make_pipeline(rag_query_service_url="")
    # No HTTP call; mock in-process stages
    with patch("rag.pipeline.SQLiteHelper.open"):
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
        await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == HttpResultKind.NOT_USED
    # No HTTP mode still enters the fallback gate path; with the mocked (unverified)
    # DB no generation is recorded. The verified path is covered separately.
    assert diag["corpus_generation"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [401, 403])
async def test_auth_error_fails_closed_without_in_process_fallback(
    monkeypatch, status: int
) -> None:
    """HTTP 401/403 -> RagPipelineError; in-process pipeline is never entered."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(*args, **kwargs):
        if kwargs.get("set_fallback_reason"):
            kwargs["set_fallback_reason"](f"http_auth_error: {status}")
        return CallRagResult("auth_error", None, status, 0.0)

    run_mock = AsyncMock()
    monkeypatch.setattr(pipeline, "run", run_mock)

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        with pytest.raises(RagPipelineError, match=str(status)):
            await pipeline.augment("query")

    run_mock.assert_not_called()
    sd = pipeline.last_search_diagnostics
    assert sd.http_result_kind == HttpResultKind.AUTH_ERROR
    assert sd.remote_status_code == status


# ── Recorded corpus generation per result kind (RAGCORPUS001 REQ-004/007) ───────


@pytest.mark.asyncio
async def test_generation_records_local_on_verified_fallback(
    tmp_path, monkeypatch
) -> None:
    """Fallback on a verified local corpus records the LOCAL generation (REQ-004)."""
    pipeline = _make_pipeline()
    pipeline._rag_db_path = _seed_local_db(tmp_path, generation=7)
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
        if kwargs.get("set_fallback_reason"):
            kwargs["set_fallback_reason"]("connection error")
        return CallRagResult("transient_failure", None, 503, 100.0)

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    # Records the generation of the corpus that serves the result (the local one).
    assert diag["corpus_generation"] == 7
    assert diag["identity_degraded"] is False
    run_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_generation_none_when_unverified(tmp_path, monkeypatch) -> None:
    """A corrupt (unverifiable) local corpus records no generation (REQ-007)."""
    pipeline = _make_pipeline(rag_query_service_url="")
    # Non-integer index_generation makes compute_identity raise; compute_local_identity
    # treats it as unverified, so no generation is recorded.
    db_path = str(tmp_path / "corrupt.db")
    db = SQLiteHelper(db_path=db_path, sqlite_vec_so="")
    db.open()
    db.executescript(_META_DDL)
    db.commit()
    db.execute(
        "INSERT INTO rag_corpus_meta VALUES (?, ?, ?, ?, ?, ?)",
        ("known-cid", "not-an-int", "emb-x", "1", "1", "now"),
    )
    db.commit()
    db.close()
    pipeline._rag_db_path = db_path
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

    await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["corpus_generation"] is None
    assert diag["identity_degraded"] is False
    run_mock.assert_awaited_once()
