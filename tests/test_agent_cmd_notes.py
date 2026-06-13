"""tests/test_agent_cmd_notes.py
Behavior-lock tests for _NotesMixin slash-command handlers.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from agent.commands.cmd_notes import _NotesMixin
from agent.commands.exceptions import UnknownSubcommandError


def _make_cmd(
    *,
    add_return: int | None = 1,
    list_return: list | None = None,
    delete_return: bool = True,
    pin_return: bool = True,
    unpin_return: bool = True,
    search_return: list | None = None,
) -> _NotesMixin:
    session = MagicMock()
    session.add_note.return_value = add_return
    session.list_notes.return_value = list_return or []
    session.delete_note.return_value = delete_return
    session.pin_note.return_value = pin_return
    session.unpin_note.return_value = unpin_return
    session.search_notes.return_value = search_return or []
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
            {
                "note_id": 1,
                "content": "hello",
                "pinned": 0,
                "created_at": "2026-01-01 00:00:00",
            }
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


class TestNotePin:
    def test_pin_success(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(pin_return=True)
        cmd._cmd_note("pin 1")
        assert "pinned" in capsys.readouterr().out.lower()
        cmd._ctx.session.pin_note.assert_called_once_with(1)

    def test_pin_not_found(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(pin_return=False)
        cmd._cmd_note("pin 99")
        assert "not found" in capsys.readouterr().out.lower()

    def test_pin_invalid_id_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._cmd_note("pin abc")
        assert "usage" in capsys.readouterr().out.lower()
        cmd._ctx.session.pin_note.assert_not_called()


class TestNoteUnpin:
    def test_unpin_success(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(unpin_return=True)
        cmd._cmd_note("unpin 1")
        assert "unpinned" in capsys.readouterr().out.lower()
        cmd._ctx.session.unpin_note.assert_called_once_with(1)

    def test_unpin_not_found(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(unpin_return=False)
        cmd._cmd_note("unpin 99")
        assert "not found" in capsys.readouterr().out.lower()

    def test_unpin_invalid_id_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._cmd_note("unpin abc")
        assert "usage" in capsys.readouterr().out.lower()
        cmd._ctx.session.unpin_note.assert_not_called()


class TestNoteSearch:
    def test_search_empty_query_shows_usage(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd()
        cmd._cmd_note("search")
        assert "usage" in capsys.readouterr().out.lower()

    def test_search_no_results(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(search_return=[])
        cmd._cmd_note("search xyz")
        assert "No matching" in capsys.readouterr().out

    def test_search_shows_results(self, capsys: pytest.CaptureFixture) -> None:
        notes = [
            {
                "note_id": 1,
                "content": "hello",
                "pinned": 1,
                "created_at": "2026-01-01 00:00:00",
            }
        ]
        cmd = _make_cmd(search_return=notes)
        cmd._cmd_note("search hello")
        out = capsys.readouterr().out
        assert "hello" in out
        cmd._ctx.session.search_notes.assert_called_once_with("hello")


class TestNoteUnknownSubcommand:
    def test_unknown_raises_unknown_subcommand_error(self) -> None:
        cmd = _make_cmd()
        with pytest.raises(UnknownSubcommandError) as exc_info:
            cmd._cmd_note("unknown")
        assert exc_info.value.sub == "unknown"
        assert "add" in exc_info.value.valid
