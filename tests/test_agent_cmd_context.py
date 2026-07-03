"""
tests/test_agent_cmd_context.py
Behavior-lock tests for _ContextMixin: _cmd_undo, _cmd_clear, _cmd_system.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from agent.commands.cmd_context import _ContextMixin, _token_source_label
from agent.services.context_view import _format_memory_status
from agent.services.context_view import budget_breakdown as _budget_breakdown

# ── Test harness ──────────────────────────────────────────────────────────────


class _FakeCmd(_ContextMixin):
    def __init__(self, ctx: Any) -> None:
        self._ctx = ctx


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.stats.stat_turns = 3
    ctx.stats.stat_tool_calls = 5
    ctx.stats.stat_tool_errors = 1
    ctx.stats.stat_latency = {}
    ctx.stats.stat_semantic_cache_hits = 0
    ctx.stats.stat_input_tokens = None
    ctx.conv.debug_mode = False
    ctx.conv.plan_mode = False
    ctx.conv.system_prompt_name = "default"
    ctx.conv.system_prompt_content = "You are helpful."
    ctx.conv.history = []
    ctx.session.session_id = 1
    ctx.services.hist_mgr = None
    ctx.services.memory = None
    ctx.services.llm = None
    ctx.cfg.llm.context_char_limit = 8000
    ctx.cfg.llm.context_token_limit = 0
    ctx.cfg.llm.tokenize_url = ""
    ctx.cfg.tool.system_prompts = {"default": "You are helpful.", "coding": "You code."}
    return ctx


def _user_msg(content: str = "hello") -> dict:
    return {"role": "user", "content": content}


def _assistant_msg(content: str = "world") -> dict:
    return {"role": "assistant", "content": content}


def _system_msg(content: str = "sys") -> dict:
    return {"role": "system", "content": content}


def _injected_msg() -> dict:
    return {"role": "user", "content": "[memory]", "_memory_injected": True}


# ── _cmd_undo ─────────────────────────────────────────────────────────────────


class TestCmdUndo:
    def test_undo_removes_last_user_and_assistant(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [
            _system_msg(),
            _user_msg("first"),
            _assistant_msg("first reply"),
            _user_msg("second"),
            _assistant_msg("second reply"),
        ]
        ctx.stats.stat_turns = 2
        cmd = _FakeCmd(ctx)
        cmd._cmd_undo()
        assert ctx.conv.history == [
            _system_msg(),
            _user_msg("first"),
            _assistant_msg("first reply"),
        ]
        assert ctx.stats.stat_turns == 1

    def test_undo_removes_memory_injection_before_user(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [
            _system_msg(),
            _user_msg("first"),
            _assistant_msg("first reply"),
            _injected_msg(),
            _user_msg("second"),
            _assistant_msg("second reply"),
        ]
        ctx.stats.stat_turns = 2
        cmd = _FakeCmd(ctx)
        cmd._cmd_undo()
        # injection marker + second user + second assistant must be removed
        assert ctx.conv.history == [
            _system_msg(),
            _user_msg("first"),
            _assistant_msg("first reply"),
        ]
        assert ctx.stats.stat_turns == 1

    def test_undo_calls_undo_last_turn(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [_system_msg(), _user_msg(), _assistant_msg()]
        ctx.stats.stat_turns = 1
        cmd = _FakeCmd(ctx)
        cmd._cmd_undo()
        ctx.session.undo_last_turn.assert_called_once()

    def test_undo_with_no_user_message_prints_nothing(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [_system_msg()]
        cmd = _FakeCmd(ctx)
        cmd._cmd_undo()
        out = capsys.readouterr().out
        assert "Nothing to undo" in out

    def test_undo_stat_turns_floor_at_zero(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [_system_msg(), _user_msg(), _assistant_msg()]
        ctx.stats.stat_turns = 0
        cmd = _FakeCmd(ctx)
        cmd._cmd_undo()
        assert ctx.stats.stat_turns == 0

    def test_undo_with_tool_messages_removes_from_user_onwards(self) -> None:
        """Tool messages after user message are included in the undo cut."""
        ctx = _make_ctx()
        ctx.conv.history = [
            _system_msg(),
            _user_msg("first"),
            _assistant_msg("first reply"),
            _user_msg("second"),
            {"role": "assistant", "content": "", "tool_calls": [{"id": "t1"}]},
            {"role": "tool", "content": "result", "tool_call_id": "t1"},
            _assistant_msg("final"),
        ]
        ctx.stats.stat_turns = 2
        cmd = _FakeCmd(ctx)
        cmd._cmd_undo()
        # Everything from the last user message onwards must be removed
        assert ctx.conv.history == [
            _system_msg(),
            _user_msg("first"),
            _assistant_msg("first reply"),
        ]


# ── _cmd_clear ────────────────────────────────────────────────────────────────


class TestCmdClear:
    def test_clear_keeps_system_message(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [_system_msg(), _user_msg(), _assistant_msg()]
        cmd = _FakeCmd(ctx)
        cmd._cmd_clear()
        assert ctx.conv.history == [_system_msg()]

    def test_clear_resets_stats(self) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [_system_msg()]
        ctx.stats.stat_turns = 5
        ctx.stats.stat_tool_calls = 10
        cmd = _FakeCmd(ctx)
        cmd._cmd_clear()
        assert ctx.stats.stat_turns == 0
        assert ctx.stats.stat_tool_calls == 0

    def test_clear_new_starts_new_session(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [_system_msg()]
        cmd = _FakeCmd(ctx)
        cmd._cmd_clear("new")
        ctx.session.start.assert_called_once()
        out = capsys.readouterr().out
        assert "New session" in out


# ── _cmd_system ───────────────────────────────────────────────────────────────


class TestCmdSystem:
    def test_system_switches_prompt(self) -> None:
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        cmd._cmd_system("coding")
        assert ctx.conv.system_prompt_name == "coding"
        assert ctx.conv.system_prompt_content == "You code."

    def test_system_unknown_name_prints_error(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        cmd._cmd_system("nonexistent")
        out = capsys.readouterr().out
        assert "Unknown" in out

    def test_system_no_name_lists_presets(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        cmd._cmd_system("")
        out = capsys.readouterr().out
        assert "Current" in out
        assert "Available" in out


# ── _budget_breakdown ─────────────────────────────────────────────────────────


class TestBudgetBreakdown:
    def test_budget_breakdown_counts_system(self) -> None:
        messages = [{"role": "system", "content": "hello"}]
        result = _budget_breakdown(messages)
        assert result.system == 5

    def test_budget_breakdown_counts_tool(self) -> None:
        messages = [{"role": "tool", "content": "result"}]
        result = _budget_breakdown(messages)
        assert result.tool_results == 6

    def test_budget_breakdown_counts_assistant(self) -> None:
        messages = [{"role": "assistant", "content": "answer"}]
        result = _budget_breakdown(messages)
        assert result.history == 6

    def test_budget_breakdown_counts_tool_calls(self) -> None:
        messages = [{"role": "assistant", "content": "", "tool_calls": [{"id": "t1"}]}]
        result = _budget_breakdown(messages)
        assert result.tool_results > 0

    def test_budget_breakdown_counts_user_as_history(self) -> None:
        messages = [{"role": "user", "content": "question"}]
        result = _budget_breakdown(messages)
        assert result.history == 8


# ── _format_memory_status ─────────────────────────────────────────────────────


class TestFormatMemoryStatus:
    def test_format_memory_status_disabled(self) -> None:
        ctx = _make_ctx()
        ctx.services.memory = None
        result = _format_memory_status(ctx)
        assert result == "disabled"

    def test_format_memory_status_enabled(self) -> None:
        ctx = _make_ctx()
        mem = MagicMock()
        mem.store.count_vec.return_value = 5
        ctx.services.memory = mem
        with patch("agent.services.context_view.count_by_type", return_value={"semantic": 3, "episodic": 7}):
            with patch("agent.services.context_view.count_entries", return_value=10):
                result = _format_memory_status(ctx)
                assert "enabled" in result
                assert "entries=10" in result


# ── _token_source_label ───────────────────────────────────────────────────────


class TestTokenSourceLabel:
    def test_token_source_label_exact(self) -> None:
        result = _token_source_label(True, False)
        assert result == "LLM usage"

    def test_token_source_label_tokenize(self) -> None:
        result = _token_source_label(False, True)
        assert result == "/tokenize (next turn)"

    def test_token_source_label_chars_div_4(self) -> None:
        result = _token_source_label(False, False)
        assert result == "category-aware estimate"


# ── _cmd_history ──────────────────────────────────────────────────────────────


class TestCmdHistory:
    def test_history_prints_last_n_messages(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [
            _system_msg(),
            _user_msg("first"),
            _assistant_msg("reply1"),
            _user_msg("second"),
            _assistant_msg("reply2"),
        ]
        cmd = _FakeCmd(ctx)
        cmd._cmd_history("2")
        out = capsys.readouterr().out
        assert "second" in out
        assert "reply2" in out

    def test_history_default_is_5(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [_system_msg(), _user_msg("q1"), _assistant_msg("a1")]
        cmd = _FakeCmd(ctx)
        cmd._cmd_history("")
        out = capsys.readouterr().out
        assert "q1" in out

    def test_history_invalid_n_shows_usage(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _FakeCmd(ctx)
        cmd._cmd_history("abc")
        out = capsys.readouterr().out
        assert "usage" in out.lower()

    def test_history_no_conversation_prints_message(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [_system_msg()]
        cmd = _FakeCmd(ctx)
        cmd._cmd_history("5")
        out = capsys.readouterr().out
        assert "No conversation history" in out

    def test_history_truncates_long_content(self, capsys: Any) -> None:
        ctx = _make_ctx()
        long_content = "x" * 200
        ctx.conv.history = [_system_msg(), _user_msg(long_content)]
        cmd = _FakeCmd(ctx)
        cmd._cmd_history("1")
        out = capsys.readouterr().out
        assert "..." in out

    def test_history_none_content_does_not_crash(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [_system_msg(), {"role": "user", "content": None}]
        cmd = _FakeCmd(ctx)
        cmd._cmd_history("1")
        out = capsys.readouterr().out
        assert "[user]" in out


# ── collect_context_state ─────────────────────────────────────────────────────


class TestCollectContextState:
    def test_collect_context_state_returns_context_state_view(self) -> None:
        from agent.services.context_view import collect_context_state
        from agent.services.models import ContextStateView

        ctx = _make_ctx()
        ctx.conv.history = [_system_msg("sys")]
        hist_mgr = MagicMock()
        hist_mgr.count_chars.return_value = 3
        hist_mgr.stat_compress_count = 0
        hist_mgr.count_tokens.return_value = None
        ctx.services.hist_mgr = hist_mgr
        result = collect_context_state(ctx)
        assert isinstance(result, ContextStateView)
        assert result.total_chars == 3
        assert result.n_msgs == 1

    def test_collect_context_state_with_hist_mgr(self) -> None:
        from agent.services.context_view import collect_context_state

        ctx = _make_ctx()
        ctx.conv.history = [_system_msg("sys")]
        hist_mgr = MagicMock()
        hist_mgr.count_chars.return_value = 100
        hist_mgr.stat_compress_count = 5
        hist_mgr.count_tokens.return_value = 25
        ctx.services.hist_mgr = hist_mgr
        result = collect_context_state(ctx)
        assert result.total_chars == 100

    def test_collect_context_state_no_hist_mgr_raises(self) -> None:
        from agent.services.context_view import collect_context_state
        from agent.services.exceptions import ContextStateBuildError

        ctx = _make_ctx()
        ctx.services.hist_mgr = None
        with pytest.raises(ContextStateBuildError, match="hist_mgr"):
            collect_context_state(ctx)

    def test_collect_context_state_with_memory(self) -> None:
        from agent.services.context_view import collect_context_state

        ctx = _make_ctx()
        hist_mgr = MagicMock()
        hist_mgr.count_chars.return_value = 0
        hist_mgr.stat_compress_count = 0
        hist_mgr.count_tokens.return_value = None
        ctx.services.hist_mgr = hist_mgr
        mem = MagicMock()
        mem.store.count_vec.return_value = 5
        ctx.services.memory = mem
        with patch("agent.services.context_view.count_by_type", return_value={"semantic": 3}):
            with patch("agent.services.context_view.count_entries", return_value=10):
                result = collect_context_state(ctx)
                assert "enabled" in result.mem_status


# ── _cmd_context ──────────────────────────────────────────────────────────────


class TestCmdContext:
    def _add_hist_mgr(self, ctx: MagicMock, n_chars: int = 10) -> None:
        hist_mgr = MagicMock()
        hist_mgr.count_chars.return_value = n_chars
        hist_mgr.stat_compress_count = 0
        hist_mgr.count_tokens.return_value = None
        ctx.services.hist_mgr = hist_mgr

    def test_cmd_context_prints_state(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [_system_msg("system prompt")]
        self._add_hist_mgr(ctx)
        cmd = _FakeCmd(ctx)
        cmd._cmd_context()
        out = capsys.readouterr().out
        assert "Messages" in out

    def test_cmd_context_prints_breakdown(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.conv.history = [
            _system_msg("sys"),
            _user_msg("user msg"),
            {"role": "tool", "content": "tool result"},
        ]
        self._add_hist_mgr(ctx)
        cmd = _FakeCmd(ctx)
        cmd._cmd_context()
        out = capsys.readouterr().out
        assert "Budget breakdown" in out
        assert "system" in out
        assert "history" in out

    def test_cmd_context_with_token_limit(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.cfg.llm.context_token_limit = 4096
        ctx.conv.history = [_system_msg("sys")]
        hist_mgr = MagicMock()
        hist_mgr.count_chars.return_value = 100
        hist_mgr.stat_compress_count = 0
        hist_mgr.count_tokens.return_value = 25
        ctx.services.hist_mgr = hist_mgr
        cmd = _FakeCmd(ctx)
        cmd._cmd_context()
        out = capsys.readouterr().out
        assert "Token limit" in out

    def test_cmd_context_shows_workflow_mode(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.cfg.workflow_mode = "auto"
        ctx.turn.pending_approval_id = None
        ctx.conv.history = [_system_msg("sys")]
        self._add_hist_mgr(ctx)
        cmd = _FakeCmd(ctx)
        cmd._cmd_context()
        out = capsys.readouterr().out
        assert "Workflow mode" in out
        assert "auto" in out

    def test_cmd_context_shows_approval_pending(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.cfg.workflow_mode = "required"
        ctx.turn.pending_approval_id = "approval-123"
        ctx.conv.history = [_system_msg("sys")]
        self._add_hist_mgr(ctx)
        cmd = _FakeCmd(ctx)
        cmd._cmd_context()
        out = capsys.readouterr().out
        assert "Approval pending" in out
        assert "/approve" in out


class TestCollectContextStateWorkflow:
    def test_collect_context_state_workflow_mode(self) -> None:
        from agent.services.context_view import collect_context_state

        ctx = _make_ctx()
        ctx.cfg.workflow_mode = "disabled"
        ctx.turn.pending_approval_id = None
        hist_mgr = MagicMock()
        hist_mgr.count_chars.return_value = 0
        hist_mgr.stat_compress_count = 0
        hist_mgr.stat_fallback_truncate_count = 0
        hist_mgr.count_tokens.return_value = None
        ctx.services.hist_mgr = hist_mgr
        result = collect_context_state(ctx)
        assert result.workflow_mode == "disabled"
        assert result.approval_pending is False

    def test_collect_context_state_approval_pending(self) -> None:
        from agent.services.context_view import collect_context_state

        ctx = _make_ctx()
        ctx.cfg.workflow_mode = "auto"
        ctx.turn.pending_approval_id = "wf-approval-abc"
        hist_mgr = MagicMock()
        hist_mgr.count_chars.return_value = 0
        hist_mgr.stat_compress_count = 0
        hist_mgr.stat_fallback_truncate_count = 0
        hist_mgr.count_tokens.return_value = None
        ctx.services.hist_mgr = hist_mgr
        result = collect_context_state(ctx)
        assert result.approval_pending is True
