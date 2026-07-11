"""MQE stage for RAG pipeline."""

from rag.llm_client import RagLLM
from rag.stage import PipelineContext, PipelineStage
from shared.types import RagConfig


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
    def __init__(self, cfg: RagConfig, llm: RagLLM) -> None:
        self._cfg = cfg
        self._llm = llm

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
