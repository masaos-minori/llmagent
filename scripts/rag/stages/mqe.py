"""MQE stage for RAG pipeline."""

import logging

from rag.stage import PipelineContext

logger = logging.getLogger(__name__)


class MqeStage:
    def __init__(self, cfg, llm) -> None:
        self._cfg = cfg
        self._llm = llm

    async def run(self, ctx: PipelineContext, **kwargs) -> None:
        if not self._cfg.get("use_mqe"):
            ctx.queries = [ctx.query]
            return
        try:
            ctx.queries = await self._llm.expand_queries(
                ctx.query, context=ctx.history_context
            )
        except Exception as e:
            logger.warning(f"MQE failed, using original query: {e}")
            ctx.queries = [ctx.query]
