"""MQE stage for RAG pipeline."""

from shared.types import RagConfig

from rag.llm import RagExpansionError, RagLLM  # noqa: F401 — re-exported for callers
from rag.stage import PipelineContext, PipelineStage


async def _run_mqe(query: str, cfg: RagConfig, llm: RagLLM) -> list[str]:
    """Run MQE query expansion.

    Raises RagExpansionError on LLM failure.
    Returns [query] when MQE is disabled.
    """
    if not cfg.use_mqe:
        return [query]
    return await llm.expand_queries(query)


class MqeStage(PipelineStage):
    def __init__(self, cfg: RagConfig, llm: RagLLM) -> None:
        self._cfg = cfg
        self._llm = llm

    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
