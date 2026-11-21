"""tests/tools/test_check_workitem_structure.py
Tests for tools/check_workitem_structure.py.

Covers:
- Required ``## `` section detection from each canonical template's fenced block.
- Case-insensitive detection: a document whose headings use different casing than
  its template is NOT reported as missing a section. This is the regression guard
  for the case-normalization fix in ``find_missing_sections`` -- ``_HEADING_RE``
  matches headings regardless of case, but the captured groups retain their
  original casing, so a plain set-membership test would falsely report a section
  as missing whenever casing differs.
- Genuinely missing sections are still reported with the correct detail.
- Kind inference from the top-level directory (including ``done/``).
- Template-leftover detection for all three kinds: an unfilled issue, plan, or
  procedure scaffold is reported; filled documents and brace-containing own
  content are not; plan and procedure scaffolds are reported (the reversed
  clean-skeleton assertion), archived ``done/`` documents stay out.
- Multi-path ``--file``: several documents aggregate; a single path keeps the
  pre-change output.
- Status value rule on active plan and procedure documents: Status cells outside the
  shared vocabulary are reported (``status-value``), vocabulary members are not, and
  archived ``done/`` documents stay out of the active rule.
- Archived value scan: holders under both ``done/`` directories are reported, paths
  listed in the status-value baseline are skipped, and the default baseline loader
  behaves like the archived-status one.
- Live repository checks: the active document set holds no value violation or
  template leftover, and the
  ``templates/execution-status.md`` options line equals the shared vocabulary.

The tool reads ``ROOT_DIR`` (a module constant) to locate templates and to build
relative file paths, so every test that exercises path handling monkeypatches
``tools.check_workitem_structure.ROOT_DIR`` to an isolated ``tmp_path`` tree and
installs copies of the three real templates underneath it. No test writes into
the repository's real ``templates/``, ``issues/``, ``plans/``, or
``implementations/`` directories.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.check_workitem_structure as cwis
from tools import _workitem_leftover_rules as wlr
from tools._workitem_status_table import STATUS_VOCABULARY

_SRC_ROOT = Path(__file__).resolve().parent.parent.parent
_TEMPLATE_NAMES = ("issue.md", "plan.md", "implementation-procedure.md")


def _write(dir_path: Path, filename: str, content: str) -> Path:
    dir_path.mkdir(parents=True, exist_ok=True)
    target = dir_path / filename
    target.write_text(content, encoding="utf-8")
    return target


def _install_templates(root: Path) -> None:
    """Copy the three real canonical templates under ``root/templates``."""
    dest = root / "templates"
    dest.mkdir(parents=True, exist_ok=True)
    for name in _TEMPLATE_NAMES:
        (dest / name).write_bytes((_SRC_ROOT / "templates" / name).read_bytes())


def test_exact_match_has_no_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    spec = cwis.TemplateSpec(
        kind="plan", required_headings=("Goal", "Priority", "Scope")
    )
    body = "\n".join(f"## {h}\n\nbody\n" for h in spec.required_headings)
    doc = _write(tmp_path, "match_plan.md", body)
    assert cwis.find_missing_sections(doc, spec) == []


def test_different_casing_is_not_reported_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Headings present but in different casing than the template must pass."""
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    spec = cwis.TemplateSpec(
        kind="plan",
        required_headings=("Goal", "Priority", "Acceptance Criteria"),
    )
    body = "\n".join(f"## {h.upper()}\n\nbody\n" for h in spec.required_headings)
    doc = _write(tmp_path, "upper_plan.md", body)
    assert cwis.find_missing_sections(doc, spec) == []


