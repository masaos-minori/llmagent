"""rag/stage.py
PipelineStage Protocol and shared PipelineContext dataclass.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Protocol

from rag.types import RagHit


@dataclasses.dataclass
class PipelineContext:
    """Mutable state passed between pipeline stages."""

    query: str
    history_context: str = ""
    queries: list[str] = dataclasses.field(default_factory=list)
    search_results: list[Any] = dataclasses.field(
        default_factory=list
    )  # list[list[RawHit]] in practice
    merged: list[RagHit] = dataclasses.field(default_factory=list)
    reranked: list[RagHit] = dataclasses.field(default_factory=list)
    augment_result: str = ""
    observers: list[Any] = dataclasses.field(default_factory=list)

    def add_observer(self, observer: Any) -> None:
        """Add an observer to be notified when stages complete."""
        self.observers.append(observer)


class PipelineStage(Protocol):
    """Synchronous or async pipeline stage — run modifies ctx in-place."""

    async def run(self, ctx: PipelineContext, **kwargs: Any) -> None: ...
