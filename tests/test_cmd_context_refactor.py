"""tests/test_cmd_context_refactor.py
Unit tests for _ContextMixin._print_token_line extracted helper.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from agent.commands.cmd_context import _ContextMixin, _token_source_label


class _CtxMixin(_ContextMixin):
    def __init__(self, ctx: Any) -> None:
        self._ctx = ctx  # type: ignore[assignment]


def _make_ctx(
    *,
    stat_input_tokens: int | None = None,
    context_token_limit: int = 0,
    tokenize_url: str = "",
) -> Any:
    ctx = MagicMock()
    ctx.stat_input_tokens = stat_input_tokens
    ctx.cfg.context_token_limit = context_token_limit
    ctx.cfg.tokenize_url = tokenize_url
    hist_mgr = MagicMock()
    hist_mgr.count_tokens = MagicMock(return_value=1000)
    ctx.services.hist_mgr = hist_mgr
    ctx.history = []
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
        ctx = _make_ctx(context_token_limit=0)
        mixin = _CtxMixin(ctx)
        mixin._print_token_line(ctx, total_chars=4000)
        out = capsys.readouterr().out
        assert "Token estimate" in out
        # limit=disabled → no percentage shown
        assert "disabled" in out

    def test_with_limit_prints_percentage(self, capsys: Any) -> None:
        ctx = _make_ctx(context_token_limit=8000)
        mixin = _CtxMixin(ctx)
        # hist_mgr.count_tokens returns 1000; limit=8000 → 12%
        mixin._print_token_line(ctx, total_chars=4000)
        out = capsys.readouterr().out
        assert "limit=" in out
        assert "%" in out
        assert "[active]" in out

    def test_exact_token_shows_token_count_label(self, capsys: Any) -> None:
        ctx = _make_ctx(stat_input_tokens=500)
        mixin = _CtxMixin(ctx)
        mixin._print_token_line(ctx, total_chars=2000)
        out = capsys.readouterr().out
        assert "Token count  " in out
        assert "LLM usage" in out

    def test_no_hist_mgr_uses_chars_fallback(self, capsys: Any) -> None:
        ctx = _make_ctx(context_token_limit=0)
        ctx.services.hist_mgr = None
        mixin = _CtxMixin(ctx)
        mixin._print_token_line(ctx, total_chars=400)
        out = capsys.readouterr().out
        # chars // 4 = 100
        assert "100" in out

    def test_tokenize_url_configured_uses_tokenize_label(self, capsys: Any) -> None:
        ctx = _make_ctx(tokenize_url="http://localhost:8080/tokenize")
        mixin = _CtxMixin(ctx)
        mixin._print_token_line(ctx, total_chars=1000)
        out = capsys.readouterr().out
        assert "/tokenize" in out
