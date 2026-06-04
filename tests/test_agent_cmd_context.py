"""
tests/test_agent_cmd_context.py
Behavior-lock tests for _ContextMixin: _cmd_undo, _cmd_clear, _cmd_system.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from agent.commands.cmd_context import _ContextMixin

# ── Test harness ──────────────────────────────────────────────────────────────


class _FakeCmd(_ContextMixin):
    def __init__(self, ctx: Any) -> None:
        self._ctx = ctx


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.stat_turns = 3
    ctx.stat_tool_calls = 5
    ctx.stat_tool_errors = 1
    ctx.stat_latency = {}
    ctx.stat_semantic_cache_hits = 0
    ctx.stat_input_tokens = None
    ctx.debug_mode = False
    ctx.plan_mode = False
    ctx.system_prompt_name = "default"
    ctx.system_prompt_content = "You are helpful."
    ctx.history = []
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
        ctx.history = [
            _system_msg(),
            _user_msg("first"),
            _assistant_msg("first reply"),
            _user_msg("second"),
            _assistant_msg("second reply"),
        ]
        ctx.stat_turns = 2
        cmd = _FakeCmd(ctx)
        cmd._cmd_undo()
        assert ctx.history == [
            _system_msg(),
            _user_msg("first"),
            _assistant_msg("first reply"),
        ]
        assert ctx.stat_turns == 1

    def test_undo_removes_memory_injection_before_user(self) -> None:
        ctx = _make_ctx()
        ctx.history = [
            _system_msg(),
            _user_msg("first"),
            _assistant_msg("first reply"),
            _injected_msg(),
            _user_msg("second"),
            _assistant_msg("second reply"),
        ]
        ctx.stat_turns = 2
        cmd = _FakeCmd(ctx)
        cmd._cmd_undo()
        # injection marker + second user + second assistant must be removed
        assert ctx.history == [
            _system_msg(),
            _user_msg("first"),
            _assistant_msg("first reply"),
        ]
        assert ctx.stat_turns == 1

    def test_undo_calls_undo_last_turn(self) -> None:
        ctx = _make_ctx()
        ctx.history = [_system_msg(), _user_msg(), _assistant_msg()]
        ctx.stat_turns = 1
        cmd = _FakeCmd(ctx)
        cmd._cmd_undo()
        ctx.session.undo_last_turn.assert_called_once()

    def test_undo_with_no_user_message_prints_nothing(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.history = [_system_msg()]
        cmd = _FakeCmd(ctx)
        cmd._cmd_undo()
        out = capsys.readouterr().out
        assert "Nothing to undo" in out

    def test_undo_stat_turns_floor_at_zero(self) -> None:
        ctx = _make_ctx()
        ctx.history = [_system_msg(), _user_msg(), _assistant_msg()]
        ctx.stat_turns = 0
        cmd = _FakeCmd(ctx)
        cmd._cmd_undo()
        assert ctx.stat_turns == 0

    def test_undo_with_tool_messages_removes_from_user_onwards(self) -> None:
        """Tool messages after user message are included in the undo cut."""
        ctx = _make_ctx()
        ctx.history = [
            _system_msg(),
            _user_msg("first"),
            _assistant_msg("first reply"),
            _user_msg("second"),
            {"role": "assistant", "content": "", "tool_calls": [{"id": "t1"}]},
            {"role": "tool", "content": "result", "tool_call_id": "t1"},
            _assistant_msg("final"),
        ]
        ctx.stat_turns = 2
        cmd = _FakeCmd(ctx)
        cmd._cmd_undo()
        # Everything from the last user message onwards must be removed
        assert ctx.history == [
            _system_msg(),
            _user_msg("first"),
            _assistant_msg("first reply"),
        ]


# ── _cmd_clear ────────────────────────────────────────────────────────────────


class TestCmdClear:
    def test_clear_keeps_system_message(self) -> None:
        ctx = _make_ctx()
        ctx.history = [_system_msg(), _user_msg(), _assistant_msg()]
        cmd = _FakeCmd(ctx)
        cmd._cmd_clear()
        assert ctx.history == [_system_msg()]

    def test_clear_resets_stats(self) -> None:
        ctx = _make_ctx()
        ctx.history = [_system_msg()]
        ctx.stat_turns = 5
        ctx.stat_tool_calls = 10
        cmd = _FakeCmd(ctx)
        cmd._cmd_clear()
        assert ctx.stat_turns == 0
        assert ctx.stat_tool_calls == 0

    def test_clear_new_starts_new_session(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.history = [_system_msg()]
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
        assert ctx.system_prompt_name == "coding"
        assert ctx.system_prompt_content == "You code."

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
