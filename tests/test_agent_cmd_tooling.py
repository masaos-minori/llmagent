"""tests/test_agent_cmd_tooling.py
Behavior-lock tests for _ToolingMixin slash-command handlers.

Covers:
  _tool_list    — empty / entries present
  _tool_show    — valid id / not found / invalid id / invalid JSON args
  _cmd_tool     — list / show / unknown subcommand
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from agent.commands.cmd_tooling import _ToolingMixin
from db.models import ToolResultRow

# ── helpers ───────────────────────────────────────────────────────────────────


def _make_entry(
    *,
    id: int = 1,
    tool_name: str = "bash",
    args_masked: str = '{"cmd": "ls"}',
    full_text: str = "output",
    summary: str | None = None,
    is_error: bool = False,
    undone: bool = False,
) -> ToolResultRow:
    return ToolResultRow(
        id=id,
        tool_name=tool_name,
        args_masked=args_masked,
        full_text=full_text,
        summary=summary,
        is_error=is_error,
        undone=undone,
    )


def _make_cmd(*, entries=None, get_return=None):
    store = MagicMock()
    store.list_recent.return_value = entries if entries is not None else []
    store.get.return_value = get_return
    session = SimpleNamespace(session_id=42)
    ctx = SimpleNamespace(tool_result_store=store, session=session)
    cmd = object.__new__(_ToolingMixin)
    cmd._ctx = ctx  # type: ignore[attr-defined]
    return cmd


# ── _tool_list ────────────────────────────────────────────────────────────────


class TestToolList:
    def test_empty_writes_no_results(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(entries=[])
        cmd._tool_list()
        assert "No tool results" in capsys.readouterr().out

    def test_entries_printed(self, capsys: pytest.CaptureFixture) -> None:
        entry = _make_entry(id=7, tool_name="read_file")
        cmd = _make_cmd(entries=[entry])
        cmd._tool_list()
        out = capsys.readouterr().out
        assert "read_file" in out
        assert "7" in out

    def test_summarized_flag_shown(self, capsys: pytest.CaptureFixture) -> None:
        entry = _make_entry(summary="short summary")
        cmd = _make_cmd(entries=[entry])
        cmd._tool_list()
        assert "yes" in capsys.readouterr().out


# ── _tool_show ────────────────────────────────────────────────────────────────


class TestToolShow:
    def test_valid_id_shows_tool_info(self, capsys: pytest.CaptureFixture) -> None:
        entry = _make_entry(id=1, tool_name="bash", full_text="hello")
        cmd = _make_cmd(get_return=entry)
        cmd._tool_show("1")
        out = capsys.readouterr().out
        assert "bash" in out
        assert "hello" in out

    def test_not_found_writes_message(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(get_return=None)
        cmd._tool_show("99")
        assert "not found" in capsys.readouterr().out

    def test_invalid_id_writes_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._tool_show("abc")
        assert "Usage" in capsys.readouterr().out

    def test_zero_id_writes_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._tool_show("0")
        assert "Usage" in capsys.readouterr().out

    def test_invalid_json_args_does_not_raise(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        entry = _make_entry(args_masked="NOT_JSON", full_text="content")
        cmd = _make_cmd(get_return=entry)
        cmd._tool_show("1")
        out = capsys.readouterr().out
        assert "Args: {}" in out
        assert "content" in out

    def test_summarized_label_shown(self, capsys: pytest.CaptureFixture) -> None:
        entry = _make_entry(summary="summary text")
        cmd = _make_cmd(get_return=entry)
        cmd._tool_show("1")
        out = capsys.readouterr().out
        assert "[summarized]" in out
        assert "Summary: summary text" in out


# ── _cmd_tool dispatch ────────────────────────────────────────────────────────


class TestCmdToolDispatch:
    def test_list_dispatched(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(entries=[])
        cmd._cmd_tool("list")
        assert "No tool results" in capsys.readouterr().out

    def test_default_dispatches_list(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(entries=[])
        cmd._cmd_tool("")
        assert "No tool results" in capsys.readouterr().out

    def test_unknown_subcommand_writes_usage(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd()
        cmd._cmd_tool("badcmd")
        assert "Usage" in capsys.readouterr().out


# ── undone display ────────────────────────────────────────────────────────────


class TestUndoneDisplay:
    def test_tool_list_shows_undone_annotation(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        entry = _make_entry(id=3, tool_name="bash", undone=True)
        cmd = _make_cmd(entries=[entry])
        cmd._tool_list()
        assert "[undone]" in capsys.readouterr().out

    def test_tool_list_no_annotation_for_active(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        entry = _make_entry(id=4, tool_name="bash", undone=False)
        cmd = _make_cmd(entries=[entry])
        cmd._tool_list()
        assert "[undone]" not in capsys.readouterr().out

    def test_tool_show_shows_undone_warning(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        entry = _make_entry(id=1, tool_name="bash", full_text="result", undone=True)
        cmd = _make_cmd(get_return=entry)
        cmd._tool_show("1")
        out = capsys.readouterr().out
        assert "undone" in out.lower()
        assert "artifact retained" in out

    def test_tool_show_no_warning_for_active(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        entry = _make_entry(id=1, tool_name="bash", full_text="result", undone=False)
        cmd = _make_cmd(get_return=entry)
        cmd._tool_show("1")
        out = capsys.readouterr().out
        assert "undone turn" not in out
