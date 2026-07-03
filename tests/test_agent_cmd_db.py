"""tests/test_agent_cmd_db.py
Behavior-lock tests for _DbMixin slash-command handlers.
"""

from __future__ import annotations

import asyncio
from typing import Any

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.commands.cmd_db import _DbMixin
from agent.commands.utils import parse_flag_int as _parse_flag_int
from agent.commands.utils import parse_flag_str as _parse_flag_str
from db.maintenance import MaintenanceMode, MaintenanceResult
from db.models import WalCheckpointCounts


def _run_db(cmd: _DbMixin, args: str) -> None:
    """Synchronously invoke the async _cmd_db handler."""
    asyncio.run(cmd._cmd_db(args))


def _make_cmd(*, delete_doc_return: bool = True) -> _DbMixin:
    session = MagicMock()
    session.delete_document.return_value = delete_doc_return
    tools = AsyncMock()
    services = SimpleNamespace(tools=tools)
    ctx = SimpleNamespace(session=session, services=services)
    cmd = object.__new__(_DbMixin)
    cmd._ctx = ctx  # type: ignore[attr-defined]

    class _RagOpsMock:
        def __init__(self, out: Any, cmd: Any) -> None:
            self._out = out  # type: ignore[attr-defined]
            self._cmd = cmd  # type: ignore[attr-defined]

        async def clean(self, rest: str) -> None:
            url = rest.strip()
            if not url:
                self._out.write_validation_error("/db rag clean <url>")  # type: ignore[attr-defined]
                return
            try:
                result = await self._cmd._ctx.services.tools.execute(  # type: ignore[attr-defined]
                    "rag_delete_document", {"url": url}
                )
                if result.is_error:
                    self._out.write_error(result.output)  # type: ignore[attr-defined]
                else:
                    self._out.write(result.output)  # type: ignore[attr-defined]
            except Exception as e:  # noqa: BLE001
                self._out.write_error(f"rag-pipeline-mcp unavailable: {e}")  # type: ignore[attr-defined]

        async def list_urls(self, rest: str) -> None:
            from agent.commands.utils import parse_command_args, parse_flag_int

            tokens = rest.split()
            parsed = parse_command_args(tokens)
            lang_raw = parsed.flags.get("lang")
            lang = str(lang_raw) if lang_raw in ("ja", "en") else None
            limit = parse_flag_int(tokens, "--limit") or 20
            args_dict = {"limit": limit}
            if lang:
                args_dict["lang"] = lang
            tools = self._cmd._ctx.services.tools  # type: ignore[attr-defined]
            if tools is None:
                self._out.write_error(  # type: ignore[attr-defined]
                    "rag-pipeline-mcp unavailable: tool executor not initialized"
                )
                return
            result = await tools.execute("rag_list_documents", args_dict)  # type: ignore[attr-defined]
            if result.is_error:
                self._out.write_error(result.output)  # type: ignore[attr-defined]
            else:
                self._out.write(result.output)  # type: ignore[attr-defined]

        async def rebuild_fts(self) -> None:
            from agent.services.rag_maintenance_service import RagMaintenanceService

            try:
                RagMaintenanceService().rebuild_fts()
                self._out.write("  [db] FTS5 index rebuilt")  # type: ignore[attr-defined]
            except Exception as e:
                self._out.write_error(f"  [db] rebuild failed: {e}")  # type: ignore[attr-defined]
                raise

        async def vec_rebuild(self) -> None:
            pass

        async def reconcile_url(self) -> None:
            pass

        async def recover(self, url: str | None = None) -> None:
            from agent.services.rag_maintenance_service import RagMaintenanceService

            svc = RagMaintenanceService()
            try:
                result = svc.recover(url)
                if result.integrity_ok:
                    self._out.write_success(f"Recovery succeeded: {result.detail} [RAG]")  # type: ignore[attr-defined]
                else:
                    self._out.write_no_data(f"Recovery failed: {result.detail} [RAG]")  # type: ignore[attr-defined]
            except Exception as e:
                self._out.write_error(f"  [db] recover failed: {e}")  # type: ignore[attr-defined]
                raise

        async def consistency(self) -> None:
            pass

    cmd._rag_ops = _RagOpsMock(cmd._out, cmd)  # type: ignore[attr-defined]

    class _SessionOpsMock:
        def __init__(self, out: Any, cmd: Any) -> None:
            self._out = out  # type: ignore[attr-defined]
            self._cmd = cmd  # type: ignore[attr-defined]

        async def health(self) -> None:
            from agent.services.db_maintenance_service import DbMaintenanceService

            svc = DbMaintenanceService()
            try:
                result = svc.health()
                self._out.write_kv(  # type: ignore[attr-defined]
                    [
                        ("integrity_ok", str(result.integrity_ok)),
                        ("db_size", f"{result.size_bytes:,} bytes"),
                        ("target", "Session"),
                    ]
                )
            except Exception as e:
                self._out.write_error(f"  [db] health failed: {e}")  # type: ignore[attr-defined]
                raise

        async def checkpoint(self, mode: str | None = None) -> None:
            from agent.services.db_maintenance_service import DbMaintenanceService

            svc = DbMaintenanceService()
            try:
                result = svc.checkpoint(mode)
                self._out.write(f"  [db] checkpoint complete mode={result.mode} pages={result.pages_written}")  # type: ignore[attr-defined]
            except Exception as e:
                self._out.write_error(f"  [db] checkpoint failed: {e}")  # type: ignore[attr-defined]
                raise

        async def vacuum(self) -> None:
            from agent.services.db_maintenance_service import DbMaintenanceService

            svc = DbMaintenanceService()
            try:
                svc.vacuum()
                self._out.write("  [db] vacuum complete")  # type: ignore[attr-defined]
            except Exception as e:
                self._out.write_error(f"  [db] vacuum failed: {e}")  # type: ignore[attr-defined]
                raise

        async def purge(self, rest: str) -> None:
            from agent.services.db_maintenance_service import DbMaintenanceService

            from agent.commands.utils import parse_command_args

            svc = DbMaintenanceService()
            try:
                tokens = rest.strip().split() if rest.strip() else []
                parsed = parse_command_args(tokens)
                max_sessions = parsed.flags.get("max-sessions")
                max_age_days = parsed.flags.get("max-age-days")
                result = svc.purge(
                    int(max_sessions) if max_sessions is not None else None,
                    int(max_age_days) if max_age_days is not None else None,
                )
                self._out.write_success(f"Purged {result.sessions_removed} sessions")  # type: ignore[attr-defined]
            except Exception as e:
                self._out.write_error(f"  [db] purge failed: {e}")  # type: ignore[attr-defined]
                raise

        async def recover(self, url: str | None = None) -> None:
            from agent.services.db_maintenance_service import DbMaintenanceService

            svc = DbMaintenanceService()
            try:
                result = svc.recover_session(url)
                if result.integrity_ok:
                    self._out.write_success(f"Recovery succeeded: {result.detail} [Session]")  # type: ignore[attr-defined]
                else:
                    self._out.write_no_data(f"Recovery failed: {result.detail} [Session]")  # type: ignore[attr-defined]
            except Exception as e:
                if "detail" not in str(e):
                    self._out.write_error(f"  [db] recover failed: {e}")  # type: ignore[attr-defined]
                raise

    cmd._session_ops = _SessionOpsMock(cmd._out, cmd)  # type: ignore[attr-defined]
    return cmd


