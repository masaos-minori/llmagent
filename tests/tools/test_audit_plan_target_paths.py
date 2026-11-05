"""Tests for tools/audit_plan_target_paths.py path auditing and exit codes."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tools.audit_plan_target_paths import audit, main

HEADER = (
    "## Implementation Target Files\n"
    "| File Path | Change Responsibility | Reason |\n"
    "|---|---|---|\n"
)
FIRST_ROW_LINE = 6


def _row(path: str, responsibility: str = "Fix thing", reason: str = "x") -> str:
    return f"| `{path}` | {responsibility} | {reason} |\n"


def _plan(tmp_path: Path, rows: list[str], trailing: str = "") -> Path:
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan\n\n" + HEADER + "".join(rows) + trailing, encoding="utf-8")
    return plan


def _touch(tmp_path: Path, rel: str) -> None:
    target = tmp_path / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("", encoding="utf-8")


def test_existing_target_has_no_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _touch(tmp_path, "scripts/x.py")
    assert audit(_plan(tmp_path, [_row("scripts/x.py")])) == []


def test_missing_target_is_reported_with_line_number(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    plan = _plan(tmp_path, [_row("scripts/missing.py")])
    assert audit(plan) == [
        f"plan.md:{FIRST_ROW_LINE}: missing target path: scripts/missing.py"
    ]


@pytest.mark.parametrize(
    "hint", ["create", "new", "generated", "manifest;", "registry;"]
)
def test_create_hint_in_second_cell_exempts_missing_target(
    hint: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    plan = _plan(tmp_path, [_row("scripts/y.py", responsibility=f"{hint} file")])
    assert audit(plan) == []


def test_create_hint_only_in_third_cell_does_not_exempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    plan = _plan(tmp_path, [_row("scripts/y.py", reason="New file")])
    assert audit(plan) == [
        f"plan.md:{FIRST_ROW_LINE}: missing target path: scripts/y.py"
    ]


def test_missing_registry_path_without_hint_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    plan = _plan(tmp_path, [_row("registry/a.yaml", responsibility="Plain")])
    assert audit(plan) == [
        f"plan.md:{FIRST_ROW_LINE}: missing (no create hint): registry/a.yaml"
    ]


def test_missing_registry_path_with_hint_is_exempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    plan = _plan(tmp_path, [_row("registry/a.yaml", responsibility="create it")])
    assert audit(plan) == []


def test_existing_registry_path_has_no_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _touch(tmp_path, "registry/a.yaml")
    plan = _plan(tmp_path, [_row("registry/a.yaml", responsibility="Plain")])
    assert audit(plan) == []


def test_header_separator_and_non_path_rows_are_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    rows = ["| TBD | note | x |\n", "| only-one-cell |\n", "| | empty | x |\n"]
    assert audit(_plan(tmp_path, rows)) == []


def test_rows_outside_the_target_section_are_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _touch(tmp_path, "scripts/exists.py")
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## Other\n"
        "| `scripts/before.py` | x | y |\n\n"
        + HEADER
        + _row("scripts/exists.py")
        + "\n## Reference Files\n"
        "| `scripts/after.py` | x | y |\n",
        encoding="utf-8",
    )
    assert audit(plan) == []


def test_main_returns_1_with_findings_and_prints_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    plan = _plan(tmp_path, [_row("scripts/missing.py")])
    monkeypatch.setattr(sys, "argv", ["audit_plan_target_paths.py", str(plan)])
    assert main() == 1
    out = capsys.readouterr().out
    assert f"plan.md:{FIRST_ROW_LINE}: missing target path: scripts/missing.py" in out
    assert out.splitlines()[-1] == "1 finding(s) across 1 plan(s)."


def test_main_returns_0_without_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    _touch(tmp_path, "scripts/x.py")
    plan = _plan(tmp_path, [_row("scripts/x.py")])
    monkeypatch.setattr(sys, "argv", ["audit_plan_target_paths.py", str(plan)])
    assert main() == 0
    assert capsys.readouterr().out.splitlines()[-1] == "0 finding(s) across 1 plan(s)."


def test_main_without_arguments_reads_plans_directory_in_sorted_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    plans = tmp_path / "plans"
    plans.mkdir()
    for name in ("b.md", "a.md"):
        (plans / name).write_text(
            "# Plan\n\n" + HEADER + _row("scripts/missing.py"), encoding="utf-8"
        )
    monkeypatch.setattr(sys, "argv", ["audit_plan_target_paths.py"])
    assert main() == 1
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("a.md:")
    assert lines[1].startswith("b.md:")
    assert lines[-1] == "2 finding(s) across 2 plan(s)."
