"""tests/test_agent_cmd_db.py
Behavior-lock tests for _DbMixin slash-command handlers.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from agent.commands.cmd_db import _DbMixin


def _make_cmd(*, delete_doc_return: bool = True) -> _DbMixin:
    session = MagicMock()
    session.delete_document.return_value = delete_doc_return
    ctx = SimpleNamespace(session=session)
    cmd = object.__new__(_DbMixin)
    cmd._ctx = ctx  # type: ignore[attr-defined]
    return cmd


class TestCmdDbClean:
    def test_clean_success(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(delete_doc_return=True)
        cmd._cmd_db("clean http://example.com")
        assert "deleted" in capsys.readouterr().out.lower()

    def test_clean_not_found(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(delete_doc_return=False)
        cmd._cmd_db("clean http://example.com")
        assert "not found" in capsys.readouterr().out.lower()

    def test_clean_empty_url_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._cmd_db("clean")
        assert "Usage" in capsys.readouterr().out
        cmd._ctx.session.delete_document.assert_not_called()


class TestCmdDbStats:
    def test_stats_error_handled(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch(
            "agent.commands.cmd_db.SQLiteHelper", side_effect=Exception("db error")
        ):
            cmd._cmd_db("stats")
        assert "error" in capsys.readouterr().out.lower()


class TestCmdDbUnknownSubcommand:
    def test_unknown_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._cmd_db("unknown")
        assert "Usage" in capsys.readouterr().out

    def test_empty_args_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._cmd_db("")
        assert "Usage" in capsys.readouterr().out