def test_mixed_casing_per_heading_is_not_reported_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A mix of casings across headings must still resolve to existing sections."""
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    spec = cwis.TemplateSpec(
        kind="plan",
        required_headings=("Goal", "Priority", "Scope"),
    )
    body = "\n".join(f"## {case}\n\nbody\n" for case in ("goal", "PRIORITY", "Scope"))
    doc = _write(tmp_path, "mixed_plan.md", body)
    assert cwis.find_missing_sections(doc, spec) == []


def test_genuinely_missing_section_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    spec = cwis.TemplateSpec(kind="plan", required_headings=("Goal", "Traceability"))
    body = "## Goal\n\nbody\n"  # Traceability absent
    doc = _write(tmp_path, "incomplete_plan.md", body)
    findings = cwis.find_missing_sections(doc, spec)
    assert len(findings) == 1
    assert findings[0]["category"] == "missing-section"
    assert findings[0]["detail"] == "missing required section: ## Traceability"
    assert findings[0]["file"] == "incomplete_plan.md"


def test_end_to_end_case_insensitive_with_real_templates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_templates(tmp_path)
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    (tmp_path / "plans").mkdir(parents=True, exist_ok=True)
    plans = tmp_path / "plans"
    spec = cwis.load_template_specs()["plan"]
    body = "\n".join(f"## {h.upper()}\n\nbody\n" for h in spec.required_headings)
    _write(plans, "20260101-000000_plan.md", body)
    assert cwis.collect_findings({"plan"}, include_done=False) == []


def test_end_to_end_missing_section_with_real_templates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_templates(tmp_path)
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    (tmp_path / "plans").mkdir(parents=True, exist_ok=True)
    plans = tmp_path / "plans"
    spec = cwis.load_template_specs()["plan"]
    present = [h for h in spec.required_headings if h != "Traceability"]
    body = "\n".join(f"## {h}\n\nbody\n" for h in present)
    _write(plans, "20260102-000000_plan.md", body)
    findings = cwis.collect_findings({"plan"}, include_done=False)
    assert len(findings) == 1
    assert findings[0]["detail"] == "missing required section: ## Traceability"


def test_infer_kind_from_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    (tmp_path / "plans").mkdir()
    (tmp_path / "plans" / "done").mkdir()
    assert cwis.infer_kind(tmp_path / "plans" / "x_plan.md") == "plan"
    assert cwis.infer_kind(tmp_path / "plans" / "done" / "x_plan.md") == "plan"
    assert cwis.infer_kind(tmp_path / "implementations" / "x.md") == "implementation"
    assert cwis.infer_kind(tmp_path / "other" / "x.md") is None


_UNIT_OK = (
    "**Unit**: schema-and-write | **Phases**: 1, 2 | **Reason**: phase 1 breaks inserts"
)


def _plan_with_block(block: str | None, *, outside: bool = False) -> str:
    """Return a minimal Plan body with an optional ``### Release units`` block."""
    steps = (
        "## Implementation steps\n1. **Phase 1: A**\n   - [ ] x\n2. **Phase 2: B**\n"
    )
    heading = "" if block is None else f"\n### Release units\n{block}\n"
    if outside:
        return f"{steps}\n## Validation plan\nbody\n{heading}"
    return f"{steps}{heading}\n## Validation plan\nbody\n"


def _unit_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str
) -> list[dict[str, str]]:
    _install_templates(tmp_path)
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    doc = _write(tmp_path / "plans", "20260103-000000_plan.md", body)
    return [
        f
        for f in cwis.collect_single_file_findings(doc)
        if f["category"] == "release-unit"
    ]


@pytest.mark.parametrize(
    "block",
    [
        _UNIT_OK,
        f"{_UNIT_OK}\n**Unit**: second | **Phases**: 2 | **Reason**: coupled",
        "N/A: no release unit",
    ],
)
def test_release_unit_valid_declarations_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, block: str
) -> None:
    assert _unit_findings(tmp_path, monkeypatch, _plan_with_block(block)) == []


@pytest.mark.parametrize(
    "block",
    [
        "N/A: no release unit. The changes land together with their call-site updates.",
        "N/A: no release unit; everything ships in the same commit.",
        "N/A: phase 1 breaks callers until another phase lands.",
        "N/A: the phases can only be validated together.",
    ],
)
def test_release_unit_na_that_says_phases_land_together_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, block: str
) -> None:
    findings = _unit_findings(tmp_path, monkeypatch, _plan_with_block(block))
    assert len(findings) == 1
    assert "declare one" in findings[0]["detail"]


@pytest.mark.parametrize(
    "block",
    [
        "N/A: no release unit",
        "N/A: every phase passes its own validation and can be merged alone.",
    ],
)
def test_release_unit_na_without_coupling_language_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, block: str
) -> None:
    assert _unit_findings(tmp_path, monkeypatch, _plan_with_block(block)) == []


def test_release_unit_absent_block_is_unaffected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _unit_findings(tmp_path, monkeypatch, _plan_with_block(None)) == []


@pytest.mark.parametrize(
    ("block", "fragment"),
    [
        ("**Unit**:  | **Phases**: 1, 2 | **Reason**: why", "missing unit name"),
        ("**Unit**: u | **Reason**: why", "expected `**Unit**"),
        ("**Unit**: u | **Phases**: 1, 2 | **Reason**:", "missing reason"),
        ("**Unit**: u | **Phases**: 1, x | **Reason**: why", "non-numeric"),
        ("**Unit**: u | **Phases**: 1, 7 | **Reason**: why", "[7] are not top-level"),
        ("   ", "block is empty"),
        ("some prose line", "expected `**Unit**"),
    ],
)
def test_release_unit_malformed_declarations_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, block: str, fragment: str
) -> None:
    findings = _unit_findings(tmp_path, monkeypatch, _plan_with_block(block))
    assert len(findings) == 1
    assert fragment in findings[0]["detail"]


