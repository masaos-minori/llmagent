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
    _ADR_FILE_RE,
    _ALLOWED_STATUSES,
    _HEADING_ORDER,
    _LEDGER_DOC,
    _REQUIRED_HEADINGS,
    _ledger_ids_from_lines,
    _load_ledger_ids,
    check_known_deviations_heading,
    check_notes_references_drift,
    check_pending_approval_form,
    check_section_headings,
    check_status_values,
    check_template_residue,
)


def _doc(*lines: str) -> DocFile:
    return DocFile(
        path=Path("adr_02_99_999_test.md"),
        rel_path="adr_02_99_999_test.md",
        lines=list(lines),
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
        assert issues[0].file == "adr_02_99_999_test.md"
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
        assert issues[0].file == "adr_02_99_999_test.md"
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
            path=Path("adr_01_index.md"), rel_path="adr_01_index.md", lines=["## X"]
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


class TestAdrFileNamePattern:
    def test_every_real_adr_file_matches(self) -> None:
        adr_dir = Path(__file__).resolve().parents[2] / "docs" / "10_adr"
        names = sorted(p.name for p in adr_dir.glob("adr_02_*.md"))
        assert len(names) == 16
        assert [n for n in names if not _ADR_FILE_RE.match(n)] == []

    def test_old_shape_does_not_match(self) -> None:
        assert _ADR_FILE_RE.match("adr_02_001_x.md") is None

    def test_missing_heading_in_new_shape_fixture_is_reported(self) -> None:
        doc = _doc("# ADR-999", "", "## Context")
        issues = check_section_headings([doc])
        assert issues, "check_section_headings skipped a new-shape ADR file"


class TestCheckStatusValues:
    def test_every_allowed_value_is_accepted(self) -> None:
        for value in _ALLOWED_STATUSES:
            doc = _doc("## Status", "", value, "", "## Summary")
            assert check_status_values([doc]) == []

    def test_unknown_value_is_reported(self) -> None:
        issues = check_status_values([_doc("## Status", "", "Draft", "", "## Summary")])
        assert [(i.severity, i.line_no) for i in issues] == [("ERROR", 3)]
        assert "Draft" in issues[0].message

    def test_value_followed_by_a_paragraph_is_accepted(self) -> None:
        doc = _doc("## Status", "", "Withdrawn", "", "The text below is a record.")
        assert check_status_values([doc]) == []

    def test_status_without_a_value_is_reported(self) -> None:
        issues = check_status_values([_doc("## Status", "", "## Summary")])
        assert [i.message for i in issues] == ["'## Status' has no value"]

    def test_missing_status_heading_is_left_to_the_heading_check(self) -> None:
        assert check_status_values([_doc("## Summary", "", "Accepted")]) == []

    def test_non_adr_files_are_ignored(self) -> None:
        doc = DocFile(
            path=Path("adr_01_index.md"),
            rel_path="adr_01_index.md",
            lines=["## Status", "", "Draft"],
        )
        assert check_status_values([doc]) == []

    def test_allowed_values_match_the_policy_document(self) -> None:
        policy = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "00_governance"
            / "governance_01_documentation-policy.md"
        ).read_text(encoding="utf-8")
        section = policy.split("## ADR Status Definitions", 1)[1].split("\n#", 1)[0]
        defined = {
            line.split("`")[1]
            for line in section.splitlines()
            if line.startswith("- `")
        }
        assert defined == set(_ALLOWED_STATUSES)


_PENDING = (
    "- **Current Decision Approval (pending)**: Changed text awaits approval; "
    "it is tracked by AAL-001. No approval is recorded here."
)


def _approval_doc(*bullets: str) -> DocFile:
    return _doc(
        "## Approval",
        "",
        "### Required Reviewers",
        "",
        "### Approval Record",
        "",
        *bullets,
        "",
        "## Related ADRs",
    )


class TestCheckPendingApprovalForm:
    def test_resolving_id_is_accepted(self) -> None:
        issues = check_pending_approval_form(
            [_approval_doc(_PENDING)], frozenset({"AAL-001"})
        )
        assert issues == []

    def test_bullet_without_an_id_is_reported(self) -> None:
        bullet = "- **Current Decision Approval (pending)**: Changed text."
        issues = check_pending_approval_form([_approval_doc(bullet)], frozenset())
        assert [i.severity for i in issues] == ["ERROR"]
        assert "cites no" in issues[0].message

    def test_unresolved_id_is_reported(self) -> None:
        issues = check_pending_approval_form(
            [_approval_doc(_PENDING)], frozenset({"AAL-002"})
        )
        assert len(issues) == 1
        assert "AAL-001" in issues[0].message

    def test_withdrawal_record_is_not_checked(self) -> None:
        doc = _doc(
            "### Withdrawal Approval Record",
            "",
            "- **Current Decision Approval (pending)**: no ID here",
        )
        assert check_pending_approval_form([doc], frozenset()) == []

    def test_bullet_outside_the_approval_record_is_ignored(self) -> None:
        doc = _doc("## Summary", "", _PENDING)
        assert check_pending_approval_form([doc], frozenset()) == []

    def test_fenced_bullet_is_ignored(self) -> None:
        doc = _doc("### Approval Record", "```", _PENDING, "```")
        assert check_pending_approval_form([doc], frozenset()) == []

    def test_non_adr_files_are_ignored(self) -> None:
        doc = DocFile(
            path=Path("adr_01_index.md"),
            rel_path="adr_01_index.md",
            lines=["### Approval Record", _PENDING],
        )
        assert check_pending_approval_form([doc], frozenset()) == []


class TestLedgerIds:
    def test_entry_headings_are_collected(self) -> None:
        lines = [
            "#### AAL-001",
            "- **ID:** AAL-001",
            "#### AAL-014",
            "#### SHARED-001",
            "### Rules",
        ]
        assert _ledger_ids_from_lines(lines) == frozenset({"AAL-001", "AAL-014"})

    def test_ledger_document_exists_and_lists_entries(self) -> None:
        assert _LEDGER_DOC.is_file()
        assert _load_ledger_ids()
