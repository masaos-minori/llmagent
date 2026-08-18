"""scripts/rag/stages/rerank.py

Rerank stage for RAG pipeline."""

import logging

from shared.types import RagConfig

from rag.llm_client import RagLLM
from rag.llm_prompts import RagRerankError
from rag.repository import RagHit, deduplicate_chunks
from rag.stage import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__rerank__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__rerank__mutmut)
async def _rerank(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_orig(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_1(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_2(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(None, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_3(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, None)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_4(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_5(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, )
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_6(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = None
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_7(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        None,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_8(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        None,
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_9(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        None,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_10(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=None,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_11(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_12(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_13(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_14(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        )
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_15(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = None
    return deduped


async def x__rerank__mutmut_16(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(None, cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_17(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, None)
    return deduped


async def x__rerank__mutmut_18(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(cfg.max_chunks_per_doc)
    return deduped


async def x__rerank__mutmut_19(
    query: str, merged: list[RagHit], cfg: RagConfig, llm: RagLLM
) -> list[RagHit]:
    """Apply Cross-Encoder rerank then dedup.

    Raises RagRerankError on LLM failure.
    Falls back to RRF order when use_rerank=False.
    """
    if not cfg.use_rerank:
        return _rerank_fallback(merged, cfg)
    result = await llm.cross_encoder_rerank(
        query,
        merged[: cfg.top_k_rerank],
        cfg.rag_top_k,
        rag_min_score=cfg.rag_min_score,
    )
    deduped: list[RagHit] = deduplicate_chunks(result, )
    return deduped

mutants_x__rerank__mutmut['_mutmut_orig'] = x__rerank__mutmut_orig # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_1'] = x__rerank__mutmut_1 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_2'] = x__rerank__mutmut_2 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_3'] = x__rerank__mutmut_3 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_4'] = x__rerank__mutmut_4 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_5'] = x__rerank__mutmut_5 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_6'] = x__rerank__mutmut_6 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_7'] = x__rerank__mutmut_7 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_8'] = x__rerank__mutmut_8 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_9'] = x__rerank__mutmut_9 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_10'] = x__rerank__mutmut_10 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_11'] = x__rerank__mutmut_11 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_12'] = x__rerank__mutmut_12 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_13'] = x__rerank__mutmut_13 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_14'] = x__rerank__mutmut_14 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_15'] = x__rerank__mutmut_15 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_16'] = x__rerank__mutmut_16 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_17'] = x__rerank__mutmut_17 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_18'] = x__rerank__mutmut_18 # type: ignore # mutmut generated
mutants_x__rerank__mutmut['x__rerank__mutmut_19'] = x__rerank__mutmut_19 # type: ignore # mutmut generated
mutants_x__rerank_fallback__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__rerank_fallback__mutmut)
def _rerank_fallback(merged: list[RagHit], cfg: RagConfig) -> list[RagHit]:
    """Fallback reranking when use_rerank=False: slice + dedup."""
    result = merged[: cfg.rag_top_k]
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


def x__rerank_fallback__mutmut_orig(merged: list[RagHit], cfg: RagConfig) -> list[RagHit]:
    """Fallback reranking when use_rerank=False: slice + dedup."""
    result = merged[: cfg.rag_top_k]
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


def x__rerank_fallback__mutmut_1(merged: list[RagHit], cfg: RagConfig) -> list[RagHit]:
    """Fallback reranking when use_rerank=False: slice + dedup."""
    result = None
    deduped: list[RagHit] = deduplicate_chunks(result, cfg.max_chunks_per_doc)
    return deduped


def x__rerank_fallback__mutmut_2(merged: list[RagHit], cfg: RagConfig) -> list[RagHit]:
    """Fallback reranking when use_rerank=False: slice + dedup."""
    result = merged[: cfg.rag_top_k]
    deduped: list[RagHit] = None
    return deduped


def x__rerank_fallback__mutmut_3(merged: list[RagHit], cfg: RagConfig) -> list[RagHit]:
    """Fallback reranking when use_rerank=False: slice + dedup."""
    result = merged[: cfg.rag_top_k]
    deduped: list[RagHit] = deduplicate_chunks(None, cfg.max_chunks_per_doc)
    return deduped


def x__rerank_fallback__mutmut_4(merged: list[RagHit], cfg: RagConfig) -> list[RagHit]:
    """Fallback reranking when use_rerank=False: slice + dedup."""
    result = merged[: cfg.rag_top_k]
    deduped: list[RagHit] = deduplicate_chunks(result, None)
    return deduped


def x__rerank_fallback__mutmut_5(merged: list[RagHit], cfg: RagConfig) -> list[RagHit]:
    """Fallback reranking when use_rerank=False: slice + dedup."""
    result = merged[: cfg.rag_top_k]
    deduped: list[RagHit] = deduplicate_chunks(cfg.max_chunks_per_doc)
    return deduped


def x__rerank_fallback__mutmut_6(merged: list[RagHit], cfg: RagConfig) -> list[RagHit]:
    """Fallback reranking when use_rerank=False: slice + dedup."""
    result = merged[: cfg.rag_top_k]
    deduped: list[RagHit] = deduplicate_chunks(result, )
    return deduped

mutants_x__rerank_fallback__mutmut['_mutmut_orig'] = x__rerank_fallback__mutmut_orig # type: ignore # mutmut generated
mutants_x__rerank_fallback__mutmut['x__rerank_fallback__mutmut_1'] = x__rerank_fallback__mutmut_1 # type: ignore # mutmut generated
mutants_x__rerank_fallback__mutmut['x__rerank_fallback__mutmut_2'] = x__rerank_fallback__mutmut_2 # type: ignore # mutmut generated
mutants_x__rerank_fallback__mutmut['x__rerank_fallback__mutmut_3'] = x__rerank_fallback__mutmut_3 # type: ignore # mutmut generated
mutants_x__rerank_fallback__mutmut['x__rerank_fallback__mutmut_4'] = x__rerank_fallback__mutmut_4 # type: ignore # mutmut generated
mutants_x__rerank_fallback__mutmut['x__rerank_fallback__mutmut_5'] = x__rerank_fallback__mutmut_5 # type: ignore # mutmut generated
mutants_x__rerank_fallback__mutmut['x__rerank_fallback__mutmut_6'] = x__rerank_fallback__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRerankStageǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁRerankStageǁrun__mutmut: MutantDict = {}  # type: ignore


class RerankStage(PipelineStage):
    """LLM-based reranking stage that reorders merged search results by relevance."""

    @_mutmut_mutated(mutants_xǁRerankStageǁ__init____mutmut)
    def __init__(self, cfg: RagConfig, llm: RagLLM) -> None:
        """Initialize with RAG configuration and LLM client for reranking."""
        self._cfg = cfg
        self._llm = llm

    def xǁRerankStageǁ__init____mutmut_orig(self, cfg: RagConfig, llm: RagLLM) -> None:
        """Initialize with RAG configuration and LLM client for reranking."""
        self._cfg = cfg
        self._llm = llm

    def xǁRerankStageǁ__init____mutmut_1(self, cfg: RagConfig, llm: RagLLM) -> None:
        """Initialize with RAG configuration and LLM client for reranking."""
        self._cfg = None
        self._llm = llm

    def xǁRerankStageǁ__init____mutmut_2(self, cfg: RagConfig, llm: RagLLM) -> None:
        """Initialize with RAG configuration and LLM client for reranking."""
        self._cfg = cfg
        self._llm = None

    @_mutmut_mutated(mutants_xǁRerankStageǁrun__mutmut)
    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_orig(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_1(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = None
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_2(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(None, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_3(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, None, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_4(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, None, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_5(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, None)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_6(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_7(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_8(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_9(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, )
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_10(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = None
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_11(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(None, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_12(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, None)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_13(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_14(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, )
            ctx._fallback_reason = "rerank_exception"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_15(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = None
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_16(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "XXrerank_exceptionXX"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_17(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "RERANK_EXCEPTION"
            logger.info("Rerank failed, falling back to RRF-ranked results")

    async def xǁRerankStageǁrun__mutmut_18(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info(None)

    async def xǁRerankStageǁrun__mutmut_19(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("XXRerank failed, falling back to RRF-ranked resultsXX")

    async def xǁRerankStageǁrun__mutmut_20(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("rerank failed, falling back to rrf-ranked results")

    async def xǁRerankStageǁrun__mutmut_21(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Execute reranking and store the reordered results in context."""
        try:
            ctx.reranked = await _rerank(ctx.query, ctx.merged, self._cfg, self._llm)
        except RagRerankError:
            ctx.reranked = _rerank_fallback(ctx.merged, self._cfg)
            ctx._fallback_reason = "rerank_exception"
            logger.info("RERANK FAILED, FALLING BACK TO RRF-RANKED RESULTS")

mutants_xǁRerankStageǁ__init____mutmut['_mutmut_orig'] = RerankStage.xǁRerankStageǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁRerankStageǁ__init____mutmut['xǁRerankStageǁ__init____mutmut_1'] = RerankStage.xǁRerankStageǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁRerankStageǁ__init____mutmut['xǁRerankStageǁ__init____mutmut_2'] = RerankStage.xǁRerankStageǁ__init____mutmut_2 # type: ignore # mutmut generated

mutants_xǁRerankStageǁrun__mutmut['_mutmut_orig'] = RerankStage.xǁRerankStageǁrun__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_1'] = RerankStage.xǁRerankStageǁrun__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_2'] = RerankStage.xǁRerankStageǁrun__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_3'] = RerankStage.xǁRerankStageǁrun__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_4'] = RerankStage.xǁRerankStageǁrun__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_5'] = RerankStage.xǁRerankStageǁrun__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_6'] = RerankStage.xǁRerankStageǁrun__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_7'] = RerankStage.xǁRerankStageǁrun__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_8'] = RerankStage.xǁRerankStageǁrun__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_9'] = RerankStage.xǁRerankStageǁrun__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_10'] = RerankStage.xǁRerankStageǁrun__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_11'] = RerankStage.xǁRerankStageǁrun__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_12'] = RerankStage.xǁRerankStageǁrun__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_13'] = RerankStage.xǁRerankStageǁrun__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_14'] = RerankStage.xǁRerankStageǁrun__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_15'] = RerankStage.xǁRerankStageǁrun__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_16'] = RerankStage.xǁRerankStageǁrun__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_17'] = RerankStage.xǁRerankStageǁrun__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_18'] = RerankStage.xǁRerankStageǁrun__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_19'] = RerankStage.xǁRerankStageǁrun__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_20'] = RerankStage.xǁRerankStageǁrun__mutmut_20 # type: ignore # mutmut generated
mutants_xǁRerankStageǁrun__mutmut['xǁRerankStageǁrun__mutmut_21'] = RerankStage.xǁRerankStageǁrun__mutmut_21 # type: ignore # mutmut generated
