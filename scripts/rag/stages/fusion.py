"""rag/stages/fusion.py
Fusion stage for RRF merge.
"""

from __future__ import annotations

import logging
from typing import Any

from rag.repository import RagScorer
from rag.stage import PipelineContext

logger = logging.getLogger(__name__)


class FusionStage:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self._cfg = cfg
        self._rrf_k = cfg.get("rrf_k", 60)

    async def run(self, ctx: PipelineContext, **kwargs: Any) -> None:
        """Run fusion stage."""
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)
        # Notify observers
        for observer in ctx.observers:
            try:
                await observer.on_stage_complete("fusion", ctx)
            except Exception as e:
                logger.warning(f"Observer failed in Fusion stage: {e}")
