"""scripts/rag/diagnostics.py

Extracted from scripts/rag/pipeline.py — get_diagnostics().

Provides PipelineDiagnostics dataclass holding its structured diagnostics
keys, reducing pipeline.py complexity and providing typed diagnostics access.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from rag.models_data import TwoStageFetchResult
from rag.models_result import SearchDiagnostics
from rag.stage import StageResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineDiagnostics:
    """Pipeline-level diagnostics wrapping SearchDiagnostics.

    Holds the structured diagnostics keys for a single pipeline run.
    """

    search_diagnostics: SearchDiagnostics
    stage_results: list[StageResult] | None = None
    timings: dict[str, float] | None = None
    fetch_result: TwoStageFetchResult | None = None
    use_rrf: bool = True

    def to_dict(self) -> dict[str, object]:
        sd = self.search_diagnostics.to_dict()
        stage_results = (
            [dict(r) for r in self.stage_results] if self.stage_results else []
        )
        fallbacks = [r for r in stage_results if r.get("status") == "fallback"]
        fetch = self.fetch_result
        fusion_mode = "rrf" if self.use_rrf else "dedup_only"
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
            "fallback_count": len(fallbacks),
            "fallback_reasons": [
                r["fallback_reason"] for r in stage_results if r.get("fallback_reason")
            ],
            "refiner_fallback_count": refiner_fallback_count,
            "refiner_returned_empty": refiner_returned_empty,
            "refiner_exception_count": refiner_exception_count,
            "refiner_exception": refiner_exception_count > 0,
            "search_diagnostics": sd,
        }
