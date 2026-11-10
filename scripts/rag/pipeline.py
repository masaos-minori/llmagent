#!/usr/bin/env python3
"""scripts/rag/pipeline.py

RAG pipeline orchestration: MQE → vector/FTS search → RRF → Cross-Encoder rerank.

Pipeline order:
  [1] MQE     — RagLLM.expand_queries
  [2] Search  — get_embedding / RagRepository.vector_search / .fts_search
  [3] RRF     — RagScorer.rrf_merge
  [4] Rerank  — RagLLM.cross_encoder_rerank

Module layout:
   rag/repository.py      — RagRepository, RagScorer, FTS helpers
   rag/llm_client.py      — RagLLM, get_embedding, summarize_tool_result
   rag/pipeline_refiner.py — Context refiner (chunk compression)
   rag/config_resolution.py — resolve_rag_config() config resolution delegate
   rag/diagnostics.py       — PipelineDiagnostics structured diagnostics
   rag/db_connection.py     — RagDatabaseConnection context-manager DB wrapper
   rag/stage_lifecycle.py   — RagPipelineStageLifecycle run() lifecycle delegate
   rag/pipeline.py          — RagPipeline core orchestration (this file)
"""

import logging
from collections.abc import Callable
from typing import cast

import httpx
from db.helper import SQLiteHelper
from shared.llm_client import build_embed_url, build_llm_url
from shared.types import RagConfig

from rag.augment import AugmentRefiner
from rag.config_resolution import resolve_rag_config
from rag.db_connection import RagDatabaseConnection
from rag.diagnostics import PipelineDiagnostics
from rag.exceptions import RagPipelineError
from rag.identity_gate import compute_local_identity
from rag.llm_client import RagLLM
from rag.models_config import RagConfigImpl
from rag.models_data import TwoStageFetchResult
from rag.models_result import SearchDiagnostics
from rag.stage import StageResult
from rag.stage_lifecycle import RagPipelineStageLifecycle
from rag.stages.augment import (
    _format_chunks as _augment_format_chunks,
)
from rag.types import PipelineRunResult

logger = logging.getLogger(__name__)

# Schema version is not persisted in the ``rag_corpus_meta`` table (no column for it), so
# the pipeline supplies it as a module-level constant rather than reading it from
# configuration (no runtime config source exists). It participates in identity equality;
# bump only on a breaking corpus-schema change so existing corpora keep a stable identity.
SCHEMA_VERSION = "1"


