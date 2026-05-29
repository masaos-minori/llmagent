#!/usr/bin/env python3
"""
rag/pipeline.py
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

import asyncio
import logging
import time
from collections.abc import Callable

import httpx
import shared.plugin_registry as plugin_registry
from shared.config_loader import ConfigLoader
from shared.types import RagConfig

from db.helper import SQLiteHelper
from rag.llm import RagLLM, get_embedding
from rag.repository import (
    RagRepository,
    RagScorer,
    SemanticCache,
    _dedup_hits,
    deduplicate_chunks,
    fetch_full_document,
)
from rag.types import RagHit

# Re-export symbols that external callers import from this module
__all__ = [
    "RagPipeline",
    "RagHit",
    "fetch_full_document",
    "get_embedding",
]

logger = logging.getLogger(__name__)

_cfg: dict | None = None


def _get_cfg() -> dict:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("common.toml", "agent.toml")
        except Exception as e:
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
        self.last_reranked: list[RagHit] = []
        # Per-step wall-clock seconds from the most recent run() call
        self.last_timings: dict[str, float] = {}
        # In-memory nearest-neighbour cache; threshold/max_size read from cfg
        self.semantic_cache: SemanticCache = SemanticCache(
            max_size=cfg.semantic_cache_max_size,
            threshold=cfg.semantic_cache_threshold,
        )

    async def expand_queries_safe(self, query: str, context: str = "") -> list[str]:
        """Run MQE with fallback to original query on any error."""
        if not self._cfg.use_mqe:
            return [query]
        try:
            return await RagLLM(
                self._http, _get_cfg().get("llm_url", "")
            ).expand_queries(query, context=context)
        except Exception as e:
            logger.warning(f"MQE failed, using original query: {e}")
            return [query]

    async def search_queries(
        self, queries: list[str], db: SQLiteHelper
    ) -> list[list[RagHit]]:
        """Run parallel embeddings then sequential DB searches for each query.

        Embeddings are fetched concurrently via asyncio.gather to reduce latency.
        DB searches remain sequential since vector/fts share a single connection.
        """
        raw = await asyncio.gather(
            *(get_embedding(q, self._http) for q in queries),
            return_exceptions=True,
        )
        all_results: list[list[RagHit]] = []
        repo = RagRepository(db)
        for q, result in zip(queries, raw):
            if isinstance(result, Exception):
                logger.warning(f"Embedding failed for '{q}': {result}")
                continue
            assert isinstance(result, list)
            try:
                vec_res = repo.vector_search(result, self._cfg.top_k_search)
                fts_res = repo.fts_search(q, self._cfg.top_k_search)
                if vec_res:
                    all_results.append(vec_res)
                if fts_res:
                    all_results.append(fts_res)
            except Exception as e:
                logger.warning(f"Search failed for '{q}': {e}")
        return all_results

    async def rerank_candidates(self, query: str, merged: list[RagHit]) -> list[RagHit]:
        """Apply Cross-Encoder rerank then dedup; fall back to RRF order on error."""
        if not self._cfg.use_rerank:
            result = merged[: self._cfg.rag_top_k]
            return deduplicate_chunks(result, self._cfg.max_chunks_per_doc)
        try:
            result = await RagLLM(
                self._http, _get_cfg().get("llm_url", "")
            ).cross_encoder_rerank(
                query,
                merged[: self._cfg.top_k_rerank],
                self._cfg.rag_top_k,
                rag_min_score=self._cfg.rag_min_score,
            )
            return deduplicate_chunks(result, self._cfg.max_chunks_per_doc)
        except Exception as e:
            logger.warning(f"Rerank failed, using RRF order: {e}")
            result = merged[: self._cfg.rag_top_k]
            return deduplicate_chunks(result, self._cfg.max_chunks_per_doc)

    async def run(
        self, query: str, db: SQLiteHelper, history_context: str = ""
    ) -> tuple[list[str], list[list[RagHit]], list[RagHit], list[RagHit]]:
        """Execute MQE → search → RRF → rerank using an open DB connection.

        history_context: recent user utterances passed to MQE for disambiguation.
        Returns (queries, all_results, merged, reranked).
        Calls on_status() at each stage and on_clear() unconditionally on exit.
        """
        try:
            self._on_status("expanding query...")
            t0 = time.perf_counter()
            queries = await self.expand_queries_safe(query, context=history_context)
            self.last_timings["rag.mqe"] = time.perf_counter() - t0

            self._on_status("searching...")
            t0 = time.perf_counter()
            all_results = await self.search_queries(queries, db)
            self.last_timings["rag.search"] = time.perf_counter() - t0
            if not all_results:
                logger.info(f"RAG: no results for '{query}'")
                return queries, [], [], []

            self._on_status("merging results...")
            t0 = time.perf_counter()
            merged = (
                RagScorer.rrf_merge(all_results, rrf_k=_get_cfg().get("rrf_k", 60))
                if self._cfg.use_rrf
                else _dedup_hits(all_results)
            )
            self.last_timings["rag.rrf"] = time.perf_counter() - t0
            logger.info(f"RAG: {len(merged)} candidates after merge")

            self._on_status("reranking...")
            t0 = time.perf_counter()
            reranked = await self.rerank_candidates(query, merged)
            self.last_timings["rag.rerank"] = time.perf_counter() - t0

            # Plugin post-stages: each hook may filter or reorder the hits list
            for stage in plugin_registry.get_pipeline_post_stages():
                try:
                    reranked = await stage(reranked, query)
                except Exception as e:
                    logger.warning(f"Pipeline post-stage {stage.__name__!r} error: {e}")

            # Store for two-stage fetch callers (e.g. REPLAgent._run_turn)
            self.last_reranked = reranked

            return queries, all_results, merged, reranked
        finally:
            self._on_clear()

    async def _augment_http(
        self, rag_url: str, query: str, history_context: str
    ) -> str | None:
        """Delegate to external RAG service; return context string or None on failure.

        None signals the caller to fall back to in-process search.
        Stores selected_hits in self.last_reranked for two-stage fetch callers.
        """
        try:
            resp = await self._http.post(
                f"{rag_url}/v1/search",
                json={"query": query, "history_context": history_context},
            )
            resp.raise_for_status()
            body = resp.json()
            hits = body.get("selected_hits", [])
            if hits:
                # store for two-stage fetch callers (orchestrator._fetch_two_stage_context)
                self.last_reranked = hits
            return str(body.get("context", ""))
        except Exception as e:
            logger.warning(
                f"RAG service call failed ({rag_url}), falling back to in-process: {e}"
            )
            return None

    async def _augment_refiner(self, reranked: list[RagHit], query: str) -> str | None:
        """Run the chunk refiner; return refined text or None to fall back to raw chunks.

        Returns None both on empty output and on any exception.
        """
        try:
            self._on_status("refining context...")
            refined = await RagLLM(
                self._http, _get_cfg().get("llm_url", "")
            ).refine_context(
                reranked,
                query,
                max_tokens=self._cfg.refiner_max_tokens,
                per_chunk_chars=self._cfg.refiner_max_chars_per_chunk,
                timeout=self._cfg.refiner_timeout,
            )
            if refined:
                return refined
            logger.warning("Refiner returned empty output; falling back to chunks")
        except Exception as e:
            logger.warning(f"Refiner failed, falling back to original chunks: {e}")
        return None

    @staticmethod
    def _format_chunks(reranked: list[RagHit]) -> str:
        """Format reranked hits as a newline-separated source+content block."""
        blocks = [
            f"[Source: {c.get('title') or c['url']} | {c['url']}]\n{c['content']}"
            for c in reranked
        ]
        return "\n\n---\n\n".join(blocks)

    async def augment(
        self,
        query: str,
        debug_fn: Callable[
            [list[str], list[list[RagHit]], list[RagHit], list[RagHit]], None
        ]
        | None = None,
        history_context: str = "",
    ) -> str:
        """Run the full pipeline and return a formatted RAG context block.

        history_context: recent user utterances for MQE disambiguation (search only).
        Opens and closes the DB per call for thread safety.
        Returns empty string when search is disabled or yields no results.
        debug_fn receives (queries, all_results, merged, reranked) when provided;
        use it to print intermediate pipeline data for debugging.

        When cfg.rag_service_url is set, delegates to the external RAG HTTP service
        (POST /v1/search) instead of running in-process. Falls back to in-process on
        HTTP failure so the REPL continues without a RAG service.
        """
        if not self._cfg.use_search:
            return ""
        # HTTP mode: delegate to external RAG service when rag_service_url is configured
        if rag_url := self._cfg.rag_service_url:
            result = await self._augment_http(rag_url, query, history_context)
            if result is not None:
                return result
        try:
            db = SQLiteHelper().open(row_factory=True)
        except Exception as e:
            logger.warning(f"DB open failed (RAG unavailable): {e}")
            return ""
        with db:
            queries, all_results, merged, reranked = await self.run(
                query, db, history_context=history_context
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
        return self._format_chunks(reranked)
