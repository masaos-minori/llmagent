"""tests/tools/test_check_issue_inventory_conformance.py

Fixture-backed unit tests for tools/check_issue_inventory_conformance.py.

Each fixture contains a minimal example that triggers exactly one violation class.
Modeled on tests/tools/test_check_needs_confirmation_inventory.py's tmp_path-fixture
pattern: build minimal fixture sets under isolated tmp_path subdirectories and call
the tool's functions directly, matching assertions against the returned Issue objects.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools._docs_consistency_lib import DocFile
from tools.check_issue_inventory_conformance import (
    GOVERNANCE_DOC_NAME,
    GOVERNANCE_DOC_PATH,
    check_closing_summary,
    check_orphaned_bullets,
    check_referential_integrity,
    check_template_field_count,
    check_vocabulary,
)


def _make_doc(path: Path) -> DocFile:
    """Helper to construct a DocFile from a path, reading its contents."""
    content = path.read_text(encoding="utf-8")
    return DocFile(path, rel_path=GOVERNANCE_DOC_NAME, lines=content.splitlines())


# ── Fixtures ──────────────────────────────────────────────────────────────────────


@pytest.fixture()
def vocabulary_violation_doc(tmp_path: Path) -> Path:
    """Document with invalid Status value ('resolved' instead of 'open/investigating/deferred')."""
    doc = tmp_path / GOVERNANCE_DOC_NAME
    doc.write_text(
        "## Part 1: Known Issues\n\n"
        "### Active Items\n\n"
        "#### RAG-XXX\n\n"
        "- **ID**: RAG-XXX\n"
        "- **Title**: Test entry\n"
        "- **Status**: resolved\n"
        "- **Type**: document-code-mismatch\n"
        "- **Severity**: High\n"
        "- **Area**: Overview\n"
        "- **Owner**: Unassigned\n"
        "- **First Found**: 2026-09-01\n"
        "- **Target**: 2026-09-15\n"
        "- **Summary**: Test summary\n"
        "- **Current Description**: Test description\n"
        "- **Observed Implementation**: Test implementation\n"
        "- **Impact**: Test impact\n"
        "- **Recommended Action**: Test action\n"
        "- **Source**: Test source\n"
        "- **Related**: None\n"
    )
    return doc


@pytest.fixture()
def template_field_count_violation_doc(tmp_path: Path) -> Path:
    """Document with fewer than 16 fields (Part 1 full entry)."""
    doc = tmp_path / GOVERNANCE_DOC_NAME
    doc.write_text(
        "## Part 1: Known Issues\n\n"
        "### Active Items\n\n"
        "#### RAG-XXX\n\n"
        "- **ID**: RAG-XXX\n"
        "- **Title**: Test entry\n"
        "- **Status**: open\n"
        "- **Type**: document-code-mismatch\n"
        "- **Severity**: High\n"
        "- **Area**: Overview\n"
        "- **Owner**: Unassigned\n"
        "- **First Found**: 2026-09-01\n"
        "- **Target**: 2026-09-15\n"
        "- **Summary**: Test summary\n"
        "- **Current Description**: Test description\n"
        "- **Observed Implementation**: Test implementation\n"
        "- **Impact**: Test impact\n"
        "- **Recommended Action**: Test action\n"
        "- **Related**: None\n"
    )
    return doc


@pytest.fixture()
def orphaned_bullet_doc(tmp_path: Path) -> Path:
    """Document with orphaned bullet after removal placeholder."""
    doc = tmp_path / GOVERNANCE_DOC_NAME
    doc.write_text(
        "## Part 1: Known Issues\n\n"
        "### Active Items\n\n"
        "RAG-001 has been removed — do not create a `#### RAG-001` heading.\n\n"
        "#### RAG-002\n\n"
        "- **ID**: RAG-002\n"
        "- **Title**: Test entry\n"
        "- **Status**: open\n"
        "- **Type**: document-code-mismatch\n"
        "- **Severity**: High\n"
        "- **Area**: Overview\n"
        "- **Owner**: Unassigned\n"
        "- **First Found**: 2026-09-01\n"
        "- **Target**: 2026-09-15\n"
        "- **Summary**: Test summary\n"
        "- **Current Description**: Test description\n"
        "- **Observed Implementation**: Test implementation\n"
        "- **Impact**: Test impact\n"
        "- **Recommended Action**: Test action\n"
        "- **Source**: Test source\n"
        "- **Related**: None\n"
    )
    return doc


@pytest.fixture()
def closing_summary_mismatch_doc(tmp_path: Path) -> Path:
    """Document with closing summary ID list mismatch."""
    doc = tmp_path / GOVERNANCE_DOC_NAME
    doc.write_text(
        "## Part 1: Known Issues\n\n"
        "### Active Items\n\n"
        "#### RAG-XXX\n\n"
        "- **ID**: RAG-XXX\n"
        "- **Title**: Test entry\n"
        "- **Status**: open\n"
        "- **Type**: document-code-mismatch\n"
        "- **Severity**: High\n"
        "- **Area**: Overview\n"
        "- **Owner**: Unassigned\n"
        "- **First Found**: 2026-09-01\n"
        "- **Target**: 2026-09-15\n"
        "- **Summary**: Test summary\n"
        "- **Current Description**: Test description\n"
        "- **Observed Implementation**: Test implementation\n"
        "- **Impact**: Test impact\n"
        "- **Recommended Action**: Test action\n"
        "- **Source**: Test source\n"
        "- **Related**: None\n"
        "\n"
        "---\n"
        "\n"
        "No other active items beyond RAG-YYY above.\n"
    )
    return doc


@pytest.fixture()
def dangling_reference_doc(tmp_path: Path) -> Path:
    """Document with dangling Related reference to non-existent ID."""
    doc = tmp_path / GOVERNANCE_DOC_NAME
    doc.write_text(
        "## Part 1: Known Issues\n\n"
        "### Active Items\n\n"
        "#### RAG-XXX\n\n"
        "- **ID**: RAG-XXX\n"
        "- **Title**: Test entry\n"
        "- **Status**: open\n"
        "- **Type**: document-code-mismatch\n"
        "- **Severity**: High\n"
        "- **Area**: Overview\n"
        "- **Owner**: Unassigned\n"
        "- **First Found**: 2026-09-01\n"
        "- **Target**: 2026-09-15\n"
        "- **Summary**: Test summary\n"
        "- **Current Description**: Test description\n"
        "- **Observed Implementation**: Test implementation\n"
        "- **Impact**: Test impact\n"
        "- **Recommended Action**: Test action\n"
        "- **Source**: Test source\n"
        "- **Related**: NC-999\n"
    )
    return doc


@pytest.fixture()
def valid_part1_doc(tmp_path: Path) -> Path:
    """Valid Part 1 entry with all 16 fields and no violations."""
    doc = tmp_path / GOVERNANCE_DOC_NAME
    doc.write_text(
        "## Part 1: Known Issues\n\n"
        "### Active Items\n\n"
        "#### RAG-XXX\n\n"
        "- **ID**: RAG-XXX\n"
        "- **Title**: Test entry\n"
        "- **Status**: open\n"
        "- **Type**: document-code-mismatch\n"
        "- **Severity**: High\n"
        "- **Area**: Overview\n"
        "- **Owner**: Unassigned\n"
        "- **First Found**: 2026-09-01\n"
        "- **Target**: 2026-09-15\n"
        "- **Summary**: Test summary\n"
        "- **Current Description**: Test description\n"
        "- **Observed Implementation**: Test implementation\n"
        "- **Impact**: Test impact\n"
        "- **Recommended Action**: Test action\n"
        "- **Source**: Test source\n"
        "- **Related**: None\n"
    )
    return doc


@pytest.fixture()
def valid_part2_doc(tmp_path: Path) -> Path:
    """Valid Part 2 entry with all 15 fields and no violations."""
    doc = tmp_path / GOVERNANCE_DOC_NAME
    doc.write_text(
        "## Part 2: Needs Confirmation Inventory\n\n"
        "### Active Items\n\n"
        "#### NC-036\n\n"
        "- **Source File**: `test.md`\n"
        "- **Section**: Test section\n"
        "- **Line Number**: ~42\n"
        "- **Question**: Test question?\n"
        "- **Evidence**: Test evidence\n"
        "- **Impact**: Test impact\n"
        "- **Required Action**: Test action\n"
        "- **Status**: open\n"
        "- **Assigned To**: Unassigned\n"
        "- **Last Reviewed**: 2026-09-06\n"
        "- **Priority**: Medium\n"
        "- **Related NC**: None\n"
        "- **Resolution Target**: Confirm test target\n"
        "- **Blocking**: No\n"
    )
    return doc


# ── Tests ─────────────────────────────────────────────────────────────────────────


class TestVocabularyViolation:
    """Verify that vocabulary conformance check detects invalid values."""

    def test_invalid_status_is_detected(self, vocabulary_violation_doc: Path) -> None:
        doc = _make_doc(vocabulary_violation_doc)
        issues = check_vocabulary(doc)
        assert any("invalid Status" in i.message for i in issues), (
            "Invalid Status value should be detected"
        )

    def test_valid_status_is_not_flagged(self, valid_part1_doc: Path) -> None:
        doc = _make_doc(valid_part1_doc)
        issues = check_vocabulary(doc)
        assert not any("invalid Status" in i.message for i in issues), (
            "Valid Status value should not be flagged"
        )

    def test_invalid_severity_is_detected(self, tmp_path: Path) -> None:
        """Test with invalid Severity value ('low' instead of 'High/Medium/Low')."""
        doc = tmp_path / GOVERNANCE_DOC_NAME
        doc.write_text(
            "## Part 1: Known Issues\n\n"
            "### Active Items\n\n"
            "#### RAG-XXX\n\n"
            "- **ID**: RAG-XXX\n"
            "- **Title**: Test entry\n"
            "- **Status**: open\n"
            "- **Type**: document-code-mismatch\n"
            "- **Severity**: low\n"
            "- **Area**: Overview\n"
            "- **Owner**: Unassigned\n"
            "- **First Found**: 2026-09-01\n"
            "- **Target**: 2026-09-15\n"
            "- **Summary**: Test summary\n"
            "- **Current Description**: Test description\n"
            "- **Observed Implementation**: Test implementation\n"
            "- **Impact**: Test impact\n"
            "- **Recommended Action**: Test action\n"
            "- **Source**: Test source\n"
            "- **Related**: None\n"
        )
        df = _make_doc(doc)
        issues = check_vocabulary(df)
        assert any("invalid Severity" in i.message for i in issues), (
            "Invalid Severity value should be detected"
        )

    def test_invalid_area_is_detected(self, tmp_path: Path) -> None:
        """Test with invalid Area value ('unknown' instead of defined set)."""
        doc = tmp_path / GOVERNANCE_DOC_NAME
        doc.write_text(
            "## Part 1: Known Issues\n\n"
            "### Active Items\n\n"
            "#### RAG-XXX\n\n"
            "- **ID**: RAG-XXX\n"
            "- **Title**: Test entry\n"
            "- **Status**: open\n"
            "- **Type**: document-code-mismatch\n"
            "- **Severity**: High\n"
            "- **Area**: unknown\n"
            "- **Owner**: Unassigned\n"
            "- **First Found**: 2026-09-01\n"
            "- **Target**: 2026-09-15\n"
            "- **Summary**: Test summary\n"
            "- **Current Description**: Test description\n"
            "- **Observed Implementation**: Test implementation\n"
            "- **Impact**: Test impact\n"
            "- **Recommended Action**: Test action\n"
            "- **Source**: Test source\n"
            "- **Related**: None\n"
        )
        df = _make_doc(doc)
        issues = check_vocabulary(df)
        assert any("invalid Area" in i.message for i in issues), (
            "Invalid Area value should be detected"
        )

    def test_invalid_owner_is_detected(self, tmp_path: Path) -> None:
        """Test with invalid Owner value ('@invalid-user' instead of Unassigned/[Name]/Team)."""
        doc = tmp_path / GOVERNANCE_DOC_NAME
        doc.write_text(
            "## Part 1: Known Issues\n\n"
            "### Active Items\n\n"
            "#### RAG-XXX\n\n"
            "- **ID**: RAG-XXX\n"
            "- **Title**: Test entry\n"
            "- **Status**: open\n"
            "- **Type**: document-code-mismatch\n"
            "- **Severity**: High\n"
            "- **Area**: Overview\n"
            "- **Owner**: @invalid-user\n"
            "- **First Found**: 2026-09-01\n"
            "- **Target**: 2026-09-15\n"
            "- **Summary**: Test summary\n"
            "- **Current Description**: Test description\n"
            "- **Observed Implementation**: Test implementation\n"
            "- **Impact**: Test impact\n"
            "- **Recommended Action**: Test action\n"
            "- **Source**: Test source\n"
            "- **Related**: None\n"
        )
        df = _make_doc(doc)
        issues = check_vocabulary(df)
        assert any("invalid Owner" in i.message for i in issues), (
            "Invalid Owner value should be detected"
        )

    def test_invalid_type_is_detected(self, tmp_path: Path) -> None:
        """Test with invalid Type value ('typo-type' instead of defined set)."""
        doc = tmp_path / GOVERNANCE_DOC_NAME
        doc.write_text(
            "## Part 1: Known Issues\n\n"
            "### Active Items\n\n"
            "#### RAG-XXX\n\n"
            "- **ID**: RAG-XXX\n"
            "- **Title**: Test entry\n"
            "- **Status**: open\n"
            "- **Type**: typo-type\n"
            "- **Severity**: High\n"
            "- **Area**: Overview\n"
            "- **Owner**: Unassigned\n"
            "- **First Found**: 2026-09-01\n"
            "- **Target**: 2026-09-15\n"
            "- **Summary**: Test summary\n"
            "- **Current Description**: Test description\n"
            "- **Observed Implementation**: Test implementation\n"
            "- **Impact**: Test impact\n"
            "- **Recommended Action**: Test action\n"
            "- **Source**: Test source\n"
            "- **Related**: None\n"
        )
        df = _make_doc(doc)
        issues = check_vocabulary(df)
        assert any("invalid Type" in i.message for i in issues), (
            "Invalid Type value should be detected"
        )

    def test_valid_part2_status_is_not_flagged(self, valid_part2_doc: Path) -> None:
        """Part 2 only validates Status field."""
        doc = _make_doc(valid_part2_doc)
        issues = check_vocabulary(doc)
        assert not any("invalid Status" in i.message for i in issues), (
            "Valid Part 2 Status should not be flagged"
        )

    def test_invalid_part2_status_is_detected(self, tmp_path: Path) -> None:
        """Test Part 2 with invalid Status value."""
        doc = tmp_path / GOVERNANCE_DOC_NAME
        doc.write_text(
            "## Part 2: Needs Confirmation Inventory\n\n"
            "### Active Items\n\n"
            "#### NC-XXX\n\n"
            "- **Source File**: `test.md`\n"
            "- **Section**: Test section\n"
            "- **Line Number**: ~42\n"
            "- **Question**: Test question?\n"
            "- **Evidence**: Test evidence\n"
            "- **Impact**: Test impact\n"
            "- **Required Action**: Test action\n"
            "- **Status**: resolved\n"
            "- **Assigned To**: Unassigned\n"
            "- **Last Reviewed**: 2026-09-06\n"
            "- **Priority**: Medium\n"
            "- **Related NC**: None\n"
            "- **Resolution Target**: Confirm test target\n"
            "- **Blocking**: No\n"
        )
        df = _make_doc(doc)
        issues = check_vocabulary(df)
        assert any("invalid Status" in i.message for i in issues), (
            "Invalid Part 2 Status should be detected"
        )


class TestTemplateFieldCountViolation:
    """Verify that template field-count check detects missing/extra fields."""

    def test_missing_fields_detected(
        self, template_field_count_violation_doc: Path
    ) -> None:
        doc = _make_doc(template_field_count_violation_doc)
        issues = check_template_field_count(doc)
        assert any("expected 16 fields" in i.message for i in issues), (
            "Missing fields should be detected"
        )

    def test_no_extra_fields_in_valid_doc(self, valid_part1_doc: Path) -> None:
        doc = _make_doc(valid_part1_doc)
        issues = check_template_field_count(doc)
        assert not any("expected 16 fields" in i.message for i in issues), (
            "Valid Part 1 entry should have exactly 16 fields"
        )

    def test_valid_part2_field_count(self, valid_part2_doc: Path) -> None:
        doc = _make_doc(valid_part2_doc)
        issues = check_template_field_count(doc)
        assert not any("expected 14 fields" in i.message for i in issues), (
            "Valid Part 2 entry should have exactly 15 fields"
        )

    def test_removal_placeholder_exempt_from_field_count(
        self, orphaned_bullet_doc: Path
    ) -> None:
        """Removal placeholders should not trigger field-count violations."""
        doc = _make_doc(orphaned_bullet_doc)
        issues = check_template_field_count(doc)
        # Only the second entry should be checked; the removal placeholder is exempt
        for issue in issues:
            if "expected 16 fields" in issue.message:
                assert "RAG-002" in issue.message or "RAG-XXX" in issue.message, (
                    "Only actual entries should be checked for field count"
                )


class TestOrphanedBullets:
    """Verify that orphaned bullet detection works correctly."""

    def test_orphaned_bullets_detected(self, orphaned_bullet_doc: Path) -> None:
        doc = _make_doc(orphaned_bullet_doc)
        issues = check_orphaned_bullets(doc)
        assert any("orphaned bullets" in i.message.lower() for i in issues), (
            "Orphaned bullets after removal placeholder should be detected"
        )

    def test_no_orphaned_bullets_in_valid_doc(self, valid_part1_doc: Path) -> None:
        doc = _make_doc(valid_part1_doc)
        issues = check_orphaned_bullets(doc)
        assert not any("orphaned bullets" in i.message.lower() for i in issues), (
            "No orphaned bullets in valid document"
        )

    def test_normal_entry_after_heading_not_flagged(self, tmp_path: Path) -> None:
        """A normal entry after a heading should not be flagged as orphaned."""
        doc = tmp_path / GOVERNANCE_DOC_NAME
        doc.write_text(
            "## Part 1: Known Issues\n\n"
            "### Active Items\n\n"
            "#### RAG-001\n\n"
            "- **ID**: RAG-001\n"
            "- **Title**: Test entry\n"
            "- **Status**: open\n"
            "- **Type**: document-code-mismatch\n"
            "- **Severity**: High\n"
            "- **Area**: Overview\n"
            "- **Owner**: Unassigned\n"
            "- **First Found**: 2026-09-01\n"
            "- **Target**: 2026-09-15\n"
            "- **Summary**: Test summary\n"
            "- **Current Description**: Test description\n"
            "- **Observed Implementation**: Test implementation\n"
            "- **Impact**: Test impact\n"
            "- **Recommended Action**: Test action\n"
            "- **Source**: Test source\n"
            "- **Related**: None\n"
            "\n"
            "#### RAG-002\n\n"
            "- **ID**: RAG-002\n"
            "- **Title**: Test entry\n"
            "- **Status**: open\n"
            "- **Type**: document-code-mismatch\n"
            "- **Severity**: High\n"
            "- **Area**: Overview\n"
            "- **Owner**: Unassigned\n"
            "- **First Found**: 2026-09-01\n"
            "- **Target**: 2026-09-15\n"
            "- **Summary**: Test summary\n"
            "- **Current Description**: Test description\n"
            "- **Observed Implementation**: Test implementation\n"
            "- **Impact**: Test impact\n"
            "- **Recommended Action**: Test action\n"
            "- **Source**: Test source\n"
            "- **Related**: None\n"
        )
        df = _make_doc(doc)
        issues = check_orphaned_bullets(df)
        assert not any("orphaned bullets" in i.message.lower() for i in issues), (
            "Normal entries after headings should not be flagged"
        )


class TestClosingSummaryConsistency:
    """Verify that closing-summary consistency check works correctly."""

    def test_closing_summary_mismatch_detected(
        self, closing_summary_mismatch_doc: Path
    ) -> None:
        doc = _make_doc(closing_summary_mismatch_doc)
        issues = check_closing_summary(doc)
        assert any("closing summary" in i.message.lower() for i in issues), (
            "Closing summary mismatch should be detected"
        )

    def test_no_closing_summary_in_minimal_doc(self, valid_part1_doc: Path) -> None:
        """Minimal docs without a closing summary should not trigger violations."""
        doc = _make_doc(valid_part1_doc)
        issues = check_closing_summary(doc)
        assert not any("closing summary" in i.message.lower() for i in issues), (
            "Docs without closing summary should not trigger violations"
        )


class TestReferentialIntegrity:
    """Verify that referential integrity check works correctly."""

    def test_dangling_reference_detected(self, dangling_reference_doc: Path) -> None:
        doc = _make_doc(dangling_reference_doc)
        issues = check_referential_integrity(doc)
        assert any(
            "NC-999" in i.message and "unresolved" in i.message.lower() for i in issues
        ), "Dangling reference to non-existent ID should be detected"

    def test_no_dangling_references_in_valid_doc(self, valid_part1_doc: Path) -> None:
        doc = _make_doc(valid_part1_doc)
        issues = check_referential_integrity(doc)
        # Valid Part 1 entry has Related: None, so no references to resolve
        assert not any("unresolved" in i.message.lower() for i in issues), (
            "Valid entry with Related: None should not have unresolved references"
        )

    def test_related_none_is_not_flagged(self, valid_part1_doc: Path) -> None:
        """Related: None should not be treated as a reference."""
        doc = _make_doc(valid_part1_doc)
        issues = check_referential_integrity(doc)
        assert not any("None" in i.message for i in issues), (
            "Related: None should not be flagged as a dangling reference"
        )


class TestGovernanceDocPathIntegration:
    """Exercises GOVERNANCE_DOC_PATH against the actual repository tree. Depends on
    docsreorg05's plans/done/20260924-115855_plan.md seq 01/03 (the governance docs move)
    and seq 07 (this tool's GOVERNANCE_DOC_PATH constant) having already been
    applied; if run before those land, this test fails with a clear assertion
    message rather than silently skipping.
    """

    def test_governance_doc_path_resolves_on_disk(self) -> None:
        assert GOVERNANCE_DOC_PATH.is_file(), f"{GOVERNANCE_DOC_PATH} not found"
