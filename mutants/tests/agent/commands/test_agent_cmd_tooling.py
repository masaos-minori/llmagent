"""tests/test_agent_cmd_tooling.py
Behavior-lock tests for _ToolingMixin._cmd_plan (/plan).

/tool list and /tool show were removed in H-8; this file now covers only /plan.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from agent.commands.cmd_tooling import _ToolingMixin

# ── helpers ───────────────────────────────────────────────────────────────────


def _make_cmd(*, plan_mode: bool = False, plan_blocked_tools=None):
    conv = SimpleNamespace(plan_mode=plan_mode)
    tool = SimpleNamespace(plan_blocked_tools=plan_blocked_tools or [])
    cfg = SimpleNamespace(tool=tool)
    ctx = SimpleNamespace(conv=conv, cfg=cfg)
    cmd = object.__new__(_ToolingMixin)
    cmd._ctx = ctx
    return cmd


# ── _cmd_plan ─────────────────────────────────────────────────────────────────


class TestCmdPlan:
    def test_toggles_on_when_currently_off(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(plan_mode=False)
        cmd._cmd_plan()
        assert cmd._ctx.conv.plan_mode is True
        assert "Plan mode: ON" in capsys.readouterr().out

    def test_toggles_off_when_currently_on(self, capsys: pytest.CaptureFixture) -> None:
        cmd = _make_cmd(plan_mode=True)
        cmd._cmd_plan()
        assert cmd._ctx.conv.plan_mode is False
        assert "Plan mode: OFF" in capsys.readouterr().out

    def test_blocked_tools_listed_when_turning_on(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd(plan_mode=False, plan_blocked_tools=["write_file", "shell_run"])
        cmd._cmd_plan()
        out = capsys.readouterr().out
        assert "Blocked tools:" in out
        assert "write_file" in out
        assert "shell_run" in out

    def test_no_blocked_tools_line_when_list_empty(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd(plan_mode=False, plan_blocked_tools=[])
        cmd._cmd_plan()
        assert "Blocked tools:" not in capsys.readouterr().out

    def test_no_blocked_tools_line_when_turning_off(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd(plan_mode=True, plan_blocked_tools=["write_file"])
        cmd._cmd_plan()
        assert "Blocked tools:" not in capsys.readouterr().out
