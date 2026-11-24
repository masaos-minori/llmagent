"""tests/tools/test_append_plan_work_items.py
Tests for tools/append_plan_work_items.py.

The tool maps each procedure document of a pass to the `Implementation steps` entry that
names its target file. `IMPL_DIR` is a module constant, so each test points it at an isolated
`tmp_path` batch directory, and `main()` reads `sys.argv`, so the tests call it through a
patched argv with the pass prefix and the plan path.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import tools.append_plan_work_items as tool

TIMESTAMP = "20261121-120000"
PLACEHOLDER = "| — | — | — | — | — | — |"

PLAN_TEMPLATE = """# Plan

## Implementation Target Files

| File Path | Type | Row | Phase | Notes | Test | Companion |
|---|---|---|---|---|---|---|
{target_rows}

## Implementation steps

1. **Phase 1: Decision gate**
   - [ ] Record the approval record (`docs/a.md`).

2. **Phase 2: Contract**
   - [ ] Create the vocabulary (`scripts/b.py`).

3. **Phase 3: Tests**
   - [ ] Cover the row (`tests/c.py`).

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
{rows}

## Traceability

- **Source issue**: issues/{marker}.md
"""


def _plan(
    tmp_path: Path, target_rows: str = "", rows: str = PLACEHOLDER, marker: str = "plan"
) -> Path:
    plan = tmp_path / "plans" / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(
        PLAN_TEMPLATE.format(target_rows=target_rows, rows=rows, marker=marker),
        encoding="utf-8",
    )
    return plan


def _target_row(path: str) -> str:
    return f"| {path} | code | 1 | 1 | — | — | — |"


def _doc(batch: Path, name: str, target: str, phase: int = 1) -> Path:
    doc = batch / name
    doc.write_text(
        f"**Release unit**: unit (Phase {phase})\n\n"
        "### Target file\n"
        f"`{target}`\n\n"
        "### Companion test files\n\n"
        "- none\n\n"
        "### Execution Status\n"
        "| Step | Description | Status | Started | Completed | Notes |\n"
        "|------|-------------|--------|---------|-----------|-------|\n"
        "| 1 | Do the work | Pending | — | — | — |\n",
        encoding="utf-8",
    )
    return doc


@pytest.fixture
def batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    directory = tmp_path / "implementations"
    directory.mkdir()
    monkeypatch.setattr(tool, "IMPL_DIR", directory)
    return directory


def _run(
    monkeypatch: pytest.MonkeyPatch, plan: Path, extra: list[str] | None = None
) -> int:
    argv = ["append_plan_work_items.py", TIMESTAMP, str(plan)] + (extra or [])
    monkeypatch.setattr(sys, "argv", argv)
    return tool.main()


def _rows(plan: Path) -> list[list[str]]:
    """Return the plan's Work Items Created rows, excluding the placeholder row."""
    lines = plan.read_text(encoding="utf-8").splitlines()
    start = lines.index(tool.WORK_ITEMS_HEADER)
    rows: list[list[str]] = []
    for line in lines[start + 1 :]:
        if line.startswith("| Item ID") or line.startswith("|---"):
            continue
        if line.startswith("| ") and line != PLACEHOLDER:
            rows.append([c.strip() for c in line.strip("|").split("|")])
    return rows


def test_appends_one_row_per_document_of_the_pass(
    batch: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _plan(
        tmp_path,
        "\n".join(_target_row(p) for p in ("docs/a.md", "scripts/b.py", "tests/c.py")),
    )
    _doc(batch, f"{TIMESTAMP}_01_docs_a.md.md", "docs/a.md", phase=1)
    _doc(batch, f"{TIMESTAMP}_02_scripts_b.py.md", "scripts/b.py", phase=2)
    _doc(batch, f"{TIMESTAMP}_03_tests_c.py.md", "tests/c.py", phase=3)

    assert _run(monkeypatch, plan) == 0
    rows = _rows(plan)
    assert [row[1] for row in rows] == ["1", "2", "3"]
    assert all(row[2] == "Procedure" and row[3] == "Pending" for row in rows)
    assert rows[0][0] == f"implementations/{TIMESTAMP}_01_docs_a.md.md"


def test_a_resumed_pass_does_not_add_the_rows_again(
    batch: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _plan(tmp_path, _target_row("docs/a.md"))
    _doc(batch, f"{TIMESTAMP}_01_docs_a.md.md", "docs/a.md")

    assert _run(monkeypatch, plan) == 0
    first = _rows(plan)
    # The placeholder row is consumed by the first pass, so a resumed pass has no marker to
    # write into and stops instead of appending the rows a second time.
    with pytest.raises(SystemExit):
        _run(monkeypatch, plan)
    assert _rows(plan) == first


def test_a_document_whose_target_is_not_a_plan_row_is_a_finding(
    batch: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _plan(tmp_path, _target_row("docs/a.md"))
    _doc(batch, f"{TIMESTAMP}_01_docs_a.md.md", "docs/a.md")
    _doc(batch, f"{TIMESTAMP}_02_docs_x.md.md", "docs/x.md")

    assert _run(monkeypatch, plan) == 1
    assert _rows(plan) == []


def test_an_uncovered_row_is_reported_and_stops_the_write(
    batch: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _plan(tmp_path, _target_row("docs/q.md"))
    before = plan.read_text(encoding="utf-8")

    assert _run(monkeypatch, plan) == 1
    assert plan.read_text(encoding="utf-8") == before


def test_a_plan_without_the_work_items_placeholder_stops_the_write(
    batch: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _plan(tmp_path, _target_row("docs/a.md"), rows="| 1 | — | — | — | — | — |")
    _doc(batch, f"{TIMESTAMP}_01_docs_a.md.md", "docs/a.md")
    before = plan.read_text(encoding="utf-8")

    with pytest.raises(SystemExit):
        _run(monkeypatch, plan)
    assert plan.read_text(encoding="utf-8") == before


def test_dry_run_prints_the_rows_and_writes_nothing(
    batch: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _plan(tmp_path, _target_row("docs/a.md"))
    _doc(batch, f"{TIMESTAMP}_01_docs_a.md.md", "docs/a.md")
    before = plan.read_text(encoding="utf-8")

    assert _run(monkeypatch, plan, ["--dry-run"]) == 0
    assert plan.read_text(encoding="utf-8") == before