def test_release_unit_block_outside_implementation_steps_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = _plan_with_block(_UNIT_OK, outside=True)
    findings = _unit_findings(tmp_path, monkeypatch, body)
    assert len(findings) == 1
    assert "outside `## Implementation steps`" in findings[0]["detail"]


def test_release_unit_real_template_skeleton_has_no_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = (_SRC_ROOT / "templates" / "plan.md").read_text(encoding="utf-8")
    fence = cwis._FENCE_RE.search(text)
    assert fence is not None
    assert "### Release units" in fence.group(1)
    assert _unit_findings(tmp_path, monkeypatch, fence.group(1)) == []


# --- archived-status (procedures archived with an unfinished row) -------------------


def _procedure_with(statuses: list[str]) -> str:
    rows = "\n".join(
        f"| {i} | Step {i} | {status} | — | — | |"
        for i, status in enumerate(statuses, start=1)
    )
    return (
        "## Execution Status\n\n### Execution Status\n"
        "| Step | Description | Status | Started | Completed | Notes |\n"
        "|------|-------------|--------|---------|-----------|-------|\n"
        f"{rows}\n"
    )


@pytest.fixture
def done_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    path = tmp_path / "implementations" / "done"
    path.mkdir(parents=True)
    return path


@pytest.mark.parametrize(
    "statuses",
    [
        ["Completed"],
        ["Completed", "Superseded"],
        ["Superseded", "Superseded"],
    ],
)
def test_archived_status_accepts_finished_or_superseded_procedures(
    done_dir: Path, statuses: list[str]
) -> None:
    _write(done_dir, "a.md", _procedure_with(statuses))

    assert cwis.find_archived_status_findings(baseline=set(), done_dir=done_dir) == []


@pytest.mark.parametrize("status", ["Pending", "In Progress", "Blocked", "pending"])
def test_archived_status_reports_an_unfinished_row(done_dir: Path, status: str) -> None:
    _write(done_dir, "a.md", _procedure_with(["Completed", status]))

    findings = cwis.find_archived_status_findings(baseline=set(), done_dir=done_dir)

    unfinished = [f for f in findings if f["category"] == "archived-status"]
    assert [f["file"] for f in unfinished] == ["implementations/done/a.md"]
    assert "Step 2" in unfinished[0]["detail"]
    assert "--superseded" in unfinished[0]["detail"]
    # A lowercase cell is also outside the exact-match vocabulary (Decision 4), so the
    # value rule reports it beside the unfinished-row finding.
    values = [f for f in findings if f["category"] == "status-value"]
    assert bool(values) == (status == "pending")


def test_archived_status_skips_baseline_paths_only(done_dir: Path) -> None:
    _write(done_dir, "old.md", _procedure_with(["Pending"]))
    _write(done_dir, "new.md", _procedure_with(["Pending"]))

    findings = cwis.find_archived_status_findings(
        baseline={"implementations/done/old.md"}, done_dir=done_dir
    )

    assert [f["file"] for f in findings] == ["implementations/done/new.md"]


def test_archived_status_ignores_a_document_without_a_status_table(
    done_dir: Path,
) -> None:
    _write(done_dir, "a.md", "# no table here\n")

    assert cwis.find_archived_status_findings(baseline=set(), done_dir=done_dir) == []


