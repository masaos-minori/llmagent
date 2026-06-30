"""rag/stage.py
PipelineStage Protocol and shared PipelineContext dataclass.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Literal, Protocol, TypedDict

from rag.models_result import SearchDiagnostics
from rag.types import (
    RagHit,  # noqa: F401 — imported for use in this module
    MergedHit,
    RankedHit,
    RawHit,
)

__all__ = [
    "PipelineContext",
    "PipelineStage",
    "RagHit",
    "StageResult",
]


class StageResult(TypedDict):
    """Per-stage outcome recorded by RagPipeline.run()."""

    stage_name: str
    status: Literal["success", "fallback", "failure"]
    elapsed_seconds: float
    fallback_reason: str | None


@dataclasses.dataclass
class PipelineContext:
    """Mutable state passed between pipeline stages."""

    query: str
    history_context: str = ""
    queries: list[str] = dataclasses.field(default_factory=list)
    search_results: list[list[RawHit]] = dataclasses.field(default_factory=list)
    merged: list[RagHit] = dataclasses.field(default_factory=list)
    reranked: list[RagHit] = dataclasses.field(default_factory=list)
    augment_result: str = ""
    stage_results: list[StageResult] = dataclasses.field(default_factory=list)
    search_diagnostics: SearchDiagnostics = dataclasses.field(
        default_factory=SearchDiagnostics
    )


class PipelineStage(Protocol):
    """Synchronous or async pipeline stage — run modifies ctx in-place."""

    async def run(self, ctx: PipelineContext, **kwargs: Any) -> None: ...
