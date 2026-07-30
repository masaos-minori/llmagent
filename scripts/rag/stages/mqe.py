"""scripts/MQE stage for RAG pipeline."""

import logging

from shared.types import RagConfig

from rag.llm_client import RagLLM
from rag.llm_prompts import RagExpansionError
from rag.stage import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)


async def _run_mqe(query: str, cfg: RagConfig, llm: RagLLM) -> list[str]:
    """Run MQE query expansion.

    Raises RagExpansionError on LLM failure.
    Returns [query] when MQE is disabled.
    """
    if not cfg.use_mqe:
        return [query]
    queries: list[str] = await llm.expand_queries(query)
    return queries


class MqeStage(PipelineStage):
    """Multi-query expansion stage that generates alternative queries via LLM."""

    def __init__(self, cfg: RagConfig, llm: RagLLM) -> None:
        """Initialize with RAG configuration and LLM client."""
        self._cfg = cfg
        self._llm = llm

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info("MQE failed, using original query as fallback")
