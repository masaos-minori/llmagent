#!/usr/bin/env python3
"""scripts/rag/pipeline.py

RAG pipeline orchestration: MQE → vector/FTS search → RRF → Cross-Encoder rerank.

Pipeline order:
  [1] MQE     — RagLLM.expand_queries
  [2] Search  — get_embedding / RagRepository.vector_search / .fts_search
  [3] RRF     — RagScorer.rrf_merge
  [4] Rerank  — RagLLM.cross_encoder_rerank

Module layout:
  rag/repository.py  — RagRepository, RagScorer, SemanticCache, FTS helpers
  rag/llm_client.py  — RagLLM, get_embedding, summarize_tool_result
  rag/pipeline_service.py — External RAG service delegation
  rag/pipeline_refiner.py — Context refiner (chunk compression)
  rag/pipeline.py    — RagPipeline core orchestration (this file)
"""

import asyncio
import logging
import sqlite3
import time
from collections.abc import Callable
from typing import Any, Literal, cast

import httpx
from db.helper import SQLiteHelper
from shared.config_loader import ConfigLoader
from shared.config_validator import RagConfigValidator
from shared.llm_client import build_embed_url, build_llm_url
from shared.types import (
    RagConfig,
    RagHit,
)

from rag.augment import AugmentRefiner
from rag.cache import SemanticCache
from rag.http_augment import _map_http_result_kind
from rag.llm_client import RagLLM, get_embedding
from rag.models_config import RagConfigImpl
from rag.models_data import TwoStageFetchResult
from rag.models_result import HttpResultKind, SearchDiagnostics
from rag.repository import (
    RagRepository,
    deduplicate_chunks,
)
from rag.stage import PipelineContext, PipelineStage, StageResult
from rag.stages.augment import (
    AugmentStage,
)
from rag.stages.augment import (
    _format_chunks as _augment_format_chunks,
)
from rag.stages.fusion import FusionStage
from rag.stages.mqe import MqeStage
from rag.stages.rerank import RerankStage
from rag.stages.search import SearchStage
from rag.types import PipelineRunResult

logger = logging.getLogger(__name__)


class _ModuleConfig:
    """Class-level cached config loader for RagPipeline."""

    _cache: dict[str, str] | None = None

    @classmethod
    def get(cls) -> dict:
        """Load config on first call; cached for the class lifetime."""
        if cls._cache is None:
            try:
                cls._cache = ConfigLoader().load_all()
            except (FileNotFoundError, ValueError) as e:
                logger.warning("Config load failed: %s", e)
                cls._cache = {}
        return cls._cache


