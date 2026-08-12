"""tests/agent/test_tool_models.py

Characterization tests for agent/tool_models.py DTOs.

GuardDecision.blocks was previously untested (GuardDecision itself has no
production callers) — added to lock behavior before simplifying its body.
"""

from __future__ import annotations

from agent.tool_enums import GuardDecisionType
from agent.tool_models import GuardDecision


class TestGuardDecisionBlocks:
    def test_pass_does_not_block(self) -> None:
        decision = GuardDecision(type=GuardDecisionType.PASS)
        assert decision.blocks is False

    def test_non_pass_blocks(self) -> None:
        decision = GuardDecision(type=GuardDecisionType.CYCLE)
        assert decision.blocks is True
