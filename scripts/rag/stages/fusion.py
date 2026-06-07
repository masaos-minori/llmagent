"""Fusion stage for RAG pipeline."""

from rag.repository import RagScorer
from rag.stage import PipelineContext


class FusionStage:
    def __init__(self, cfg) -> None:
        self._cfg = cfg
        self._rrf_k = cfg.get("rrf_k", 20)

    async def run(self, ctx: PipelineContext, **kwargs) -> None:
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)
