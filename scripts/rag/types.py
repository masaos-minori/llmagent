#!/usr/bin/env python3
"""rag/types.py
Shared type definitions for the RAG pipeline.

RawHit / MergedHit / RankedHit model the three search pipeline stages.
The hit dataclasses and RagHit alias are defined in shared/types.py and
re-exported here for backward compatibility.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rag.stage import StageResult

from shared.types import MergedHit, RagHit, RankedHit, RawHit

from rag.models_result import SearchDiagnostics

__all__ = [
    "MergedHit",
    "PipelineRunResult",
    "RagHit",
    "RagQuery",
    "RankedHit",
    "RawHit",
    "SearchDiagnostics",
]


@dataclasses.dataclass
class RagQuery:
    """Represents a single query string with optional context."""

    query: str
    context: str = ""


@dataclasses.dataclass
class PipelineRunResult:
    """Typed result from RagPipeline.run()."""

    queries: list[str]
    search_results: list[list[RawHit]]
    merged: list[RagHit]
    reranked: list[RagHit]
    stage_results: list[StageResult]
    diagnostics: SearchDiagnostics
    result_source: str | None = None
