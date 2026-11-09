"""scripts/rag/stages/augment.py

Augment stage for RAG pipeline."""

from typing import Literal

from rag.repository import RagHit
from rag.stage import PipelineContext, PipelineStage
from rag.utils import (
    RAG_BLOCK_END,
    RAG_BLOCK_START,
    sanitize_document,
    sanitize_field,
)

# Private aliases of the rag.utils marker constants: importable from this module
# (existing imports depend on them) while a single definition lives in rag.utils.
_RAG_BLOCK_START = RAG_BLOCK_START
_RAG_BLOCK_END = RAG_BLOCK_END


def _format_chunks(reranked: list[RagHit]) -> str:
    """Format reranked hits with sanitization and boundary markers.

    Title and url are sanitized to a single line so a crawled title cannot
    start a new line that mimics a header or a boundary marker.
    """
    if not reranked:
        return f"{_RAG_BLOCK_START}\n\n{_RAG_BLOCK_END}"
    blocks = []
    for c in reranked:
        title = sanitize_field(c.title or "")
        url = sanitize_field(c.url or "")
        label = title or url
        blocks.append(f"[Source: {label} | {url}]\n{sanitize_document(c.content)}")
    content = "\n\n---\n\n".join(blocks)
    return f"{_RAG_BLOCK_START}\n{content}\n{_RAG_BLOCK_END}"


class AugmentStage(PipelineStage):
    """Text augmentation stage that formats reranked chunks into RAG context blocks."""

    def get_status(
        self, ctx: PipelineContext
    ) -> tuple[Literal["success", "fallback"], str | None]:
        """Return execution status of this stage with optional reason string."""
        if not ctx.reranked:
            return "fallback", "no reranked results"
        return "success", None

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Format reranked chunks into a RAG context block and store in context."""
        ctx.augment_result = _format_chunks(ctx.reranked)
