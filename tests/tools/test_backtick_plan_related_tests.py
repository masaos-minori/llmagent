"""tests/tools/test_backtick_plan_related_tests.py

Tests for tools/backtick_plan_related_tests.py: the three places it backticks, that it
changes nothing else (other tables, headers, prose cells), idempotence, `--dry-run`, the
missing-file exit code, and that a normalized Plan is readable by
tools/close_procedures_batch.py (target paths and step citations).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools import _workitem_citation_check as wcc
from tools import backtick_plan_related_tests as bprt
from tools import close_procedures_batch as cpb

_PLAN = """## Goal
- x

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason | Related Requirement | Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tools/a.py | Create | why | REQ-001 | ev | tests/tools/test_a.py | Verified |
| tests/tools/test_a.py | Create | why, with comma | REQ-001 | ev | tests/tools/test_a.py | Verified |
| tools/data.txt | Create | why | REQ-001 | ev | N/A: data file, covered through the tests of a | Verified |
| `tools/c.py` | Modify | why | REQ-001 | ev | `uv run pytest tests/tools/test_c.py` | Verified |

## Implementation steps
1. **Phase 1: Tests**
   - [ ] Write them (REQ-001; tests/tools/test_a.py)
2. **Phase 2: Code**
   - [ ] Write the tool (REQ-001; tools/a.py, tools/data.txt and `tools/c.py`)

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tools/a.py | Create | Low | N/A | N/A | not applicable, tests/tools/test_a.py text |

## Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests | Pending | — | — | tools/a.py note |
"""


def _plan_file(tmp_path: Path, text: str = _PLAN) -> Path:
    path = tmp_path / "plan.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_the_three_places_are_backticked_and_nothing_else_changes(
    tmp_path: Path,
) -> None:
    path = _plan_file(tmp_path)

    assert bprt.main([str(path)]) == 0

    result = path.read_text(encoding="utf-8")
    assert wcc.find_plain_citations(result) == []
    assert (
        "| `tools/a.py` | Create | why | REQ-001 | ev | `tests/tools/test_a.py` |"
        in result
    )
    assert "(REQ-001; `tests/tools/test_a.py`)" in result
    assert "(REQ-001; `tools/a.py`, `tools/data.txt` and `tools/c.py`)" in result
    assert result.replace("`", "") == _PLAN.replace("`", "")
    # headers, prose cells, and the other tables are byte for byte unchanged
    for kept in (
        "| File Path | Change Responsibility | Reason | Related Requirement | Evidence | Related Tests | Validation Status |",
        "N/A: data file, covered through the tests of a",
        "| tools/a.py | Create | Low | N/A | N/A | not applicable, tests/tools/test_a.py text |",
        "| 1 | Tests | Pending | — | — | tools/a.py note |",
        "`uv run pytest tests/tools/test_c.py`",
    ):
        assert kept in result


def test_a_second_run_changes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _plan_file(tmp_path)
    bprt.main([str(path)])
    once = path.read_bytes()
    capsys.readouterr()

    assert bprt.main([str(path)]) == 0

    assert path.read_bytes() == once
    assert "no plain citations" in capsys.readouterr().out


def test_a_fully_backticked_plan_is_unchanged(tmp_path: Path) -> None:
    normalized = bprt.wcc.wrap_plain_citations(_PLAN)
    path = _plan_file(tmp_path, normalized)

    bprt.main([str(path)])

    assert path.read_text(encoding="utf-8") == normalized


def test_dry_run_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _plan_file(tmp_path)

    assert bprt.main([str(path), "--dry-run"]) == 0

    assert path.read_text(encoding="utf-8") == _PLAN
    assert "tools/a.py" in capsys.readouterr().out


def test_a_missing_file_exits_two(tmp_path: Path) -> None:
    assert bprt.main([str(tmp_path / "absent.md")]) == 2


def test_a_normalized_plan_maps_its_steps_in_the_batch_close_tool(
    tmp_path: Path,
) -> None:
    path = _plan_file(tmp_path)
    bprt.main([str(path)])
    text = path.read_text(encoding="utf-8")

    targets = cpb.parse_target_paths(text)
    steps = cpb.parse_plan_steps(text, targets)

    assert targets == {
        "tools/a.py",
        "tests/tools/test_a.py",
        "tools/data.txt",
        "tools/c.py",
    }
    assert [step.cited for step in steps] == [
        ("tests/tools/test_a.py",),
        ("tools/a.py", "tools/data.txt", "tools/c.py"),
    ]


def test_the_plain_plan_cannot_be_mapped_before_normalizing() -> None:
    targets = cpb.parse_target_paths(_PLAN)

    assert targets == {"tools/c.py"}
    assert all(
        "tools/a.py" not in step.cited for step in cpb.parse_plan_steps(_PLAN, targets)
    )
