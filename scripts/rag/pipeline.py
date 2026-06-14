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
  rag/pipeline.py    — RagPipeline (this file)
"""

import logging
import sqlite3
import time
from collections.abc import Callable
from typing import Any

import httpx
import orjson
from db.helper import SQLiteHelper
from shared.config_loader import ConfigLoader
from shared.types import RagConfig

from rag.cache import SemanticCache
from rag.llm import RagLLM, get_embedding
from rag.models import TwoStageFetchResult
from rag.repository import (
    RagRepository,
    deduplicate_chunks,
    fetch_full_document,
)
from rag.stage import PipelineContext
from rag.stages.augment import AugmentStage
from rag.stages.fusion import FusionStage
from rag.stages.mqe import MqeStage
from rag.stages.rerank import RerankStage
from rag.stages.search import SearchStage
from rag.types import MergedHit, RankedHit, RawHit
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

_cfg: dict[str, Any] | None = None

_RAG_BLOCK_START = "[RAG_CONTEXT_START]"
_RAG_BLOCK_END = "[RAG_CONTEXT_END]"


class RagPipelineError(RuntimeError):
    """Raised when a pipeline-level operation fails (e.g. DB open, stage failure)."""


def _get_cfg() -> dict[str, Any]:
    """Load config on first call; cached for the module lifetime.

    Used by service.py to override config via module-level _cfg assignment.
    """
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("common.toml", "agent.toml")
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


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
        # In-memory nearest-neighbour cache; threshold/max_size read from cfg
        self.semantic_cache: SemanticCache = SemanticCache(
            max_size=cfg.semantic_cache_max_size,
            threshold=cfg.semantic_cache_threshold,
        )
        # Initialize stages; load url/config from module-level cfg cache
        _module_cfg = _get_cfg()
        self._llm = RagLLM(self._http, _module_cfg.get("llm_url", ""), cfg=_module_cfg)
        self._embed_url: str = _module_cfg.get("embed_url", "")

    async def search_queries(
        self,
        queries: list[str],
        db: SQLiteHelper,
    ) -> list[list[RagHit]]:
        """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
        import asyncio

        raw = await asyncio.gather(
            *(get_embedding(q, self._http, self._embed_url) for q in queries),
            return_exceptions=True,
        )
        all_results: list[list[RagHit]] = []
        repo = RagRepository(db)
        for q, result in zip(queries, raw):
            if isinstance(result, Exception):
                logger.warning(f"Embedding failed for '{q}': {result}")
                continue
            if not isinstance(result, list):
                logger.warning(
                    f"Unexpected embedding result type for '{q}': {type(result).__name__}"
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
                logger.warning(f"Search DB failure for '{q}': {e}")
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
    ) -> tuple[list[str], list[list[RawHit]], list[RagHit], list[RagHit]]:
        """Execute MQE→search→RRF→rerank on an open DB; returns (queries, all_results, merged, reranked); on_clear() called on exit."""
        try:
            ctx = PipelineContext(query=query, history_context=history_context)
            self.last_timings = {}
            stages: list = [
                MqeStage(self._cfg.__dict__, self._llm),
                SearchStage(self._cfg.__dict__, self._http, self._embed_url),
                FusionStage(self._cfg.__dict__),
                RerankStage(self._cfg.__dict__, self._llm),
                AugmentStage(),
            ]
            for stage in stages:
                t0 = time.perf_counter()
                await stage.run(ctx, db=db)
                self.last_timings[stage.__class__.__name__] = time.perf_counter() - t0

            # Store for two-stage fetch callers (e.g. REPLAgent._run_turn)
            self.last_fetch_result = TwoStageFetchResult(
                hits=ctx.reranked,
                min_score_applied=self._cfg.rag_min_score,
                max_chunks_per_doc=self._cfg.max_chunks_per_doc,
            )

            return ctx.queries, ctx.search_results, ctx.merged, ctx.reranked
        finally:
            self._on_clear()

    async def _augment_http(
        self,
        rag_url: str,
        query: str,
        history_context: str,
    ) -> str | None:
        """Delegate to external RAG service; None on failure triggers in-process fallback; stores hits in last_fetch_result."""
        try:
            resp = await self._http.post(
                f"{rag_url}/v1/search",
                json={"query": query, "history_context": history_context},
            )
            resp.raise_for_status()
            body = orjson.loads(resp.content)
            hits = body.get("selected_hits", [])
            if hits:
                # store for two-stage fetch callers (orchestrator._fetch_two_stage_context)
                self.last_fetch_result = TwoStageFetchResult(
                    hits=hits,
                    min_score_applied=0.0,
                    max_chunks_per_doc=0,
                )
            context_raw = body.get("context")
            if context_raw is None:
                return ""
            if not isinstance(context_raw, str):
                raise ValueError(
                    f"RAG service 'context' field must be str,"
                    f" got {type(context_raw).__name__}"
                )
            return context_raw
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            ValueError,
        ) as e:
            logger.warning(
                f"RAG service call failed ({rag_url}), falling back to in-process: {e}",
            )
            return None

    async def _augment_refiner(self, reranked: list[RagHit], query: str) -> str | None:
        """Run the chunk refiner; returns None on empty output or LLM failure so caller falls back to raw chunks."""
        try:
            self._on_status("refining context...")
            refined = await self._llm.refine_context(
                reranked,
                query,
                max_tokens=self._cfg.refiner_max_tokens,
                per_chunk_chars=self._cfg.refiner_max_chars_per_chunk,
                timeout=self._cfg.refiner_timeout,
            )
            if refined:
                return refined
            logger.warning("Refiner returned empty output; falling back to chunks")
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            logger.warning(f"Refiner failed, falling back to original chunks: {e}")
        return None

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
        debug_fn: Callable[
            [list[str], list[list[RawHit]], list[RagHit], list[RagHit]],
            None,
        ]
        | None = None,
        history_context: str = "",
    ) -> str:
        """Run full pipeline and return a context block; '' when disabled or no results; delegates to rag_service_url when set."""
        if not self._cfg.use_search:
            return ""
        # HTTP mode: delegate to external RAG service when rag_service_url is configured
        if rag_url := self._cfg.rag_service_url:
            result = await self._augment_http(rag_url, query, history_context)
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
            queries, all_results, merged, reranked = await self.run(
                query,
                db,
                history_context=history_context,
            )
        # run() already calls on_clear() in its finally block
        if debug_fn is not None:
            debug_fn(queries, all_results, merged, reranked)
        if not reranked:
            return ""
        # Refiner: compress chunks to query-relevant key points before injection
        if self._cfg.use_refiner:
            refined = await self._augment_refiner(reranked, query)
            if refined is not None:
                return refined
        context_block = self._format_chunks(reranked)
        if self._cfg.use_semantic_cache and emb is not None and context_block:
            self.semantic_cache.put(emb, history_context, context_block)
        return context_block
