"""shared/action_result.py

Universal action/result contract for all machine-interpreted outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ActionType = Literal[
    "continue",
    "call_tool",
    "retrieve_more_context",
    "ask_user",
    "fail",
    "retry",
]


@dataclass(frozen=True)
class ActionResult:
    """Schema-driven result for any machine decision path."""

    action: ActionType
    reason: str = ""
    required_context: list[str] = field(default_factory=list)
    payload: dict[str, object] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    confidence: float = 1.0
