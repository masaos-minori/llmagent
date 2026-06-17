"""Fusion (RRF) stage for RAG pipeline."""

from rag.repository import RagScorer
from rag.stage import PipelineContext, PipelineStage

_DEFAULT_RRF_K = 60


class FusionStage(PipelineStage):
    def __init__(self, rrf_k: int = _DEFAULT_RRF_K) -> None:
        self._rrf_k = rrf_k

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)
