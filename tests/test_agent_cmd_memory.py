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
from unittest.mock import MagicMock

import pytest
from agent.commands.cmd_memory import MemoryOpResult, _MemoryMixin
from agent.memory.layer import MemoryLayer

# ── helpers ────────────────────────────────────────────────────────────────────


def _make_layer(
    *,
    get_entry_return=None,
    delete_return: bool = True,
    prune_return: int = 3,
    count_prunable_return: int = 2,
    pin_return: bool = True,
    unpin_return: bool = True,
) -> MagicMock:
    # spec=MemoryLayer により isinstance チェックを通過させる
    layer = MagicMock(spec=MemoryLayer)
    layer.get_entry.return_value = get_entry_return
    layer.delete_entry.return_value = delete_return
    layer.prune.return_value = prune_return
    layer.count_prunable.return_value = count_prunable_return
    layer.pin_entry.return_value = pin_return
    layer.unpin_entry.return_value = unpin_return
    return layer


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
        layer = _make_layer(delete_return=True)
        cmd = _make_cmd()
        cmd._memory_delete(layer, ["mid-001"])
        out = capsys.readouterr().out
        assert "Deleted" in out
        layer.delete_entry.assert_called_once_with("mid-001")

    def test_delete_not_found(self, capsys: pytest.CaptureFixture) -> None:
        layer = _make_layer(delete_return=False)
        cmd = _make_cmd()
        cmd._memory_delete(layer, ["mid-999"])
        out = capsys.readouterr().out
        assert "not found" in out.lower()

    def test_delete_no_args(self, capsys: pytest.CaptureFixture) -> None:
        layer = _make_layer()
        cmd = _make_cmd()
        cmd._memory_delete(layer, [])
        out = capsys.readouterr().out
        assert "Usage" in out
        layer.delete_entry.assert_not_called()

    def test_delete_dry_run_entry_exists(self, capsys: pytest.CaptureFixture) -> None:
        entry = MagicMock()
        layer = _make_layer(get_entry_return=entry)
        cmd = _make_cmd()
        cmd._memory_delete(layer, ["--dry-run", "mid-001"])
        out = capsys.readouterr().out
        assert "dry-run" in out
        assert "would delete" in out
        layer.delete_entry.assert_not_called()

    def test_delete_dry_run_entry_missing(self, capsys: pytest.CaptureFixture) -> None:
        layer = _make_layer(get_entry_return=None)
        cmd = _make_cmd()
        cmd._memory_delete(layer, ["--dry-run", "missing-id"])
        out = capsys.readouterr().out
        assert "dry-run" in out
        assert "not found" in out.lower()
        layer.delete_entry.assert_not_called()

    def test_delete_calls_audit_logger(self) -> None:
        audit = MagicMock()
        layer = _make_layer(delete_return=True)
        cmd = _make_cmd(audit_logger=audit)
        cmd._memory_delete(layer, ["mid-001"])
        audit.info.assert_called_once()
        payload = audit.info.call_args[0][0]
        assert "memory_op" in payload
        assert "deleted" in payload

    def test_delete_audit_logger_none(self) -> None:
        layer = _make_layer(delete_return=True)
        cmd = _make_cmd(audit_logger=None)
        cmd._ctx.services.audit_logger = None  # type: ignore[union-attr]
        cmd._memory_delete(layer, ["mid-001"])  # should not raise


# ── _memory_prune ──────────────────────────────────────────────────────────────


class TestMemoryPrune:
    def test_prune_normal(self, capsys: pytest.CaptureFixture) -> None:
        layer = _make_layer(prune_return=7)
        cmd = _make_cmd()
        ctx = cmd._ctx
        cmd._memory_prune(layer, ctx, ["14"])  # type: ignore[arg-type]
        out = capsys.readouterr().out
        assert "Pruned 7" in out
        layer.prune.assert_called_once_with(14)

    def test_prune_uses_config_days(self, capsys: pytest.CaptureFixture) -> None:
        layer = _make_layer(prune_return=0)
        cmd = _make_cmd(memory_retention_days=60)
        ctx = cmd._ctx
        cmd._memory_prune(layer, ctx, [])  # type: ignore[arg-type]
        layer.prune.assert_called_once_with(60)

    def test_prune_dry_run(self, capsys: pytest.CaptureFixture) -> None:
        layer = _make_layer(count_prunable_return=4)
        cmd = _make_cmd()
        ctx = cmd._ctx
        cmd._memory_prune(layer, ctx, ["--dry-run", "30"])  # type: ignore[arg-type]
        out = capsys.readouterr().out
        assert "dry-run" in out
        assert "would prune 4" in out
        layer.prune.assert_not_called()
        layer.count_prunable.assert_called_once_with(30)

    def test_prune_calls_audit_logger(self) -> None:
        audit = MagicMock()
        layer = _make_layer(prune_return=3)
        cmd = _make_cmd(audit_logger=audit)
        ctx = cmd._ctx
        cmd._memory_prune(layer, ctx, ["7"])  # type: ignore[arg-type]
        audit.info.assert_called_once()
        payload = audit.info.call_args[0][0]
        assert "pruned" in payload


# ── _memory_pin ────────────────────────────────────────────────────────────────


class TestMemoryPin:
    def test_pin_success(self, capsys: pytest.CaptureFixture) -> None:
        layer = _make_layer(pin_return=True)
        cmd = _make_cmd()
        cmd._memory_pin(layer, ["mid-001"], pin=True)
        out = capsys.readouterr().out
        assert "pinned" in out
        layer.pin_entry.assert_called_once_with("mid-001")

    def test_unpin_success(self, capsys: pytest.CaptureFixture) -> None:
        layer = _make_layer(unpin_return=True)
        cmd = _make_cmd()
        cmd._memory_pin(layer, ["mid-001"], pin=False)
        out = capsys.readouterr().out
        assert "unpinned" in out
        layer.unpin_entry.assert_called_once_with("mid-001")

    def test_pin_calls_audit_logger(self) -> None:
        audit = MagicMock()
        layer = _make_layer(pin_return=True)
        cmd = _make_cmd(audit_logger=audit)
        cmd._memory_pin(layer, ["mid-001"], pin=True)
        audit.info.assert_called_once()
        payload = audit.info.call_args[0][0]
        assert "pinned" in payload

    def test_pin_not_found_no_audit(self) -> None:
        audit = MagicMock()
        layer = _make_layer(pin_return=False)
        cmd = _make_cmd(audit_logger=audit)
        cmd._memory_pin(layer, ["bad-id"], pin=True)
        audit.info.assert_not_called()

    def test_pin_no_args(self, capsys: pytest.CaptureFixture) -> None:
        layer = _make_layer()
        cmd = _make_cmd()
        cmd._memory_pin(layer, [], pin=True)
        out = capsys.readouterr().out
        assert "Usage" in out
        layer.pin_entry.assert_not_called()
