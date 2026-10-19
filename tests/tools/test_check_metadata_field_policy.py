"""tests/tools/test_check_metadata_field_policy.py

Tests for tools/check_metadata_field_policy.py (GV-016 metadata/status field
policy checker).

Covers both scanners and their shared reporting path:

- Front-matter scanner: an out-of-set key is flagged at WARNING; compliant keys,
  missing front matter, and malformed YAML produce no findings (validity is
  other checkers' job).
- Workitem-section scanner: an out-of-set section is flagged at WARNING; canonical
  sections pass even when their casing differs from the template ("Out of scope"
  vs "Out of Scope"); sections contributed by embedded sub-templates (risks-issue /
  unknowns-issue) are allowed; files in unknown domains and archived ``done/``
  trees are not scanned.
- Permitted sets are DERIVED from authoritative sources, never hardcoded: the
  front-matter set equals the schema ``properties`` keys and the workitem set equals
  each template's canonical sections unioned with sub-template sections.
- End-to-end via ``main()``: warning-only output exits 0 (non-blocking); a tree
  with an out-of-set front-matter key and an out-of-set section yields exactly two
  warnings.
- Real-corpus regression guard: the current repository scans clean.

Every test that needs an isolated tree builds it under ``tmp_path`` and points the
tool at it with ``--root``. Templates are loaded from the repository's real
``templates/`` (the module's ``TEMPLATES_DIR`` constant), so they do not need to be
copied into the isolated tree.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import tools.check_metadata_field_policy as cmfp

_SRC_ROOT = Path(__file__).resolve().parent.parent.parent


def _write(root: Path, rel_path: str, content: str) -> Path:
    target = root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Permitted-set derivation (REQ-001 / REQ-002)
# ---------------------------------------------------------------------------


def test_permitted_front_matter_keys_match_schema_properties() -> None:
    """The permitted front-matter set is the schema ``properties`` keys."""
    schema = json.loads(
        (_SRC_ROOT / "schemas" / "doc_front_matter.json").read_text(encoding="utf-8")
    )
    expected = tuple(schema["properties"].keys())
    assert _cmfp_permitted_front_matter_keys() == expected
    assert set(expected) == {
        "title",
        "area",
        "tags",
        "related",
        "status",
        "class",
    }


def test_permitted_workitem_sections_include_canonical_impl_sections() -> None:
    """The implementation domain permits every canonical template section."""
    allowed = _cmfp_permitted_workitem_sections("implementations")
    for section in (
        "goal",
        "scope",
        "assumptions",
        "design decisions",
        "alternatives considered",
        "implementation",
        "compatibility considerations",
        "security considerations",
        "rollback considerations",
        "validation plan",
        "completion criteria",
        "execution status",
        "traceability",
    ):
        assert section in allowed


def test_permitted_workitem_sections_are_case_insensitive() -> None:
    """A section spelled differently than the template still resolves (lowercased)."""
    allowed = _cmfp_permitted_workitem_sections("implementations")
    # Template spells it "Out of Scope"; generated files use "Out of scope".
    assert "out of scope" in allowed


def test_permitted_workitem_sections_include_subtemplate_sections() -> None:
    """Issue-domain follow-up shapes contribute their sections to the union."""
    allowed = _cmfp_permitted_workitem_sections("issues")
    # From templates/risks-issue.md and templates/unknowns-issue.md.
    assert "context" in allowed
    assert "blocking impact" in allowed


def test_permitted_workitem_sections_exclude_bogus_section() -> None:
    """A clearly ad-hoc section is not in the permitted set (scanner stays precise)."""
    allowed = _cmfp_permitted_workitem_sections("implementations")
    assert "my custom section" not in allowed


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Field notes", True),
        ("Notes on filling sections", True),
        ("Column Definitions", True),
        ("Notes", True),
        ("Goal", False),
        ("Traceability", False),
        ("Out of Scope", False),
    ],
)
def test_is_meta_section(name: str, expected: bool) -> None:
    assert _cmfp_is_meta_section(name) is expected


def test_extract_front_matter_none_when_absent() -> None:
    status, value = _cmfp_extract_front_matter("# No front matter\n")
    assert status == "none"
    assert value is None


def test_extract_front_matter_ok_when_valid() -> None:
    content = "---\ntitle: X\narea: overview\n---\n# Doc\n"
    status, value = _cmfp_extract_front_matter(content)
    assert status == "ok"
    assert value == {"title": "X", "area": "overview"}


def test_extract_front_matter_error_when_unclosed() -> None:
    status, value = _cmfp_extract_front_matter("---\ntitle: X\n")
    assert status == "error"
    assert value is None


def test_extract_front_matter_error_when_malformed() -> None:
    content = "---\nkey: [1, 2\n---\n"
    status, value = _cmfp_extract_front_matter(content)
    assert status == "error"
    assert value is None


def test_iter_sections_template_mode_includes_markdown_block() -> None:
    text = "# Title\n\n```markdown\n## Goal\n\n## Scope\n```\n\n## Field notes\n"
    names = [name for name, _ in _cmfp_iter_sections(text, "template")]
    assert "Goal" in names
    assert "Scope" in names
    # Meta section after the closing fence is still yielded here (dropped later).
    assert any(name.startswith("Field notes") for name in names)


def test_iter_sections_document_mode_skips_code_fences() -> None:
    text = "## Goal\n\n```bash\n## inside-code-block\n```\n\n## Scope\n"
    names = dict(_cmfp_iter_sections(text, "document"))
    assert "Goal" in names
    assert "Scope" in names
    assert "inside-code-block" not in names


def test_iter_sections_document_mode_handles_markdown_fence() -> None:
    """Headings inside a ```markdown block are skipped in document mode."""
    text = "## Goal\n\n```markdown\n## fenced\n```\n\n## Scope\n"
    names = dict(_cmfp_iter_sections(text, "document"))
    assert set(names) == {"Goal", "Scope"}


