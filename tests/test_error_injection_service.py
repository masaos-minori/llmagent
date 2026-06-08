"""
tests/test_error_injection_service.py
Unit tests for ErrorInjectionService.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from agent.error_injection_service import ErrorInjectionService


def _make_context() -> MagicMock:
    ctx = MagicMock()
    ctx.conv.history = []
    ctx.tool_result_store = MagicMock()
    ctx.session.session_id = 1
    return ctx


class TestInjectMidTurnError:
    def test_appends_tool_message_to_history(self) -> None:
        ctx = _make_context()
        svc = ErrorInjectionService(ctx)
        e = MagicMock()
        e.phase = "stream"
        e.kind = "ConnectionError"
        e.url = "http://localhost"
        e.status_code = None
        e.retryable = True
        e.partial_text = None

        svc.inject_mid_turn_error(e, turn=0)

        assert len(ctx.conv.history) == 1
        entry = ctx.conv.history[0]
        assert entry["role"] == "tool"
        assert entry["name"] == "llm_transport_error"
        assert "ConnectionError" in entry["content"]

    def test_stores_in_tool_result_store(self) -> None:
        ctx = _make_context()
        svc = ErrorInjectionService(ctx)
        e = MagicMock()
        e.phase = "stream"
        e.kind = "ConnectionError"
        e.url = "http://localhost"
        e.status_code = None
        e.retryable = True
        e.partial_text = None

        svc.inject_mid_turn_error(e, turn=3)

        ctx.tool_result_store.store.assert_called_once()
        call_kwargs = ctx.tool_result_store.store.call_args[1]
        assert call_kwargs["turn"] == 3
        assert call_kwargs["tool_name"] == "llm_transport_error"
        assert call_kwargs["is_error"] is True

    def test_returns_summary_string(self) -> None:
        ctx = _make_context()
        svc = ErrorInjectionService(ctx)
        e = MagicMock()
        e.phase = "pre_stream"
        e.kind = "ConnectionError"
        e.url = "http://localhost"
        e.status_code = 503
        e.retryable = False
        e.partial_text = None

        summary = svc.inject_mid_turn_error(e, turn=0)

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_generates_unique_tool_call_ids(self) -> None:
        ctx1 = _make_context()
        ctx2 = _make_context()
        svc1 = ErrorInjectionService(ctx1)
        svc2 = ErrorInjectionService(ctx2)
        e = MagicMock()
        e.phase = "stream"
        e.kind = "Timeout"
        e.url = "http://localhost"
        e.status_code = None
        e.retryable = True
        e.partial_text = None

        svc1.inject_mid_turn_error(e, turn=0)
        svc2.inject_mid_turn_error(e, turn=0)

        id1 = ctx1.conv.history[0]["tool_call_id"]
        id2 = ctx2.conv.history[0]["tool_call_id"]
        assert id1 != id2

    def test_sets_partial_true_in_content(self) -> None:
        ctx = _make_context()
        svc = ErrorInjectionService(ctx)
        e = MagicMock()
        e.phase = "stream"
        e.kind = "ConnectionError"
        e.url = "http://localhost"
        e.status_code = None
        e.retryable = True
        e.partial_text = "some partial response"

        svc.inject_mid_turn_error(e, turn=0)

        entry = ctx.conv.history[0]
        assert '"partial":true' in entry["content"]