def test_archived_status_baseline_file_is_loaded_without_comments(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "baseline.txt"
    baseline.write_text("# comment\nimplementations/done/a.md\n\n", encoding="utf-8")

    assert cwis.load_archived_status_baseline(baseline) == {"implementations/done/a.md"}
    assert cwis.load_archived_status_baseline(tmp_path / "missing.txt") == set()


def test_archived_status_cli_exit_codes(
    done_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(done_dir, "a.md", _procedure_with(["Pending"]))
    empty = tmp_path / "empty.txt"
    empty.write_text("", encoding="utf-8")
    listed = tmp_path / "listed.txt"
    listed.write_text("implementations/done/a.md\n", encoding="utf-8")

    assert cwis.main(["--archived-status", "--baseline", str(empty)]) == 1
    assert "implementations/done/a.md" in capsys.readouterr().out
    assert cwis.main(["--archived-status", "--baseline", str(listed)]) == 0


def test_the_committed_archive_has_no_violation_outside_the_baseline() -> None:
    """The real archive and the real baseline: a new unfinished archive entry fails here."""
    assert cwis.main(["--archived-status"]) == 0


# --- issue template-leftover detection (REQ-002) and multi-path --file (REQ-001) ---


def _issue_scaffold() -> str:
    """The raw fenced example of the real issue template: an unfilled scaffold."""
    text = (_SRC_ROOT / "templates" / "issue.md").read_text(encoding="utf-8")
    fence = cwis._FENCE_RE.search(text)
    assert fence is not None
    return fence.group(1)


_FILLED_ISSUE_SECTIONS: dict[str, str] = {
    "Priority": "High",
    "Summary": "Gate the work item structure check on changed top-level documents.",
    "Background": "N/A: covered by Summary",
    "Problem": "A raw git commit can skip the structure check entirely.",
    "Reason for Change": "Close the gate gap before more procedures archive.",
    "Implementation Intent": "Extend the existing checker, gate, and hook definitions.",
    "Target Files or Areas": "tools/check_workitem_structure.py",
    "Required Changes": "- Accept several paths after the flag.",
    "Constraints": "N/A: none",
    "Acceptance Criteria": "- The regression tests pass.",
    "Testing Expectations": "- Unit tests under tests/tools/.",
    "Documentation Impact": "Update the tool description rows.",
    "Out of Scope": "Checkers for other document kinds.",
    "Dependencies": "N/A: none",
    "Unresolved Questions": "N/A: none",
    "AI Implementation Instruction": "Keep the diff scoped to the task.",
    "Traceability": (
        "- **Workflow phase**: `issue-creator`\n"
        "- **Source issue**: N/A: this document is the issue\n"
        "- **Source requirement**: N/A: no standalone requirement document is generated\n"
        "- **Source plan**: N/A: not filed from a Plan\n"
        "- **Source implementation procedure**: N/A: not filed from an implementation\n"
        "- **Generated at**: 20261117-000000\n"
        "- **Related target files**: tools/check_workitem_structure.py"
    ),
}


def _filled_issue() -> str:
    return "\n".join(
        f"## {heading}\n{body}\n" for heading, body in _FILLED_ISSUE_SECTIONS.items()
    )


@pytest.fixture
def issue_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _install_templates(tmp_path)
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    issues = tmp_path / "issues"
    issues.mkdir(parents=True, exist_ok=True)
    return issues


def test_unfilled_issue_scaffold_is_reported_as_template_leftover(
    issue_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = _write(issue_root, "20260104-000000_issue.md", _issue_scaffold())
    findings = cwis.collect_single_file_findings(doc)
    leftovers = [f for f in findings if f["category"] == "template-leftover"]
    assert leftovers
    assert all(f["file"] == "issues/20260104-000000_issue.md" for f in leftovers)
    assert cwis.main(["--file", str(doc)]) == 1
    assert "verbatim issue-template leftover" in capsys.readouterr().out


def test_scaffold_leftovers_name_the_title_and_placeholder_lines(
    issue_root: Path,
) -> None:
    doc = _write(issue_root, "20260104-000001_issue.md", _issue_scaffold())
    details = [f["detail"] for f in cwis.collect_single_file_findings(doc)]
    assert any("# <Issue Title>" in d for d in details)
    assert any("**Generated at**" in d for d in details)


def test_filled_issue_has_no_leftover_and_exits_zero(issue_root: Path) -> None:
    spec = cwis.load_template_specs()["issue"]
    assert {h.lower() for h in spec.required_headings} == {
        h.lower() for h in _FILLED_ISSUE_SECTIONS
    }
    doc = _write(issue_root, "20260104-000002_issue.md", _filled_issue())
    assert cwis.collect_single_file_findings(doc) == []
    assert cwis.main(["--file", str(doc)]) == 0


def test_braces_in_the_documents_own_content_are_not_reported(
    issue_root: Path,
) -> None:
    body = _filled_issue() + "\nOwn analysis with {custom} braces and {another} one.\n"
    doc = _write(issue_root, "20260104-000003_issue.md", body)
    assert cwis.collect_single_file_findings(doc) == []


def test_directory_scan_reports_issue_scaffold_leftover(issue_root: Path) -> None:
    _write(issue_root, "20260104-000004_issue.md", _issue_scaffold())
    findings = cwis.collect_findings({"issue"}, include_done=False)
    assert [f["category"] for f in findings if f["category"] == "template-leftover"]
    assert all("20260104-000004_issue.md" in f["file"] for f in findings)


@pytest.mark.parametrize(
    ("dir_name", "template_name"),
    [
        ("plans", "plan.md"),
        ("implementations", "implementation-procedure.md"),
    ],
)
def test_plan_and_procedure_skeletons_are_reported_as_leftovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dir_name: str, template_name: str
) -> None:
    """An unfilled plan or procedure scaffold is reported (reversed assertion)."""
    _install_templates(tmp_path)
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    fence = cwis._FENCE_RE.search(
        (_SRC_ROOT / "templates" / template_name).read_text(encoding="utf-8")
    )
    assert fence is not None
    doc = _write(tmp_path / dir_name, "20260105-000000_doc.md", fence.group(1))
    findings = cwis.collect_single_file_findings(doc)
    leftovers = [f for f in findings if f["category"] == "template-leftover"]
    assert leftovers
    details = " ".join(f["detail"] for f in leftovers)
    assert "unfilled Traceability value" in details
    if template_name == "plan.md":
        assert "all-empty table row" in details
        assert "bracket line" in details
    assert cwis.main(["--file", str(doc)]) == 1


def test_file_flag_accepts_several_paths_and_keeps_single_path_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_templates(tmp_path)
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    spec = cwis.load_template_specs()["plan"]
    good = _write(
        tmp_path / "plans",
        "good_plan.md",
        "\n".join(f"## {h}\nbody\n" for h in spec.required_headings),
    )
    bad = _write(
        tmp_path / "plans",
        "bad_plan.md",
        "\n".join(
            f"## {h}\nbody\n" for h in spec.required_headings if h != "Traceability"
        ),
    )
    assert cwis.main(["--file", str(good)]) == 0
    assert (
        capsys.readouterr().out == "No findings.\n"
    )  # single-path output is unchanged
    assert cwis.main(["--file", str(good), str(bad)]) == 1
    multi = capsys.readouterr().out
    assert "bad_plan.md" in multi
    assert "good_plan.md" not in multi
    assert cwis.main(["--file", str(good), str(good)]) == 0


# --- status-value rule on active plan and procedure documents (REQ-003) -------------


_STATUS_VALUE_CASES: list[tuple[list[str], bool]] = [
    (["Completed", "Pending", "In Progress", "Blocked", "Superseded", "N/A"], False),
    (["N/A"], False),
    (["Done"], True),
    (["N/A: not relevant"], True),
    (["pending"], True),
    ([""], True),
]


def _active_doc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dir_name: str,
    kind: str,
    statuses: list[str],
    *,
    filename: str = "20260106-000000_doc.md",
) -> Path:
    """A plan or procedure document: full template skeleton plus a status table."""
    _install_templates(tmp_path)
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    spec = cwis.load_template_specs()[kind]
    body = "\n".join(f"## {h}\nbody\n" for h in spec.required_headings)
    return _write(tmp_path / dir_name, filename, f"{body}\n{_procedure_with(statuses)}")


@pytest.mark.parametrize(
    ("dir_name", "kind"), [("plans", "plan"), ("implementations", "implementation")]
)
@pytest.mark.parametrize(("statuses", "reported"), _STATUS_VALUE_CASES)
def test_active_value_rule_reports_only_out_of_vocabulary_statuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dir_name: str,
    kind: str,
    statuses: list[str],
    reported: bool,
) -> None:
    doc = _active_doc(tmp_path, monkeypatch, dir_name, kind, statuses)

    values = [
        f
        for f in cwis.collect_single_file_findings(doc)
        if f["category"] == "status-value"
    ]
    assert bool(values) == reported
    if reported:
        assert values[0]["file"] == f"{dir_name}/20260106-000000_doc.md"
        assert "outside the vocabulary" in values[0]["detail"]


