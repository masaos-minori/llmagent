# Implementation: H-8 — Replace /tool tests with /plan tests in test_agent_cmd_tooling.py

## Goal

Remove all test coverage for the deleted `/tool list`/`/tool show` commands and add behavior-lock
tests for `_cmd_plan()` (`/plan`), which previously had no dedicated test in this file (per the
plan's U-1 finding).

## Scope

**Target**: `tests/test_agent_cmd_tooling.py`

**Supersedes**: `implementations/20260708-164202_test_agent_cmd_tooling.py.md` (the H-7 doc for
this same file, which reworked the `ToolResultStore` mocking strategy so `/tool` tests kept
passing). Since H-8 deletes `/tool list`/`/tool show` entirely, the tests that H-7's doc was
about to fix no longer exist at all after this doc's change — H-7's doc becomes moot for this
file specifically once H-8 lands. **If H-7's test doc was already applied, this doc's full-file
replacement removes its `monkeypatch`/`ToolResultStore`-patching machinery along with everything
else; if H-7's test doc was NOT yet applied, this doc replaces the ORIGINAL (pre-H-7) file
content directly.** Either starting point converges to the same end state shown in Step 2 below.

**Depends on**: `scripts/agent/commands/cmd_tooling.py`'s H-8 change already applied (or applied
together with this doc).

## Assumptions

1. `_cmd_plan()`'s behavior (verified by reading the current source):
   - Toggles `ctx.conv.plan_mode` (boolean flip).
   - Writes `f"Plan mode: {state}"` where `state` is `"ON"` or `"OFF"`.
   - When toggled ON and `ctx.cfg.tool.plan_blocked_tools` is non-empty, additionally writes
     `"  Blocked tools:"` followed by one `f"    - {t}"` line per blocked tool name.
   - When toggled OFF, or when `plan_blocked_tools` is empty, no blocked-tools lines are written.
2. `MixinBase`'s `self._ctx` and `self._out` attributes are the only dependencies `_cmd_plan()`
   needs — a minimal `SimpleNamespace`-based `ctx` (with `conv.plan_mode` and
   `cfg.tool.plan_blocked_tools`) and a capturing `_out` (or `capsys`, matching this file's
   existing convention of writing to stdout and reading via `capsys.readouterr()`) suffice.

## Implementation

### Target file

`tests/test_agent_cmd_tooling.py`

### Procedure

#### Step 1: Replace the entire file content

Replace `tests/test_agent_cmd_tooling.py` in full with:

```python
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
    cmd._ctx = ctx  # type: ignore[attr-defined]
    return cmd


# ── _cmd_plan ─────────────────────────────────────────────────────────────────


class TestCmdPlan:
    def test_toggles_on_when_currently_off(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        cmd = _make_cmd(plan_mode=False)
        cmd._cmd_plan()
        assert cmd._ctx.conv.plan_mode is True
        assert "Plan mode: ON" in capsys.readouterr().out

    def test_toggles_off_when_currently_on(
        self, capsys: pytest.CaptureFixture
    ) -> None:
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
```

Note: `_cmd_plan()` writes via `self._out.write(...)`. `MixinBase._out` is a CLASS-level default
attribute (`_out: OutputPort = CliOutputPort()`, defined in `agent/commands/mixin_base.py`,
overridden per-instance by `CommandRegistry.__init__()` in production). Since
`object.__new__(_ToolingMixin)` bypasses `__init__`, `cmd._out` falls back to this class-level
default, `CliOutputPort()`, whose `.write(text)` method calls `print(text)` (see
`agent/commands/output_port.py`). This is why `capsys.readouterr()` captures the output without
`_make_cmd()` needing to wire `_out` explicitly — confirmed by reading both files; no further
verification needed.

### Method

- Full-file replacement — the file becomes entirely about `/plan`, matching
  `cmd_tooling.py`'s new, narrower scope after H-8.
- Test names describe expected behavior positively (toggle-on, toggle-off, blocked-tools-shown,
  blocked-tools-hidden-when-empty, blocked-tools-hidden-when-off) rather than mirroring internal
  implementation details.

### Details

- `ToolResultRow` import (used by the old `_make_entry()` helper) is removed — no longer needed
  since `/tool` tests are gone.
- `MagicMock`/`patch` imports (needed by either the original mocking strategy or H-7's
  `monkeypatch`-based rework) are removed — `_cmd_plan()` has no external dependency requiring
  mocking, only a plain `SimpleNamespace`-based `ctx`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_agent_cmd_tooling.py` | 0 errors |
| Type check | `mypy tests/test_agent_cmd_tooling.py` | no new errors |
| Grep (old /tool tests gone) | `grep -n "TestToolList\|TestToolShow\|TestCmdToolDispatch\|TestUndoneDisplay" tests/test_agent_cmd_tooling.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_agent_cmd_tooling.py -v` | all 5 new `TestCmdPlan` tests pass |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |

## Risks

- None identified beyond the general H-7/H-8 sequencing note in Scope.
