"""tests/tools/test_sync_plan_workitem_status.py
Tests for tools/sync_plan_workitem_status.py.

The tool decides each Plan row from the archived procedure's own Execution Status, not from
the fact that the file is under `implementations/done/`. `DONE_DIR` is a module constant, so
each test points it at an isolated `tmp_path` archive.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.sync_plan_workitem_status as sync

PLAN_TEMPLATE = """# Plan

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
{rows}

## Next section
"""


def _procedure(statuses: list[str]) -> str:
    rows = "\n".join(
        f"| {i} | Step {i} | {status} | — | — | |"
        for i, status in enumerate(statuses, start=1)
    )
    return (
        "### Execution Status\n"
        "| Step | Description | Status | Started | Completed | Notes |\n"
        "|------|-------------|--------|---------|-----------|-------|\n"
        f"{rows}\n"
    )


def _plan(tmp_path: Path, names: list[str]) -> Path:
    rows = "\n".join(
        f"| `implementations/{name}` | 1 | Procedure | Pending | — | — |"
        for name in names
    )
    plan = tmp_path / "plan.md"
    plan.write_text(PLAN_TEMPLATE.format(rows=rows), encoding="utf-8")
    return plan


@pytest.fixture
def done(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    directory = tmp_path / "done"
    directory.mkdir()
    monkeypatch.setattr(sync, "DONE_DIR", directory)
    return directory


def _status_of(plan: Path, name: str) -> str:
    for line in plan.read_text(encoding="utf-8").splitlines():
        if name in line:
            return line.strip("|").split("|")[3].strip()
    raise AssertionError(f"{name} not in plan")


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (["Completed", "Completed"], "Completed"),
        (["Completed", "Superseded"], "Superseded"),
        (["Superseded"], "Superseded"),
        (["Completed", "Pending"], "Pending"),
        (["Completed", "In Progress"], "Pending"),
        (["Blocked"], "Pending"),
    ],
)
def test_row_follows_the_procedure_own_status(
    tmp_path: Path, done: Path, statuses: list[str], expected: str
) -> None:
    (done / "a.md").write_text(_procedure(statuses), encoding="utf-8")
    plan = _plan(tmp_path, ["a.md"])

    assert sync.main([str(plan)]) == 0

    assert _status_of(plan, "a.md") == expected


def test_unfinished_procedure_is_reported_as_skipped(
    tmp_path: Path, done: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (done / "a.md").write_text(_procedure(["Pending"]), encoding="utf-8")
    plan = _plan(tmp_path, ["a.md"])

    sync.main([str(plan)])

    out = capsys.readouterr().out
    assert "Skipped" in out and "a.md" in out
    assert "updated: 0 row(s)" in out


def test_unreadable_table_is_skipped_not_completed(tmp_path: Path, done: Path) -> None:
    (done / "a.md").write_text("# no status table\n", encoding="utf-8")
    plan = _plan(tmp_path, ["a.md"])

    sync.main([str(plan)])

    assert _status_of(plan, "a.md") == "Pending"


def test_procedure_not_archived_is_untouched(tmp_path: Path, done: Path) -> None:
    plan = _plan(tmp_path, ["still-open.md"])

    sync.main([str(plan)])

    assert _status_of(plan, "still-open.md") == "Pending"


def test_only_the_finished_procedures_change(tmp_path: Path, done: Path) -> None:
    (done / "ok.md").write_text(_procedure(["Completed"]), encoding="utf-8")
    (done / "gone.md").write_text(_procedure(["Superseded"]), encoding="utf-8")
    (done / "open.md").write_text(_procedure(["Pending"]), encoding="utf-8")
    plan = _plan(tmp_path, ["ok.md", "gone.md", "open.md"])

    sync.main([str(plan)])

    assert [_status_of(plan, n) for n in ("ok.md", "gone.md", "open.md")] == [
        "Completed",
        "Superseded",
        "Pending",
    ]


def test_dry_run_writes_nothing(tmp_path: Path, done: Path) -> None:
    (done / "a.md").write_text(_procedure(["Completed"]), encoding="utf-8")
    plan = _plan(tmp_path, ["a.md"])
    before = plan.read_text(encoding="utf-8")

    assert sync.main([str(plan), "--dry-run"]) == 0

    assert plan.read_text(encoding="utf-8") == before


def test_usage_errors_exit_2(tmp_path: Path) -> None:
    assert sync.main([]) == 2
    assert sync.main([str(tmp_path / "missing.md")]) == 2
