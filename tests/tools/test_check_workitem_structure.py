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

    assert [f["category"] for f in findings] == ["archived-status"]
    assert findings[0]["file"] == "implementations/done/a.md"
    assert "Step 2" in findings[0]["detail"]
    assert "--superseded" in findings[0]["detail"]


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
