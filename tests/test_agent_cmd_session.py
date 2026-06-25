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
    title_pending: bool = False,
) -> MagicMock:
    s = MagicMock()
    s.session_id = session_id
    s.list_sessions.return_value = list_return or []
    s.delete_session.return_value = delete_return
    s.is_title_pending.return_value = title_pending
    return s


def _make_cmd(
    *,
    session_id: int | None = 1,
    sessions: list | None = None,
    title_pending: bool = False,
) -> _SessionMixin:
    session = _make_session(
        session_id=session_id, list_return=sessions, title_pending=title_pending
    )
    ctx = SimpleNamespace(
        session=session,
        conv=SimpleNamespace(history=[], llm_url=""),
        cfg=SimpleNamespace(llm=SimpleNamespace(context_char_limit=8000)),
        services=SimpleNamespace(
            hist_mgr=MagicMock(),
            llm=MagicMock(),
            http=MagicMock(),
            audit_logger=MagicMock(),
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

    def test_list_shows_generating_when_title_pending(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        sessions = [
            {
                "session_id": 1,
                "title": "Test",
                "created_at": "2026-01-01",
                "is_current": True,
            }
        ]
        cmd = _make_cmd(sessions=sessions, title_pending=True)
        cmd._cmd_session("list")
        out = capsys.readouterr().out
        assert "(generating...)" in out

    def test_list_shows_no_title_when_title_is_none(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        sessions = [
            {
                "session_id": 2,
                "title": None,
                "created_at": "2026-01-01",
                "is_current": False,
            }
        ]
        cmd = _make_cmd(sessions=sessions)
        cmd._cmd_session("list")
        out = capsys.readouterr().out
        assert "(no title)" in out

    def test_list_shows_no_title_when_title_is_empty_string(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        sessions = [
            {
                "session_id": 3,
                "title": "",
                "created_at": "2026-01-01",
                "is_current": False,
            }
        ]
        cmd = _make_cmd(sessions=sessions)
        cmd._cmd_session("list")
        out = capsys.readouterr().out
        assert "(no title)" in out


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


class TestGenerateSessionTitle:
    @pytest.mark.asyncio
    async def test_fallback_empty_input_sets_new_session_title(self) -> None:
        from unittest.mock import AsyncMock, patch

        cmd = _make_cmd()
        from agent.services.exceptions import SessionTitleGenerationError

        with patch(
            "agent.services.session_title.SessionTitleService",
        ) as MockSvc:
            MockSvc.return_value.generate = AsyncMock(
                side_effect=SessionTitleGenerationError("test fail")
            )
            await cmd._generate_session_title("")

        cmd._ctx.session.set_title.assert_called_with("(New Session)")

    @pytest.mark.asyncio
    async def test_fallback_long_input_truncates_with_ellipsis(self) -> None:
        from unittest.mock import AsyncMock, patch

        cmd = _make_cmd()
        from agent.services.exceptions import SessionTitleGenerationError

        long_input = "a" * 40
        with patch(
            "agent.services.session_title.SessionTitleService",
        ) as MockSvc:
            MockSvc.return_value.generate = AsyncMock(
                side_effect=SessionTitleGenerationError("test fail")
            )
            await cmd._generate_session_title(long_input)

        call_args = cmd._ctx.session.set_title.call_args[0][0]
        assert call_args.endswith("...")
        assert len(call_args) <= 32

    @pytest.mark.asyncio
    async def test_fallback_short_input_uses_as_is(self) -> None:
        from unittest.mock import AsyncMock, patch

        cmd = _make_cmd()
        from agent.services.exceptions import SessionTitleGenerationError

        with patch(
            "agent.services.session_title.SessionTitleService",
        ) as MockSvc:
            MockSvc.return_value.generate = AsyncMock(
                side_effect=SessionTitleGenerationError("test fail")
            )
            await cmd._generate_session_title("Hello World")

        cmd._ctx.session.set_title.assert_called_with("Hello World")

    @pytest.mark.asyncio
    async def test_pending_state_cleared_on_success(self) -> None:
        from unittest.mock import AsyncMock, patch

        cmd = _make_cmd()
        with patch(
            "agent.services.session_title.SessionTitleService",
        ) as MockSvc:
            MockSvc.return_value.generate = AsyncMock(return_value=None)
            await cmd._generate_session_title("hello")

        cmd._ctx.session.set_title_pending.assert_any_call(True)
        cmd._ctx.session.set_title_pending.assert_called_with(False)

    @pytest.mark.asyncio
    async def test_pending_state_cleared_on_failure(self) -> None:
        from unittest.mock import AsyncMock, patch

        cmd = _make_cmd()
        from agent.services.exceptions import SessionTitleGenerationError

        with patch(
            "agent.services.session_title.SessionTitleService",
        ) as MockSvc:
            MockSvc.return_value.generate = AsyncMock(
                side_effect=SessionTitleGenerationError("fail")
            )
            await cmd._generate_session_title("test")

        cmd._ctx.session.set_title_pending.assert_called_with(False)


class TestGenerateSessionTitleVisibility:
    """audit_logger.warning is called on fallback; fallback set_title DB error is handled."""

    @pytest.mark.asyncio
    async def test_audit_logger_warning_called_on_failure(self) -> None:
        from unittest.mock import AsyncMock, MagicMock, patch

        from agent.services.exceptions import SessionTitleGenerationError

        cmd = _make_cmd()
        audit_logger = MagicMock()
        cmd._ctx.services = SimpleNamespace(
            hist_mgr=MagicMock(),
            llm=MagicMock(),
            http=MagicMock(),
            audit_logger=audit_logger,
        )

        with patch("agent.services.session_title.SessionTitleService") as MockSvc:
            MockSvc.return_value.generate = AsyncMock(
                side_effect=SessionTitleGenerationError("LLM error")
            )
            await cmd._generate_session_title("first user message")

        audit_logger.warning.assert_called_once()
        call_args = audit_logger.warning.call_args[0]
        assert "session_title_fallback" in call_args[0]

    @pytest.mark.asyncio
    async def test_fallback_set_title_db_error_does_not_propagate(self) -> None:
        """If fallback set_title() raises, the exception is logged but not re-raised."""
        import sqlite3
        from unittest.mock import AsyncMock, patch

        from agent.services.exceptions import SessionTitleGenerationError

        cmd = _make_cmd()
        cmd._ctx.session.set_title.side_effect = sqlite3.Error("disk full")

        with patch("agent.services.session_title.SessionTitleService") as MockSvc:
            MockSvc.return_value.generate = AsyncMock(
                side_effect=SessionTitleGenerationError("fail")
            )
            await cmd._generate_session_title("hello")

        cmd._ctx.session.set_title_pending.assert_called_with(False)
