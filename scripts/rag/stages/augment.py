"""Augment stage for RAG pipeline."""

from rag.stage import PipelineContext


class AugmentStage:
    def __init__(self) -> None:
        pass

    async def run(self, ctx: PipelineContext, **kwargs) -> None:
        from rag.pipeline import RagPipeline

        ctx.augment_result = RagPipeline._format_chunks(ctx.reranked)
