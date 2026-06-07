"""MQE stage for RAG pipeline."""

import logging

from rag.llm import RagLLM
from rag.stage import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)


async def _run_mqe(query: str, cfg: dict, llm: RagLLM) -> list[str]:
    """Run MQE with fallback to original query on any error."""
    if not cfg.get("use_mqe", True):
        return [query]
    try:
        return await llm.expand_queries(query)
    except Exception as e:
        logger.warning(f"MQE failed, using original query: {e}")
        return [query]


class MqeStage(PipelineStage):
    def __init__(self, cfg, llm) -> None:
        self._cfg = cfg
        self._llm = llm

    async def run(self, ctx: PipelineContext, **kwargs) -> None:
        # Moves MQE logic from RagPipeline._expand_queries() / run()
        ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