def test_multi_path_file_flag_aggregates_status_value_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    good = _active_doc(
        tmp_path, monkeypatch, "plans", "plan", ["Completed"], filename="good_plan.md"
    )
    bad = _active_doc(
        tmp_path,
        monkeypatch,
        "implementations",
        "implementation",
        ["Done"],
        filename="bad_procedure.md",
    )

    assert cwis.main(["--file", str(good), str(bad)]) == 1
    out = capsys.readouterr().out
    assert "outside the vocabulary" in out
    assert "implementations/bad_procedure.md" in out
    assert "plans/good_plan.md" not in out


def test_directory_scan_value_rule_skips_archived_documents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _active_doc(
        tmp_path, monkeypatch, "plans", "plan", ["Completed"], filename="good_plan.md"
    )
    _active_doc(
        tmp_path,
        monkeypatch,
        "implementations",
        "implementation",
        ["Done"],
        filename="bad_procedure.md",
    )
    _active_doc(
        tmp_path,
        monkeypatch,
        "plans/done",
        "plan",
        ["Done"],
        filename="archived_plan.md",
    )

    findings = cwis.collect_findings({"plan", "implementation"}, include_done=True)
    values = [f for f in findings if f["category"] == "status-value"]
    assert [f["file"] for f in values] == ["implementations/bad_procedure.md"]


# --- archived status-value scan: baseline grandfathering (REQ-004) ------------------


def test_archived_value_scan_skips_baseline_listed_paths(
    done_dir: Path, tmp_path: Path
) -> None:
    plans_done = tmp_path / "plans" / "done"
    _write(done_dir, "a.md", _procedure_with(["Done"]))
    _write(plans_done, "p.md", _procedure_with(["Complete"]))

    findings = cwis.find_archived_status_value_findings(
        (done_dir, plans_done), value_baseline={"implementations/done/a.md"}
    )

    assert [(f["category"], f["file"]) for f in findings] == [
        ("status-value", "plans/done/p.md")
    ]


