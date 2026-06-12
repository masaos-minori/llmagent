"""rag/stage.py
PipelineStage Protocol and shared PipelineContext dataclass.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Protocol

from rag.types import MergedHit, RankedHit, RawHit

RagHit = RawHit | MergedHit | RankedHit


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


class PipelineStage(Protocol):
    """Synchronous or async pipeline stage — run modifies ctx in-place."""

    async def run(self, ctx: PipelineContext, **kwargs: Any) -> None: ...
