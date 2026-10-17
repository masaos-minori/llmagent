"""Tests for tools/check_skills_heading_cycles.py."""

from __future__ import annotations

import pytest

from tools._docs_consistency_lib import Issue
from tools.check_skills_heading_cycles import (
    build_edges,
    find_cycles,
    resolve_heading,
    split_sections,
)


def _files(**contents: str) -> dict[str, str]:
    return {
        name.replace("__", "/").replace("_md", ".md"): text
        for name, text in contents.items()
    }


def test_split_sections_ignores_headings_inside_code_fences() -> None:
    text = "# Title\nbody\n```bash\n# not a heading\n```\n## Next\nmore\n"
    headings = [s.heading for s in split_sections(text)]
    assert headings == ["(preamble)", "Title", "Next"]


def test_resolve_heading_quoted_step_and_unquoted_forms() -> None:
    headings = ["Core rules", "Step 3: Create Documents", "Output language"]
    assert resolve_heading(headings, ', section "Core rules".') == "Core rules"
    assert resolve_heading(headings, " Step 3 in full.") == "Step 3: Create Documents"
    assert resolve_heading(headings, " Output language for docs") == "Output language"
    assert resolve_heading(headings, " for details") is None


def test_find_cycles_reports_two_section_cycle() -> None:
    files = _files(
        a_md='## Rules\nSee `b.md`, section "Procedure".\n',
        b_md='## Procedure\nSee `a.md`, section "Rules".\n',
    )
    cycles = find_cycles(build_edges(files))
    assert cycles == [[("a.md", "Rules"), ("b.md", "Procedure")]]


def test_find_cycles_ignores_one_directional_references() -> None:
    files = _files(
        a_md='## Rules\nSee `b.md`, section "Procedure".\n',
        b_md="## Procedure\nNo outgoing reference here.\n",
    )
    assert find_cycles(build_edges(files)) == []


def test_bare_file_references_create_no_edge() -> None:
    files = _files(
        a_md="## Rules\nSee `b.md` for details.\n",
        b_md="## Procedure\nSee `a.md` for details.\n",
    )
    assert build_edges(files) == {}


def test_find_cycles_reports_three_node_cycle_and_separate_cycles_only() -> None:
    files = _files(
        a_md='## Alpha\nSee `b.md`, section "Bravo".\n',
        b_md='## Bravo\nSee `c.md`, section "Charlie".\n',
        c_md='## Charlie\nSee `a.md`, section "Alpha".\n',
        d_md='## Delta\nSee `e.md`, section "E".\n',
        e_md="## E\nNothing.\n",
    )
    cycles = find_cycles(build_edges(files))
    assert cycles == [[("a.md", "Alpha"), ("b.md", "Bravo"), ("c.md", "Charlie")]]


def test_find_cycles_reports_multiple_independent_cycles() -> None:
    files = _files(
        a_md='## Alpha\nSee `b.md`, section "Bravo".\n',
        b_md='## Bravo\nSee `a.md`, section "Alpha".\n',
        c_md='## Charlie\nSee `d.md`, section "Delta".\n',
        d_md='## Delta\nSee `c.md`, section "Charlie".\n',
    )
    assert len(find_cycles(build_edges(files))) == 2


def test_same_file_reference_is_ignored() -> None:
    files = _files(
        a_md='## Alpha\nSee `a.md`, section "Bravo".\n## Bravo\nSee `a.md`, section "Alpha".\n'
    )
    assert build_edges(files) == {}


def test_duplicate_headings_get_distinct_nodes() -> None:
    headings = [s.heading for s in split_sections("## Rules\nx\n## Rules\ny\n")]
    assert headings == ["(preamble)", "Rules", "Rules (2)"]


def test_references_inside_code_fences_are_ignored() -> None:
    files = _files(
        a_md='## Alpha\n```md\nSee `b.md`, section "Bravo".\n```\n',
        b_md='## Bravo\nSee `a.md`, section "Alpha".\n',
    )
    assert find_cycles(build_edges(files)) == []


def test_tilde_and_long_fences_hide_headings() -> None:
    text = (
        "## Real\n~~~\n## fake1\n~~~\n````\n## fake2\n```\n## fake3\n````\n## After\n"
    )
    headings = [s.heading for s in split_sections(text)]
    assert headings == ["(preamble)", "Real", "After"]


def test_relative_reference_with_parent_segment_is_resolved() -> None:
    files = {
        "skills/x/SKILL.md": '## Alpha\nSee `../y/doc.md`, section "Bravo".\n',
        "skills/y/doc.md": '## Bravo\nSee `skills/x/SKILL.md`, section "Alpha".\n',
    }
    assert len(find_cycles(build_edges(files))) == 1


def test_reference_list_does_not_lend_quoted_heading_to_neighbour() -> None:
    files = _files(
        a_md='## Alpha\nSee `b.md` and `c.md`, section "X".\n',
        b_md='## X\nSee `a.md`, section "Alpha".\n',
        c_md="## X\nNothing.\n",
    )
    edges = build_edges(files)
    assert ("b.md", "X") not in edges.get(("a.md", "Alpha"), set())


def test_step_form_wins_over_a_later_quoted_phrase() -> None:
    headings = ["Step 3: Build", "foo bar baz"]
    assert resolve_heading(headings, ' Step 3, then "foo bar baz".') == "Step 3: Build"


def test_unquoted_heading_requires_word_boundary() -> None:
    assert resolve_heading(["Output language"], " Output languages differ") is None
    assert (
        resolve_heading(["Output language"], " Output language for docs")
        == "Output language"
    )


def test_main_exit_codes_and_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from tools import check_skills_heading_cycles as tool

    monkeypatch.setattr(tool, "collect_issues", lambda: [])
    assert tool.main(["--format", "json"]) == 0
    assert capsys.readouterr().out.strip() == "[]"

    issue = Issue(
        file="a.md", line_no=3, severity="ERROR", message="circular-reference: x"
    )
    monkeypatch.setattr(tool, "collect_issues", lambda: [issue])
    assert tool.main([]) == 1
    assert tool.main(["--format", "json"]) == 1
    assert "circular-reference" in capsys.readouterr().out