def test_archived_value_scan_default_baseline_missing_file_reports_every_holder(
    done_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cwis, "STATUS_VALUE_BASELINE", tmp_path / "missing.txt")
    _write(done_dir, "a.md", _procedure_with(["Skipped"]))

    findings = cwis.find_archived_status_value_findings((done_dir,))

    assert [f["file"] for f in findings] == ["implementations/done/a.md"]


def test_archived_value_scan_default_baseline_file_skips_listed_paths(
    done_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline = tmp_path / "baseline.txt"
    baseline.write_text("# comment\nimplementations/done/a.md\n\n", encoding="utf-8")
    monkeypatch.setattr(cwis, "STATUS_VALUE_BASELINE", baseline)
    _write(done_dir, "a.md", _procedure_with(["Done"]))
    _write(done_dir, "b.md", _procedure_with(["Complete", "Deferred"]))

    findings = cwis.find_archived_status_value_findings((done_dir,))

    assert [f["file"] for f in findings] == ["implementations/done/b.md"]


def test_archived_status_cli_reports_value_findings(
    done_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cwis, "STATUS_VALUE_BASELINE", tmp_path / "missing.txt")
    _write(done_dir, "a.md", _procedure_with(["Completed", "Done"]))

    assert cwis.main(["--archived-status"]) == 1
    out = capsys.readouterr().out
    assert "outside the vocabulary" in out
    assert (
        "Step 2" not in out
    )  # 'Done' is not an unfinished row: no archived-status finding


def test_the_committed_archived_value_baseline_covers_the_live_archive() -> None:
    """A new archived holder outside the committed baseline fails here."""
    assert cwis.find_archived_status_value_findings() == []


# --- live repository state and template equality (REQ-005) --------------------------


def test_the_live_active_documents_hold_no_status_value_violation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cwis, "ROOT_DIR", _SRC_ROOT)
    findings = cwis.collect_findings({"plan", "implementation"}, include_done=False)
    assert [f for f in findings if f["category"] == "status-value"] == []


def test_execution_status_template_options_equal_the_shared_vocabulary() -> None:
    text = (_SRC_ROOT / "templates" / "execution-status.md").read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.startswith("Status options:")]
    assert len(lines) == 1
    options = {part.strip() for part in lines[0].split(":", 1)[1].split(" / ")}
    assert options == set(STATUS_VOCABULARY)


# --- plan and procedure scaffold leftovers (REQ-001 to REQ-004) ---------------------


def _scaffold(template_name: str) -> str:
    """The raw fenced example of a real template: an unfilled scaffold."""
    text = (_SRC_ROOT / "templates" / template_name).read_text(encoding="utf-8")
    fence = cwis._FENCE_RE.search(text)
    assert fence is not None
    return fence.group(1)


_PLAN_BRACKET_LINE = "[Why this requirement exists]"

_EXECUTION_TABLES = (
    "### Execution Status\n"
    "| Step | Description | Status | Started | Completed | Notes |\n"
    "|------|-------------|--------|---------|-----------|-------|\n"
    "| 1 | Land the change | Pending | — | — | |\n\n"
    "### Blocker Log\n"
    "| Step | Blocker Description | Resolved | Resolution Date |\n"
    "|------|---------------------|----------|-----------------|\n"
    "| — | — | — | — |\n\n"
    "### Work Items Created\n"
    "| Item ID | Related Step | Type | Status | Owner | Due Date |\n"
    "|---------|--------------|------|--------|-------|----------|\n"
    "| — | — | — | — | — | — |"
)


def _filled_body(kind: str) -> str:
    """A filled document body: every required heading, no scaffold line kept.

    Body prose carries `{inline}` braces (own content, not a scaffold line),
    the Execution Status family keeps the dash placeholder rows of
    `templates/execution-status.md`, and the plan Goal holds the template's
    verbatim Freeze paragraph (the rules never compare prose).
    """
    freeze = "\n".join(
        line
        for line in (_SRC_ROOT / "templates" / "plan.md")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.startswith("**Freeze status**")
    )
    traceability = (
        "- **Workflow phase**: `plan-to-implementation-procedure`\n"
        "- **Requirement ID**: REQ-001\n"
        "- **Source issue**: issues/20260105-000000_gate-gap.md\n"
        "- **Source plan**: plans/20260105-000001_gate-gap.md\n"
        "- **Generated at**: 20260105-000002\n"
        "- **Related target files**: tools/foo.py"
    )
    bodies: dict[str, str] = {}
    for heading in cwis.load_template_specs()[kind].required_headings:
        if heading == "Execution Status":
            bodies[heading] = _EXECUTION_TABLES
        elif heading == "Traceability":
            bodies[heading] = traceability
        elif heading == "Implementation steps":
            bodies[heading] = "1. **Phase 1: Landing (REQ-001)**\n   - Land the change."
        elif heading == "Goal" and kind == "plan":
            bodies[heading] = freeze
        else:
            bodies[heading] = "Filled prose with {inline} braces."
    return "\n".join(f"## {heading}\n{bodies[heading]}\n" for heading in bodies)


