"""scripts/rag/stages/fusion.py

Fusion (RRF) stage for RAG pipeline."""

import logging

from rag.repository import RagScorer, _dedup_hits
from rag.stage import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)

_DEFAULT_RRF_K = 60


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁFusionStageǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁFusionStageǁrun__mutmut: MutantDict = {}  # type: ignore


class FusionStage(PipelineStage):
    """Reciprocal Rank Fusion (RRF) stage for merging search results from multiple queries."""

    @_mutmut_mutated(mutants_xǁFusionStageǁ__init____mutmut)
    def __init__(self, rrf_k: int = _DEFAULT_RRF_K, use_rrf: bool = True) -> None:
        """Initialize with RRF constant k and whether to apply RRF scoring."""
        self._rrf_k = rrf_k
        self._use_rrf = use_rrf

    def xǁFusionStageǁ__init____mutmut_orig(self, rrf_k: int = _DEFAULT_RRF_K, use_rrf: bool = True) -> None:
        """Initialize with RRF constant k and whether to apply RRF scoring."""
        self._rrf_k = rrf_k
        self._use_rrf = use_rrf

    def xǁFusionStageǁ__init____mutmut_1(self, rrf_k: int = _DEFAULT_RRF_K, use_rrf: bool = False) -> None:
        """Initialize with RRF constant k and whether to apply RRF scoring."""
        self._rrf_k = rrf_k
        self._use_rrf = use_rrf

    def xǁFusionStageǁ__init____mutmut_2(self, rrf_k: int = _DEFAULT_RRF_K, use_rrf: bool = True) -> None:
        """Initialize with RRF constant k and whether to apply RRF scoring."""
        self._rrf_k = None
        self._use_rrf = use_rrf

    def xǁFusionStageǁ__init____mutmut_3(self, rrf_k: int = _DEFAULT_RRF_K, use_rrf: bool = True) -> None:
        """Initialize with RRF constant k and whether to apply RRF scoring."""
        self._rrf_k = rrf_k
        self._use_rrf = None

    @_mutmut_mutated(mutants_xǁFusionStageǁrun__mutmut)
    async def run(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                "FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit"
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)

    async def xǁFusionStageǁrun__mutmut_orig(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                "FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit"
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)

    async def xǁFusionStageǁrun__mutmut_1(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if self._use_rrf:
            logger.info(
                "FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit"
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)

    async def xǁFusionStageǁrun__mutmut_2(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                None
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)

    async def xǁFusionStageǁrun__mutmut_3(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                "XXFusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefitXX"
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)

    async def xǁFusionStageǁrun__mutmut_4(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                "fusionstage: dedup-only mode (use_rrf=false) — rank signal disabled, mqe provides no ranking benefit"
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)

    async def xǁFusionStageǁrun__mutmut_5(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                "FUSIONSTAGE: DEDUP-ONLY MODE (USE_RRF=FALSE) — RANK SIGNAL DISABLED, MQE PROVIDES NO RANKING BENEFIT"
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)

    async def xǁFusionStageǁrun__mutmut_6(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                "FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit"
            )
            ctx.merged = None
            return
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)

    async def xǁFusionStageǁrun__mutmut_7(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                "FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit"
            )
            ctx.merged = _dedup_hits(None)
            return
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=self._rrf_k)

    async def xǁFusionStageǁrun__mutmut_8(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                "FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit"
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = None

    async def xǁFusionStageǁrun__mutmut_9(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                "FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit"
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = RagScorer.rrf_merge(None, rrf_k=self._rrf_k)

    async def xǁFusionStageǁrun__mutmut_10(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                "FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit"
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, rrf_k=None)

    async def xǁFusionStageǁrun__mutmut_11(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                "FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit"
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = RagScorer.rrf_merge(rrf_k=self._rrf_k)

    async def xǁFusionStageǁrun__mutmut_12(self, ctx: PipelineContext, **kwargs: object) -> None:
        """Merge search results using RRF or dedup-only mode based on configuration."""
        if not self._use_rrf:
            logger.info(
                "FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit"
            )
            ctx.merged = _dedup_hits(ctx.search_results)
            return
        ctx.merged = RagScorer.rrf_merge(ctx.search_results, )

mutants_xǁFusionStageǁ__init____mutmut['_mutmut_orig'] = FusionStage.xǁFusionStageǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁFusionStageǁ__init____mutmut['xǁFusionStageǁ__init____mutmut_1'] = FusionStage.xǁFusionStageǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁFusionStageǁ__init____mutmut['xǁFusionStageǁ__init____mutmut_2'] = FusionStage.xǁFusionStageǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁFusionStageǁ__init____mutmut['xǁFusionStageǁ__init____mutmut_3'] = FusionStage.xǁFusionStageǁ__init____mutmut_3 # type: ignore # mutmut generated

mutants_xǁFusionStageǁrun__mutmut['_mutmut_orig'] = FusionStage.xǁFusionStageǁrun__mutmut_orig # type: ignore # mutmut generated
mutants_xǁFusionStageǁrun__mutmut['xǁFusionStageǁrun__mutmut_1'] = FusionStage.xǁFusionStageǁrun__mutmut_1 # type: ignore # mutmut generated
mutants_xǁFusionStageǁrun__mutmut['xǁFusionStageǁrun__mutmut_2'] = FusionStage.xǁFusionStageǁrun__mutmut_2 # type: ignore # mutmut generated
mutants_xǁFusionStageǁrun__mutmut['xǁFusionStageǁrun__mutmut_3'] = FusionStage.xǁFusionStageǁrun__mutmut_3 # type: ignore # mutmut generated
mutants_xǁFusionStageǁrun__mutmut['xǁFusionStageǁrun__mutmut_4'] = FusionStage.xǁFusionStageǁrun__mutmut_4 # type: ignore # mutmut generated
mutants_xǁFusionStageǁrun__mutmut['xǁFusionStageǁrun__mutmut_5'] = FusionStage.xǁFusionStageǁrun__mutmut_5 # type: ignore # mutmut generated
mutants_xǁFusionStageǁrun__mutmut['xǁFusionStageǁrun__mutmut_6'] = FusionStage.xǁFusionStageǁrun__mutmut_6 # type: ignore # mutmut generated
mutants_xǁFusionStageǁrun__mutmut['xǁFusionStageǁrun__mutmut_7'] = FusionStage.xǁFusionStageǁrun__mutmut_7 # type: ignore # mutmut generated
mutants_xǁFusionStageǁrun__mutmut['xǁFusionStageǁrun__mutmut_8'] = FusionStage.xǁFusionStageǁrun__mutmut_8 # type: ignore # mutmut generated
mutants_xǁFusionStageǁrun__mutmut['xǁFusionStageǁrun__mutmut_9'] = FusionStage.xǁFusionStageǁrun__mutmut_9 # type: ignore # mutmut generated
mutants_xǁFusionStageǁrun__mutmut['xǁFusionStageǁrun__mutmut_10'] = FusionStage.xǁFusionStageǁrun__mutmut_10 # type: ignore # mutmut generated
mutants_xǁFusionStageǁrun__mutmut['xǁFusionStageǁrun__mutmut_11'] = FusionStage.xǁFusionStageǁrun__mutmut_11 # type: ignore # mutmut generated
mutants_xǁFusionStageǁrun__mutmut['xǁFusionStageǁrun__mutmut_12'] = FusionStage.xǁFusionStageǁrun__mutmut_12 # type: ignore # mutmut generated
