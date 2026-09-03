"""tests/tools/test_check_known_deviation_sync.py
Tests for tools/check_known_deviation_sync.py.

Each scenario builds its own minimal fixture pair (one canonical Known Issues
document, one ADR document) under an isolated `tmp_path` subdirectory, then
calls the tool's parsing/cross-check functions directly -- matching
tests/tools/test_check_compat_shims.py's tmp_path-fixture-test pattern. Live
`docs/`-tree validation (AC-1..AC-5) is out of scope for this file; see the
source implementation procedure's Out of scope section.
"""

from __future__ import annotations

from pathlib import Path

from tools._docs_consistency_lib import DocFile, discover_md_files
from tools.check_known_deviation_sync import (
    cross_check,
    parse_adr_references,
    parse_canonical_statuses,
)


def _write(dir_path: Path, filename: str, content: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / filename).write_text(content, encoding="utf-8")


def _discover(dir_path: Path) -> list[DocFile]:
    return discover_md_files(dir_path, prefix="")


class TestStatusMatch:
    """An ADR reference whose signal agrees with the canonical Status
    produces no Status-mismatch or dangling finding."""

    def test_matching_open_status_produces_no_finding(self, tmp_path: Path) -> None:
        canonical_dir = tmp_path / "docs"
        _write(
            canonical_dir,
            "04_mcp_90_inconsistencies_and_known_issues.md",
            "### ID-001: Some tracked deviation\n\n- **Status**: open\n",
        )
        adr_dir = tmp_path / "adr"
        _write(
            adr_dir,
            "ADR-001-example.md",
            "## Known Deviations\n\n"
            "- **Known Issue**: ID-001 — still present, tracked upstream\n",
        )

        statuses, parse_issues = parse_canonical_statuses(_discover(canonical_dir))
        assert parse_issues == []
        assert statuses["ID-001"].raw_status == "open"

        adr_refs = parse_adr_references(_discover(adr_dir))
        assert len(adr_refs) == 1
        assert adr_refs[0].id == "ID-001"
        assert adr_refs[0].signal == "open-like"

        assert cross_check(statuses, adr_refs) == []


class TestStatusMismatch:
    """A canonical Status that disagrees with the ADR's open/resolved signal
    is reported as an ERROR Status-mismatch finding."""

    def test_disagreeing_status_is_reported(self, tmp_path: Path) -> None:
        canonical_dir = tmp_path / "docs"
        _write(
            canonical_dir,
            "04_mcp_90_inconsistencies_and_known_issues.md",
            "### ID-002: Another tracked deviation\n\n- **Status**: resolved\n",
        )
        adr_dir = tmp_path / "adr"
        _write(
            adr_dir,
            "ADR-002-example.md",
            "## Known Deviations\n\n"
            "- **Known Issue**: ID-002 — still open per implementation\n",
        )

        statuses, parse_issues = parse_canonical_statuses(_discover(canonical_dir))
        assert parse_issues == []

        adr_refs = parse_adr_references(_discover(adr_dir))
        assert len(adr_refs) == 1
        assert adr_refs[0].signal == "open-like"

        findings = cross_check(statuses, adr_refs)
        assert len(findings) == 1
        assert findings[0].severity == "ERROR"
        assert "ID-002" in findings[0].message
        assert "mismatch" in findings[0].message.lower()


class TestDanglingReference:
    """An ADR-referenced ID with no matching canonical `### <ID>` entry
    anywhere in the discovered set is reported as a dangling reference."""

    def test_unresolvable_id_is_reported_as_dangling(self, tmp_path: Path) -> None:
        canonical_dir = tmp_path / "docs"
        # An unrelated ID exists in the canonical set, but ID-003 (the one the
        # ADR cites) does not -- proving the dangling report is driven by the
        # specific ID's absence, not by an empty canonical set overall.
        _write(
            canonical_dir,
            "05_agent_90_inconsistencies_and_known_issues.md",
            "### ID-999: Unrelated tracked deviation\n\n- **Status**: open\n",
        )
        adr_dir = tmp_path / "adr"
        _write(
            adr_dir,
            "ADR-003-example.md",
            "## Known Deviations\n\n"
            "- **Known Issue**: ID-003 — referenced but never tracked\n",
        )

        statuses, parse_issues = parse_canonical_statuses(_discover(canonical_dir))
        assert parse_issues == []
        assert "ID-003" not in statuses

        adr_refs = parse_adr_references(_discover(adr_dir))
        assert len(adr_refs) == 1

        findings = cross_check(statuses, adr_refs)
        assert len(findings) == 1
        assert findings[0].severity == "WARNING"
        assert "ID-003" in findings[0].message
        assert "dangling" in findings[0].message.lower()


