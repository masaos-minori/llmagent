"""
tests/test_tool_approval_concurrency.py

Optional concurrency test for the approval flow to verify no race conditions
occur under rapid successive prompts.
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from agent.tool_enums import RiskLevel


class _QueueInput:
    """Thread-safe queue-backed input mock for simulating concurrent prompts."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()

    async def enqueue(self, value: str) -> None:
        await self._queue.put(value)

    async def get(self) -> str:
        return await self._queue.get()

    def make_input_mock(self) -> MagicMock:
        mock = MagicMock()
        mock.return_value = asyncio.create_task(self._get_impl())
        return mock

    async def _get_impl(self) -> str:
        val = await self._queue.get()
        return val.strip().lower()


@pytest.mark.asyncio
async def test_rapid_successive_approvals_no_race() -> None:
    """Verify each approval decision is processed independently regardless of timing."""
    from agent.tool_approval import _prompt_user_approval

    q = _QueueInput()
    responses = ["yes", "no", "yes"]
    for r in responses:
        await q.enqueue(r)

    call_count = 0

    async def _mock_to_thread(func, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        return await func(*args, **kwargs)

    with patch("asyncio.to_thread", side_effect=_mock_to_thread):
        results = []
        for i in range(len(responses)):
            if i < len(responses) - 1:
                result = await _prompt_user_approval(RiskLevel.LOW)
            else:
                result = await _prompt_user_approval(RiskLevel.HIGH)
            results.append(result)

    assert results == [True, False, True]
    assert call_count == len(responses)


@pytest.mark.asyncio
async def test_rapid_mixed_approvals_no_race() -> None:
    """Verify mixed yes/no decisions are correct regardless of timing."""
    from agent.tool_approval import _prompt_user_approval

    q = _QueueInput()
    # Mix of LOW/MEDIUM (expect y/n) and HIGH (expect yes/no)
    responses = [
        ("y", RiskLevel.LOW),
        ("n", RiskLevel.MEDIUM),
        ("yes", RiskLevel.HIGH),
        ("no", RiskLevel.HIGH),
    ]

    for resp, _ in responses:
        await q.enqueue(resp)

    call_count = 0

    async def _mock_to_thread(func, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        return await func(*args, **kwargs)

    with patch("asyncio.to_thread", side_effect=_mock_to_thread):
        results = []
        for resp, risk in responses:
            result = await _prompt_user_approval(risk)
            results.append(result)

    expected = [True, False, True, False]
    assert results == expected
    assert call_count == len(responses)


@pytest.mark.asyncio
async def test_high_risk_requires_full_yes_not_abbreviated() -> None:
    """HIGH risk level must require full word 'yes', not 'y' or 'Y'."""
    from agent.tool_approval import _prompt_user_approval

    q = _QueueInput()
    await q.enqueue("y")

    async def _mock_to_thread(func, *args, **kwargs):
        return await func(*args, **kwargs)

    with patch("asyncio.to_thread", side_effect=_mock_to_thread):
        result = await _prompt_user_approval(RiskLevel.HIGH)

    assert result is False

    await q.enqueue("YES")

    with patch("asyncio.to_thread", side_effect=_mock_to_thread):
        result = await _prompt_user_approval(RiskLevel.HIGH)

    assert result is True
