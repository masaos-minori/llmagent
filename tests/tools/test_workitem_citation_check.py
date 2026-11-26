"""tests/tools/test_workitem_citation_check.py

Tests for tools/_workitem_citation_check.py: the plain path citations of a Plan in the
`File Path` and `Related Tests` columns of `Implementation Target Files` and in
`Implementation steps`, the idempotent wrapping, and the finding records. The Plans are
synthetic.
"""

from __future__ import annotations

from pathlib import Path

from tools import _workitem_citation_check as wcc

_HEADER = (
    "| File Path | Change Responsibility | Reason | Related Requirement | Evidence | Related Tests | Validation Status |\n"
    "|---|---|---|---|---|---|---|\n"
)


def _plan(rows: list[str], steps: str = "", extra: str = "") -> str:
    return (
        "## Goal\n- x\n\n## Implementation Target Files\n**Freeze status**: Frozen\n\n"
        + _HEADER
        + "\n".join(rows)
        + "\n\n## Reference Files\n| File Path | Why |\n|---|---|\n| tests/tools/test_other.py | read |\n\n"
        + "## Implementation steps\n"
        + steps
        + "\n## Affected areas\n| File | Change |\n|---|---|\n| tools/a.py | tests/tools/test_a.py text |\n"
        + extra
    )


def _row(path: str, tests: str = "N/A: none") -> str:
    return f"| {path} | Create | why | REQ-001 | ev | {tests} | Verified |"


def _kinds(text: str) -> list[tuple[str, str]]:
    return [(c.kind, c.path) for c in wcc.find_plain_citations(text)]


def test_a_plain_file_path_cell_is_reported() -> None:
    assert _kinds(_plan([_row("tools/a.py")])) == [("File Path", "tools/a.py")]


def test_a_backticked_file_path_cell_is_not_reported() -> None:
    assert _kinds(_plan([_row("`tools/a.py`")])) == []


def test_a_cell_with_trailing_text_or_no_path_is_never_reported_or_wrapped() -> None:
    rows = [_row("tests/ (full suite)"), _row("docs/ (entire tree)"), "| | | | | | | |"]
    text = _plan(rows)

    assert _kinds(text) == []
    assert wcc.wrap_plain_citations(text) == text


def test_a_plain_test_path_in_related_tests_is_reported() -> None:
    text = _plan([_row("`tools/a.py`", "tests/tools/test_a.py, tests/tools/test_b.py")])

    assert _kinds(text) == [
        ("Related Tests", "tests/tools/test_a.py"),
        ("Related Tests", "tests/tools/test_b.py"),
    ]


def test_backticked_tests_and_paths_inside_a_backticked_command_are_not_reported() -> (
    None
):
    text = _plan(
        [
            _row(
                "`tools/a.py`",
                "`tests/tools/test_a.py`, `uv run pytest tests/tools/test_b.py`",
            )
        ]
    )

    assert _kinds(text) == []


def test_prose_with_a_comma_in_related_tests_is_untouched() -> None:
    text = _plan(
        [_row("`tools/a.py`", "N/A: data file, covered through the tests of a")]
    )

    assert _kinds(text) == []
    assert wcc.wrap_plain_citations(text) == text


def test_a_plain_target_path_in_the_steps_is_reported() -> None:
    steps = "1. **Phase 1**\n   - [ ] Do it (REQ-001; tools/a.py)\n"
    text = _plan([_row("`tools/a.py`")], steps)

    assert _kinds(text) == [("Implementation steps", "tools/a.py")]


def test_a_backticked_target_path_in_the_steps_is_not_reported() -> None:
    steps = "1. **Phase 1**\n   - [ ] Do it (REQ-001; `tools/a.py`, run `uv run python tools/a.py`)\n"

    assert _kinds(_plan([_row("`tools/a.py`")], steps)) == []


def test_a_shorter_target_path_never_matches_inside_a_longer_path() -> None:
    steps = "1. **Phase 1**\n   - [ ] Do it (tools/a.py.md and tools/a.py)\n"
    text = _plan([_row("`tools/a.py`"), _row("`tools/a.py.md`")], steps)

    assert sorted(_kinds(text)) == [
        ("Implementation steps", "tools/a.py"),
        ("Implementation steps", "tools/a.py.md"),
    ]


def test_other_tables_are_never_reported() -> None:
    text = _plan([_row("`tools/a.py`")])

    assert "| tools/a.py | tests/tools/test_a.py text |" in text
    assert _kinds(text) == []


def test_wrapping_removes_every_plain_citation_and_is_idempotent() -> None:
    steps = "1. **Phase 1**\n   - [ ] Do it (REQ-001; tools/a.py and tools/b.py, tools/a.py)\n"
    text = _plan(
        [_row("tools/a.py", "tests/tools/test_a.py"), _row("tools/b.py")], steps
    )

    wrapped = wcc.wrap_plain_citations(text)

    assert wcc.find_plain_citations(wrapped) == []
    assert wcc.wrap_plain_citations(wrapped) == wrapped
    assert "| `tools/a.py` |" in wrapped
    assert "| `tests/tools/test_a.py` |" in wrapped
    assert "(REQ-001; `tools/a.py` and `tools/b.py`, `tools/a.py`)" in wrapped
    assert wrapped.replace("`", "") == text.replace("`", "")


def test_offsets_locate_the_plain_path_in_its_line() -> None:
    text = _plan([_row("tools/a.py")])
    lines = text.split("\n")

    (citation,) = wcc.find_plain_citations(text)

    assert lines[citation.line_index][citation.start : citation.end] == "tools/a.py"


def test_findings_name_the_file_the_path_and_the_line(tmp_path: Path) -> None:
    plan = tmp_path / "plans" / "20260101-000000_x.md"
    plan.parent.mkdir()
    text = _plan([_row("tools/a.py")])
    plan.write_text(text, encoding="utf-8")

    findings = wcc.find_plan_citation_findings(plan, tmp_path)

    assert len(findings) == 1
    assert findings[0]["category"] == "plain-path-citation"
    assert findings[0]["file"] == "plans/20260101-000000_x.md"
    assert "File Path: tools/a.py is not in backticks" in findings[0]["detail"]
    assert (
        "tools/backtick_plan_related_tests.py plans/20260101-000000_x.md"
        in findings[0]["detail"]
    )
    assert (
        f"line {text.split(chr(10)).index(_row('tools/a.py')) + 1}"
        in findings[0]["detail"]
    )


def test_a_plan_without_a_target_table_has_no_citations() -> None:
    assert wcc.find_plain_citations("## Goal\n- x\n") == []
