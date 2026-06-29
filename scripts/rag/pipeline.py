#!/usr/bin/env python3
"""rag/pipeline.py
RAG pipeline orchestration: MQE → vector/FTS search → RRF → Cross-Encoder rerank.

Pipeline order:
  [1] MQE     — RagLLM.expand_queries
  [2] Search  — get_embedding / RagRepository.vector_search / .fts_search
  [3] RRF     — RagScorer.rrf_merge
  [4] Rerank  — RagLLM.cross_encoder_rerank

Module layout:
  rag/types.py       — RagHit TypedDict; re-exports LLMMessage from shared/types.py
  rag/repository.py  — RagRepository, RagScorer, SemanticCache, FTS helpers
  rag/llm.py         — RagLLM, get_embedding, summarize_tool_result
  rag/pipeline_service.py — External RAG service delegation
  rag/pipeline_refiner.py — Context refiner (chunk compression)
  rag/pipeline.py    — RagPipeline core orchestration (this file)
"""

import asyncio
import dataclasses
import logging
import sqlite3
import time
from collections.abc import Callable
from typing import Literal

import httpx
from db.helper import SQLiteHelper
from shared.config_loader import ConfigLoader
from shared.config_validator import RagConfigValidator
from shared.plugin_registry import (
    get_pipeline_post_stages,
    run_pipeline_stages,
)
from shared.types import RagConfig

from rag.cache import SemanticCache
from rag.llm_client import RagLLM, get_embedding
from rag.models_data import TwoStageFetchResult
from rag.models_result import HttpResultKind, ResultSource, SearchDiagnostics
from rag.pipeline_refiner import RefineResult, refine_context
from rag.pipeline_service import call_rag_service
from rag.repository import (
    RagRepository,
    deduplicate_chunks,
    fetch_full_document,
)
from rag.stage import PipelineContext, PipelineStage, StageResult
from rag.stages.augment import AugmentStage
from rag.stages.fusion import FusionStage
from rag.stages.mqe import MqeStage
from rag.stages.rerank import RerankStage
from rag.stages.search import SearchStage
from rag.types import MergedHit, PipelineRunResult, RankedHit, RawHit
from rag.utils import sanitize_document

RagHit = RawHit | MergedHit | RankedHit

# Re-export symbols that external callers import from this module
__all__ = [
    "RagHit",
    "RagPipeline",
    "RagPipelineError",
    "fetch_full_document",
]

logger = logging.getLogger(__name__)

