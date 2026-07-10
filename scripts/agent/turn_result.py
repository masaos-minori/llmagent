"""agent/turn_result.py
TurnResult frozen dataclass for LLM turn lifecycle.

Defined separately from orchestrator.py so that llm_turn_runner.py
can import TurnResult without creating a circular dependency.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from shared.llm_client import LLMTransportError


@dataclasses.dataclass(frozen=True)
class TurnResult:
    """Typed result of one LLM turn."""

    action: Literal["continue", "fail"]
    answer: str = ""
    error_kind: str | None = None
    reason: str = ""
    exception: LLMTransportError | None = dataclasses.field(default=None, compare=False)
    # When False, the answer should NOT be persisted as a normal assistant message.
    # Used for LLM transport errors to avoid polluting conversation history.
    persist_as_assistant: bool = True
