"""tests/test_llm_partial_completion.py
Verify partial-completion handling on the live runner path (LLMTurnRunner._handle_llm_error):
partial output never enters ctx.conv.history, reaches the diagnostic channels, and
increments the single counter ctx.stats.stat_partial_completions.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from agent.context import RuntimeStats
from agent.llm_turn_runner import LLMTurnRunner


def _make_transport_error(
    partial_text: str = "partial output", kind: str = "PREMATURE_EOF"
):
    from shared.llm_exceptions import LLMTransportError

    return LLMTransportError(
        kind=kind,  # type: ignore[arg-type]
        phase="in_stream",
        url="http://localhost/llm",
        partial_text=partial_text,
    )


def _make_diagnostic_store():
    ds = MagicMock()
    ds.save = MagicMock()
    ds.save_partial_completion = MagicMock()
    return ds


def _make_ctx(history: list | None = None):
    """Runner-shaped context: a real RuntimeStats and no services_required.

    The handler must not need the LLM client attribute (REQ-001): a context without
    `services_required` pins that.
    """
    if history is None:
        history = []
    return SimpleNamespace(
        session=SimpleNamespace(session_id="test-sess-1"),
        stats=RuntimeStats(),
        conv=SimpleNamespace(history=history),
        diagnostics=_make_diagnostic_store(),
    )


# ── history invariant ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_partial_completion_does_not_append_to_history() -> None:
    ctx = _make_ctx(history=[{"role": "user", "content": "hello"}])
    initial_len = len(ctx.conv.history)
    e = _make_transport_error(partial_text="partial output")
    result = await LLMTurnRunner(ctx, MagicMock())._handle_llm_error(e, turn=1)
    assert len(ctx.conv.history) == initial_len
    assert result.action == "fail"


# ── diagnostic store ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_partial_completion_saved_to_diagnostic_channel() -> None:
    ctx = _make_ctx()
    e = _make_transport_error(partial_text="partial output")
    await LLMTurnRunner(ctx, MagicMock())._handle_llm_error(e, turn=1)
    ctx.diagnostics.save.assert_called_once()
    call_args = ctx.diagnostics.save.call_args[0]
    assert call_args[1] == "llm_transport_error"
    assert call_args[2].endswith("\n[INCOMPLETE: PREMATURE_EOF]")
    ctx.diagnostics.save_partial_completion.assert_called_once()


# ── stat counter ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_partial_completion_increments_stat() -> None:
    ctx = _make_ctx()
    e = _make_transport_error(partial_text="partial output")
    await LLMTurnRunner(ctx, MagicMock())._handle_llm_error(e, turn=1)
    assert ctx.stats.stat_partial_completions == 1


# ── non-partial error ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_non_partial_error_leaves_stat_at_zero() -> None:
    ctx = _make_ctx()
    e = _make_transport_error(partial_text="", kind="CONNECT_ERROR")
    result = await LLMTurnRunner(ctx, MagicMock())._handle_llm_error(e, turn=1)
    assert ctx.stats.stat_partial_completions == 0
    assert result.action == "fail"
