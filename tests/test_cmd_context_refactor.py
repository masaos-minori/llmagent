"""tests/test_cmd_context_refactor.py
Unit tests for _ContextMixin._print_token_line extracted helper.

_print_token_line now accepts a pre-built state dict produced by
_collect_context_state(); these tests build that dict directly.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from agent.commands.cmd_context import _ContextMixin, _token_source_label


class _CtxMixin(_ContextMixin):
    def __init__(self, ctx: Any) -> None:
        self._ctx = ctx  # type: ignore[assignment]


def _make_state(
    *,
    token_is_exact: bool = False,
    token_estimate: int = 1000,
    token_limit: int = 0,
    tokenize_configured: bool = False,
) -> dict:
    """Build a minimal state dict for _print_token_line."""
    return {
        "token_is_exact": token_is_exact,
        "token_estimate": token_estimate,
        "token_limit": token_limit,
        "tokenize_configured": tokenize_configured,
    }


def _make_ctx_mock() -> Any:
    """Build a minimal AgentContext mock (unused after refactor but kept for _CtxMixin)."""
    ctx = MagicMock()
    ctx.conv.history = []
    return ctx


class TestTokenSourceLabel:
    def test_exact_returns_llm_usage(self) -> None:
        assert _token_source_label(True, False) == "LLM usage"

    def test_tokenize_configured_returns_label(self) -> None:
        assert _token_source_label(False, True) == "/tokenize (next turn)"

    def test_fallback_returns_chars4(self) -> None:
        assert _token_source_label(False, False) == "chars/4"


class TestPrintTokenLine:
    def test_no_limit_prints_estimate(self, capsys: Any) -> None:
        mixin = _CtxMixin(_make_ctx_mock())
        state = _make_state(token_limit=0, token_estimate=1000)
        mixin._print_token_line(state)
        out = capsys.readouterr().out
        assert "Token estimate" in out
        # limit=disabled → no percentage shown
        assert "disabled" in out

    def test_with_limit_prints_percentage(self, capsys: Any) -> None:
        mixin = _CtxMixin(_make_ctx_mock())
        # token_estimate=1000; limit=8000 → 12%
        state = _make_state(token_limit=8000, token_estimate=1000)
        mixin._print_token_line(state)
        out = capsys.readouterr().out
        assert "limit=" in out
        assert "%" in out
        assert "[active]" in out

    def test_exact_token_shows_token_count_label(self, capsys: Any) -> None:
        mixin = _CtxMixin(_make_ctx_mock())
        state = _make_state(token_is_exact=True, token_estimate=500, token_limit=0)
        mixin._print_token_line(state)
        out = capsys.readouterr().out
        assert "Token count  " in out
        assert "LLM usage" in out

    def test_no_hist_mgr_uses_chars_fallback(self, capsys: Any) -> None:
        mixin = _CtxMixin(_make_ctx_mock())
        # chars=400 // 4 = 100 (calculated by caller; pass pre-computed estimate)
        state = _make_state(token_limit=0, token_estimate=100)
        mixin._print_token_line(state)
        out = capsys.readouterr().out
        assert "100" in out

    def test_tokenize_url_configured_uses_tokenize_label(self, capsys: Any) -> None:
        mixin = _CtxMixin(_make_ctx_mock())
        state = _make_state(tokenize_configured=True, token_estimate=250, token_limit=0)
        mixin._print_token_line(state)
        out = capsys.readouterr().out
        assert "/tokenize" in out
