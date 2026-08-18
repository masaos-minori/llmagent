"""scripts/rag/stages/mqe.py

MQE stage for RAG pipeline."""

import logging

from shared.types import RagConfig

from rag.llm_client import RagLLM
from rag.llm_prompts import RagExpansionError
from rag.stage import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__run_mqe__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__run_mqe__mutmut)
async def _run_mqe(query: str, cfg: RagConfig, llm: RagLLM) -> list[str]:
    """Run MQE query expansion.

    Raises RagExpansionError on LLM failure.
    Returns [query] when MQE is disabled.
    """
    if not cfg.use_mqe:
        return [query]
    queries: list[str] = await llm.expand_queries(query)
    return queries


async def x__run_mqe__mutmut_orig(query: str, cfg: RagConfig, llm: RagLLM) -> list[str]:
    """Run MQE query expansion.

    Raises RagExpansionError on LLM failure.
    Returns [query] when MQE is disabled.
    """
    if not cfg.use_mqe:
        return [query]
    queries: list[str] = await llm.expand_queries(query)
    return queries


async def x__run_mqe__mutmut_1(query: str, cfg: RagConfig, llm: RagLLM) -> list[str]:
    """Run MQE query expansion.

    Raises RagExpansionError on LLM failure.
    Returns [query] when MQE is disabled.
    """
    if cfg.use_mqe:
        return [query]
    queries: list[str] = await llm.expand_queries(query)
    return queries


async def x__run_mqe__mutmut_2(query: str, cfg: RagConfig, llm: RagLLM) -> list[str]:
    """Run MQE query expansion.

    Raises RagExpansionError on LLM failure.
    Returns [query] when MQE is disabled.
    """
    if not cfg.use_mqe:
        return [query]
    queries: list[str] = None
    return queries


async def x__run_mqe__mutmut_3(query: str, cfg: RagConfig, llm: RagLLM) -> list[str]:
    """Run MQE query expansion.

    Raises RagExpansionError on LLM failure.
    Returns [query] when MQE is disabled.
    """
    if not cfg.use_mqe:
        return [query]
    queries: list[str] = await llm.expand_queries(None)
    return queries

mutants_x__run_mqe__mutmut['_mutmut_orig'] = x__run_mqe__mutmut_orig # type: ignore # mutmut generated
mutants_x__run_mqe__mutmut['x__run_mqe__mutmut_1'] = x__run_mqe__mutmut_1 # type: ignore # mutmut generated
mutants_x__run_mqe__mutmut['x__run_mqe__mutmut_2'] = x__run_mqe__mutmut_2 # type: ignore # mutmut generated
mutants_x__run_mqe__mutmut['x__run_mqe__mutmut_3'] = x__run_mqe__mutmut_3 # type: ignore # mutmut generated
mutants_xǁMqeStageǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁMqeStageǁrun__mutmut: MutantDict = {}  # type: ignore


class MqeStage(PipelineStage):
    """Multi-query expansion stage that generates alternative queries via LLM."""

    @_mutmut_mutated(mutants_xǁMqeStageǁ__init____mutmut)
    def __init__(self, cfg: RagConfig, llm: RagLLM) -> None:
        """Initialize with RAG configuration and LLM client."""
        self._cfg = cfg
        self._llm = llm

    def xǁMqeStageǁ__init____mutmut_orig(self, cfg: RagConfig, llm: RagLLM) -> None:
        """Initialize with RAG configuration and LLM client."""
        self._cfg = cfg
        self._llm = llm

    def xǁMqeStageǁ__init____mutmut_1(self, cfg: RagConfig, llm: RagLLM) -> None:
        """Initialize with RAG configuration and LLM client."""
        self._cfg = None
        self._llm = llm

    def xǁMqeStageǁ__init____mutmut_2(self, cfg: RagConfig, llm: RagLLM) -> None:
        """Initialize with RAG configuration and LLM client."""
        self._cfg = cfg
        self._llm = None

    @_mutmut_mutated(mutants_xǁMqeStageǁrun__mutmut)
    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info("MQE failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_orig(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info("MQE failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_1(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = None
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info("MQE failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_2(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(None, self._cfg, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info("MQE failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_3(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, None, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info("MQE failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_4(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._cfg, None)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info("MQE failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_5(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(self._cfg, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info("MQE failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_6(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info("MQE failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_7(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._cfg, )
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info("MQE failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_8(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
        except RagExpansionError:
            ctx.queries = None
            ctx._fallback_reason = "mqe_exception"
            logger.info("MQE failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_9(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = None
            logger.info("MQE failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_10(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "XXmqe_exceptionXX"
            logger.info("MQE failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_11(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "MQE_EXCEPTION"
            logger.info("MQE failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_12(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info(None)

    async def xǁMqeStageǁrun__mutmut_13(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info("XXMQE failed, using original query as fallbackXX")

    async def xǁMqeStageǁrun__mutmut_14(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info("mqe failed, using original query as fallback")

    async def xǁMqeStageǁrun__mutmut_15(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute multi-query expansion and store results in context."""
        try:
            ctx.queries = await _run_mqe(ctx.query, self._cfg, self._llm)
        except RagExpansionError:
            ctx.queries = [ctx.query]
            ctx._fallback_reason = "mqe_exception"
            logger.info("MQE FAILED, USING ORIGINAL QUERY AS FALLBACK")

mutants_xǁMqeStageǁ__init____mutmut['_mutmut_orig'] = MqeStage.xǁMqeStageǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁMqeStageǁ__init____mutmut['xǁMqeStageǁ__init____mutmut_1'] = MqeStage.xǁMqeStageǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁMqeStageǁ__init____mutmut['xǁMqeStageǁ__init____mutmut_2'] = MqeStage.xǁMqeStageǁ__init____mutmut_2 # type: ignore # mutmut generated

mutants_xǁMqeStageǁrun__mutmut['_mutmut_orig'] = MqeStage.xǁMqeStageǁrun__mutmut_orig # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_1'] = MqeStage.xǁMqeStageǁrun__mutmut_1 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_2'] = MqeStage.xǁMqeStageǁrun__mutmut_2 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_3'] = MqeStage.xǁMqeStageǁrun__mutmut_3 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_4'] = MqeStage.xǁMqeStageǁrun__mutmut_4 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_5'] = MqeStage.xǁMqeStageǁrun__mutmut_5 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_6'] = MqeStage.xǁMqeStageǁrun__mutmut_6 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_7'] = MqeStage.xǁMqeStageǁrun__mutmut_7 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_8'] = MqeStage.xǁMqeStageǁrun__mutmut_8 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_9'] = MqeStage.xǁMqeStageǁrun__mutmut_9 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_10'] = MqeStage.xǁMqeStageǁrun__mutmut_10 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_11'] = MqeStage.xǁMqeStageǁrun__mutmut_11 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_12'] = MqeStage.xǁMqeStageǁrun__mutmut_12 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_13'] = MqeStage.xǁMqeStageǁrun__mutmut_13 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_14'] = MqeStage.xǁMqeStageǁrun__mutmut_14 # type: ignore # mutmut generated
mutants_xǁMqeStageǁrun__mutmut['xǁMqeStageǁrun__mutmut_15'] = MqeStage.xǁMqeStageǁrun__mutmut_15 # type: ignore # mutmut generated