class RagPipeline:
    """Orchestrates MQE → KNN+BM25 search → RRF → Cross-Encoder rerank.

    Wraps RagLLM, RagRepository, and RagScorer into a single runnable unit.
    on_status / on_clear callbacks decouple progress display from pipeline logic.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        cfg: RagConfig,
        *,
        module_cfg: dict | None = None,
        on_status: Callable[[str], None] | None = None,
        on_clear: Callable[[], None] | None = None,
        augment_refiner: AugmentRefiner | None = None,
    ) -> None:
        """Initialize with HTTP client, config, and optional status/clear callbacks."""
        self._http = http
        self._on_status = on_status or (lambda _: None)
        self._on_clear = on_clear or (lambda: None)
        # Populated after each run(); enables two-stage fetch by callers
        self.last_fetch_result: TwoStageFetchResult | None = None
        # Per-step wall-clock seconds from the most recent run() call
        self.last_timings: dict[str, float] = {}
        # Per-stage outcomes from the most recent run() call
        self.last_stage_results: list[StageResult] = []
        # Search diagnostics from the most recent run() call
        self.last_search_diagnostics: SearchDiagnostics = SearchDiagnostics()
        # Cumulative search failure counters across all run() calls on this instance
        self.stat_search_embed_failed: int = 0
        self.stat_search_fts_errors: int = 0
        # RAGCORPUS001 (REQ-004): corpus generation of the last accepted result, surfaced by
        # get_diagnostics(); None when no verified local corpus produced the result.
        self._last_corpus_generation: int | None = None

        # Resolve configuration via delegate
        self._cfg = resolve_rag_config(cfg, module_cfg=module_cfg)
        self._llm = RagLLM(
            self._http,
            build_llm_url(self._cfg.llm_url),
            cfg=self._cfg,
        )
        self._embed_url: str = build_embed_url(self._cfg.embed_url)
        # DB settings stored for augment(); used when db_path is provided explicitly.
        self._rag_db_path: str = self._cfg.rag_db_path
        self._sqlite_vec_so: str = self._cfg.sqlite_vec_so
        self._sqlite_timeout: int = self._cfg.sqlite_timeout
        self._sqlite_busy_timeout_ms: int = self._cfg.sqlite_busy_timeout_ms

        # AugmentRefiner: refiner concern
        if augment_refiner is not None:
            self._augment_refiner = augment_refiner
        else:
            self._augment_refiner = AugmentRefiner(
                cfg=self._cfg,
                on_status=self._on_status,
                search_diagnostics=self.last_search_diagnostics,
                llm=self._llm,
            )

        logger.info(
            "RagPipeline init: use_rrf=%s rrf_k=%d",
            self._cfg.use_rrf,
            self._cfg.rrf_k,
        )
        if not self._cfg.use_rrf:
            logger.warning(
                "use_rrf=False: RRF fusion disabled — retrieval quality degraded; "
                "use only for diagnostics or single-query testing"
            )

    async def run(
        self,
        query: str,
        db: SQLiteHelper,
        history_context: str = "",
    ) -> PipelineRunResult:
        """Execute MQE→search→RRF→rerank on an open DB; returns PipelineRunResult; on_clear() called on exit."""
        lifecycle = RagPipelineStageLifecycle(
            cast(RagConfigImpl, self._cfg),
            cast(Callable[..., object], self._llm),
            self._http,
            self._embed_url,
        )
        try:
            result = await lifecycle.run(query, db, history_context=history_context)
            self.last_timings = lifecycle.last_timings
            self.last_stage_results = lifecycle.last_stage_results
            self.last_fetch_result = lifecycle.last_fetch_result
            if lifecycle.last_search_diagnostics is not None:
                self.last_search_diagnostics = lifecycle.last_search_diagnostics
                self.stat_search_embed_failed += lifecycle.stat_search_embed_failed
                self.stat_search_fts_errors += lifecycle.stat_search_fts_errors
            return result
        finally:
            self._on_clear()

    async def augment(
        self,
        query: str,
        debug_fn: Callable[..., None] | None = None,
        history_context: str = "",
    ) -> str:
        """Run full pipeline and return a context block; '' when disabled or no results.

        Return values:
            - ``str`` (non-empty): Augmented context from one of the pipeline stages
            - ``""`` (empty string): Pipeline disabled (``use_search=False``), no cache
              hit, no search results, or all stages produced empty output

        Fallback chain (each step produces the final result unless it returns None):
            1. Search pipeline: semantic + FTS5 + RRF merge + rerank → reranked hits
            2. Refiner: ``refine_context()`` → refined text (final) or None (fallback)
            3. Raw chunks: ``_format_chunks(reranked)`` → formatted text (final)

        Raw-chunk fallback conditions (step 3 is reached when):
            - ``use_refiner=False`` (config disabled) → skip refiner, go to raw chunks
            - Refiner returned ``None`` (empty LLM output or error) → use raw reranked hits

        Raw-chunk format:
            ``_format_chunks()`` wraps reranked hits in ``[RAG_CONTEXT_START]...[RAG_CONTEXT_END]``
            markers with chunk content and metadata (title, URL, score).

        Side effects:
            - Updates ``self.last_stage_results`` with per-stage status

        Raises:
            RagPipelineError: If the underlying database connection fails.
        """
        if not self._cfg.use_search:
            return ""
        # Reset per-request refiner state so a long-lived pipeline never accumulates
        # stage records or carries stale diagnostics.
        self._augment_refiner.reset_request_state()
        try:
            with RagDatabaseConnection(
                rag_db_path=self._rag_db_path,
                sqlite_vec_so=self._sqlite_vec_so,
                sqlite_timeout=self._sqlite_timeout,
                sqlite_busy_timeout_ms=self._sqlite_busy_timeout_ms,
            ) as db:
                # REQ-004: record the generation of the corpus that serves the result.
                local_identity = compute_local_identity(
                    db, schema_version=SCHEMA_VERSION
                )
                self._last_corpus_generation = (
                    local_identity.index_generation if local_identity.verified else None
                )
                pipeline_result = await self.run(
                    query,
                    db,
                    history_context=history_context,
                )
        except RuntimeError as e:
            raise RagPipelineError(f"DB open failed (RAG unavailable): {e}") from e
        # run() already calls on_clear() in its finally block
        if debug_fn is not None:
            debug_fn(
                pipeline_result.queries,
                pipeline_result.search_results,
                pipeline_result.merged,
                pipeline_result.reranked,
                rrf_config={
                    "use_rrf": self._cfg.use_rrf,
                    "rrf_k": self._cfg.rrf_k,
                },
            )
        if not pipeline_result.reranked:
            return ""
        # Refiner: compress chunks to query-relevant key points before injection
        if self._cfg.use_refiner:
            refined = await self._augment_refiner.run_refiner(
                pipeline_result.reranked, query
            )
            if refined.text is not None:
                refined_text: str = refined.text
                return refined_text
        context_block: str = _augment_format_chunks(pipeline_result.reranked)
        return context_block

    def get_diagnostics(self) -> dict:
        """Return structured diagnostics for the last pipeline execution.

        Safe to call before ``run()`` / ``augment()`` — returns empty/zero values.
        Callers should serialize with ``orjson.dumps(pipeline.get_diagnostics())``.
        """
        diagnostics = PipelineDiagnostics.to_dict(
            PipelineDiagnostics.from_run_result(
                embed_ok=self.last_search_diagnostics.embed_ok,
                embed_failed=self.last_search_diagnostics.embed_failed,
                fts_errors=self.last_search_diagnostics.fts_errors,
                stage_results=self.last_stage_results,
                timings=self.last_timings,
                fetch_result=self.last_fetch_result,
                use_rrf=self._cfg.use_rrf,
                rrf_k=self._cfg.rrf_k,
            )
        )
        # RAGCORPUS001 (REQ-004): surface the accepted corpus generation. Added here
        # rather than in PipelineDiagnostics.to_dict()
        # so the frozen diagnostics contract in tests/rag/test_diagnostics.py stays
        # byte-for-byte stable. getattr defaults keep this safe when called before
        # augment() (some tests build the pipeline via RagPipeline.__new__).
        diagnostics["corpus_generation"] = getattr(
            self, "_last_corpus_generation", None
        )
        return diagnostics
