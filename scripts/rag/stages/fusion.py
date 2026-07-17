"""Fusion (RRF) stage for RAG pipeline."""

import logging

from rag.repository import RagScorer, _dedup_hits
from rag.stage import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)

_DEFAULT_RRF_K = 60


class FusionStage(PipelineStage):
    def __init__(self, rrf_k: int = _DEFAULT_RRF_K, use_rrf: bool = True) -> None:
        self._rrf_k = rrf_k
        self._use_rrf = use_rrf

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        if not self._use_rrf:
            logger.info(
                "FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit"
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)
