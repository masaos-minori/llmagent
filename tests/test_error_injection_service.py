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


def _make_error(**kwargs) -> MagicMock:
    e = MagicMock()
    e.phase = kwargs.get("phase", "stream")
    e.kind = kwargs.get("kind", "ConnectionError")
    e.url = kwargs.get("url", "http://localhost")
    e.status_code = kwargs.get("status_code", None)
    e.retryable = kwargs.get("retryable", True)
    e.partial_text = kwargs.get("partial_text", None)
    return e


class TestInjectMidTurnError:
    def test_stores_in_diagnostic_store_only(self) -> None:
        """Mid-turn errors must go to diagnostic store, not conversation history."""
        ctx = _make_context()
        svc = ErrorInjectionService(ctx)
        e = _make_error()

        svc.inject_mid_turn_error(e, turn=0)

        assert len(ctx.conv.history) == 0
        ctx.diagnostics.save.assert_called_once()
        call_args = ctx.diagnostics.save.call_args
        assert call_args[0][1] == "mid_turn_error"

    def test_stores_in_tool_result_store(self) -> None:
        ctx = _make_context()
        svc = ErrorInjectionService(ctx)
        e = _make_error()

        svc.inject_mid_turn_error(e, turn=3)

        ctx.tool_result_store.store.assert_called_once()
        call_kwargs = ctx.tool_result_store.store.call_args[1]
        assert call_kwargs["turn"] == 3
        assert call_kwargs["tool_name"] == "llm_transport_error"
        assert call_kwargs["is_error"] is True
        ctx.diagnostics.save.assert_called_once()

    def test_returns_summary_string(self) -> None:
        ctx = _make_context()
        svc = ErrorInjectionService(ctx)
        e = _make_error(phase="pre_stream", status_code=503, retryable=False)

        summary = svc.inject_mid_turn_error(e, turn=0)

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_multiple_errors_each_store_in_diagnostics(self) -> None:
        """Each inject_mid_turn_error call stores exactly one diagnostic entry."""
        ctx1 = _make_context()
        ctx2 = _make_context()
        svc1 = ErrorInjectionService(ctx1)
        svc2 = ErrorInjectionService(ctx2)
        e = _make_error(kind="Timeout")

        svc1.inject_mid_turn_error(e, turn=0)
        svc2.inject_mid_turn_error(e, turn=0)

        assert ctx1.diagnostics.save.call_count == 1
        assert ctx2.diagnostics.save.call_count == 1

    def test_partial_text_reflected_in_diagnostic_content(self) -> None:
        """Partial-completion errors store detail containing partial flag in diagnostics."""
        ctx = _make_context()
        svc = ErrorInjectionService(ctx)
        e = _make_error(partial_text="some partial response")

        svc.inject_mid_turn_error(e, turn=0)

        assert len(ctx.conv.history) == 0
        ctx.diagnostics.save.assert_called_once()
        content_arg = ctx.diagnostics.save.call_args[0][2]
        assert "partial" in content_arg