@pytest.fixture
def doc_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _install_templates(tmp_path)
    monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)
    return tmp_path


def _leftovers_of(doc: Path) -> list[dict[str, str]]:
    return [
        f
        for f in cwis.collect_single_file_findings(doc)
        if f["category"] == "template-leftover"
    ]


def test_filled_plan_and_procedure_report_no_leftovers(doc_root: Path) -> None:
    plan = _write(doc_root / "plans", "20260105-000010_plan.md", _filled_body("plan"))
    proc = _write(
        doc_root / "implementations",
        "20260105-000011_procedure.md",
        _filled_body("implementation"),
    )
    assert _leftovers_of(plan) == []
    assert cwis.collect_single_file_findings(plan) == []
    assert _leftovers_of(proc) == []
    assert cwis.collect_single_file_findings(proc) == []


def test_plan_scaffold_leftovers_name_line_number_and_text(doc_root: Path) -> None:
    doc = _write(doc_root / "plans", "20260105-000012_plan.md", _scaffold("plan.md"))
    leftovers = _leftovers_of(doc)
    assert all(f["file"] == "plans/20260105-000012_plan.md" for f in leftovers)
    assert all("line" in f["detail"] for f in leftovers)
    assert any(_PLAN_BRACKET_LINE in f["detail"] for f in leftovers)
    assert any("- **Generated at**: {timestamp}" in f["detail"] for f in leftovers)
    assert any(f["detail"].startswith("all-empty table row") for f in leftovers)


@pytest.mark.parametrize(
    ("dir_name", "kind", "reported"),
    [("plans", "plan", True), ("implementations", "implementation", False)],
)
def test_bracket_rule_is_plan_only(
    doc_root: Path, dir_name: str, kind: str, reported: bool
) -> None:
    body = _filled_body(kind).replace(
        "Filled prose with {inline} braces.",
        f"Filled prose.\n{_PLAN_BRACKET_LINE}\n",
        1,
    )
    doc = _write(doc_root / dir_name, f"20260105-000013_{kind}.md", body)
    bracket = [f for f in _leftovers_of(doc) if "bracket line" in f["detail"]]
    assert bool(bracket) == reported


def test_bracket_findings_follow_a_rewritten_fence(doc_root: Path) -> None:
    """The bracket set is derived from the template fence at run time."""
    template = doc_root / "templates" / "plan.md"
    template.write_text(
        template.read_text(encoding="utf-8").replace(
            _PLAN_BRACKET_LINE, "[A replacement placeholder]"
        ),
        encoding="utf-8",
    )
    old = _write(
        doc_root / "plans",
        "20260105-000014_plan.md",
        _filled_body("plan").replace(
            "Filled prose with {inline} braces.",
            f"Filled prose.\n{_PLAN_BRACKET_LINE}\n",
            1,
        ),
    )
    new = _write(
        doc_root / "plans",
        "20260105-000015_plan.md",
        _filled_body("plan").replace(
            "Filled prose with {inline} braces.",
            "Filled prose.\n[A replacement placeholder]\n",
            1,
        ),
    )
    assert not [f for f in _leftovers_of(old) if "bracket line" in f["detail"]]
    assert [f for f in _leftovers_of(new) if "bracket line" in f["detail"]]


def test_directory_scan_reports_plan_and_procedure_scaffolds(doc_root: Path) -> None:
    _write(doc_root / "plans", "20260105-000016_plan.md", _scaffold("plan.md"))
    _write(
        doc_root / "implementations",
        "20260105-000017_procedure.md",
        _scaffold("implementation-procedure.md"),
    )
    findings = cwis.collect_findings({"plan", "implementation"}, include_done=False)
    files = {f["file"] for f in findings if f["category"] == "template-leftover"}
    assert files == {
        "plans/20260105-000016_plan.md",
        "implementations/20260105-000017_procedure.md",
    }