class TestCmdDbClean:
    def _make_tool_result(self, output: str, is_error: bool = False) -> MagicMock:
        r = MagicMock()
        r.is_error = is_error
        r.output = output
        return r

    def test_clean_success(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._ctx.services.tools.execute = AsyncMock(
            return_value=self._make_tool_result("Deleted: http://example.com")
        )
        _run_db(cmd, "rag clean http://example.com")
        assert "deleted" in capsys.readouterr().out.lower()

    def test_clean_not_found(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._ctx.services.tools.execute = AsyncMock(
            return_value=self._make_tool_result(
                "not found: http://example.com", is_error=True
            )
        )
        _run_db(cmd, "rag clean http://example.com")
        assert "not found" in capsys.readouterr().out.lower()

    def test_clean_empty_url_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "rag clean")
        assert "usage" in capsys.readouterr().out.lower()
        cmd._ctx.services.tools.execute.assert_not_awaited()


class TestCmdDbStats:
    def test_stats_error_raises(self) -> None:
        cmd = _make_cmd()
        with patch(
            "agent.services.rag_maintenance_service.SQLiteHelper",
            side_effect=Exception("db error"),
        ):
            with pytest.raises(Exception, match="db error"):
                _run_db(cmd, "rag stats")


class TestCmdDbUnknownSubcommand:
    def test_unknown_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "unknown")
        assert "usage" in capsys.readouterr().out.lower()

    def test_empty_args_shows_usage(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "")
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
        with patch(
            "agent.services.rag_maintenance_service.SQLiteHelper"
        ) as MockHelperRag:
            mock_db_rag = MagicMock()
            mock_db_rag.fetchall.side_effect = [
                [{"n": 100}],
                [{"n": 500}],
            ]
            open_mock_rag = MagicMock()
            open_mock_rag.return_value.__enter__ = MagicMock(return_value=mock_db_rag)
            open_mock_rag.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock_rag = MagicMock()
            helper_mock_rag.open = open_mock_rag
            MockHelperRag.return_value = helper_mock_rag
            with patch(
                "agent.services.db_maintenance_service.SQLiteHelper"
            ) as MockHelperSession:
                mock_db_session = MagicMock()
                mock_db_session.fetchall.side_effect = [
                    [{"n": 10}],
                    [{"n": 200}],
                ]
                open_mock_session = MagicMock()
                open_mock_session.return_value.__enter__ = MagicMock(
                    return_value=mock_db_session
                )
                open_mock_session.return_value.__exit__ = MagicMock(return_value=False)
                helper_mock_session = MagicMock()
                helper_mock_session.open = open_mock_session
                MockHelperSession.return_value = helper_mock_session
                _run_db(cmd, "rag stats")
                out = capsys.readouterr().out
                assert "documents" in out
                assert "chunks" in out
                assert "100" in out

    def test_stats_sqlite_error_raises(self) -> None:
        import sqlite3

        cmd = _make_cmd()
        with patch("agent.services.rag_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            mock_db.fetchall.side_effect = sqlite3.Error("db error")
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            with pytest.raises(sqlite3.Error, match="db error"):
                _run_db(cmd, "rag stats")


# ── _db_list_urls ─────────────────────────────────────────────────────────────


class TestDbListUrls:
    def _make_result(self, output: str, is_error: bool = False) -> MagicMock:
        r = MagicMock()
        r.is_error = is_error
        r.output = output
        return r

    def test_list_urls_tools_none_shows_error(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd()
        cmd._ctx.services.tools = None
        _run_db(cmd, "rag urls")
        out = capsys.readouterr().out
        assert "unavailable" in out.lower()

    def test_list_urls_shows_output(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        cmd._ctx.services.tools.execute = AsyncMock(
            return_value=self._make_result("http://example.com/page1  [ja]")
        )
        _run_db(cmd, "rag urls")
        out = capsys.readouterr().out
        assert "http://example.com/page1" in out

    def test_list_urls_with_lang_filter(self) -> None:
        cmd = _make_cmd()
        cmd._ctx.services.tools.execute = AsyncMock(return_value=self._make_result(""))
        _run_db(cmd, "rag urls --lang ja")
        cmd._ctx.services.tools.execute.assert_awaited_once_with(
            "rag_list_documents", {"limit": 20, "lang": "ja"}
        )

    def test_list_urls_with_limit_filter(self) -> None:
        cmd = _make_cmd()
        cmd._ctx.services.tools.execute = AsyncMock(return_value=self._make_result(""))
        _run_db(cmd, "rag urls --limit 50")
        cmd._ctx.services.tools.execute.assert_awaited_once_with(
            "rag_list_documents", {"limit": 50}
        )

    def test_list_urls_error_result_shows_error(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd()
        cmd._ctx.services.tools.execute = AsyncMock(
            return_value=self._make_result("service error", is_error=True)
        )
        _run_db(cmd, "rag urls")
        out = capsys.readouterr().out
        assert "service error" in out


# ── _db_rebuild_fts ───────────────────────────────────────────────────────────


class TestDbRebuildFts:
    def test_rebuild_fts_success(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch("agent.services.rag_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            _run_db(cmd, "rag rebuild-fts")
            out = capsys.readouterr().out
            assert "rebuilt" in out.lower()

    def test_rebuild_fts_error_raises(self) -> None:
        import sqlite3

        cmd = _make_cmd()
        with patch("agent.services.rag_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            mock_db.execute.side_effect = sqlite3.Error("fts error")
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            with pytest.raises(sqlite3.Error, match="fts error"):
                _run_db(cmd, "rag rebuild-fts")


# ── _db_health ────────────────────────────────────────────────────────────────


class TestDbHealth:
    def test_health_prints_metrics(self, capsys: pytest.CaptureFixture) -> None:
        from db.models import DbHealthMetrics

        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            mock_db.health_check.return_value = DbHealthMetrics(
                journal_mode="wal",
                integrity="ok",
                page_count=100,
                page_size=4096,
                freelist_count=0,
                db_size_bytes=10240,
            )
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            _run_db(cmd, "session health")
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
                _run_db(cmd, "session health")


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
                mock_cp.return_value = WalCheckpointCounts(
                    busy=0, log_size=10, pages_checkpointed=10
                )
                _run_db(cmd, "session checkpoint")
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
                mock_cp.return_value = WalCheckpointCounts(
                    busy=0, log_size=5, pages_checkpointed=5
                )
                _run_db(cmd, "session checkpoint FULL")
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
                _run_db(cmd, "session vacuum")
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
                    _run_db(cmd, "session vacuum")


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
                mock_purge.return_value = MaintenanceResult(
                    success=True,
                    action="purge",
                    mode=MaintenanceMode.STRICT,
                    data={"age_deleted": 5, "count_deleted": 3},
                )
                _run_db(cmd, "session purge")
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
                mock_purge.return_value = MaintenanceResult(
                    success=True,
                    action="purge",
                    mode=MaintenanceMode.STRICT,
                    data={"age_deleted": 0, "count_deleted": 0},
                )
                _run_db(cmd, "session purge --max-sessions 10")
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
                mock_purge.return_value = MaintenanceResult(
                    success=True,
                    action="purge",
                    mode=MaintenanceMode.STRICT,
                    data={"age_deleted": 0, "count_deleted": 0},
                )
                _run_db(cmd, "session purge --max-age-days 30")
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
                    _run_db(cmd, "session purge")


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
            "agent.services.rag_maintenance_service.recover_corruption"
        ) as mock_rec:
            mock_rec.return_value = self._make_recovery_result(True)
            _run_db(cmd, "rag recover")
            out = capsys.readouterr().out
            assert "succeeded" in out.lower()

    def test_recover_with_backup_path(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch(
            "agent.services.rag_maintenance_service.recover_corruption"
        ) as mock_rec:
            mock_rec.return_value = self._make_recovery_result(True, "restored")
            _run_db(cmd, "rag recover /path/to/backup.db")
            mock_rec.assert_called_once_with("/path/to/backup.db")

    def test_recover_failure(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch(
            "agent.services.rag_maintenance_service.recover_corruption"
        ) as mock_rec:
            mock_rec.return_value = self._make_recovery_result(False, "no_backup")
            _run_db(cmd, "rag recover")
            out = capsys.readouterr().out
            assert "failed" in out.lower()

    def test_recover_error_raises(self) -> None:
        cmd = _make_cmd()
        with patch(
            "agent.services.rag_maintenance_service.recover_corruption",
            side_effect=Exception("fail"),
        ):
            with pytest.raises(Exception, match="fail"):
                _run_db(cmd, "rag recover")


# ── _db_help ──────────────────────────────────────────────────────────────────


class TestDbHelp:
    def test_help_shows_rag_and_session_labels(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "help")
        out = capsys.readouterr().out
        assert "RAG" in out
        assert "Session" in out

    def test_help_shows_scoped_forms(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "help")
        out = capsys.readouterr().out
        assert "rag stats" in out
        assert "session stats" in out

    def test_help_shows_workflow_note(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "help")
        out = capsys.readouterr().out
        assert "Session" in out


# ── scoped /db rag ... ────────────────────────────────────────────────────────


class TestCmdDbRagScope:
    def test_rag_stats_calls_rag_stats(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with patch("agent.services.rag_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            mock_db.fetchall.side_effect = [
                [{"n": 50}],
                [{"n": 200}],
            ]
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            _run_db(cmd, "rag stats")
            out = capsys.readouterr().out
            assert "documents" in out
            assert "RAG" in out

    def test_rag_unknown_shows_rag_help(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "rag unknown_subcmd")
        out = capsys.readouterr().out
        assert "/db rag" in out

    def test_rag_no_subcmd_shows_rag_help(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "rag")
        out = capsys.readouterr().out
        assert "/db rag" in out


# ── scoped /db session ... ────────────────────────────────────────────────────


class TestCmdDbSessionScope:
    def test_session_stats_calls_session_stats(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd()
        with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
            mock_db = MagicMock()
            mock_db.fetchall.side_effect = [
                [{"n": 5}],
                [{"n": 100}],
            ]
            open_mock = MagicMock()
            open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
            open_mock.return_value.__exit__ = MagicMock(return_value=False)
            helper_mock = MagicMock()
            helper_mock.open = open_mock
            MockHelper.return_value = helper_mock
            _run_db(cmd, "session stats")
            out = capsys.readouterr().out
            assert "sessions" in out
            assert "Session" in out

    def test_session_unknown_shows_session_help(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "session unknown_subcmd")
        out = capsys.readouterr().out
        assert "/db session" in out

    def test_session_no_subcmd_shows_session_help(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "session")
        out = capsys.readouterr().out
        assert "/db session" in out


# ── backward compatibility ────────────────────────────────────────────────────


class TestCmdDbBackwardCompat:
    def test_session_recover_success(self, capsys: pytest.CaptureFixture) -> None:
        from db.models import RecoveryResult

        cmd = _make_cmd()
        with patch(
            "agent.services.db_maintenance_service.recover_corruption",
            return_value=RecoveryResult(success=True, action="ok", detail="ok"),
        ):
            _run_db(cmd, "session recover")
            out = capsys.readouterr().out
            assert "Session" in out
            assert "succeeded" in out.lower()

    def test_session_recover_failure(self, capsys: pytest.CaptureFixture) -> None:
        from db.models import RecoveryResult

        cmd = _make_cmd()
        with patch(
            "agent.services.db_maintenance_service.recover_corruption",
            return_value=RecoveryResult(
                success=False, action="failed", detail="corrupted"
            ),
        ):
            _run_db(cmd, "session recover")
            out = capsys.readouterr().out
            assert "Session" in out
            assert "failed" in out.lower()

    def test_flat_stats_still_works(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        with (
            patch(
                "agent.services.rag_maintenance_service.SQLiteHelper"
            ) as MockHelperRag,
            patch(
                "agent.services.db_maintenance_service.SQLiteHelper"
            ) as MockHelperSession,
        ):
            for MockHelper in (MockHelperRag, MockHelperSession):
                mock_db = MagicMock()
                mock_db.fetchall.side_effect = [[{"n": 1}], [{"n": 2}]]
                open_mock = MagicMock()
                open_mock.return_value.__enter__ = MagicMock(return_value=mock_db)
                open_mock.return_value.__exit__ = MagicMock(return_value=False)
                helper_mock = MagicMock()
                helper_mock.open = open_mock
                MockHelper.return_value = helper_mock
            _run_db(cmd, "rag stats")
            out = capsys.readouterr().out
            assert "documents" in out


# ── flat DB aliases are invalid ────────────────────────────────────────────────


class TestCmdDbFlatAliasesInvalid:
    def test_flat_urls_is_invalid(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "urls")
        out = capsys.readouterr().out
        assert "usage" in out.lower()
        assert "/db rag" in out or "/db session" in out

    def test_flat_clean_is_invalid(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "clean http://example.com")
        out = capsys.readouterr().out
        assert "usage" in out.lower()
        assert "/db rag" in out or "/db session" in out

    def test_flat_rebuild_fts_is_invalid(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "rebuild-fts")
        out = capsys.readouterr().out
        assert "usage" in out.lower()
        assert "/db rag" in out or "/db session" in out

    def test_flat_recover_is_invalid(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "recover")
        out = capsys.readouterr().out
        assert "usage" in out.lower()
        assert "/db rag" in out or "/db session" in out

    def test_flat_recover_with_backup_is_invalid(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "recover /path/to/backup.db")
        out = capsys.readouterr().out
        assert "usage" in out.lower()
        assert "/db rag" in out or "/db session" in out

    def test_flat_stats_is_invalid(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "stats")
        out = capsys.readouterr().out
        assert "usage" in out.lower()
        assert "/db rag" in out or "/db session" in out

    def test_flat_health_is_invalid(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "health")
        out = capsys.readouterr().out
        assert "usage" in out.lower()
        assert "/db rag" in out or "/db session" in out

    def test_flat_checkpoint_is_invalid(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "checkpoint")
        out = capsys.readouterr().out
        assert "usage" in out.lower()
        assert "/db rag" in out or "/db session" in out

    def test_flat_vacuum_is_invalid(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "vacuum")
        out = capsys.readouterr().out
        assert "usage" in out.lower()
        assert "/db rag" in out or "/db session" in out

    def test_flat_purge_is_invalid(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "purge")
        out = capsys.readouterr().out
        assert "usage" in out.lower()
        assert "/db rag" in out or "/db session" in out

    def test_flat_consistency_is_invalid(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd()
        _run_db(cmd, "consistency")
        out = capsys.readouterr().out
        assert "usage" in out.lower()
        assert "/db rag" in out or "/db session" in out
