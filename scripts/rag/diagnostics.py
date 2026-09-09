"""scripts/rag/diagnostics.py

Extracted from scripts/rag/pipeline.py — get_diagnostics().

Provides PipelineDiagnostics dataclass mirroring get_diagnostics()'s
current dict keys exactly, reducing pipeline.py complexity and providing
typed diagnostics access.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from rag.models_data import TwoStageFetchResult
from rag.models_result import HttpResultKind
from rag.stage import StageResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchDiagnostics:
    """Search execution diagnostics for a single pipeline run."""

    embed_ok: int
    embed_failed: int
    fts_errors: int
    degraded: bool

    def to_dict(self) -> dict[str, object]:
        """Produce the exact same dict shape as the current get_diagnostics()."""
        return {
            "embed_ok": self.embed_ok,
            "embed_failed": self.embed_failed,
            "fts_errors": self.fts_errors,
            "degraded": self.degraded,
        }

    @classmethod
    def from_run_result(
        cls, *, embed_ok: int, embed_failed: int, fts_errors: int
    ) -> SearchDiagnostics:
        """Build SearchDiagnostics from a run result."""
        degraded = embed_failed > 0 or fts_errors > 0
        return cls(
            embed_ok=embed_ok,
            embed_failed=embed_failed,
            fts_errors=fts_errors,
            degraded=degraded,
        )


@dataclass(frozen=True)
class PipelineDiagnostics:
    """Pipeline-level diagnostics wrapping SearchDiagnostics.

    Mirrors get_diagnostics()'s current dict keys exactly, excluding
    cumulative counters (stat_search_embed_failed, stat_search_fts_errors).
    """

    search_diagnostics: SearchDiagnostics
    stage_results: list[StageResult] | None = None
    timings: dict[str, float] | None = None
    fetch_result: TwoStageFetchResult | None = None
    use_rrf: bool = True
    rrf_k: int = 60
    http_result_kind: HttpResultKind | None = None

    def to_dict(self) -> dict[str, object]:
        """Produce the exact same dict shape as the current get_diagnostics()."""
        sd = self.search_diagnostics.to_dict()
        stage_results = (
            [dict(r) for r in self.stage_results] if self.stage_results else []
        )
        fallbacks = [r for r in stage_results if r.get("status") == "fallback"]
        fetch = self.fetch_result
        fusion_mode = "rrf" if self.use_rrf else "dedup_only"
        http_result_kind = self.http_result_kind
        refiner_fallbacks = [
            r
            for r in stage_results
            if r.get("stage_name") == "Refiner" and r.get("status") == "fallback"
        ]
        refiner_fallback_count = len(refiner_fallbacks)
        refiner_returned_empty = sum(
            1
            for r in refiner_fallbacks
            if str(r.get("fallback_reason", "")) == "refiner_returned_empty"
        )
        refiner_exception_count = sum(
            1
            for r in refiner_fallbacks
            if str(r.get("fallback_reason", "")).startswith("refiner_exception:")
        )
        return {
            "stage_results": stage_results,
            "timings": dict(self.timings) if self.timings else {},
            "fetch_result": (
                {
                    "hits": len(fetch.hits),
                    "min_score_applied": fetch.min_score_applied,
                }
                if fetch is not None
                else None
            ),
            "fusion_mode": fusion_mode,
            "http_result_kind": http_result_kind,
            "fallback_count": len(fallbacks),
            "fallback_reasons": [
                r["fallback_reason"] for r in stage_results if r.get("fallback_reason")
            ],
            "refiner_fallback_count": refiner_fallback_count,
            "refiner_returned_empty": refiner_returned_empty,
            "refiner_exception_count": refiner_exception_count,
            "refiner_exception": refiner_exception_count > 0,
            "hit_counts": {
                "merged": len(fetch.hits) if fetch is not None else 0,
            },
            "search_diagnostics": sd,
        }

    @classmethod
    def from_run_result(
        cls,
        *,
        embed_ok: int,
        embed_failed: int,
        fts_errors: int,
        stage_results: list[StageResult] | None = None,
        timings: dict[str, float] | None = None,
        fetch_result: TwoStageFetchResult | None = None,
        use_rrf: bool = True,
        rrf_k: int = 60,
        http_result_kind: HttpResultKind | None = None,
    ) -> PipelineDiagnostics:
        """Build PipelineDiagnostics from a run result."""
        search_diag = SearchDiagnostics.from_run_result(
            embed_ok=embed_ok, embed_failed=embed_failed, fts_errors=fts_errors
        )
        return cls(
            search_diagnostics=search_diag,
            stage_results=stage_results,
            timings=timings,
            fetch_result=fetch_result,
            use_rrf=use_rrf,
            rrf_k=rrf_k,
            http_result_kind=http_result_kind,
        )
