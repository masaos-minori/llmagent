"""scripts/rag/stage_lifecycle.py

Extracted from scripts/rag/pipeline.py — stage lifecycle management.

Provides RagPipelineStageLifecycle class that encapsulates the entire
stage execution loop including stage creation, execution, status tracking,
and fallback detection.
"""

import logging
import sqlite3
import time
from collections.abc import Callable
from typing import Literal, cast

import httpx
from db.helper import SQLiteHelper

from rag.llm_client import RagLLM
from rag.models_config import RagConfigImpl
from rag.models_data import TwoStageFetchResult
from rag.models_result import SearchDiagnostics
from rag.stage import PipelineContext, PipelineStage, StageResult
from rag.stages.augment import AugmentStage
from rag.stages.fusion import FusionStage
from rag.stages.mqe import MqeStage
from rag.stages.rerank import RerankStage
from rag.stages.search import SearchStage
from rag.types import PipelineRunResult

logger = logging.getLogger(__name__)


class RagPipelineStageLifecycle:
    """Encapsulates the RAG pipeline stage execution loop.

    Accepts RagConfigImpl (not RagConfig) since resolve_rag_config()
    returns the concrete type.
    """

    def __init__(
        self,
        cfg: RagConfigImpl,
        llm: Callable[..., object],
        http_client: httpx.AsyncClient,
        embed_url: str | None,
    ) -> None:
        self._cfg = cfg
        self._llm = llm
        self._http = http_client
        self._embed_url = embed_url
        self.last_timings: dict[str, float] = {}
        self.last_stage_results: list[StageResult] = []
        self.last_fetch_result: TwoStageFetchResult | None = None
        self.last_search_diagnostics: SearchDiagnostics | None = None
        self.stat_search_embed_failed: int = 0
        self.stat_search_fts_errors: int = 0

    def _get_stage_status(
        self, stage: PipelineStage, ctx: PipelineContext
    ) -> tuple[Literal["success", "fallback", "failure"], str | None]:
        """Return the execution status of a pipeline stage with an optional reason string."""
        if hasattr(stage, "get_status"):
            return stage.get_status(ctx)
        return "success", None

    async def _run_stage(
        self, stage: PipelineStage, ctx: PipelineContext, db: SQLiteHelper
    ) -> None:
        """Run a single pipeline stage and record its result."""
        t0 = time.perf_counter()
        exc_msg: str | None = None
        try:
            await stage.run(ctx, db=db)
        except (
            RuntimeError,
            sqlite3.OperationalError,
            httpx.HTTPStatusError,
            httpx.RequestError,
            TimeoutError,
        ) as e:
            exc_msg = str(e)
            logger.warning("Stage %s failed: %s", stage.__class__.__name__, e)
        elapsed = time.perf_counter() - t0
        self.last_timings[stage.__class__.__name__] = elapsed
        stage_status: Literal["success", "fallback", "failure"]
        stage_reason: str | None
        if exc_msg is not None:
            stage_status, stage_reason = "failure", exc_msg
        else:
            stage_status, stage_reason = self._get_stage_status(stage, ctx)
        ctx.stage_results.append(
            StageResult(
                stage_name=stage.__class__.__name__,
                status=stage_status,
                elapsed_seconds=elapsed,
                fallback_reason=stage_reason,
            )
        )

    async def run(
        self,
        query: str,
        db: SQLiteHelper,
        history_context: str = "",
    ) -> PipelineRunResult:
        """Execute MQE→search→RRF→rerank on an open DB; returns PipelineRunResult; on_clear() called on exit."""
        ctx = PipelineContext(query=query, history_context=history_context)
        self.last_timings = {}
        pre_augment_stages: list = [
            MqeStage(cast(RagConfigImpl, self._cfg), cast(RagLLM, self._llm)),
            SearchStage(
                cast(RagConfigImpl, self._cfg), self._http, self._embed_url or ""
            ),
            FusionStage(use_rrf=self._cfg.use_rrf, rrf_k=self._cfg.rrf_k),
            RerankStage(cast(RagConfigImpl, self._cfg), cast(RagLLM, self._llm)),
        ]
        for stage in pre_augment_stages:
            await self._run_stage(stage, ctx, db)

        augment_stage = AugmentStage()
        t0 = time.perf_counter()
        await augment_stage.run(ctx, db=db)
        elapsed = time.perf_counter() - t0
        self.last_timings[augment_stage.__class__.__name__] = elapsed
        ctx.stage_results.append(
            StageResult(
                stage_name=augment_stage.__class__.__name__,
                status="success",
                elapsed_seconds=elapsed,
                fallback_reason=None,
            )
        )

        # Store for two-stage fetch callers (e.g. REPLAgent._run_turn)
        self.last_fetch_result = TwoStageFetchResult(
            hits=ctx.reranked,
            min_score_applied=self._cfg.rag_min_score,
            max_chunks_per_doc=self._cfg.max_chunks_per_doc,
        )
        self.last_stage_results = list(ctx.stage_results)
        # Save search diagnostics and accumulate cumulative counters
        self.last_search_diagnostics = ctx.search_diagnostics
        self.stat_search_embed_failed += ctx.search_diagnostics.embed_failed
        self.stat_search_fts_errors += ctx.search_diagnostics.fts_errors
        fallbacks = [r for r in ctx.stage_results if r["status"] == "fallback"]
        if fallbacks:
            logger.info(
                "Pipeline fallback stages: %s",
                ", ".join(
                    f"{r['stage_name']}({r['fallback_reason']})" for r in fallbacks
                ),
            )

        return PipelineRunResult(
            queries=ctx.queries,
            search_results=ctx.search_results,
            merged=ctx.merged,
            reranked=ctx.reranked,
            stage_results=list(ctx.stage_results),
            diagnostics=ctx.search_diagnostics,
        )
