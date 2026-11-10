"""scripts/rag/augment.py

Refiner concern for RAG pipeline.

Encapsulates context refinement logic extracted from RagPipeline. Uses
constructor injection for dependency management.

Module layout:
  rag/pipeline_refiner.py — RefineResult, refine_context
  rag/augment.py        — AugmentRefiner (this file)
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from shared.types import RagConfig, RagHit

from rag.llm_client import RagLLM
from rag.models_result import SearchDiagnostics
from rag.pipeline_refiner import RefineResult, refine_context
from rag.stage import StageResult

logger = logging.getLogger(__name__)


class AugmentRefiner:
    """Owns context refinement related state and behavior.

    Constructor injection of config, status callback, diagnostics, and RagLLM.
    Follows same pattern as other stage modules being created.
    """

    def __init__(
        self,
        cfg: RagConfig,
        *,
        on_status: Callable[[str], None] | None = None,
        search_diagnostics: SearchDiagnostics | None = None,
        llm: RagLLM | None = None,
    ) -> None:
        """Initialize with required dependencies."""
        self._cfg = cfg
        self._on_status = on_status or (lambda _: None)
        self._search_diagnostics = search_diagnostics or SearchDiagnostics()
        self._llm = llm
        self._last_stage_results: list[StageResult] = []

    @property
    def last_stage_results(self) -> list[StageResult]:
        """Return accumulated stage results."""
        return getattr(self, "_last_stage_results", [])

    @last_stage_results.setter
    def last_stage_results(self, value: list[StageResult]) -> None:
        self._last_stage_results = value

    def reset_request_state(self) -> None:
        """Reset per-request refiner state to the frozen defaults.

        Called once at the top of every ``RagPipeline.augment()`` (on every path) so
        a long-lived pipeline does not accumulate stage records or carry
        stale diagnostics across requests. Assigns fresh objects rather than
        clearing the existing list, so a list previously handed to
        ``RagPipeline.last_stage_results`` is never mutated in place.
        """
        self._search_diagnostics = SearchDiagnostics()
        self._last_stage_results = []

    @property
    def search_diagnostics(self) -> SearchDiagnostics:
        """Return search diagnostics."""
        return self._search_diagnostics

    @search_diagnostics.setter
    def search_diagnostics(self, value: SearchDiagnostics) -> None:
        self._search_diagnostics = value

    async def run_refiner(
        self,
        reranked: list[RagHit],
        query: str,
    ) -> RefineResult:
        """Run refiner and return result."""
        if self._llm is None:
            raise ValueError("RagLLM dependency not injected")
        t0 = time.perf_counter()
        refined = await refine_context(
            self._llm,
            self._on_status,
            reranked,
            query,
            max_tokens=self._cfg.refiner_max_tokens,
            per_chunk_chars=self._cfg.refiner_max_chars_per_chunk,
            timeout=self._cfg.refiner_timeout,
        )
        elapsed = time.perf_counter() - t0
        from typing import Literal

        refiner_status: Literal["success", "fallback"] = (
            "success" if refined.text is not None else "fallback"
        )
        self.last_stage_results.append(
            StageResult(
                stage_name="Refiner",
                status=refiner_status,
                elapsed_seconds=elapsed,
                fallback_reason=refined.reason,
            )
        )
        if refined.text is None:
            logger.info(
                "augment: refiner fallback (reason=%s); using raw chunks",
                refined.reason,
            )
        return refined
