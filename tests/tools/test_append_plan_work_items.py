"""tests/tools/test_append_plan_work_items.py
Tests for tools/append_plan_work_items.py.

The tool maps each procedure document of a pass to the `Implementation steps` entry that
names its target file, and falls back to the `### Requirement Traceability` phase when the
step names the rows only by a wildcard. `IMPLEMENTATIONS_DIR` is a module constant, so each
test points it at an isolated `tmp_path` batch directory.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.append_plan_work_items as tool

TIMESTAMP = "20261121-120000"
MARKER = f"<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: {TIMESTAMP} -->"

PLAN_TEMPLATE = """# Plan

## Implementation steps

1. **Phase 1: Decision gate**
   - [ ] Record the approval record (`docs/a.md`).

2. **Phase 2: Contract**
   - [ ] Create the vocabulary (`scripts/b.py`).

3. **Phase 3: Wildcard**
   - [ ] Every row under `tests/`.

### Release units
**Unit**: contract | **Phases**: 2, 3 | **Reason**: shared validation

### Requirement Traceability

| Requirement ID | Evidence | Target file | Implementation step | Acceptance criterion | Test | Status |
|---|---|---|---|---|---|---|
| REQ-001 | issue | `docs/a.md` | Phase 1, Phase 7 | AC-11 | T-11 | Explicit in issue |
| REQ-002 | issue | `scripts/b.py` | Phase 2 | AC-01 | T-01 | Explicit in issue |
| REQ-003 | issue | `tests/c.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
{rows}

## Traceability

{marker}
"""


def _plan(tmp_path: Path, rows: str = "", marker: str = MARKER) -> Path:
    plan = tmp_path / "plans" / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(PLAN_TEMPLATE.format(rows=rows, marker=marker), encoding="utf-8")
    return plan


def _doc(batch: Path, name: str, target: str, source_plan: str) -> Path:
    doc = batch / name
    doc.write_text(
        "## Traceability\n"
        f"- **Source plan**: {source_plan}\n"
        f"- **Related target files**: `{target}`\n",
        encoding="utf-8",
    )
    return doc


@pytest.fixture
def batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    directory = tmp_path / "implementations"
    directory.mkdir()
    monkeypatch.setattr(tool, "IMPLEMENTATIONS_DIR", directory)
    return directory


def _rows(plan: Path) -> list[list[str]]:
    return tool.table_data_rows(
        plan.read_text(encoding="utf-8"), tool.WORK_ITEMS_HEADING
    )


def test_appends_one_row_per_document_of_the_pass(batch: Path, tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    _doc(batch, f"{TIMESTAMP}_01_docs_a.md.md", "docs/a.md", f"plans/{plan.name}")
    _doc(batch, f"{TIMESTAMP}_02_scripts_b.py.md", "scripts/b.py", f"plans/{plan.name}")
    _doc(batch, f"{TIMESTAMP}_03_tests_c.py.md", "tests/c.py", f"plans/{plan.name}")

    assert tool.main([str(plan)]) == 0
    rows = _rows(plan)
    assert [row[1] for row in rows] == ["1", "2", "3"]
    assert all(row[2] == "Procedure" and row[3] == "Pending" for row in rows)
    assert rows[0][0] == f"implementations/{TIMESTAMP}_01_docs_a.md.md"


def test_rows_are_not_added_twice_on_a_resumed_pass(
    batch: Path, tmp_path: Path
) -> None:
    plan = _plan(tmp_path)
    _doc(batch, f"{TIMESTAMP}_01_docs_a.md.md", "docs/a.md", f"plans/{plan.name}")

    assert tool.main([str(plan)]) == 0
    first = _rows(plan)
    assert tool.main([str(plan)]) == 0
    assert _rows(plan) == first


def test_a_document_of_another_plan_is_not_added(batch: Path, tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    _doc(batch, f"{TIMESTAMP}_01_docs_a.md.md", "docs/a.md", "plans/done/other-plan.md")

    assert tool.main([str(plan)]) == 0
    assert _rows(plan) == []


def test_an_unresolvable_step_is_reported_and_stops_the_write(
    batch: Path, tmp_path: Path
) -> None:
    plan = _plan(tmp_path)
    # A target file named by neither the steps list nor the traceability table has no step.
    _doc(batch, f"{TIMESTAMP}_01_docs_q.md.md", "docs/q.md", f"plans/{plan.name}")
    before = plan.read_text(encoding="utf-8")

    assert tool.main([str(plan)]) == 1
    assert plan.read_text(encoding="utf-8") == before


def test_missing_plan_exits_two_and_an_absent_marker_exits_one(
    batch: Path, tmp_path: Path
) -> None:
    plan = _plan(tmp_path, marker="")
    _doc(batch, f"{TIMESTAMP}_01_docs_a.md.md", "docs/a.md", f"plans/{plan.name}")
    assert tool.main([str(plan)]) == 1
    assert tool.main([str(tmp_path / "no-plan.md")]) == 2


def test_dry_run_prints_the_diff_and_writes_nothing(
    batch: Path, tmp_path: Path
) -> None:
    plan = _plan(tmp_path)
    _doc(batch, f"{TIMESTAMP}_01_docs_a.md.md", "docs/a.md", f"plans/{plan.name}")
    before = plan.read_text(encoding="utf-8")

    assert tool.main([str(plan), "--dry-run"]) == 0
    assert plan.read_text(encoding="utf-8") == before
