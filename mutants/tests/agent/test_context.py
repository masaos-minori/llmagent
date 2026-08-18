import asyncio

import pytest
from agent.context import AgentContext

from scripts.agent.context import TurnState


class TestServicesRequired:
    """Characterization tests for AgentContext.services_required — previously untested."""

    def test_raises_when_services_not_initialized(self) -> None:
        ctx = AgentContext.__new__(AgentContext)
        ctx.services = None
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = ctx.services_required

    def test_returns_services_when_set(self) -> None:
        ctx = AgentContext.__new__(AgentContext)
        sentinel = object()
        ctx.services = sentinel
        assert ctx.services_required is sentinel


@pytest.mark.asyncio
async def test_turn_state_concurrency():
    """
    Verifies that TurnState correctly handles concurrent add_tool_call operations
    using asyncio.gather, ensuring no updates are lost.
    """
    turn_state = TurnState()
    n = 50
    tool_calls = [{"name": f"tool_{i}", "args": {}} for i in range(n)]

    # Launch N concurrent tasks
    await asyncio.gather(*(turn_state.add_tool_call(tc) for tc in tool_calls))

    # Assertions
    assert len(await turn_state.get_tool_calls()) == n
    assert turn_state.turn_count == n