def test_multi_path_file_flag_aggregates_leftover_findings(
    doc_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    filled = _write(doc_root / "plans", "filled_plan.md", _filled_body("plan"))
    plan_scaffold = _write(doc_root / "plans", "scaffold_plan.md", _scaffold("plan.md"))
    proc_scaffold = _write(
        doc_root / "implementations",
        "scaffold_procedure.md",
        _scaffold("implementation-procedure.md"),
    )
    assert (
        cwis.main(["--file", str(filled), str(plan_scaffold), str(proc_scaffold)]) == 1
    )
    out = capsys.readouterr().out
    assert "scaffold_plan.md" in out
    assert "scaffold_procedure.md" in out
    assert "filled_plan.md" not in out


@pytest.mark.parametrize("include_done", [False, True])
def test_archived_scaffolds_are_not_scanned_for_leftovers(
    doc_root: Path, include_done: bool
) -> None:
    _write(
        doc_root / "plans" / "done",
        "20260105-000018_plan.md",
        _scaffold("plan.md"),
    )
    findings = cwis.collect_findings({"plan"}, include_done=include_done)
    assert [f for f in findings if f["category"] == "template-leftover"] == []


def test_the_live_active_documents_hold_no_template_leftover(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cwis, "ROOT_DIR", _SRC_ROOT)
    findings = cwis.collect_findings({"plan", "implementation"}, include_done=False)
    assert [f for f in findings if f["category"] == "template-leftover"] == []


# --- rule module entry points without the checker layer (AC-1) ----------------------


def test_rule_module_entry_points_report_scaffolds_not_filled(doc_root: Path) -> None:
    """The rule module's entry points work without the checker layer (AC-1)."""
    brackets = wlr.plan_bracket_lines(doc_root / "templates" / "plan.md")
    assert _PLAN_BRACKET_LINE in brackets
    plan_scaffold = _write(
        doc_root / "plans", "20260105-000019_plan.md", _scaffold("plan.md")
    )
    filled_plan = _write(
        doc_root / "plans", "20260105-000020_plan.md", _filled_body("plan")
    )
    proc_scaffold = _write(
        doc_root / "implementations",
        "20260105-000021_procedure.md",
        _scaffold("implementation-procedure.md"),
    )
    filled_proc = _write(
        doc_root / "implementations",
        "20260105-000022_procedure.md",
        _filled_body("implementation"),
    )
    issue_scaffold = _write(
        doc_root / "issues", "20260105-000023_issue.md", _scaffold("issue.md")
    )
    filled_issue = _write(
        doc_root / "issues", "20260105-000024_issue.md", _filled_issue()
    )
    assert wlr.find_plan_leftover_findings(plan_scaffold, doc_root, brackets)
    assert wlr.find_plan_leftover_findings(filled_plan, doc_root, brackets) == []
    assert wlr.find_procedure_leftover_findings(proc_scaffold, doc_root)
    assert wlr.find_procedure_leftover_findings(filled_proc, doc_root) == []
    assert wlr.find_issue_leftover_findings(issue_scaffold, doc_root)
    assert wlr.find_issue_leftover_findings(filled_issue, doc_root) == []


# --- advisory length rule for documentation-only procedures -------------------------


def _docs_procedure(target_line: str, extra_lines: int) -> str:
    body = _filled_body("implementation")
    return (
        f"{body}\n## Implementation\n### Target file\n{target_line}\n"
        + "Padding line.\n" * extra_lines
    )


@pytest.mark.parametrize("target_line", ["`docs/a.md`", "- `docs/a.md`"])
def test_long_docs_procedure_is_reported_but_does_not_fail(
    doc_root: Path, target_line: str
) -> None:
    doc = _write(
        doc_root / "implementations",
        "20260105-000020_procedure.md",
        _docs_procedure(target_line, 70),
    )
    findings = [
        f
        for f in cwis.collect_single_file_findings(doc)
        if f["category"] == "procedure-length"
    ]
    assert len(findings) == 1
    assert findings[0]["file"] == "implementations/20260105-000020_procedure.md"
    assert cwis.main(["--file", str(doc)]) == 0


def test_short_docs_procedure_and_long_code_procedure_are_not_reported(
    doc_root: Path,
) -> None:
    short = _write(
        doc_root / "implementations",
        "20260105-000021_procedure.md",
        "## Goal\n### Target file\n`docs/a.md`\n",
    )
    code = _write(
        doc_root / "implementations",
        "20260105-000022_procedure.md",
        _docs_procedure("`scripts/a.py`", 70),
    )
    for doc in (short, code):
        assert [
            f
            for f in cwis.collect_single_file_findings(doc)
            if f["category"] == "procedure-length"
        ] == []


def test_length_finding_does_not_mask_a_blocking_finding(doc_root: Path) -> None:
    doc = _write(
        doc_root / "implementations",
        "20260105-000023_procedure.md",
        "## Goal\n### Target file\n`docs/a.md`\n" + "Padding line.\n" * 70,
    )
    assert cwis.main(["--file", str(doc)]) == 1
