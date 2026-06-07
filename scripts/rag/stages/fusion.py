"""Fusion (RRF) stage for RAG pipeline."""

from rag.repository import RagScorer
from rag.stage import PipelineContext, PipelineStage


class FusionStage(PipelineStage):
    def __init__(self, cfg) -> None:
        self._cfg = cfg
        self._rrf_k = cfg.get("rrf_k", 60)

    async def run(self, ctx: PipelineContext, **kwargs) -> None:
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)