class RagPipelineError(RuntimeError):
    """Raised when a pipeline-level operation fails (e.g. DB open, stage failure)."""


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
        # In-memory nearest-neighbour cache; threshold/max_size read from cfg

        # Resolve configuration: priority: cfg > module_cfg > ConfigLoader().load_all()
        self._cfg: RagConfig
        if isinstance(cfg, RagConfigImpl):
            self._cfg = cfg
        else:
            _raw_cfg: dict[str, Any] = {}
            if isinstance(cfg, dict):
                _raw_cfg = cfg
            elif cfg is not None and hasattr(cfg, "__dict__"):
                _raw_cfg = cfg.__dict__
            else:
                _raw_cfg = module_cfg if module_cfg is not None else _ModuleConfig.get()
            # Fill missing RagConfigImpl fields from any non-dict config source
            # Dataclass fields without explicit init args don't appear in __dict__
            _required_fields = frozenset(
                {
                    "llm_url",
                    "embed_url",
                    "rag_db_path",
                    "sqlite_vec_so",
                    "sqlite_timeout",
                    "sqlite_busy_timeout_ms",
                    "embed_retry",
                    "embed_workers",
                    "rag_pipeline_service_url",
                    "mqe_prompt_template",
                    "mqe_n_queries",
                    "rerank_prompt_template",
                    "use_search",
                    "rag_service_url",
                }
            )
            _defaults_for_missing = {
                "llm_url": "",
                "embed_url": "",
                "rag_db_path": "",
                "sqlite_vec_so": "",
                "sqlite_timeout": 30,
                "sqlite_busy_timeout_ms": 30000,
                "mqe_n_queries": 3,
                "mqe_prompt_template": "",
                "rerank_prompt_template": "",
                "embed_retry": 3,
                "embed_workers": 4,
                "rag_pipeline_service_url": None,
                "use_search": True,
                "rag_service_url": None,
            }
            for k in _required_fields:
                if k not in _raw_cfg:
                    _raw_cfg[k] = _defaults_for_missing[k]
            validator = RagConfigValidator()
            validation_result = validator.validate(_raw_cfg)
            for warning in validation_result.warnings:
                logger.warning("rag config warning: %s", warning)
            for error in validation_result.errors:
                logger.error("rag config error: %s", error)
            if not validation_result.ok:
                raise ValueError(
                    f"RAG config validation failed: {validation_result.errors}"
                )
            self._cfg = cast(RagConfig, RagConfigImpl(**_raw_cfg))
        self.semantic_cache: SemanticCache = SemanticCache(
            max_size=self._cfg.semantic_cache_max_size,
            threshold=self._cfg.semantic_cache_threshold,
        )

        self._llm = RagLLM(
            self._http,
            build_llm_url(self._cfg.llm_url),
            cfg=cast(RagConfig, self._cfg),
        )
        self._embed_url: str = build_embed_url(self._cfg.embed_url)
        # DB settings stored for augment(); used when db_path is provided explicitly.
        self._rag_db_path: str = self._cfg.rag_db_path
        self._sqlite_vec_so: str = self._cfg.sqlite_vec_so
        self._sqlite_timeout: int = self._cfg.sqlite_timeout
        self._sqlite_busy_timeout_ms: int = self._cfg.sqlite_busy_timeout_ms

        # AugmentRefiner: HTTP augment + refiner concern
        self._augment_refiner = AugmentRefiner(
            http=self._http,
            cfg=self._cfg,
            on_status=self._on_status,
            set_fetch_result=lambda fr: setattr(self, "last_fetch_result", fr),
            set_fallback_reason=lambda _: None,
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

    def _get_stage_status(
        self, stage: PipelineStage, ctx: PipelineContext
    ) -> tuple[Literal["success", "fallback", "failure"], str | None]:
        """Return the execution status of a pipeline stage with an optional reason string."""
        if hasattr(stage, "get_status"):
            return cast(
                tuple[Literal["success", "fallback", "failure"], str | None],
                stage.get_status(ctx),
            )
        return "success", None

    async def _run_stage(
        self, stage: PipelineStage, ctx: PipelineContext, db: SQLiteHelper
    ) -> None:
        """Run a single pipeline stage and record its result."""
        t0 = time.perf_counter()
        exc_msg: str | None = None
        try:
            await stage.run(ctx, db=db)
        except (
            RuntimeError,
            sqlite3.OperationalError,
            httpx.HTTPStatusError,
            httpx.RequestError,
            TimeoutError,
        ) as e:
            exc_msg = str(e)
            logger.warning("Stage %s failed: %s", stage.__class__.__name__, e)
        elapsed = time.perf_counter() - t0
        self.last_timings[stage.__class__.__name__] = elapsed
        stage_status: Literal["success", "fallback", "failure"]
        stage_reason: str | None
        if exc_msg is not None:
            stage_status, stage_reason = "failure", exc_msg
        else:
            stage_status, stage_reason = self._get_stage_status(stage, ctx)
        ctx.stage_results.append(
            StageResult(
                stage_name=stage.__class__.__name__,
                status=stage_status,
                elapsed_seconds=elapsed,
                fallback_reason=stage_reason,
            )
        )

    async def search_queries(
        self,
        queries: list[str],
        db: SQLiteHelper,
    ) -> list[list[RagHit]]:
        """Fetch embeddings concurrently then perform vector + FTS searches sequentially.

        Sequential DB execution avoids shared-connection conflicts across queries.
        Returns an empty list when all embedding fetches fail.
        """
        raw = await asyncio.gather(
            *(get_embedding(q, self._http, self._embed_url) for q in queries),
            return_exceptions=True,
        )
        all_results: list[list[RagHit]] = []
        repo = RagRepository(db)
        for q, result in zip(queries, raw):
            if isinstance(result, Exception):
                logger.warning("Embedding failed for '%s': %s", q, result)
                continue
            if not isinstance(result, list):
                logger.warning(
                    "Unexpected embedding result type for '%s': %s",
                    q,
                    type(result).__name__,
                )
                continue
            try:
                vec_res = repo.vector_search(result, self._cfg.top_k_search)
                fts_res = repo.fts_search(q, self._cfg.top_k_search)
                if vec_res:
                    all_results.append(vec_res)
                if fts_res:
                    all_results.append(fts_res)
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.warning("Search DB failure for '%s': %s", q, e)
        return all_results

    async def rerank_candidates(self, query: str, merged: list[RagHit]) -> list[RagHit]:
        """Apply Cross-Encoder rerank then dedup.

        When ``use_rerank=False``, returns the top-k merged hits without reranking.

        Raises RagRerankError on LLM failure when use_rerank=True.
        """
        if not self._cfg.use_rerank:
            result = merged[: self._cfg.rag_top_k]
            deduped: list[RagHit] = deduplicate_chunks(
                result, self._cfg.max_chunks_per_doc
            )
            return deduped
        result = await self._llm.cross_encoder_rerank(
            query,
            merged[: self._cfg.top_k_rerank],
            self._cfg.rag_top_k,
            rag_min_score=self._cfg.rag_min_score,
        )
        deduped2: list[RagHit] = deduplicate_chunks(
            result, self._cfg.max_chunks_per_doc
        )
        return deduped2

    async def run(
        self,
        query: str,
        db: SQLiteHelper,
        history_context: str = "",
    ) -> PipelineRunResult:
        """Execute MQE→search→RRF→rerank on an open DB; returns PipelineRunResult; on_clear() called on exit."""
        try:
            ctx = PipelineContext(query=query, history_context=history_context)
            self.last_timings = {}
            pre_augment_stages: list = [
                MqeStage(cast(RagConfig, self._cfg), self._llm),
                SearchStage(cast(RagConfig, self._cfg), self._http, self._embed_url),
                FusionStage(use_rrf=self._cfg.use_rrf, rrf_k=self._cfg.rrf_k),
                RerankStage(cast(RagConfig, self._cfg), self._llm),
            ]
            for stage in pre_augment_stages:
                await self._run_stage(stage, ctx, db)

            augment_stage = AugmentStage()
            t0 = time.perf_counter()
            await augment_stage.run(ctx, db=db)
            elapsed = time.perf_counter() - t0
            self.last_timings[augment_stage.__class__.__name__] = elapsed
            ctx.stage_results.append(
                StageResult(
                    stage_name=augment_stage.__class__.__name__,
                    status="success",
                    elapsed_seconds=elapsed,
                    fallback_reason=None,
                )
            )

            # Store for two-stage fetch callers (e.g. REPLAgent._run_turn)
            self.last_fetch_result = TwoStageFetchResult(
                hits=ctx.reranked,
                min_score_applied=self._cfg.rag_min_score,
                max_chunks_per_doc=self._cfg.max_chunks_per_doc,
            )
            self.last_stage_results = list(ctx.stage_results)
            # Save search diagnostics and accumulate cumulative counters
            self.last_search_diagnostics = ctx.search_diagnostics
            self.stat_search_embed_failed += ctx.search_diagnostics.embed_failed
            self.stat_search_fts_errors += ctx.search_diagnostics.fts_errors
            fallbacks = [r for r in ctx.stage_results if r["status"] == "fallback"]
            if fallbacks:
                logger.info(
                    "Pipeline fallback stages: %s",
                    ", ".join(
                        f"{r['stage_name']}({r['fallback_reason']})" for r in fallbacks
                    ),
                )

            return PipelineRunResult(
                queries=ctx.queries,
                search_results=ctx.search_results,
                merged=ctx.merged,
                reranked=ctx.reranked,
                stage_results=list(ctx.stage_results),
                diagnostics=ctx.search_diagnostics,
            )
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

        Identity vs truthiness:
            The HTTP and refiner stages use ``is not None`` identity checks (not
            truthiness). This means ``""`` from HTTP is treated as a valid result,
            while only explicit ``None`` triggers fallback.

        Fallback chain (each step produces the final result unless it returns None):
            1. HTTP mode: ``call_rag_service()`` → str/"" (final) or None (fallback)
            2. Semantic cache: cached string (final) or None (fallback)
            3. Search pipeline: semantic + FTS5 + RRF merge + rerank → reranked hits
            4. Refiner: ``refine_context()`` → refined text (final) or None (fallback)
            5. Raw chunks: ``_format_chunks(reranked)`` → formatted text (final)

        Raw-chunk fallback conditions (step 5 is reached when):
            - ``use_refiner=False`` (config disabled) → skip refiner, go to raw chunks
            - Refiner returned ``None`` (empty LLM output or error) → use raw reranked hits
            - HTTP stage returned ``None`` → entire in-process pipeline runs, ending at raw chunks

        Raw-chunk format:
            ``_format_chunks()`` wraps reranked hits in ``[RAG_CONTEXT_START]...[RAG_CONTEXT_END]``
            markers with chunk content and metadata (title, URL, score).

        Side effects:
            - Updates ``self.last_stage_results`` with per-stage status
            - Updates ``self.last_fetch_result`` when HTTP stage is used
            - May update semantic cache on successful augment

        Raises:
            RagPipelineError: If the underlying database connection fails.
        """
        if not self._cfg.use_search:
            return ""
        # HTTP mode: delegate to external RAG service when rag_service_url is configured
        if rag_url := self._cfg.rag_service_url:
            result = await self._augment_refiner.run_http_augment(
                query, history_context, rag_url
            )
            self.last_search_diagnostics = self._augment_refiner.search_diagnostics
            self.last_stage_results = list(self._augment_refiner.last_stage_results)
            if result is not None:
                return result
        # Semantic cache lookup (in-process mode only)
        emb: list[float] | None = None
        if self._cfg.use_semantic_cache and self._embed_url:
            try:
                emb = await get_embedding(query, self._http, self._embed_url)
            except (httpx.HTTPError, OSError, TimeoutError):
                emb = None
            if emb is not None:
                cached = self.semantic_cache.lookup(emb, history_context)
                if cached is not None:
                    result422: str = cached
                    return result422
        try:
            if self._rag_db_path:
                db = SQLiteHelper(
                    db_path=self._rag_db_path,
                    sqlite_vec_so=self._sqlite_vec_so,
                    sqlite_timeout=self._sqlite_timeout,
                    sqlite_busy_timeout_ms=self._sqlite_busy_timeout_ms,
                ).open(row_factory=True)
            else:
                db = SQLiteHelper().open(row_factory=True)
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            raise RagPipelineError(f"DB open failed (RAG unavailable): {e}") from e
        with db:
            pipeline_result = await self.run(
                query,
                db,
                history_context=history_context,
            )
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
        if self._cfg.use_semantic_cache and emb is not None and context_block:
            if not self.semantic_cache.put(emb, history_context, context_block):
                logger.warning(
                    "Failed to store embedding in semantic cache (dimension mismatch)"
                )
        return context_block

    def get_diagnostics(self) -> dict:
        """Return structured diagnostics for the last pipeline execution.

        Safe to call before ``run()`` / ``augment()`` — returns empty/zero values.
        Callers should serialize with ``orjson.dumps(pipeline.get_diagnostics())``.
        """
        stage_results = [dict(r) for r in self.last_stage_results]
        fallbacks = [r for r in stage_results if r.get("status") == "fallback"]
        fetch = self.last_fetch_result
        fusion_mode = "rrf" if self._cfg.use_rrf else "dedup_only"
        http_result_kind_raw = getattr(
            self.last_search_diagnostics, "http_result_kind", None
        )
        if isinstance(http_result_kind_raw, HttpResultKind):
            http_result_kind = http_result_kind_raw
        else:
            http_result_kind = _map_http_result_kind(http_result_kind_raw)
        refiner_fallbacks = [
            r
            for r in stage_results
            if r.get("stage_name") == "Refiner" and r.get("status") == "fallback"
        ]
        refiner_fallback_count = len(refiner_fallbacks)
        refiner_returned_empty = sum(
            1
            for r in refiner_fallbacks
            if str(r.get("fallback_reason", "")) == "refiner_returned_empty"
        )
        refiner_exception_count = sum(
            1
            for r in refiner_fallbacks
            if str(r.get("fallback_reason", "")).startswith("refiner_exception:")
        )
        return {
            "stage_results": stage_results,
            "timings": dict(self.last_timings),
            "fetch_result": (
                {
                    "hits": len(fetch.hits),
                    "min_score_applied": fetch.min_score_applied,
                }
                if fetch is not None
                else None
            ),
            "fusion_mode": fusion_mode,
            "http_result_kind": http_result_kind,
            "fallback_count": len(fallbacks),
            "fallback_reasons": [
                r["fallback_reason"] for r in stage_results if r.get("fallback_reason")
            ],
            "refiner_fallback_count": refiner_fallback_count,
            "refiner_returned_empty": refiner_returned_empty,
            "refiner_exception_count": refiner_exception_count,
            "refiner_exception": refiner_exception_count > 0,
            "hit_counts": {
                "merged": len(fetch.hits) if fetch is not None else 0,
            },
            "search_diagnostics": {
                "embed_ok": self.last_search_diagnostics.embed_ok,
                "embed_failed": self.last_search_diagnostics.embed_failed,
                "fts_errors": self.last_search_diagnostics.fts_errors,
                "degraded": (
                    self.last_search_diagnostics.embed_failed > 0
                    or self.last_search_diagnostics.fts_errors > 0
                ),
            },
        }

    def invalidate_cache(self) -> None:
        """Clear all cached semantic-search entries.

        Call after any corpus-changing operation this pipeline instance is aware
        of (e.g. MCP rag_delete_document) so subsequent queries don't return
        context for a document that no longer exists. Delegates to
        SemanticCache.invalidate(), which is thread-safe.
        """
        self.semantic_cache.invalidate()
