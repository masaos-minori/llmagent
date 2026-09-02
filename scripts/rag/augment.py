#!/usr/bin/env python3
"""scripts/rag/augment.py

HTTP augment + refiner concern for RAG pipeline.

Encapsulates HTTP augment delegation and context refinement logic extracted
from RagPipeline. Uses constructor injection for dependency management.

Module layout:
  rag/http_augment.py   — HttpAugment, _map_http_result_kind
  rag/pipeline_refiner.py — RefineResult, refine_context
  rag/augment.py        — AugmentRefiner (this file)
"""

from __future__ import annotations

import dataclasses
import logging
import time
from collections.abc import Callable

import httpx
from shared.types import RagConfig, RagHit

from rag.http_augment import HttpAugment, _map_http_result_kind
from rag.llm_client import RagLLM
from rag.models_data import TwoStageFetchResult
from rag.models_result import HttpResultKind, ResultSource, SearchDiagnostics
from rag.pipeline_refiner import RefineResult, refine_context
from rag.stage import StageResult

logger = logging.getLogger(__name__)


class AugmentRefiner:
    """Owns all HTTP augment and context refinement related state and behavior.

    Constructor injection of HttpAugment, config, and result type dependencies.
    Follows same pattern as other stage modules being created.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        cfg: RagConfig,
        *,
        on_status: Callable[[str], None] | None = None,
        set_fetch_result: Callable[[TwoStageFetchResult], None] | None = None,
        set_fallback_reason: Callable[[str], None] | None = None,
        search_diagnostics: SearchDiagnostics | None = None,
        llm: RagLLM | None = None,
    ) -> None:
        """Initialize with required dependencies."""
        self._http = http
        self._cfg = cfg
        self._on_status = on_status or (lambda _: None)
        self._set_fetch_result = set_fetch_result or (lambda _: None)
        self._set_fallback_reason = set_fallback_reason or (lambda _: None)
        self._search_diagnostics = search_diagnostics or SearchDiagnostics()
        self._llm = llm

    async def run_http_augment(
        self,
        query: str,
        history_context: str,
        rag_url: str,
    ) -> str | None:
        """Run HTTP augment via HttpAugment and return result or None for fallback."""
        http_aug = HttpAugment(
            self._http,
            rag_url,
            auth_token=self._cfg.rag_auth_token or "",
            set_fetch_result=lambda fr: self._set_fetch_result(fr),
            set_fallback_reason=lambda _: self._set_fallback_reason(_),
        )
        result = await http_aug.run(query, history_context)
        # Apply diagnostics from HttpAugment result
        if result.result is not None:
            result_source = ResultSource.REMOTE
        else:
            result_source = ResultSource.FALLBACK

        self._search_diagnostics = dataclasses.replace(
            self._search_diagnostics,
            result_source=result_source,
            http_result_kind=_map_http_result_kind(result.http_result_kind),
            remote_status_code=result.status_code,
            remote_latency_ms=result.latency_ms,
        )
        # Apply stage result from HttpAugment
        if http_aug.stage_result is not None:
            self._last_stage_results.append(http_aug.stage_result)
        http_result: str | None = result.result
        return http_result

    @property
    def last_stage_results(self) -> list[StageResult]:
        """Return accumulated stage results."""
        return getattr(self, "_last_stage_results", [])

    @last_stage_results.setter
    def last_stage_results(self, value: list[StageResult]) -> None:
        self._last_stage_results = value

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

        refiner_status: Literal["success", "fallback"] = "success" if refined.text is not None else "fallback"
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

    @staticmethod
    def map_http_result_kind(kind: str | None) -> HttpResultKind:
        """Map HTTP result kind string to HttpResultKind enum."""
        if kind is None:
            return HttpResultKind.NOT_USED
        return _map_http_result_kind(kind)
