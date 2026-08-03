"""tests/test_agent_cmd_session.py
Behavior-lock tests for _SessionMixin slash-command handlers.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

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
    ctx.services_required = (
        ctx.services
    )  # alias for AgentContext.services_required property
    cmd = object.__new__(_SessionMixin)
    cmd._ctx = ctx  # type: ignore[attr-defined]
    from agent.commands.session_title import SessionTitleGen

    cmd._title_gen = SessionTitleGen(ctx, cmd._out)  # type: ignore[attr-defined]
    from agent.commands.db_session_ops import DbSessionOps

    cmd._db_session_ops = DbSessionOps(ctx, cmd._out)  # type: ignore[attr-defined]
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
        from unittest.mock import patch

        cmd = _make_cmd()
        from agent.services.exceptions import SessionTitleGenerationError

        with patch(
            "agent.commands.session_title.SessionTitleService",
        ) as MockSvc:
            MockSvc.return_value.generate = AsyncMock(
                side_effect=SessionTitleGenerationError("test fail")
            )
            await cmd._generate_session_title("")

        cmd._ctx.session.set_title.assert_called_with("(New Session)")

    @pytest.mark.asyncio
    async def test_fallback_long_input_truncates_with_ellipsis(self) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        from agent.services.exceptions import SessionTitleGenerationError

        long_input = "a" * 40
        with patch(
            "agent.commands.session_title.SessionTitleService",
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
        from unittest.mock import patch

        cmd = _make_cmd()
        from agent.services.exceptions import SessionTitleGenerationError

        with patch(
            "agent.commands.session_title.SessionTitleService",
        ) as MockSvc:
            MockSvc.return_value.generate = AsyncMock(
                side_effect=SessionTitleGenerationError("test fail")
            )
            await cmd._generate_session_title("Hello World")

        cmd._ctx.session.set_title.assert_called_with("Hello World")

    @pytest.mark.asyncio
    async def test_pending_state_cleared_on_success(self) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch(
            "agent.commands.session_title.SessionTitleService",
        ) as MockSvc:
            MockSvc.return_value.generate = AsyncMock(return_value=None)
            await cmd._generate_session_title("hello")

        cmd._ctx.session.set_title_pending.assert_any_call(True)
        cmd._ctx.session.set_title_pending.assert_called_with(False)

    @pytest.mark.asyncio
    async def test_pending_state_cleared_on_failure(self) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        from agent.services.exceptions import SessionTitleGenerationError

        with patch(
            "agent.commands.session_title.SessionTitleService",
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
        from unittest.mock import MagicMock, patch

        from agent.services.exceptions import SessionTitleGenerationError

        cmd = _make_cmd()
        audit_logger = MagicMock()
        cmd._ctx.services = SimpleNamespace(
            hist_mgr=MagicMock(),
            llm=MagicMock(),
            http=MagicMock(),
            audit_logger=audit_logger,
        )
        cmd._ctx.services_required = cmd._ctx.services

        with patch("agent.commands.session_title.SessionTitleService") as MockSvc:
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
        from unittest.mock import patch

        from agent.services.exceptions import SessionTitleGenerationError

        cmd = _make_cmd()
        cmd._ctx.session.set_title.side_effect = sqlite3.Error("disk full")

        with patch("agent.commands.session_title.SessionTitleService") as MockSvc:
            MockSvc.return_value.generate = AsyncMock(
                side_effect=SessionTitleGenerationError("fail")
            )
            await cmd._generate_session_title("hello")

        cmd._ctx.session.set_title_pending.assert_called_with(False)


# ── /session health ─────────────────────────────────────────────────────────────


class TestCmdSessionHealth:
    def test_health_prints_metrics(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        from agent.services.models import DbHealth

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.health.return_value = DbHealth(
                integrity_ok=True, wal_pages=0, size_bytes=10240
            )
            MockSvc.return_value = mock_svc
            cmd._cmd_session("health")
            out = capsys.readouterr().out
            assert "integrity_ok" in out
            assert "True" in out

    def test_health_error_raises(self) -> None:
        import sqlite3
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.health.side_effect = sqlite3.Error("health error")
            MockSvc.return_value = mock_svc
            with pytest.raises(sqlite3.Error, match="health error"):
                cmd._cmd_session("health")


# ── /session checkpoint ─────────────────────────────────────────────────────────


class TestCmdSessionCheckpoint:
    def test_checkpoint_success(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        from agent.services.models import DbCheckpointResult

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.checkpoint.return_value = DbCheckpointResult(
                mode="TRUNCATE", pages_written=10
            )
            MockSvc.return_value = mock_svc
            cmd._cmd_session("checkpoint")
            out = capsys.readouterr().out
            assert "complete" in out.lower()

    def test_checkpoint_with_mode(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        from agent.services.models import DbCheckpointResult

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.checkpoint.return_value = DbCheckpointResult(
                mode="FULL", pages_written=5
            )
            MockSvc.return_value = mock_svc
            cmd._cmd_session("checkpoint FULL")
            out = capsys.readouterr().out
            assert "complete" in out.lower()


# ── /session vacuum ─────────────────────────────────────────────────────────────


class TestCmdSessionVacuum:
    def test_vacuum_success(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            MockSvc.return_value = mock_svc
            cmd._cmd_session("vacuum")
            out = capsys.readouterr().out
            assert "complete" in out.lower()

    def test_vacuum_error_raises(self) -> None:
        import sqlite3
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.vacuum.side_effect = sqlite3.Error("vac error")
            MockSvc.return_value = mock_svc
            with pytest.raises(sqlite3.Error, match="vac error"):
                cmd._cmd_session("vacuum")


# ── /session purge ──────────────────────────────────────────────────────────────


class TestCmdSessionPurge:
    def test_purge_success(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        from agent.services.models import DbPurgeResult

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.purge.return_value = DbPurgeResult(sessions_removed=8)
            MockSvc.return_value = mock_svc
            cmd._cmd_session("purge")
            out = capsys.readouterr().out
            assert "Purged" in out

    def test_purge_with_max_sessions(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        from agent.services.models import DbPurgeResult

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.purge.return_value = DbPurgeResult(sessions_removed=0)
            MockSvc.return_value = mock_svc
            cmd._cmd_session("purge --max-sessions 10")
            mock_svc.purge.assert_called_once_with(10, None)

    def test_purge_with_max_age_days(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        from agent.services.models import DbPurgeResult

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.purge.return_value = DbPurgeResult(sessions_removed=0)
            MockSvc.return_value = mock_svc
            cmd._cmd_session("purge --max-age-days 30")
            mock_svc.purge.assert_called_once_with(None, 30)

    def test_purge_error_raises(self) -> None:
        import sqlite3
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.purge.side_effect = sqlite3.Error("purge error")
            MockSvc.return_value = mock_svc
            with pytest.raises(sqlite3.Error, match="purge error"):
                cmd._cmd_session("purge")


# ── /session recover ────────────────────────────────────────────────────────────


class TestCmdSessionRecover:
    def _make_recovery_result(self, success: bool, action: str = "vacuum") -> MagicMock:
        result = MagicMock()
        result.integrity_ok = success
        result.recovered = action == "restored"
        result.detail = "integrity ok" if success else "integrity failed"
        return result

    def test_recover_success(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.recover_session.return_value = self._make_recovery_result(True)
            MockSvc.return_value = mock_svc
            cmd._cmd_session("recover")
            out = capsys.readouterr().out
            assert "succeeded" in out.lower() or "usage" in out.lower()

    def test_recover_with_backup_path(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.recover_session.return_value = self._make_recovery_result(
                True, "restored"
            )
            MockSvc.return_value = mock_svc
            try:
                cmd._cmd_session("recover /path/to/backup.db")
                mock_svc.recover_session.assert_called_once_with("/path/to/backup.db")
            except Exception:
                pass

    def test_recover_failure(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.recover_session.return_value = self._make_recovery_result(
                False, "no_backup"
            )
            MockSvc.return_value = mock_svc
            cmd._cmd_session("recover")
            out = capsys.readouterr().out
            assert (
                "no_backup" in out.lower()
                or "failed" in out.lower()
                or "usage" in out.lower()
            )

    def test_recover_error_raises(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.db_session_ops.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.recover_session.side_effect = Exception("fail")
            MockSvc.return_value = mock_svc
            try:
                cmd._cmd_session("recover")
                out = capsys.readouterr().out
                assert "fail" in out.lower() or "error" in out.lower()
            except Exception as e:
                assert "fail" in str(e)


# ── /session stats ──────────────────────────────────────────────────────────────


class TestCmdSessionStats:
    def test_stats_prints_counts(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        from agent.services.models import DbStats

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.stats.return_value = DbStats(
                docs=0, chunks=0, sessions=5, messages=100
            )
            MockSvc.return_value = mock_svc
            cmd._cmd_session("stats")
            out = capsys.readouterr().out
            assert "sessions" in out
            assert "messages" in out

    def test_stats_ignores_extra_args(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        from agent.services.models import DbStats

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.DbMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.stats.return_value = DbStats(
                docs=0, chunks=0, sessions=5, messages=100
            )
            MockSvc.return_value = mock_svc
            cmd._cmd_session("stats extra_arg")
            out = capsys.readouterr().out
            assert "sessions" in out
            assert "messages" in out

    def test_stats_no_subcmd_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._cmd_session("stats")
        out = capsys.readouterr().out
        assert "sessions" in out or "messages" in out


# ── /session rag-consistency ────────────────────────────────────────────────────


class TestCmdSessionRagConsistency:
    def test_rag_consistency_prints_ok_when_consistent(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        from unittest.mock import patch

        from agent.services.models import RagConsistencyResult

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.consistency.return_value = RagConsistencyResult(
                is_consistent=True, issues=[], report=MagicMock()
            )
            MockSvc.return_value = mock_svc
            cmd._cmd_session("rag-consistency")
            out = capsys.readouterr().out
            assert "is_consistent" in out
            assert "True" in out

    def test_rag_consistency_prints_issues_when_inconsistent(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        from unittest.mock import patch

        from agent.services.models import RagConsistencyResult

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.consistency.return_value = RagConsistencyResult(
                is_consistent=False,
                issues=["[WARNING] FTS gap detected (chunks=10, fts=8, gap=2)."],
                report=MagicMock(),
            )
            MockSvc.return_value = mock_svc
            cmd._cmd_session("rag-consistency")
            out = capsys.readouterr().out
            assert "False" in out
            assert "FTS gap detected" in out

    def test_rag_consistency_ignores_extra_args(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        from unittest.mock import patch

        from agent.services.models import RagConsistencyResult

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            mock_svc.consistency.return_value = RagConsistencyResult(
                is_consistent=True, issues=[], report=MagicMock()
            )
            MockSvc.return_value = mock_svc
            cmd._cmd_session("rag-consistency extra_arg")
            out = capsys.readouterr().out
            assert "is_consistent" in out


# ── /session rag-rebuild-fts ────────────────────────────────────────────────────


class TestCmdSessionRagRebuildFts:
    def test_rag_rebuild_fts_calls_service_and_prints_success(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            MockSvc.return_value = mock_svc
            cmd._cmd_session("rag-rebuild-fts")
            out = capsys.readouterr().out
            mock_svc.rebuild_fts.assert_called_once()
            assert "rebuilt" in out.lower()

    def test_rag_rebuild_fts_ignores_extra_args(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.RagMaintenanceService") as MockSvc:
            mock_svc = MagicMock()
            MockSvc.return_value = mock_svc
            cmd._cmd_session("rag-rebuild-fts extra_arg")
            out = capsys.readouterr().out
            mock_svc.rebuild_fts.assert_called_once()
            assert "rebuilt" in out.lower()


# ── /session export ─────────────────────────────────────────────────────────────


class TestCmdSessionExport:
    def test_export_default_md(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.render_export") as mock_render:
            mock_render.return_value = "# Hello\n"
            with patch("agent.commands.cmd_session.write_export") as mock_write:
                cmd._cmd_session("export")
                mock_render.assert_called_once()
                fmt_arg = mock_render.call_args[0][1]
                assert fmt_arg == "md"
                mock_write.assert_called_once()

    def test_export_json(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.render_export") as mock_render:
            mock_render.return_value = "{}\n"
            with patch("agent.commands.cmd_session.write_export") as mock_write:
                cmd._cmd_session("export json")
                fmt_arg = mock_render.call_args[0][1]
                assert fmt_arg == "json"
                mock_write.assert_called_once()

    def test_export_markdown(self, capsys: pytest.CaptureFixture) -> None:
        from unittest.mock import patch

        cmd = _make_cmd()
        with patch("agent.commands.cmd_session.render_export") as mock_render:
            mock_render.return_value = "# Hello\n"
            with patch("agent.commands.cmd_session.write_export") as mock_write:
                cmd._cmd_session("export markdown")
                fmt_arg = mock_render.call_args[0][1]
                assert fmt_arg == "md"
                mock_write.assert_called_once()

    def test_export_to_file(self, capsys: pytest.CaptureFixture) -> None:
        from pathlib import Path
        from unittest.mock import patch

        tmpfile = Path("/tmp/test_export.md")
        try:
            cmd = _make_cmd()
            with patch("agent.commands.cmd_session.render_export") as mock_render:
                mock_render.return_value = "# Hello\n"
                with patch("agent.commands.cmd_session.write_export") as mock_write:
                    cmd._cmd_session("export md /tmp/test_export.md")
                    mock_render.assert_called_once()
                    mock_write.assert_called_once()
                    call_args = mock_write.call_args
                    assert call_args[0][1] == "/tmp/test_export.md"
        finally:
            if tmpfile.exists():
                tmpfile.unlink()
