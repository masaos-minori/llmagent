"""tests/test_agent_cmd_db.py
Behavior-lock tests for _DbMixin slash-command handlers.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from agent.commands.cmd_db import _DbMixin
from agent.commands.utils import parse_flag_int as _parse_flag_int
from agent.commands.utils import parse_flag_str as _parse_flag_str


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
        assert "usage" in capsys.readouterr().out.lower()
        cmd._ctx.session.delete_document.assert_not_called()


class TestCmdDbStats:
    def test_stats_error_raises(self) -> None:
        cmd = _make_cmd()
        with patch(
            "agent.services.db_maintenance_service.SQLiteHelper",
            side_effect=Exception("db error"),
        ):
            with pytest.raises(Exception, match="db error"):
                cmd._cmd_db("stats")


class TestCmdDbUnknownSubcommand:
    def test_unknown_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._cmd_db("unknown")
        assert "usage" in capsys.readouterr().out.lower()

    def test_empty_args_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._cmd_db("")
        assert "usage" in capsys.readouterr().out.lower()


# ── _parse_flag_int ───────────────────────────────────────────────────────────


class TestParseFlagInt:
    def test_parse_flag_int_found(self) -> None:
        tokens = ["--limit", "10", "--lang", "ja"]
        result = _parse_flag_int(tokens, "--limit")
        assert result == 10

    def test_parse_flag_int_not_found(self) -> None:
        tokens = ["--lang", "ja"]
        result = _parse_flag_int(tokens, "--limit")
        assert result is None

    def test_parse_flag_int_invalid_value(self) -> None:
        tokens = ["--limit", "abc"]
        result = _parse_flag_int(tokens, "--limit")
        assert result is None

    def test_parse_flag_int_at_end_no_value(self) -> None:
        tokens = ["--limit"]
        result = _parse_flag_int(tokens, "--limit")
        assert result is None


# ── _parse_flag_str ───────────────────────────────────────────────────────────


class TestParseFlagStr:
    def test_parse_flag_str_found(self) -> None:
        tokens = ["--lang", "ja", "--limit", "10"]
        result = _parse_flag_str(tokens, "--lang")
        assert result == "ja"

    def test_parse_flag_str_not_found(self) -> None:
        tokens = ["--limit", "10"]
        result = _parse_flag_str(tokens, "--lang")
        assert result is None

    def test_parse_flag_str_at_end_no_value(self) -> None:
        tokens = ["--lang"]
        result = _parse_flag_str(tokens, "--lang")
        assert result is None


# ── _db_stats ─────────────────────────────────────────────────────────────────


class TestDbStats:
    def test_stats_prints_counts(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            mock_db.fetchall.side_effect = [
                [{"n": 100}],
                [{"n": 500}],
                [{"n": 10}],
                [{"n": 200}],
            ]
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            cmd._cmd_db("stats")
            out = capsys.readouterr().out
            assert "documents" in out
            assert "chunks" in out
            assert "100" in out

    def test_stats_sqlite_error_raises(self) -> None:
        import sqlite3

        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            mock_db.fetchall.side_effect = sqlite3.Error("db error")
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            with pytest.raises(sqlite3.Error, match="db error"):
                cmd._cmd_db("stats")


# ── _db_list_urls ─────────────────────────────────────────────────────────────


class TestDbListUrls:
    def test_list_urls_empty(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._ctx.session.list_documents.return_value = []
        cmd._cmd_db("urls")
        out = capsys.readouterr().out
        assert "No documents found" in out

    def test_list_urls_shows_documents(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        rows = [
            {
                "url": "http://example.com/page1",
                "lang": "ja",
                "chunk_count": 10,
                "fetched_at": "2026-01-01",
            }
        ]
        cmd._ctx.session.list_documents.return_value = rows
        cmd._cmd_db("urls")
        out = capsys.readouterr().out
        assert "http://example.com/page1" in out

    def test_list_urls_with_lang_filter(self) -> None:
        cmd = _make_cmd()
        cmd._ctx.session.list_documents.return_value = []
        cmd._cmd_db("urls --lang ja")
        cmd._ctx.session.list_documents.assert_called_once_with("ja", 20)

    def test_list_urls_with_limit_filter(self) -> None:
        cmd = _make_cmd()
        cmd._ctx.session.list_documents.return_value = []
        cmd._cmd_db("urls --limit 50")
        cmd._ctx.session.list_documents.assert_called_once_with(None, 50)

    def test_list_urls_truncates_long_url(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        long_url = "http://example.com/" + "x" * 100
        rows = [
            {
                "url": long_url,
                "lang": "en",
                "chunk_count": 5,
                "fetched_at": "2026-01-01",
            }
        ]
        cmd._ctx.session.list_documents.return_value = rows
        cmd._cmd_db("urls")
        out = capsys.readouterr().out
        assert "..." in out


# ── _db_rebuild_fts ───────────────────────────────────────────────────────────


class TestDbRebuildFts:
    def test_rebuild_fts_success(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            cmd._cmd_db("rebuild-fts")
            out = capsys.readouterr().out
            assert "rebuilt" in out.lower()

    def test_rebuild_fts_error_raises(self) -> None:
        import sqlite3

        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            mock_db.execute.side_effect = sqlite3.Error("fts error")
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            with pytest.raises(sqlite3.Error, match="fts error"):
                cmd._cmd_db("rebuild-fts")


# ── _db_health ────────────────────────────────────────────────────────────────


class TestDbHealth:
    def test_health_prints_metrics(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            mock_db.health_check.return_value = {
                "journal_mode": "wal",
                "integrity": "ok",
                "page_count": 100,
                "page_size": 4096,
                "freelist_count": 0,
                "db_size_bytes": 10240,
            }
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            cmd._cmd_db("health")
            out = capsys.readouterr().out
            assert "integrity_ok" in out
            assert "True" in out

    def test_health_error_raises(self) -> None:
        import sqlite3

        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            mock_db.health_check.side_effect = sqlite3.Error("health error")
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            with pytest.raises(sqlite3.Error, match="health error"):
                cmd._cmd_db("health")


# ── _db_checkpoint ────────────────────────────────────────────────────────────


class TestDbCheckpoint:
    def test_checkpoint_success(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            with patch(
                "agent.services.db_maintenance_service.checkpoint_wal"
            ) as mock_cp:
                mock_cp.return_value = {
                    "busy": 0,
                    "pages_in_wal": 10,
                    "pages_checkpointed": 10,
                }
                cmd._cmd_db("checkpoint")
                out = capsys.readouterr().out
                assert "complete" in out.lower()

    def test_checkpoint_with_mode(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            with patch(
                "agent.services.db_maintenance_service.checkpoint_wal"
            ) as mock_cp:
                mock_cp.return_value = {
                    "busy": 0,
                    "pages_in_wal": 5,
                    "pages_checkpointed": 5,
                }
                cmd._cmd_db("checkpoint FULL")
                out = capsys.readouterr().out
                assert "complete" in out.lower()


# ── _db_vacuum ────────────────────────────────────────────────────────────────


class TestDbVacuum:
    def test_vacuum_success(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            with patch("agent.services.db_maintenance_service.vacuum_db"):
                cmd._cmd_db("vacuum")
                out = capsys.readouterr().out
                assert "complete" in out.lower()

    def test_vacuum_error_raises(self) -> None:
        import sqlite3

        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            with patch(
                "agent.services.db_maintenance_service.vacuum_db",
                side_effect=sqlite3.Error("vac error"),
            ):
                with pytest.raises(sqlite3.Error, match="vac error"):
                    cmd._cmd_db("vacuum")


# ── _db_purge ─────────────────────────────────────────────────────────────────


class TestDbPurge:
    def test_purge_success(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            with patch(
                "agent.services.db_maintenance_service.purge_old_sessions"
            ) as mock_purge:
                mock_purge.return_value = {"age_deleted": 5, "count_deleted": 3}
                cmd._cmd_db("purge")
                out = capsys.readouterr().out
                assert "Purged" in out

    def test_purge_with_max_sessions(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            with patch(
                "agent.services.db_maintenance_service.purge_old_sessions"
            ) as mock_purge:
                mock_purge.return_value = {"age_deleted": 0, "count_deleted": 0}
                cmd._cmd_db("purge --max-sessions 10")
                mock_purge.assert_called_once()
                call_args = mock_purge.call_args
                assert call_args[0][1] is not None

    def test_purge_with_max_age_days(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            with patch(
                "agent.services.db_maintenance_service.purge_old_sessions"
            ) as mock_purge:
                mock_purge.return_value = {"age_deleted": 0, "count_deleted": 0}
                cmd._cmd_db("purge --max-age-days 30")
                mock_purge.assert_called_once()

    def test_purge_error_raises(self) -> None:
        import sqlite3

        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            with patch(
                "agent.services.db_maintenance_service.purge_old_sessions",
                side_effect=sqlite3.Error("purge error"),
            ):
                with pytest.raises(sqlite3.Error, match="purge error"):
                    cmd._cmd_db("purge")


# ── _db_recover ───────────────────────────────────────────────────────────────


class TestDbRecover:
    def _make_recovery_result(self, success: bool, action: str = "vacuum") -> MagicMock:
        result = MagicMock()
        result.success = success
        result.action = action
        result.detail = "integrity ok" if success else "integrity failed"
        return result

    def test_recover_success(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch(
            "agent.services.db_maintenance_service.recover_corruption"
        ) as mock_rec:
            mock_rec.return_value = self._make_recovery_result(True)
            cmd._cmd_db("recover")
            out = capsys.readouterr().out
            assert "succeeded" in out.lower()

    def test_recover_with_backup_path(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch(
            "agent.services.db_maintenance_service.recover_corruption"
        ) as mock_rec:
            mock_rec.return_value = self._make_recovery_result(True, "restored")
            cmd._cmd_db("recover /path/to/backup.db")
            mock_rec.assert_called_once_with("/path/to/backup.db")

    def test_recover_failure(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch(
            "agent.services.db_maintenance_service.recover_corruption"
        ) as mock_rec:
            mock_rec.return_value = self._make_recovery_result(False, "no_backup")
            cmd._cmd_db("recover")
            out = capsys.readouterr().out
            assert "failed" in out.lower()

    def test_recover_error_raises(self) -> None:
        cmd = _make_cmd()
        with patch(
            "agent.services.db_maintenance_service.recover_corruption",
            side_effect=Exception("fail"),
        ):
            with pytest.raises(Exception, match="fail"):
                cmd._cmd_db("recover")
