"""Augment stage for RAG pipeline."""

from rag.repository import RagHit
from rag.stage import PipelineContext, PipelineStage
from rag.utils import sanitize_document

_RAG_BLOCK_START = "[RAG_CONTEXT_START]"
_RAG_BLOCK_END = "[RAG_CONTEXT_END]"


def _format_chunks(reranked: list[RagHit]) -> str:
    """Format reranked hits with sanitization and boundary markers."""
    if not reranked:
        return f"{_RAG_BLOCK_START}\n\n{_RAG_BLOCK_END}"
    blocks = [
        f"[Source: {c.title if c.title else c.url} | {c.url}]\n{sanitize_document(c.content)}"
        for c in reranked
    ]
    content = "\n\n---\n\n".join(blocks)
    return f"{_RAG_BLOCK_START}\n{content}\n{_RAG_BLOCK_END}"


class AugmentStage(PipelineStage):
    """Text augmentation stage that formats reranked chunks into RAG context blocks."""

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Format reranked chunks into a RAG context block and store in context."""
        ctx.augment_result = _format_chunks(ctx.reranked)
