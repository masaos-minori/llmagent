"""rag/stages/mqe.py
MQE stage for query expansion.
"""

from __future__ import annotations

import logging
from typing import Any

from rag.llm import RagLLM
from rag.stage import PipelineContext

logger = logging.getLogger(__name__)


async def _run_mqe(query: str, cfg: dict[str, Any], llm: RagLLM) -> list[str]:
    """Run MQE with fallback to original query on any error."""
    if not cfg.get("use_mqe", False):
        return [query]
    try:
        return await llm.expand_queries(query)
    except Exception as e:
        # Log the error but continue with the original query
        logger.warning(f"MQE failed, using original query: {e}")
        return [query]


class MqeStage:
    def __init__(self, cfg: dict[str, Any], llm: RagLLM) -> None:
        self._cfg = cfg
        self._llm = llm

    async def run(self, ctx: PipelineContext, **kwargs: Any) -> None:
        """Run MQE stage."""
        ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
        # Notify observers
        for observer in ctx.observers:
            try:
                await observer.on_stage_complete("mqe", ctx)
            except Exception as e:
                logger.warning(f"Observer failed in MQE stage: {e}")
