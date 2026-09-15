"""tests/tools/test_check_adr_structure.py
Tests for tools/check_adr_structure.py.

Each scenario builds an in-memory DocFile (a small set of lines) and calls
check_known_deviations_heading()/check_notes_references_drift() directly --
matching tests/tools/test_check_adr_reference.py's direct-function-call
pattern. Live docs/adr/*.md validation is exercised separately by running the
tool against the real repository, not duplicated here as a unit test.
"""

from __future__ import annotations

from pathlib import Path

from tools._docs_consistency_lib import DocFile
from tools.check_adr_structure import (
    check_known_deviations_heading,
    check_notes_references_drift,
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
            "### Implementation References",
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
            "### Implementation References",
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
            "### Implementation References",
            "",
            "- `scripts/unrelated.py` — not cited by Notes at all",
            "",
            "## Completion Checklist",
        )
        assert check_notes_references_drift([doc]) == []
