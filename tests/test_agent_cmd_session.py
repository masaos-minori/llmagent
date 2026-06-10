"""tests/test_agent_cmd_session.py
Behavior-lock tests for _SessionMixin slash-command handlers.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from agent.commands.cmd_session import _SessionMixin


def _make_session(
    *,
    session_id: int | None = 1,
    list_return: list | None = None,
    delete_return: bool = True,
) -> MagicMock:
    s = MagicMock()
    s.session_id = session_id
    s.list_sessions.return_value = list_return or []
    s.delete_session.return_value = delete_return
    return s


def _make_cmd(
    *, session_id: int | None = 1, sessions: list | None = None
) -> _SessionMixin:
    session = _make_session(session_id=session_id, list_return=sessions)
    ctx = SimpleNamespace(
        session=session,
        conv=SimpleNamespace(history=[], llm_url=""),
        cfg=SimpleNamespace(llm=SimpleNamespace(context_char_limit=8000)),
        services=SimpleNamespace(
            hist_mgr=MagicMock(), llm=MagicMock(), http=MagicMock()
        ),
    )
    cmd = object.__new__(_SessionMixin)
    cmd._ctx = ctx  # type: ignore[attr-defined]
    return cmd


class TestCmdSessionList:
    def test_list_no_sessions_prints_message(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd(sessions=[])
        cmd._cmd_session("list")
        assert "No sessions" in capsys.readouterr().out

    def test_list_shows_sessions(self, capsys: pytest.CaptureFixture) -> None:
        sessions = [
            {
                "session_id": 1,
                "title": "Test",
                "created_at": "2026-01-01",
                "is_current": True,
            }
        ]
        cmd = _make_cmd(sessions=sessions)
        cmd._cmd_session("list")
        out = capsys.readouterr().out
        assert "Test" in out

    def test_list_default_limit_is_20(self) -> None:
        cmd = _make_cmd(sessions=[])
        cmd._cmd_session("list")
        cmd._ctx.session.list_sessions.assert_called_once_with(20)

    def test_list_custom_limit(self) -> None:
        cmd = _make_cmd(sessions=[])
        cmd._cmd_session("list 5")
        cmd._ctx.session.list_sessions.assert_called_once_with(5)


class TestCmdSessionDelete:
    def test_delete_success(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(session_id=1)
        cmd._ctx.session.delete_session.return_value = True
        cmd._cmd_session("delete 2")
        assert "deleted" in capsys.readouterr().out.lower()

    def test_delete_not_found(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(session_id=1)
        cmd._ctx.session.delete_session.return_value = False
        cmd._cmd_session("delete 99")
        assert "not found" in capsys.readouterr().out.lower()

    def test_delete_current_session_blocked(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd(session_id=1)
        cmd._cmd_session("delete 1")
        assert "Cannot delete" in capsys.readouterr().out
        cmd._ctx.session.delete_session.assert_not_called()

    def test_delete_invalid_id(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._cmd_session("delete abc")
        assert "Invalid" in capsys.readouterr().out


class TestCmdSessionRename:
    def test_rename_updates_title(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._cmd_session("rename My New Title")
        cmd._ctx.session.set_title.assert_called_once_with("My New Title")
        assert "renamed" in capsys.readouterr().out.lower()


class TestCmdSessionUsage:
    def test_unknown_subcommand_shows_usage(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd()
        cmd._cmd_session("unknown")
        assert "usage" in capsys.readouterr().out.lower()

    def test_empty_args_defaults_to_list(self) -> None:
        cmd = _make_cmd(sessions=[])
        cmd._cmd_session("")
        cmd._ctx.session.list_sessions.assert_called_once()
