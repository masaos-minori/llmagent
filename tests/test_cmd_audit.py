"""tests/test_cmd_audit.py
Unit tests for agent.commands.cmd_audit._AuditMixin._cmd_audit().
"""

from __future__ import annotations

import pathlib
from typing import Any
from unittest.mock import MagicMock

import orjson
from agent.commands.cmd_audit import _AuditMixin

# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


def _make_ctx(audit_log_file: str) -> Any:
    ctx = MagicMock()
    ctx.cfg.obs.audit_log_file = audit_log_file
    return ctx


class _Audit(_AuditMixin):
    def __init__(self, ctx: Any) -> None:
        self._ctx = ctx  # type: ignore[assignment]


def _write_log(path: pathlib.Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _evt(event: str, task_id: str, tool: str) -> str:
    return orjson.dumps(
        {"event": event, "task_id": task_id, "tool": tool, "ts": 0.0}
    ).decode()


# ---------------------------------------------------------------------------
# TestAuditTail
# ---------------------------------------------------------------------------


class TestAuditTail:
    def test_default_20_lines(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        log = tmp_path / "audit.log"
        lines = [f"line{i}" for i in range(30)]
        _write_log(log, lines)
        a = _Audit(_make_ctx(str(log)))
        a._cmd_audit("")
        out = capsys.readouterr().out
        assert "line29" in out
        assert "line9" not in out

    def test_custom_n(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        log = tmp_path / "audit.log"
        _write_log(log, [f"line{i}" for i in range(10)])
        a = _Audit(_make_ctx(str(log)))
        a._cmd_audit("tail 3")
        out = capsys.readouterr().out
        assert "line9" in out
        assert "line6" not in out

    def test_file_not_found(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        a = _Audit(_make_ctx(str(tmp_path / "missing.log")))
        a._cmd_audit("tail")
        out = capsys.readouterr().out
        assert "not found" in out.lower()

    def test_empty_file(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        log = tmp_path / "audit.log"
        log.write_text("", encoding="utf-8")
        a = _Audit(_make_ctx(str(log)))
        a._cmd_audit("")
        out = capsys.readouterr().out
        assert "empty" in out.lower()

    def test_invalid_n(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        log = tmp_path / "audit.log"
        _write_log(log, ["line"])
        a = _Audit(_make_ctx(str(log)))
        a._cmd_audit("tail abc")
        out = capsys.readouterr().out
        assert "usage" in out.lower()


# ---------------------------------------------------------------------------
# TestAuditTurn
# ---------------------------------------------------------------------------


class TestAuditTurn:
    def test_matching_events(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        log = tmp_path / "audit.log"
        _write_log(
            log,
            [
                _evt("tool_exec", "turn-aaa", "tool_x"),
                _evt("tool_exec", "turn-bbb", "tool_y"),
                _evt("tool_exec", "turn-aaa", "tool_z"),
            ],
        )
        a = _Audit(_make_ctx(str(log)))
        a._cmd_audit("turn turn-aaa")
        out = capsys.readouterr().out
        assert "tool_x" in out
        assert "tool_z" in out
        assert "tool_y" not in out

    def test_no_match(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        log = tmp_path / "audit.log"
        _write_log(log, [_evt("tool_exec", "turn-aaa", "tool_x")])
        a = _Audit(_make_ctx(str(log)))
        a._cmd_audit("turn turn-zzz")
        out = capsys.readouterr().out
        assert "no events" in out.lower()

    def test_missing_task_id(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        log = tmp_path / "audit.log"
        _write_log(log, [_evt("tool_exec", "turn-aaa", "tool_x")])
        a = _Audit(_make_ctx(str(log)))
        a._cmd_audit("turn")
        out = capsys.readouterr().out
        assert "usage" in out.lower()

    def test_skips_non_json_lines(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        log = tmp_path / "audit.log"
        _write_log(
            log,
            [
                "Loaded 3 plugin(s) from /opt/llm/plugins",
                _evt("tool_exec", "turn-aaa", "tool_x"),
            ],
        )
        a = _Audit(_make_ctx(str(log)))
        a._cmd_audit("turn turn-aaa")
        out = capsys.readouterr().out
        assert "tool_x" in out


# ---------------------------------------------------------------------------
# TestAuditTool
# ---------------------------------------------------------------------------


class TestAuditTool:
    def test_matching_events(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        log = tmp_path / "audit.log"
        _write_log(
            log,
            [
                _evt("tool_exec", "t1", "github__list_prs"),
                _evt("tool_exec", "t2", "shell__run"),
                _evt("tool_exec", "t3", "github__list_prs"),
            ],
        )
        a = _Audit(_make_ctx(str(log)))
        a._cmd_audit("tool github__list_prs")
        out = capsys.readouterr().out
        assert out.count("github__list_prs") >= 2
        assert "shell__run" not in out

    def test_no_match(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        log = tmp_path / "audit.log"
        _write_log(log, [_evt("tool_exec", "t1", "shell__run")])
        a = _Audit(_make_ctx(str(log)))
        a._cmd_audit("tool no_such_tool")
        out = capsys.readouterr().out
        assert "no events" in out.lower()

    def test_missing_tool_name(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        log = tmp_path / "audit.log"
        _write_log(log, [_evt("tool_exec", "t1", "shell__run")])
        a = _Audit(_make_ctx(str(log)))
        a._cmd_audit("tool")
        out = capsys.readouterr().out
        assert "usage" in out.lower()

    def test_cap_at_50(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        log = tmp_path / "audit.log"
        lines = [_evt("tool_exec", f"t{i}", "big_tool") for i in range(60)]
        _write_log(log, lines)
        a = _Audit(_make_ctx(str(log)))
        a._cmd_audit("tool big_tool")
        out = capsys.readouterr().out
        assert "omitted" in out


# ---------------------------------------------------------------------------
# TestAuditUnknownSubcommand
# ---------------------------------------------------------------------------


class TestAuditUnknownSubcommand:
    def test_unknown_sub(self, tmp_path: pathlib.Path, capsys: Any) -> None:
        log = tmp_path / "audit.log"
        _write_log(log, ["x"])
        a = _Audit(_make_ctx(str(log)))
        a._cmd_audit("badcmd")
        out = capsys.readouterr().out
        assert "usage" in out.lower()
