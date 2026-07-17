"""Fusion (RRF) stage for RAG pipeline."""

import logging

from rag.repository import RagScorer, _dedup_hits
from rag.stage import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)

_DEFAULT_RRF_K = 60


class FusionStage(PipelineStage):
    """Reciprocal Rank Fusion (RRF) stage for merging search results from multiple queries."""

    def __init__(self, rrf_k: int = _DEFAULT_RRF_K, use_rrf: bool = True) -> None:
        """Initialize with RRF constant k and whether to apply RRF scoring."""
        self._rrf_k = rrf_k
        self._use_rrf = use_rrf

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                "FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit"
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)
