"""agent/tool_models.py

Immutable DTO models for the tool execution subsystem.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.tool_enums import ApprovalDecisionType, GuardDecisionType, RiskLevel


@dataclass(frozen=True)
class ToolCallRequest:
    """Parsed, validated representation of a single LLM tool call."""

    id: str
    name: str
    args: dict[str, Any]


@dataclass(frozen=True)
class ToolMeta:
    """Scheduling metadata for a single tool."""

    resource_scope: str
    requires_serial: bool
    is_write: bool


@dataclass(frozen=True)
class ToolExecutionResult:
    """Result of executing one tool call."""

    tc_id: str
    name: str
    args: dict[str, Any]
    full_text: str
    is_error: bool
    llm_text: str


@dataclass(frozen=True)
class ApprovalOutcome:
    """Structured result of a single tool approval evaluation."""

    tool_name: str
    risk_level: RiskLevel
    decision: ApprovalDecisionType
    escalation_reason: str = ""
    preview: str = ""

    @property
    def approved(self) -> bool:
        """True when the approval decision allows auto-execution."""
        return self.decision in (
            ApprovalDecisionType.AUTO,
            ApprovalDecisionType.APPROVED,
        )


@dataclass(frozen=True)
class GuardDecision:
    """Result of a tool-loop guard check."""

    type: GuardDecisionType
    message: str | None = None

    @property
    def blocks(self) -> bool:
        """True when this decision prevents further tool execution."""
        result: bool = self.type != GuardDecisionType.PASS
        return result
