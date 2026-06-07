"""rag/stages/rerank.py
Rerank stage for Cross-Encoder.
"""

from __future__ import annotations

import logging
from typing import Any

from rag.llm import RagLLM
from rag.repository import deduplicate_chunks
from rag.stage import PipelineContext

logger = logging.getLogger(__name__)


async def _rerank(
    query: str,
    merged: list,
    cfg: dict[str, Any],
    llm: RagLLM,
) -> list:
    """Apply Cross-Encoder rerank then dedup; fall back to RRF order on error."""
    if not cfg.get("use_rerank", True):
        result = merged[: cfg.get("rag_top_k", 10)]
        return deduplicate_chunks(result, cfg.get("max_chunks_per_doc", 5))
    try:
        result = await llm.cross_encoder_rerank(
            query,
            merged[: cfg.get("top_k_rerank", 100)],
            cfg.get("rag_top_k", 10),
            rag_min_score=cfg.get("rag_min_score", 0.0),
        )
        return deduplicate_chunks(result, cfg.get("max_chunks_per_doc", 5))
    except Exception as e:
        logger.warning(f"Rerank failed, using RRF order: {e}")
        result = merged[: cfg.get("rag_top_k", 10)]
        return deduplicate_chunks(result, cfg.get("max_chunks_per_doc", 5))


class RerankStage:
    def __init__(self, cfg: dict[str, Any], llm: RagLLM) -> None:
        self._cfg = cfg
        self._llm = llm

    async def run(self, ctx: PipelineContext, **kwargs: Any) -> None:
        """Run rerank stage."""
        ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        # Notify observers
        for observer in ctx.observers:
            try:
                await observer.on_stage_complete("rerank", ctx)
            except Exception as e:
                logger.warning(f"Observer failed in Rerank stage: {e}")
