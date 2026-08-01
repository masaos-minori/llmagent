import asyncio
from dataclasses import dataclass, field
from typing import Any

import pytest


@dataclass
class TurnState:
    """
    Mock implementation of TurnState to test concurrency.
    In production, this uses asyncio.Lock for thread-safe updates.
    """

    current_turn_id: str | None = None
    background_tasks: set[asyncio.Task[Any]] = field(default_factory=set)
    last_error_kind: str | None = None
    pending_approval_id: str | None = None
    pending_approval_task_id: str | None = None

    # For testing purposes
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _tool_calls: list[dict[str, Any]] = field(default_factory=list)
    _turn_count: int = 0

    async def add_tool_call(self, tool_call: dict[str, Any]) -> None:
        async with self._lock:
            await asyncio.sleep(0.01)  # Simulate IO/processing delay
            self._tool_calls.append(tool_call)
            self._turn_count += 1

    def get_tool_calls(self) -> list[dict[str, Any]]:
        return self._tool_calls

    @property
    def turn_count(self) -> int:
        return self._turn_count


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
    assert len(turn_state.get_tool_calls()) == n
    assert turn_state.turn_count == n


if __name__ == "__main__":
    pytest.main([__file__])
