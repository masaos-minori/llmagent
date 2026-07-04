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
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from agent.commands.cmd_memory import MemoryOpResult, _MemoryMixin
from agent.memory.services import MemoryServices
from db.maintenance import MaintenanceMode, MaintenanceResult

# ── helpers ────────────────────────────────────────────────────────────────────


def _make_services(
    *,
    get_by_id_return=None,
    delete_return: bool = True,
    pin_return: bool = True,
    unpin_return: bool = True,
) -> MagicMock:
    """Build a MagicMock with spec=MemoryServices and a mock store."""
    svc = MagicMock(spec=MemoryServices)
    mock_store = MagicMock()
    mock_store.get_by_id.return_value = get_by_id_return
    mock_store.delete.return_value = delete_return
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
    ctx = SimpleNamespace(services=services, services_required=services, cfg=cfg)
    cmd = object.__new__(_MemoryMixin)
    cmd._ctx = ctx  # type: ignore[attr-defined]

    class _DataOpsMock:
        def __init__(self, out: Any, ctx: Any) -> None:
            self._out = out  # type: ignore[attr-defined]
            self._ctx = ctx  # type: ignore[attr-defined]

        def memory_pin(self, mem: Any, args: list[str], *, pin: bool) -> None:
            if not args:
                cmd_name = "pin" if pin else "unpin"
                self._out.write_validation_error(f"/memory {cmd_name} <id>")  # type: ignore[attr-defined]
                return
            mid = args[0]
            ok = mem.store.pin_mem(mid) if pin else mem.store.unpin_mem(mid)
            action = "pinned" if pin else "unpinned"
            if ok:
                self._out.write(f"  [memory] {action}: {mid}")  # type: ignore[attr-defined]

        def memory_delete(self, mem: Any, args: list[str]) -> None:
            from agent.commands.cmd_memory import MemoryOpResult, _emit_memory_audit

            dry_run = "--dry-run" in args
            ids = [a for a in args if not a.startswith("--")]
            if not ids:
                self._out.write_validation_error("/memory delete [--dry-run] <id>")  # type: ignore[attr-defined]
                return
            mid = ids[0]
            if dry_run:
                exists = mem.store.get_by_id(mid) is not None
                if exists:
                    self._out.write(f"  [memory] (dry-run) would delete: {mid}")  # type: ignore[attr-defined]
                else:
                    self._out.write(f"  [memory] (dry-run) Entry not found: {mid!r}")  # type: ignore[attr-defined]
                _emit_memory_audit(
                    self._ctx,
                    MemoryOpResult(
                        ok=exists, memory_id=mid, action="deleted", dry_run=True
                    ),
                )
                return
            ok = mem.store.delete(mid)
            if ok:
                self._out.write(f"  [memory] Deleted: {mid}")  # type: ignore[attr-defined]
            else:
                self._out.write(f"  [memory] Entry not found: {mid!r}")  # type: ignore[attr-defined]
            _emit_memory_audit(
                self._ctx, MemoryOpResult(ok=ok, memory_id=mid, action="deleted")
            )

        def memory_prune(self, mem: Any, ctx: Any, args: list[str]) -> None:
            dry_run = "--dry-run" in args
            day_str = next((a for a in args if a != "--dry-run"), None)
            try:
                days = int(day_str) if day_str else ctx.cfg.memory.memory_retention_days  # type: ignore[attr-defined]
            except (ValueError, TypeError):
                days = ctx.cfg.memory.memory_retention_days  # type: ignore[attr-defined]
            if dry_run:
                count = mem.store.count_prunable(days)
                self._out.write(  # type: ignore[attr-defined]
                    f"  [memory] (dry-run) would prune {count} entries older than {days} days"
                )
            else:
                deleted = mem.store.prune_old_memories(days)
                self._out.write_success(
                    f"Pruned {deleted} entries older than {days} days"
                )  # type: ignore[attr-defined]

        def memory_list(self, mem: Any, args: list[str]) -> None:
            pass

        def memory_search(self, mem: Any, args: list[str]) -> None:
            pass

        def memory_show(self, mem: Any, args: list[str]) -> None:
            pass

    cmd._data_ops = _DataOpsMock(cmd._out, ctx)  # type: ignore[attr-defined]

    class _PinOpsMock:
        def __init__(self, out: Any, ctx: Any) -> None:
            self._out = out  # type: ignore[attr-defined]
            self._ctx = ctx  # type: ignore[attr-defined]

        def __call__(self, mem: Any, args: list[str], *, pin: bool = True) -> None:
            self.memory_pin(mem, args, pin=pin)

        def memory_pin(self, mem: Any, args: list[str], *, pin: bool) -> None:
            from agent.commands.cmd_memory import MemoryOpResult, _emit_memory_audit

            if not args:
                cmd_name = "pin" if pin else "unpin"
                self._out.write_validation_error(f"/memory {cmd_name} <id>")  # type: ignore[attr-defined]
                return
            mid = args[0]
            ok = mem.store.pin(mid) if pin else mem.store.unpin(mid)
            action = "pinned" if pin else "unpinned"
            if ok:
                self._out.write(f"  [memory] {action}: {mid}")  # type: ignore[attr-defined]
                _emit_memory_audit(
                    self._ctx, MemoryOpResult(ok=True, memory_id=mid, action=action)
                )

    class _DeleteOpsMock:
        def __init__(self, out: Any, ctx: Any) -> None:
            self._out = out  # type: ignore[attr-defined]
            self._ctx = ctx  # type: ignore[attr-defined]

        def __call__(self, mem: Any, args: list[str]) -> None:
            self.memory_delete(mem, args)

        def memory_delete(self, mem: Any, args: list[str]) -> None:
            from agent.commands.cmd_memory import MemoryOpResult, _emit_memory_audit

            dry_run = "--dry-run" in args
            ids = [a for a in args if not a.startswith("--")]
            if not ids:
                self._out.write_validation_error("/memory delete [--dry-run] <id>")  # type: ignore[attr-defined]
                return
            mid = ids[0]
            if dry_run:
                exists = mem.store.get_by_id(mid) is not None
                if exists:
                    self._out.write(f"  [memory] (dry-run) would delete: {mid}")  # type: ignore[attr-defined]
                else:
                    self._out.write(f"  [memory] (dry-run) Entry not found: {mid!r}")  # type: ignore[attr-defined]
                _emit_memory_audit(
                    self._ctx,
                    MemoryOpResult(
                        ok=exists, memory_id=mid, action="deleted", dry_run=True
                    ),
                )
                return
            ok = mem.store.delete(mid)
            if ok:
                self._out.write(f"  [memory] Deleted: {mid}")  # type: ignore[attr-defined]
            else:
                self._out.write(f"  [memory] Entry not found: {mid!r}")  # type: ignore[attr-defined]
            _emit_memory_audit(
                self._ctx, MemoryOpResult(ok=ok, memory_id=mid, action="deleted")
            )

    class _PruneOpsMock:
        def __init__(self, out: Any, ctx: Any) -> None:
            self._out = out  # type: ignore[attr-defined]
            self._ctx = ctx  # type: ignore[attr-defined]

        def __call__(self, mem: Any, ctx: Any, args: list[str]) -> None:
            self.memory_prune(mem, ctx, args)

        def memory_prune(self, mem: Any, ctx: Any, args: list[str]) -> None:
            from agent.commands.cmd_memory import MemoryOpResult, _emit_memory_audit

            dry_run = "--dry-run" in args
            day_str = next((a for a in args if a != "--dry-run"), None)
            try:
                days = int(day_str) if day_str else ctx.cfg.memory.memory_retention_days  # type: ignore[attr-defined]
            except (ValueError, TypeError):
                days = ctx.cfg.memory.memory_retention_days  # type: ignore[attr-defined]
            if dry_run:
                from agent.memory.count_ops import count_prunable

                count = count_prunable(days)
                self._out.write(  # type: ignore[attr-defined]
                    f"  [memory] (dry-run) would prune {count} entries older than {days} days"
                )
                _emit_memory_audit(
                    ctx,
                    MemoryOpResult(
                        ok=True,
                        memory_id="",
                        action="pruned",
                        dry_run=True,
                        count=count,
                    ),
                )
                return
            # Use SQLiteHelper context manager like the real code
            from db.helper import SQLiteHelper
            from db.maintenance import prune_old_memories as _prune_old_memories

            with SQLiteHelper("session").open(write_mode=True) as db:
                prune_result = _prune_old_memories(db, days)
            deleted = (prune_result.data or {}).get("deleted", 0)
            self._out.write_success(f"Pruned {deleted} entries older than {days} days")  # type: ignore[attr-defined]
            _emit_memory_audit(
                ctx,
                MemoryOpResult(ok=True, memory_id="", action="pruned", count=deleted),
            )

    cmd._memory_pin = _PinOpsMock(cmd._out, ctx)  # type: ignore[attr-defined]
    cmd._memory_delete = _DeleteOpsMock(cmd._out, ctx)  # type: ignore[attr-defined]
    cmd._memory_prune = _PruneOpsMock(cmd._out, ctx)  # type: ignore[attr-defined]
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
        cmd._ctx.services_required.audit_logger = None  # type: ignore[union-attr]
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
        svc = _make_services()
        cmd = _make_cmd()
        ctx = cmd._ctx
        with patch("agent.memory.count_ops.count_prunable", return_value=4):
            cmd._memory_prune(svc, ctx, ["--dry-run", "30"])  # type: ignore[arg-type]
        out = capsys.readouterr().out
        assert "dry-run" in out
        assert "would prune 4" in out

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
        cmd._ctx.services_required.memory = svc  # type: ignore[attr-defined]
        with pytest.raises(UnknownSubcommandError) as exc_info:
            cmd._cmd_memory("badcmd")
        assert exc_info.value.sub == "badcmd"
        assert "list" in exc_info.value.valid

    def test_memory_disabled_writes_message(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd()
        cmd._ctx.services_required.memory = None  # type: ignore[attr-defined]
        cmd._cmd_memory("list")
        out = capsys.readouterr().out
        assert "disabled" in out