class TestFalsePositiveAvoidance:
    """A slug-shaped bullet whose ID-shaped substring is immediately followed
    by more hyphenated text (mirroring
    ADR-004-D1-profile-config-model-still-present's shape) must not be
    misread as a bare candidate ID -- regression for the anchoring-rule fix
    that avoided a false positive on ADR-012's INV-03 mention."""

    def test_slug_suffix_is_not_extracted_as_bare_id(self, tmp_path: Path) -> None:
        canonical_dir = tmp_path / "docs"
        _write(
            canonical_dir,
            "90_shared_90_inconsistencies_and_known_issues.md",
            "### ID-004: Tracked deviation with a slug-shaped citation\n\n"
            "- **Status**: open\n",
        )
        adr_dir = tmp_path / "adr"
        _write(
            adr_dir,
            "ADR-004-example.md",
            "## Known Deviations\n\n"
            "- **Known Issue**: ID-004-EXTRA-slug-suffix — profile config "
            "model still present\n",
        )

        statuses, _parse_issues = parse_canonical_statuses(_discover(canonical_dir))
        assert "ID-004" in statuses

        adr_refs = parse_adr_references(_discover(adr_dir))
        assert adr_refs == []
        assert not any(ref.id == "ID-004" for ref in adr_refs)

        assert cross_check(statuses, adr_refs) == []


class TestConsolidatedGovernanceFormat:
    """The consolidated `docs/00_governance_03_issue-and-uncertainty-management.md`
    format (`#### <ID>` heading, no colon/title on the same line) must resolve
    identically to the legacy `### <ID>: <title>` per-area format — regression
    for the confirmed bug where discover_canonical_docs()/_CANONICAL_ID_HEADER_RE
    only recognized the now-deleted per-area files' heading style, so every
    real ADR reference resolved as a false-positive dangling warning."""

    def test_four_hash_id_only_heading_resolves(self, tmp_path: Path) -> None:
        canonical_dir = tmp_path / "docs"
        _write(
            canonical_dir,
            "00_governance_03_issue-and-uncertainty-management.md",
            "## Part 1: Known Issues\n\n"
            "#### RAG-999\n\n"
            "- **ID**: RAG-999\n"
            "- **Status**: open\n",
        )
        adr_dir = tmp_path / "adr"
        _write(
            adr_dir,
            "ADR-006-example.md",
            "## Known Deviations\n\n"
            "- **Known Issue**: RAG-999 — still open per implementation\n",
        )

        statuses, parse_issues = parse_canonical_statuses(_discover(canonical_dir))
        assert parse_issues == []
        assert statuses["RAG-999"].raw_status == "open"

        adr_refs = parse_adr_references(_discover(adr_dir))
        assert cross_check(statuses, adr_refs) == []

    def test_part_2_needs_confirmation_ids_are_not_parsed_as_known_issues(
        self, tmp_path: Path
    ) -> None:
        """A `#### NC-<N>` heading under '## Part 2' is ID-shaped
        (letters-dash-digits) but belongs to a different inventory — it must
        not be captured as a Known Issue status, and must not swallow the
        preceding Part 1 entry's body across the Part boundary."""
        canonical_dir = tmp_path / "docs"
        _write(
            canonical_dir,
            "00_governance_03_issue-and-uncertainty-management.md",
            "## Part 1: Known Issues\n\n"
            "#### RAG-998\n\n"
            "- **Status**: resolved\n\n"
            "## Part 2: Needs Confirmation Inventory\n\n"
            "#### NC-030\n\n"
            "- **Status**: open\n",
        )

        statuses, parse_issues = parse_canonical_statuses(_discover(canonical_dir))
        assert parse_issues == []
        assert statuses["RAG-998"].raw_status == "resolved"
        assert "NC-030" not in statuses


class TestNoIdHeadings:
    """A canonical document defining zero `### <ID>` headings at all does not
    exempt an ADR reference that would otherwise belong to it -- the
    reference is still reported as dangling, mirroring AC-3."""

    def test_reference_against_headingless_canonical_doc_is_dangling(
        self, tmp_path: Path
    ) -> None:
        canonical_dir = tmp_path / "docs"
        _write(
            canonical_dir,
            "06_eventbus_90_inconsistencies_and_known_issues.md",
            "# Event Bus: Inconsistencies and Known Issues\n\n"
            "This document currently has no tracked entries.\n",
        )
        adr_dir = tmp_path / "adr"
        _write(
            adr_dir,
            "ADR-005-example.md",
            "## Known Deviations\n\n"
            "- **Known Issue**: ID-005 — would belong to the eventbus doc\n",
        )

        statuses, parse_issues = parse_canonical_statuses(_discover(canonical_dir))
        assert statuses == {}
        assert parse_issues == []

        adr_refs = parse_adr_references(_discover(adr_dir))
        assert len(adr_refs) == 1

        findings = cross_check(statuses, adr_refs)
        assert len(findings) == 1
        assert findings[0].severity == "WARNING"
        assert "ID-005" in findings[0].message
        assert "dangling" in findings[0].message.lower()