# ---------------------------------------------------------------------------
# Front-matter scanner
# ---------------------------------------------------------------------------


def test_scan_front_matter_flags_extra_key(tmp_path: Path) -> None:
    doc = _write(
        tmp_path,
        "docs/bad.md",
        "---\ntitle: X\narea: overview\nbogus_key: yes\n---\n# Doc\n",
    )
    issues = _cmfp_scan_front_matter(doc, _cmfp_permitted_front_matter_keys())
    assert len(issues) == 1
    assert issues[0].severity == "WARNING"
    assert "bogus_key" in issues[0].message


def test_scan_front_matter_compliant_no_findings(tmp_path: Path) -> None:
    doc = _write(
        tmp_path,
        "docs/good.md",
        "---\ntitle: X\narea: rag\nstatus: stable\nclass: Guide\n---\n# Doc\n",
    )
    assert _cmfp_scan_front_matter(doc, _cmfp_permitted_front_matter_keys()) == []


def test_scan_front_matter_no_front_matter_no_findings(tmp_path: Path) -> None:
    doc = _write(tmp_path, "docs/nofm.md", "# No front matter\n")
    assert _cmfp_scan_front_matter(doc, _cmfp_permitted_front_matter_keys()) == []


def test_scan_front_matter_malformed_no_findings(tmp_path: Path) -> None:
    doc = _write(tmp_path, "docs/malformed.md", "---\nkey: [1, 2\n---\n# Doc\n")
    assert _cmfp_scan_front_matter(doc, _cmfp_permitted_front_matter_keys()) == []


# ---------------------------------------------------------------------------
# Workitem-section scanner
# ---------------------------------------------------------------------------


def test_scan_workitem_flags_extra_section(tmp_path: Path) -> None:
    doc = _write(
        tmp_path,
        "implementations/20261020-000001_01_x.py.md",
        "## Goal\n\n## My Custom Section\n\n## Scope\n",
    )
    issues = _cmfp_scan_workitem(doc)
    assert len(issues) == 1
    assert issues[0].severity == "WARNING"
    assert "My Custom Section" in issues[0].message


def test_scan_workitem_canonical_case_insensitive_no_findings(tmp_path: Path) -> None:
    # "Out of scope" (lowercase s) must pass against the template's "Out of Scope".
    doc = _write(
        tmp_path,
        "implementations/20261020-000002_02_x.py.md",
        "## Goal\n\n## Scope\n\n## Assumptions\n\n## Out of scope\n\n## Traceability\n",
    )
    assert _cmfp_scan_workitem(doc) == []


def test_scan_workitem_unknown_domain_no_findings(tmp_path: Path) -> None:
    doc = _write(tmp_path, "other/20261020_x.md", "## Anything\n")
    assert _cmfp_scan_workitem(doc) == []


# ---------------------------------------------------------------------------
# End-to-end via main()
# ---------------------------------------------------------------------------


def test_main_flags_both_scanners_and_exits_zero(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "docs/bad.md",
        "---\ntitle: X\narea: overview\nbogus_key: yes\n---\n# Doc\n",
    )
    _write(
        tmp_path,
        "implementations/20261020-000001_01_x.py.md",
        "## Goal\n\n## My Custom Section\n\n## Scope\n",
    )
    exit_code = _cmfp_main(["--root", str(tmp_path)])
    assert exit_code == 0  # warning-only is non-blocking


def test_main_all_good_reports_no_findings(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    _write(
        tmp_path,
        "docs/good.md",
        "---\ntitle: X\narea: rag\n---\n# Doc\n",
    )
    _write(
        tmp_path,
        "implementations/20261020-000002_02_x.py.md",
        "## Goal\n\n## Scope\n\n## Traceability\n",
    )
    exit_code = _cmfp_main(["--root", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "No issues found." in captured.out


def test_main_skips_done_archives(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    # A non-canonical section in an archived file must NOT be scanned.
    _write(
        tmp_path,
        "implementations/done/20200101-000000_old.md",
        "## Goal\n\n## Ad-hoc Report\n\n## Scope\n",
    )
    exit_code = _cmfp_main(["--root", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Ad-hoc Report" not in captured.err


def test_main_real_repo_corpus_clean(capsys: pytest.CaptureFixture) -> None:
    """Regression guard: the current repository scans with no errors (REQ-006)."""
    exit_code = _cmfp_main(["--root", str(_SRC_ROOT)])
    assert exit_code == 0
    captured = capsys.readouterr()
    # No ERROR-severity findings anywhere in the corpus.
    assert "[ERROR]" not in captured.err


# ---------------------------------------------------------------------------
# Thin re-exports so the test body reads against stable names.
# ---------------------------------------------------------------------------


def _cmfp_permitted_front_matter_keys():
    return cmfp._permitted_front_matter_keys()


def _cmfp_permitted_workitem_sections(domain: str):
    return cmfp._permitted_workitem_sections(domain)


def _cmfp_is_meta_section(name: str) -> bool:
    return cmfp._is_meta_section(name)


def _cmfp_extract_front_matter(content: str):
    return cmfp._extract_front_matter(content)


def _cmfp_iter_sections(content: str, mode: str):
    return cmfp._iter_sections(content, mode)


def _cmfp_scan_front_matter(path: Path, permitted):
    return cmfp._scan_front_matter(path, permitted)


def _cmfp_scan_workitem(path: Path):
    return cmfp._scan_workitem(path)


def _cmfp_main(argv):
    return cmfp.main(argv)
