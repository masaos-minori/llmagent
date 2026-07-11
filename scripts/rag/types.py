#!/usr/bin/env python3
"""rag/types.py
RAG-pipeline-specific type definitions.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rag.stage import StageResult

from rag.models_result import SearchDiagnostics
from shared.types import RagHit, RawHit

__all__ = [
    "PipelineRunResult",
    "RagQuery",
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
