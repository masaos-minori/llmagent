"""Augment stage for RAG pipeline."""

from rag.stage import PipelineContext, PipelineStage


def _format_chunks(reranked: list) -> str:
    """Format reranked hits with sanitization and boundary markers."""
    from rag.pipeline import _RAG_BLOCK_END, _RAG_BLOCK_START, sanitize_document

    blocks = [
        f"[Source: {c.get('title') or c['url']} | {c['url']}]\n{sanitize_document(c['content'])}"
        for c in reranked
    ]
    content = "\n\n---\n\n".join(blocks)
    return f"{_RAG_BLOCK_START}\n{content}\n{_RAG_BLOCK_END}"


class AugmentStage(PipelineStage):
    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        ctx.augment_result = _format_chunks(ctx.reranked)