_RAG_BLOCK_START = "[RAG_CONTEXT_START]"
_RAG_BLOCK_END = "[RAG_CONTEXT_END]"


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
        on_status: Callable[[str], None] | None = None,
        on_clear: Callable[[], None] | None = None,
    ) -> None:
        self._http = http
        self._cfg = cfg
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
        self.semantic_cache: SemanticCache = SemanticCache(
            max_size=cfg.semantic_cache_max_size,
            threshold=cfg.semantic_cache_threshold,
        )
        # Validate RAG config cross-file consistency
        _module_cfg = _ModuleConfig.get()
        validator = RagConfigValidator()
        result = validator.validate(_module_cfg)
        for warning in result.warnings:
            logger.warning("rag config warning: %s", warning)
        for error in result.errors:
            logger.error("rag config error: %s", error)
        if not result.ok:
            raise ValueError(f"RAG config validation failed: {result.errors}")
        # Initialize stages; load url/config from class-level cache
        self._llm = RagLLM(self._http, _module_cfg.get("llm_url", ""), cfg=_module_cfg)
        self._embed_url: str = _module_cfg.get("embed_url", "")
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
        name = type(stage).__name__
        if name == "MqeStage":
            return self._mqe_status()
        if name == "SearchStage":
            return self._search_status(ctx)
        if name == "FusionStage":
            return self._fusion_status()
        if name == "RerankStage":
            return self._rerank_status()
        return "success", None

    def _mqe_status(self) -> tuple[Literal["success", "fallback"], str | None]:
        if not self._cfg.use_mqe:
            return "fallback", "use_mqe=False"
        return "success", None

    def _search_status(
        self, ctx: PipelineContext
    ) -> tuple[Literal["success", "fallback"], str | None]:
        if not ctx.search_results:
            return "fallback", "no search results"
        return "success", None

    def _fusion_status(self) -> tuple[Literal["success", "fallback"], str | None]:
        if not self._cfg.use_rrf:
            return "fallback", "use_rrf=False"
        return "success", None

    def _rerank_status(self) -> tuple[Literal["success", "fallback"], str | None]:
        if not self._cfg.use_rerank:
            return "fallback", "use_rerank=False"
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
        """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
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

        Raises RagRerankError on LLM failure when use_rerank=True.
        """
        if not self._cfg.use_rerank:
            result = merged[: self._cfg.rag_top_k]
            return deduplicate_chunks(result, self._cfg.max_chunks_per_doc)
        result = await self._llm.cross_encoder_rerank(
            query,
            merged[: self._cfg.top_k_rerank],
            self._cfg.rag_top_k,
            rag_min_score=self._cfg.rag_min_score,
        )
        return deduplicate_chunks(result, self._cfg.max_chunks_per_doc)

    async def run(
        self,
        query: str,
        db: SQLiteHelper,
        history_context: str = "",
        hook_strict: bool = False,
    ) -> PipelineRunResult:
        """Execute MQE→search→RRF→rerank on an open DB; returns PipelineRunResult; on_clear() called on exit."""
        try:
            ctx = PipelineContext(query=query, history_context=history_context)
            self.last_timings = {}
            pre_augment_stages: list = [
                MqeStage(self._cfg, self._llm),
                SearchStage(self._cfg, self._http, self._embed_url),
                FusionStage(use_rrf=self._cfg.use_rrf, rrf_k=self._cfg.rrf_k),
                RerankStage(self._cfg, self._llm),
            ]
            for stage in pre_augment_stages:
                await self._run_stage(stage, ctx, db)

            # Post-rerank plugin hooks (before AugmentStage)
            if get_pipeline_post_stages():
                t0 = time.perf_counter()
                ctx.reranked = await run_pipeline_stages(
                    get_pipeline_post_stages(), ctx.reranked, query, strict=hook_strict
                )
                elapsed = time.perf_counter() - t0
                self.last_timings["PluginHooks"] = elapsed
                ctx.stage_results.append(
                    StageResult(
                        stage_name="PluginHooks",
                        status="success",
                        elapsed_seconds=elapsed,
                        fallback_reason=None,
                    )
                )

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

    @staticmethod
    def _format_chunks(reranked: list[RagHit]) -> str:
        """Format reranked hits with sanitization and boundary markers."""
        blocks = [
            f"[Source: {c.title if c.title else c.url} | {c.url}]\n{sanitize_document(c.content)}"
            for c in reranked
        ]
        content = "\n\n---\n\n".join(blocks)
        return f"{_RAG_BLOCK_START}\n{content}\n{_RAG_BLOCK_END}"

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
            result = await self._run_http_augment(query, history_context, rag_url)
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
                    return cached
        try:
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
            refined = await self._run_refiner(pipeline_result.reranked, query)
            if refined.text is not None:
                return refined.text
        context_block = self._format_chunks(pipeline_result.reranked)
        if self._cfg.use_semantic_cache and emb is not None and context_block:
            self.semantic_cache.put(emb, history_context, context_block)
        return context_block

    async def _run_http_augment(
        self,
        query: str,
        history_context: str,
        rag_url: str,
    ) -> str | None:
        """Run HTTP augment and return result or None for fallback."""
        t0 = time.perf_counter()
        http_fallback_reasons: list[str] = []
        result, remote_status_code, remote_latency_ms = await call_rag_service(
            self._http,
            rag_url,
            query,
            history_context,
            auth_token=self._cfg.rag_auth_token,
            set_fetch_result=lambda fr: setattr(self, "last_fetch_result", fr),
            set_fallback_reason=http_fallback_reasons.append,
        )
        elapsed = time.perf_counter() - t0
        http_status: Literal["success", "fallback"] = (
            "success" if result is not None else "fallback"
        )
        http_fallback_reason = (
            http_fallback_reasons[0] if http_fallback_reasons else "in-process fallback"
        )
        self.last_stage_results.append(
            StageResult(
                stage_name="HttpAugment",
                status=http_status,
                elapsed_seconds=elapsed,
                fallback_reason=(http_fallback_reason if result is None else None),
            )
        )
        self._http_result_kind = (
            "remote_nonempty"
            if result and len(result) > 0
            else "remote_empty"
            if result == ""
            else "in_process_fallback"
        )
        # Assign SearchDiagnostics remote mode fields
        if result is not None:
            self.last_search_diagnostics = dataclasses.replace(
                self.last_search_diagnostics,
                result_source=ResultSource.REMOTE,
                http_result_kind=HttpResultKind.EMPTY
                if result == ""
                else HttpResultKind.SUCCESS,
                remote_status_code=remote_status_code,
                remote_latency_ms=remote_latency_ms,
            )
        else:
            self.last_search_diagnostics = dataclasses.replace(
                self.last_search_diagnostics,
                result_source=ResultSource.FALLBACK,
                http_result_kind=HttpResultKind.ERROR,
                remote_status_code=remote_status_code,
                remote_latency_ms=remote_latency_ms,
                fallback_reason=http_fallback_reason,
            )
        return result if result is not None else None

    async def _run_refiner(
        self,
        reranked: list[RagHit],
        query: str,
    ) -> RefineResult:
        """Run refiner and return result."""
        t0 = time.perf_counter()
        refined = await refine_context(
            self._llm,
            self._on_status,
            reranked,
            query,
            max_tokens=self._cfg.refiner_max_tokens,
            per_chunk_chars=self._cfg.refiner_max_chars_per_chunk,
            timeout=self._cfg.refiner_timeout,
        )
        elapsed = time.perf_counter() - t0
        refiner_status: Literal["success", "fallback"] = (
            "success" if refined.text is not None else "fallback"
        )
        self.last_stage_results.append(
            StageResult(
                stage_name="Refiner",
                status=refiner_status,
                elapsed_seconds=elapsed,
                fallback_reason=refined.reason,
            )
        )
        if refined.text is None:
            logger.info(
                "augment: refiner fallback (reason=%s); using raw chunks",
                refined.reason,
            )
        return refined

    def get_diagnostics(self) -> dict:
        """Return structured diagnostics for the last pipeline execution.

        Safe to call before ``run()`` / ``augment()`` — returns empty/zero values.
        Callers should serialize with ``orjson.dumps(pipeline.get_diagnostics())``.
        """
        stage_results = [dict(r) for r in self.last_stage_results]
        fallbacks = [r for r in stage_results if r.get("status") == "fallback"]
        fetch = self.last_fetch_result
        fusion_mode = "rrf" if self._cfg.use_rrf else "dedup_only"
        http_result_kind = getattr(self, "_http_result_kind", None)
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
