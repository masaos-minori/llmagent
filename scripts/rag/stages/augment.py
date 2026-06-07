"""rag/stages/augment.py
Augment stage for formatting output.
"""

from __future__ import annotations

import logging
from typing import Any

from rag.stage import PipelineContext
from rag.types import RagHit

logger = logging.getLogger(__name__)


def _format_chunks(reranked: list[RagHit]) -> str:
    """Format reranked hits as a newline-separated source+content block."""
    blocks = [
        f"[Source: {c.get('title') or c['url']} | {c['url']}]\n{c['content']}"
        for c in reranked
    ]
    return "\n\n---\n\n".join(blocks)


class AugmentStage:
    async def run(self, ctx: PipelineContext, **kwargs: Any) -> None:
        """Run augment stage."""
        ctx.augment_result = _format_chunks(ctx.reranked)
        # Notify observers
        for observer in ctx.observers:
            try:
                await observer.on_stage_complete("augment", ctx)
            except Exception as e:
                logger.warning(f"Observer failed in Augment stage: {e}")
