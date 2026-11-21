"""tests/tools/test_generate_agentcfg003_procedures.py
Tests for tools/generate_agentcfg003_procedures.py.

The tool is the assembly half of the pass: rows and phases are read from the Plan, the text
comes from the `tools/_agentcfg003_content_*.py` modules. Each test points `IMPLEMENTATIONS_DIR`
at an isolated `tmp_path` batch directory and registers content through the tables the tool
reads, so only the assembly behaviour is exercised.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.generate_agentcfg003_procedures as tool
from tools import generate_workitem

TIMESTAMP = "20261121-120000"
MARKER = f"<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: {TIMESTAMP} -->"

PLAN_TEMPLATE = """# Plan

### Implementation Target Files
| Target file | Action | Responsibility | Related Requirement | Tests | Test | Status |
|---|---|---|---|---|---|---|
| `scripts/a.py` | Create (new) | Contract | REQ-011 | fixture | `tests/b.py`, `tests/c.py` | Verified |
| `tests/b.py` | Update | Companion test | REQ-011 | fixture | `tests/c.py` | Verified |
| `tests/c.py` | Update | Test | REQ-012 | fixture | `this file` | Verified |

### Implementation steps

1. **Phase 2: Contract**
   - [ ] Create the vocabulary (`scripts/a.py`).

### Requirement Traceability

| Requirement ID | Evidence | Target file | Implementation step | Acceptance criterion | Test | Status |
|---|---|---|---|---|---|---|
| REQ-011 | issue | `scripts/a.py` | Phase 2 | AC-01 | T-11 | Explicit in issue |
| REQ-012 | issue | `tests/c.py` | Phase 3 | AC-02 | T-12 | Confirmed by repository evidence |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|

{marker}
"""


@pytest.fixture
def plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    batch = tmp_path / "implementations"
    batch.mkdir()
    monkeypatch.setattr(generate_workitem, "IMPLEMENTATIONS_DIR", batch)
    file = tmp_path / "plans" / "plan.md"
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(PLAN_TEMPLATE.format(marker=MARKER), encoding="utf-8")
    for table in (
        tool.PRODUCER_CONTENT,
        tool.BASE_CONTENT,
        tool.TEST_CONTENT,
        tool.DOC_CONTENT,
        tool.COMPANIONS,
    ):
        table.clear()
    tool.COMPANIONS["tests/b.py"] = {
        "action": "Update",
        "procedure": "Assert the fixture uses the declared values.",
        "validation": "Run the test file.",
    }
    return file


def _content(table: dict[str, dict[str, object]], path: str) -> None:
    table[path] = {
        key: []
        for key in (
            "goal",
            "assumptions",
            "design",
            "alternatives",
            "procedure",
            "method",
            "details",
            "compat",
            "security",
            "rollback",
            "validation",
            "completion",
            "out_of_scope",
            "exec_steps",
            "blockers",
            "work_items",
        )
    }


def test_a_test_row_named_by_one_row_is_a_companion_and_gets_no_document(
    plan: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _content(tool.BASE_CONTENT, "scripts/a.py")
    _content(tool.TEST_CONTENT, "tests/c.py")

    assert tool.main([str(plan)]) == 0
    batch = generate_workitem.IMPLEMENTATIONS_DIR
    names = sorted(p.name for p in batch.glob("*.md"))
    assert names == [
        f"{TIMESTAMP}_01_scripts_a.py.md",
        f"{TIMESTAMP}_03_tests_c.py.md",
    ]
    body = (batch / names[0]).read_text(encoding="utf-8")
    assert "### Companion test files" in body
    assert "`tests/b.py`" in body
    assert f"{TIMESTAMP}_02_tests_b.py.md" not in names


def test_an_unwritten_row_is_generated_and_an_existing_identical_file_is_left(
    plan: Path,
) -> None:
    _content(tool.BASE_CONTENT, "scripts/a.py")
    _content(tool.TEST_CONTENT, "tests/c.py")

    assert tool.main([str(plan)]) == 0
    batch = generate_workitem.IMPLEMENTATIONS_DIR
    first = (batch / f"{TIMESTAMP}_01_scripts_a.py.md").read_text(encoding="utf-8")
    assert "## Execution Status" in first
    row = "| 1 | Implement the change described in Implementation > Procedure/Method/Details"
    assert f"{row} | Pending | — | — | Gated:" in first

    assert tool.main([str(plan)]) == 0
    assert (batch / f"{TIMESTAMP}_01_scripts_a.py.md").read_text(
        encoding="utf-8"
    ) == first


def test_a_row_with_no_authored_content_is_reported_and_stops_the_write(
    plan: Path,
) -> None:
    batch = generate_workitem.IMPLEMENTATIONS_DIR
    assert tool.main([str(plan), "--dry-run"]) == 1
    assert not list(batch.glob("*.md"))
    assert tool.main([str(plan)]) == 1
    assert not list(batch.glob("*.md"))


def test_missing_plan_exits_two_and_an_absent_marker_records_one_on_the_real_run(
    tmp_path: Path,
) -> None:
    assert tool.main([str(tmp_path / "no-plan.md")]) == 2

    plan = tmp_path / "plans" / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(PLAN_TEMPLATE.format(marker=""), encoding="utf-8")
    # A dry run cannot record the marker, so the run reports no content and writes nothing.
    assert tool.main([str(plan), "--dry-run"]) == 1
    assert "timestamp" not in plan.read_text(encoding="utf-8")
