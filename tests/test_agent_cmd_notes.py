"""tests/test_agent_cmd_notes.py
Behavior-lock tests for _NotesMixin slash-command handlers.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from agent.commands.cmd_notes import _NotesMixin


def _make_cmd(
    *,
    add_return: int | None = 1,
    list_return: list | None = None,
    delete_return: bool = True,
) -> _NotesMixin:
    session = MagicMock()
    session.add_note.return_value = add_return
    session.list_notes.return_value = list_return or []
    session.delete_note.return_value = delete_return
    ctx = SimpleNamespace(session=session)
    cmd = object.__new__(_NotesMixin)
    cmd._ctx = ctx  # type: ignore[attr-defined]
    return cmd


class TestNoteAdd:
    def test_add_success(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(add_return=1)
        cmd._cmd_note("add remember this")
        assert "added" in capsys.readouterr().out.lower()
        cmd._ctx.session.add_note.assert_called_once_with("remember this")

    def test_add_empty_text_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._cmd_note("add")
        assert "usage" in capsys.readouterr().out.lower()
        cmd._ctx.session.add_note.assert_not_called()

    def test_add_failure_prints_error(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(add_return=None)
        cmd._cmd_note("add something")
        assert "Failed" in capsys.readouterr().out


class TestNoteList:
    def test_list_empty(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(list_return=[])
        cmd._cmd_note("list")
        assert "No notes" in capsys.readouterr().out

    def test_list_shows_notes(self, capsys: pytest.CaptureFixture) -> None:
        notes = [
            {"note_id": 1, "content": "hello", "created_at": "2026-01-01 00:00:00"}
        ]
        cmd = _make_cmd(list_return=notes)
        cmd._cmd_note("list")
        assert "hello" in capsys.readouterr().out

    def test_list_truncates_long_content(self, capsys: pytest.CaptureFixture) -> None:
        notes = [
            {"note_id": 1, "content": "x" * 100, "created_at": "2026-01-01 00:00:00"}
        ]
        cmd = _make_cmd(list_return=notes)
        cmd._cmd_note("list")
        out = capsys.readouterr().out
        assert "..." in out


class TestNoteDelete:
    def test_delete_success(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(delete_return=True)
        cmd._cmd_note("delete 1")
        assert "deleted" in capsys.readouterr().out.lower()

    def test_delete_not_found(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(delete_return=False)
        cmd._cmd_note("delete 99")
        assert "not found" in capsys.readouterr().out.lower()

    def test_delete_invalid_id_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._cmd_note("delete abc")
        assert "usage" in capsys.readouterr().out.lower()
        cmd._ctx.session.delete_note.assert_not_called()


class TestNoteUnknownSubcommand:
    def test_unknown_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._cmd_note("unknown")
        assert "usage" in capsys.readouterr().out.lower()
