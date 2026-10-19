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
