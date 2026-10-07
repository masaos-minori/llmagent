"""tests/tools/test_check_adr_structure.py
Tests for tools/check_adr_structure.py.

Each scenario builds an in-memory DocFile (a small set of lines) and calls
check_known_deviations_heading()/check_notes_references_drift() directly --
matching tests/tools/test_check_adr_reference.py's direct-function-call
pattern. Live docs/10_adr/*.md validation is exercised separately by running the
tool against the real repository, not duplicated here as a unit test.
"""

from __future__ import annotations

from pathlib import Path

from tools._docs_consistency_lib import DocFile
from tools.check_adr_structure import (
    _HEADING_ORDER,
    _REQUIRED_HEADINGS,
    check_known_deviations_heading,
    check_notes_references_drift,
    check_section_headings,
    check_template_residue,
)


def _doc(*lines: str) -> DocFile:
    return DocFile(
        path=Path("ADR-999-test.md"), rel_path="ADR-999-test.md", lines=list(lines)
    )


class TestCheckKnownDeviationsHeading:
    def test_missing_known_deviations_heading_flagged_error(self) -> None:
        doc = _doc(
            "## Implementation Notes",
            "",
            "some notes",
            "",
            "## Review Triggers",
        )
        issues = check_known_deviations_heading([doc])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"
        assert issues[0].file == "ADR-999-test.md"
        assert "Known Deviations" in issues[0].message

    def test_present_known_deviations_heading_not_flagged(self) -> None:
        doc = _doc(
            "## Implementation Notes",
            "",
            "## Known Deviations",
            "",
            "no deviations",
        )
        assert check_known_deviations_heading([doc]) == []


class TestCheckNotesReferencesDrift:
    def test_notes_path_absent_from_references_flagged_warning(self) -> None:
        doc = _doc(
            "## Implementation Notes",
            "",
            "Uses `scripts/foo.py` to do the thing.",
            "",
            "## Related Documents",
            "",
            "## Implementation References",
            "",
            "- `scripts/bar.py` — unrelated file",
            "",
            "## Completion Checklist",
        )
        issues = check_notes_references_drift([doc])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert issues[0].file == "ADR-999-test.md"
        assert "scripts/foo.py" in issues[0].message

    def test_notes_path_present_in_references_not_flagged(self) -> None:
        doc = _doc(
            "## Implementation Notes",
            "",
            "Uses `scripts/foo.py` to do the thing.",
            "",
            "## Related Documents",
            "",
            "## Implementation References",
            "",
            "- `scripts/foo.py` — the same file",
            "",
            "## Completion Checklist",
        )
        assert check_notes_references_drift([doc]) == []

    def test_notes_with_zero_paths_not_flagged_regardless_of_references(
        self,
    ) -> None:
        doc = _doc(
            "## Implementation Notes",
            "",
            "現在の実装がDecisionをどのように実現しているかを簡潔に記載する。",
            "",
            "## Related Documents",
            "",
            "## Implementation References",
            "",
            "- `scripts/unrelated.py` — not cited by Notes at all",
            "",
            "## Completion Checklist",
        )
        assert check_notes_references_drift([doc]) == []


def _full_adr(*, omit: str | None = None, extra: str | None = None) -> DocFile:
    titles = [t for t in _REQUIRED_HEADINGS if t != omit]
    lines = [f"## {t}" for t in titles]
    if extra:
        lines.insert(3, f"## {extra}")
    return _doc(*lines)


class TestCheckSectionHeadings:
    def test_complete_adr_has_no_findings(self) -> None:
        assert check_section_headings([_full_adr()]) == []

    def test_conditional_sections_between_invariants_and_verification_are_allowed(
        self,
    ) -> None:
        titles = list(_HEADING_ORDER)
        doc = _doc(*[f"## {t}" for t in titles])
        assert check_section_headings([doc]) == []

    def test_unknown_heading_is_reported(self) -> None:
        issues = check_section_headings([_full_adr(extra="Traceability")])
        assert any("not an allowed ADR heading" in i.message for i in issues)

    def test_missing_required_heading_is_reported(self) -> None:
        issues = check_section_headings([_full_adr(omit="Status")])
        assert [i.message for i in issues] == ["missing required heading '## Status'"]

    def test_out_of_order_heading_is_reported(self) -> None:
        lines = [f"## {t}" for t in _REQUIRED_HEADINGS]
        lines[0], lines[1] = lines[1], lines[0]
        issues = check_section_headings([_doc(*lines)])
        assert any("out of order" in i.message for i in issues)

    def test_non_adr_files_are_ignored(self) -> None:
        doc = DocFile(
            path=Path("adr-index.md"), rel_path="adr-index.md", lines=["## X"]
        )
        assert check_section_headings([doc]) == []

    def test_headings_inside_code_fences_are_ignored(self) -> None:
        lines = [f"## {t}" for t in _REQUIRED_HEADINGS]
        lines += ["```", "## Not A Heading", "```"]
        assert check_section_headings([_doc(*lines)]) == []


class TestCheckTemplateResidue:
    def test_instruction_text_is_reported(self) -> None:
        issues = check_template_residue([_doc("Briefly describe how it works.")])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"

    def test_global_invariant_id_is_reported(self) -> None:
        issues = check_template_residue([_doc("See INV-024 for details.")])
        assert len(issues) == 1
        assert "ADR-local" in issues[0].message

    def test_local_invariant_id_is_accepted(self) -> None:
        assert check_template_residue([_doc("See ADR-014 INV-02.")]) == []
