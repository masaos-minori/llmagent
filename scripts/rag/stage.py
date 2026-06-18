"""rag/stage.py
PipelineStage Protocol and shared PipelineContext dataclass.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Protocol, TypedDict

from rag.types import MergedHit, RankedHit, RawHit

RagHit = RawHit | MergedHit | RankedHit


class StageResult(TypedDict):
    """Per-stage outcome recorded by RagPipeline.run()."""

    stage_name: str
    status: str  # "success" | "fallback" | "failure"
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


class PipelineStage(Protocol):
    """Synchronous or async pipeline stage — run modifies ctx in-place."""

    async def run(self, ctx: PipelineContext, **kwargs: Any) -> None: ...
