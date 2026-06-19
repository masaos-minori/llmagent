"""tests/test_agent_cmd_memory.py
Behavior-lock tests for _MemoryMixin slash-command handlers.

Covers:
  _memory_delete  — normal / not-found / dry-run
  _memory_prune   — normal / dry-run
  _memory_pin     — pin / unpin
  _emit_memory_audit — None guard / audit_logger call
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from agent.commands.cmd_memory import MemoryOpResult, _MemoryMixin
from agent.memory.services import MemoryServices
from agent.memory.store import MemoryStore
from db.maintenance import MaintenanceMode, MaintenanceResult

# ── helpers ────────────────────────────────────────────────────────────────────


def _make_services(
    *,
    get_by_id_return=None,
    delete_return: bool = True,
    count_prunable_return: int = 2,
    pin_return: bool = True,
    unpin_return: bool = True,
) -> MagicMock:
    """Build a MagicMock with spec=MemoryServices and a mock store."""
    svc = MagicMock(spec=MemoryServices)
    mock_store = MagicMock(spec=MemoryStore)
    mock_store.get_by_id.return_value = get_by_id_return
    mock_store.delete.return_value = delete_return
    mock_store.count_prunable.return_value = count_prunable_return
    mock_store.pin.return_value = pin_return
    mock_store.unpin.return_value = unpin_return
    svc.store = mock_store
    return svc


def _make_cmd(*, audit_logger=None, memory_retention_days: int = 30) -> _MemoryMixin:
    """Build a minimal _MemoryMixin with a fake _ctx."""
    audit = audit_logger if audit_logger is not None else MagicMock()
    services = SimpleNamespace(audit_logger=audit)
    cfg = SimpleNamespace(
        memory=SimpleNamespace(memory_retention_days=memory_retention_days)
    )
    ctx = SimpleNamespace(services=services, cfg=cfg)
    cmd = object.__new__(_MemoryMixin)
    cmd._ctx = ctx  # type: ignore[attr-defined]
    return cmd


# ── MemoryOpResult ─────────────────────────────────────────────────────────────


class TestMemoryOpResult:
    def test_defaults(self) -> None:
        r = MemoryOpResult(ok=True, memory_id="abc", action="deleted")
        assert r.dry_run is False
        assert r.count == 0
        assert r.messages == []

    def test_fields_set(self) -> None:
        r = MemoryOpResult(
            ok=False, memory_id="x", action="pruned", dry_run=True, count=5
        )
        assert r.ok is False
        assert r.dry_run is True
        assert r.count == 5


# ── _memory_delete ─────────────────────────────────────────────────────────────


class TestMemoryDelete:
    def test_delete_success(self, capsys: pytest.CaptureFixture) -> None:
        svc = _make_services(delete_return=True)
        cmd = _make_cmd()
        cmd._memory_delete(svc, ["mid-001"])
        out = capsys.readouterr().out
        assert "Deleted" in out
        svc.store.delete.assert_called_once_with("mid-001")

    def test_delete_not_found(self, capsys: pytest.CaptureFixture) -> None:
        svc = _make_services(delete_return=False)
        cmd = _make_cmd()
        cmd._memory_delete(svc, ["mid-999"])
        out = capsys.readouterr().out
        assert "not found" in out.lower()

    def test_delete_no_args(self, capsys: pytest.CaptureFixture) -> None:
        svc = _make_services()
        cmd = _make_cmd()
        cmd._memory_delete(svc, [])
        out = capsys.readouterr().out
        assert "usage" in out.lower()
        svc.store.delete.assert_not_called()

    def test_delete_dry_run_entry_exists(self, capsys: pytest.CaptureFixture) -> None:
        entry = MagicMock()
        svc = _make_services(get_by_id_return=entry)
        cmd = _make_cmd()
        cmd._memory_delete(svc, ["--dry-run", "mid-001"])
        out = capsys.readouterr().out
        assert "dry-run" in out
        assert "would delete" in out
        svc.store.delete.assert_not_called()

    def test_delete_dry_run_entry_missing(self, capsys: pytest.CaptureFixture) -> None:
        svc = _make_services(get_by_id_return=None)
        cmd = _make_cmd()
        cmd._memory_delete(svc, ["--dry-run", "missing-id"])
        out = capsys.readouterr().out
        assert "dry-run" in out
        assert "not found" in out.lower()
        svc.store.delete.assert_not_called()

    def test_delete_calls_audit_logger(self) -> None:
        audit = MagicMock()
        svc = _make_services(delete_return=True)
        cmd = _make_cmd(audit_logger=audit)
        cmd._memory_delete(svc, ["mid-001"])
        audit.info.assert_called_once()
        payload = audit.info.call_args[0][0]
        assert "memory_op" in payload
        assert "deleted" in payload

    def test_delete_audit_logger_none(self) -> None:
        svc = _make_services(delete_return=True)
        cmd = _make_cmd(audit_logger=None)
        cmd._ctx.services.audit_logger = None  # type: ignore[union-attr]
        cmd._memory_delete(svc, ["mid-001"])  # should not raise


# ── _memory_prune ──────────────────────────────────────────────────────────────


class TestMemoryPrune:
    def test_prune_normal(self, capsys: pytest.CaptureFixture) -> None:
        svc = _make_services()
        cmd = _make_cmd()
        ctx = cmd._ctx
        mock_helper = MagicMock()
        mock_helper.__enter__ = MagicMock(return_value=mock_helper)
        mock_helper.__exit__ = MagicMock(return_value=False)
        mock_helper.open.return_value = mock_helper
        prune_result = MaintenanceResult(
            success=True,
            action="prune",
            mode=MaintenanceMode.STRICT,
            data={"deleted": 7},
        )
        with (
            patch("db.helper.SQLiteHelper", return_value=mock_helper),
            patch(
                "db.maintenance.prune_old_memories", return_value=prune_result
            ) as mock_prune,
        ):
            cmd._memory_prune(svc, ctx, ["14"])  # type: ignore[arg-type]
        out = capsys.readouterr().out
        assert "Pruned 7" in out
        mock_prune.assert_called_once()

    def test_prune_uses_config_days(self, capsys: pytest.CaptureFixture) -> None:
        svc = _make_services()
        cmd = _make_cmd(memory_retention_days=60)
        ctx = cmd._ctx
        prune_result = MaintenanceResult(
            success=True,
            action="prune",
            mode=MaintenanceMode.STRICT,
            data={"deleted": 0},
        )
        with (
            patch("db.helper.SQLiteHelper") as mock_helper_cls,
            patch("db.maintenance.prune_old_memories", return_value=prune_result),
        ):
            mock_h = MagicMock()
            mock_h.__enter__ = MagicMock(return_value=mock_h)
            mock_h.__exit__ = MagicMock(return_value=False)
            mock_h.open.return_value = mock_h
            mock_helper_cls.return_value = mock_h
            cmd._memory_prune(svc, ctx, [])  # type: ignore[arg-type]
        # days defaults to memory_retention_days=60; verify output
        out = capsys.readouterr().out
        assert "60 days" in out

    def test_prune_dry_run(self, capsys: pytest.CaptureFixture) -> None:
        svc = _make_services(count_prunable_return=4)
        cmd = _make_cmd()
        ctx = cmd._ctx
        cmd._memory_prune(svc, ctx, ["--dry-run", "30"])  # type: ignore[arg-type]
        out = capsys.readouterr().out
        assert "dry-run" in out
        assert "would prune 4" in out
        svc.store.count_prunable.assert_called_once_with(30)

    def test_prune_calls_audit_logger(self) -> None:
        audit = MagicMock()
        svc = _make_services()
        cmd = _make_cmd(audit_logger=audit)
        ctx = cmd._ctx
        prune_result = MaintenanceResult(
            success=True,
            action="prune",
            mode=MaintenanceMode.STRICT,
            data={"deleted": 3},
        )
        with (
            patch("db.helper.SQLiteHelper") as mock_helper_cls,
            patch("db.maintenance.prune_old_memories", return_value=prune_result),
        ):
            mock_h = MagicMock()
            mock_h.__enter__ = MagicMock(return_value=mock_h)
            mock_h.__exit__ = MagicMock(return_value=False)
            mock_h.open.return_value = mock_h
            mock_helper_cls.return_value = mock_h
            cmd._memory_prune(svc, ctx, ["7"])  # type: ignore[arg-type]
        audit.info.assert_called_once()
        payload = audit.info.call_args[0][0]
        assert "pruned" in payload


# ── _memory_pin ────────────────────────────────────────────────────────────────


class TestMemoryPin:
    def test_pin_success(self, capsys: pytest.CaptureFixture) -> None:
        svc = _make_services(pin_return=True)
        cmd = _make_cmd()
        cmd._memory_pin(svc, ["mid-001"], pin=True)
        out = capsys.readouterr().out
        assert "pinned" in out
        svc.store.pin.assert_called_once_with("mid-001")

    def test_unpin_success(self, capsys: pytest.CaptureFixture) -> None:
        svc = _make_services(unpin_return=True)
        cmd = _make_cmd()
        cmd._memory_pin(svc, ["mid-001"], pin=False)
        out = capsys.readouterr().out
        assert "unpinned" in out
        svc.store.unpin.assert_called_once_with("mid-001")

    def test_pin_calls_audit_logger(self) -> None:
        audit = MagicMock()
        svc = _make_services(pin_return=True)
        cmd = _make_cmd(audit_logger=audit)
        cmd._memory_pin(svc, ["mid-001"], pin=True)
        audit.info.assert_called_once()
        payload = audit.info.call_args[0][0]
        assert "pinned" in payload


class TestMemoryUnknownSubcommand:
    def test_unknown_subcommand_raises(self) -> None:
        from agent.commands.exceptions import UnknownSubcommandError

        svc = _make_services()
        cmd = _make_cmd()
        cmd._ctx.services.memory = svc  # type: ignore[attr-defined]
        with pytest.raises(UnknownSubcommandError) as exc_info:
            cmd._cmd_memory("badcmd")
        assert exc_info.value.sub == "badcmd"
        assert "list" in exc_info.value.valid

    def test_memory_disabled_writes_message(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd()
        cmd._ctx.services.memory = None  # type: ignore[attr-defined]
        cmd._cmd_memory("list")
        out = capsys.readouterr().out
        assert "disabled" in out
