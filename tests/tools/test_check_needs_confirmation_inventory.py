"""tests/tools/test_check_needs_confirmation_inventory.py
Tests for tools/check_needs_confirmation_inventory.py.

Each scenario builds its own minimal fixture set under an isolated `tmp_path`
subdirectory and calls the tool's functions directly, matching
tests/tools/test_check_known_deviation_sync.py's tmp_path-fixture pattern.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from tools._docs_consistency_lib import discover_md_files
from tools.check_needs_confirmation_inventory import (
    _GOVERNANCE_META_DOCS,
    INVENTORY_DOC_PATH,
    NcEntry,
    _parse_inventory_entries,
    check_blocking_reference,
    check_last_reviewed,
    check_missing_nc_fields,
    check_priority_valid,
    check_untracked_inline_markers,
)


def _write(dir_path: Path, filename: str, content: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / filename).write_text(content, encoding="utf-8")


class TestGovernanceMetaDocsCurrency:
    """_GOVERNANCE_META_DOCS must name filenames that actually exist under
    docs/00_governance_*.md today -- regression for a confirmed bug where
    this set named seven predecessor filenames that no longer exist (all
    renamed/consolidated), so real governance documents discussing the
    "Needs confirmation" label itself were treated as ordinary domain
    content instead of being exempted."""

    def test_named_docs_exist_on_disk(self) -> None:
        docs_dir = INVENTORY_DOC_PATH.parent.parent
        missing = []
        for name in _GOVERNANCE_META_DOCS:
            # Check root level (legacy), target subfolder (post-reorg), and governance subdir.
            if not (docs_dir / name).is_file():
                sub = name.split("_")[0] + "_" + name.split("_")[1]
                if not (docs_dir / sub / name).is_file():
                    gov_subdir = docs_dir / "00_governance"
                    if not (gov_subdir / name).is_file():
                        missing.append(name)
        assert missing == [], (
            f"_GOVERNANCE_META_DOCS names non-existent files: {missing}"
        )

    def test_current_governance_filenames_are_covered(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        docs_dir = repo_root / "docs"
        real_governance_docs: set[str] = set()
        # Check root level (legacy) and the target subfolder (post-reorg).
        for p in docs_dir.glob("governance_*.md"):
            real_governance_docs.add(p.name)
        gov_subdir = docs_dir / "00_governance"
        if gov_subdir.is_dir():
            for p in gov_subdir.glob("governance_*.md"):
                real_governance_docs.add(p.name)
        assert real_governance_docs <= _GOVERNANCE_META_DOCS, (
            "A real docs/00_governance/*.md file is missing from "
            "_GOVERNANCE_META_DOCS: "
            f"{real_governance_docs - _GOVERNANCE_META_DOCS}"
        )


class TestUntrackedInlineMarkers:
    """A meta/governance doc's own discussion of 'Needs confirmation' is
    exempted; an ordinary domain doc's untracked inline marker is flagged."""

    def test_governance_meta_doc_is_exempted(self, tmp_path: Path) -> None:
        docs_dir = tmp_path / "docs"
        _write(
            docs_dir,
            "governance_03_issue-and-uncertainty-management.md",
            "This document defines the Needs confirmation label itself.\n",
        )
        files = discover_md_files(docs_dir, prefix="")
        issues = check_untracked_inline_markers(docs_dir, files, entries=[])
        assert issues == []

    def test_ordinary_doc_with_untracked_marker_is_flagged(
        self, tmp_path: Path
    ) -> None:
        docs_dir = tmp_path / "docs"
        _write(
            docs_dir,
            "05_agent_example.md",
            "Needs confirmation: is this value correct?\n",
        )
        files = discover_md_files(docs_dir, prefix="")
        issues = check_untracked_inline_markers(docs_dir, files, entries=[])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert "untracked" in issues[0].message.lower()


class TestMissingNcFields:
    """check_missing_nc_fields validates required fields for active NC items."""

    def test_complete_entry_passes(self) -> None:
        entry = NcEntry("NC-1", "example.md", "open", "alice", "2026-10-01")
        issues = check_missing_nc_fields([entry])
        assert issues == []

    def test_missing_assigned_to_is_flagged(self) -> None:
        entry = NcEntry("NC-1", "example.md", "open", None, "2026-10-01")
        issues = check_missing_nc_fields([entry])
        assert len(issues) == 1
        assert "Assigned To" in issues[0].message

    def test_unassigned_owner_is_flagged(self) -> None:
        entry = NcEntry("NC-1", "example.md", "open", "Unassigned", "2026-10-01")
        issues = check_missing_nc_fields([entry])
        assert len(issues) == 1
        assert "Assigned To" in issues[0].message

    def test_missing_resolution_target_is_flagged(self) -> None:
        entry = NcEntry("NC-1", "example.md", "open", "bob", None)
        issues = check_missing_nc_fields([entry])
        assert len(issues) == 1
        assert "Resolution Target" in issues[0].message

    def test_resolved_item_is_excluded(self) -> None:
        entry = NcEntry("NC-1", "example.md", "resolved", None, None)
        issues = check_missing_nc_fields([entry])
        assert issues == []

    def test_multiple_issues_for_both_missing_fields(self) -> None:
        entry = NcEntry("NC-1", "example.md", "open", None, None)
        issues = check_missing_nc_fields([entry])
        assert len(issues) == 2
        assert any("Assigned To" in i.message for i in issues)
        assert any("Resolution Target" in i.message for i in issues)


class TestGovernanceDocMarkerClassification:
    """Verify that the governance doc exemption distinguishes definitional
    mentions from unresolved-item markers."""

    def test_definitional_mention_not_reported(self, tmp_path: Path) -> None:
        """A governance doc discussing the 'Needs confirmation' label itself
        must not be flagged as having an untracked marker."""
        docs_dir = tmp_path / "docs"
        _write(
            docs_dir,
            "governance_01_documentation-policy.md",
            "The Needs confirmation label indicates an item requiring review.\n"
            "See the Needs confirmation Inventory for details.\n",
        )
        files = discover_md_files(docs_dir, prefix="")
        issues = check_untracked_inline_markers(docs_dir, files, entries=[])
        assert issues == []

    def test_status_cell_marker_reported(self, tmp_path: Path) -> None:
        """A governance doc with a status-cell marker (Needs Confirmation in
        a table cell) must be flagged as an untracked marker."""
        docs_dir = tmp_path / "docs"
        _write(
            docs_dir,
            "governance_01_documentation-policy.md",
            "| Field | Value |\n| --- | --- |\n| Status | Needs Confirmation |\n",
        )
        files = discover_md_files(docs_dir, prefix="")
        issues = check_untracked_inline_markers(docs_dir, files, entries=[])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert "untracked" in issues[0].message.lower()


class TestExitCodeBehavior:
    """Verify main()'s exit-code contract: warnings → 0, ERROR → non-zero."""

    def test_warnings_only_returns_zero(self, tmp_path: Path) -> None:
        """A run yielding only WARNING findings must return exit code 0."""
        docs_dir = tmp_path / "docs"
        _write(
            docs_dir,
            "governance_03_issue-and-uncertainty-management.md",
            "## Part 2:\n#### NC-1\n**Status:** resolved\n**Source File:** `example.md`\n",
        )
        _write(
            docs_dir,
            "05_agent_example.md",
            "Needs confirmation: is this value correct?\n",
        )
        import tools.check_needs_confirmation_inventory as mod

        orig_docs_dir = mod.DOCS_DIR
        orig_inv_path = mod.INVENTORY_DOC_PATH
        try:
            mod.DOCS_DIR = docs_dir
            mod.INVENTORY_DOC_PATH = (
                docs_dir / "governance_03_issue-and-uncertainty-management.md"
            )
            result = mod.main()
            assert result == 0, (
                f"Expected exit code 0 for WARNING-only findings, got {result}"
            )
        finally:
            mod.DOCS_DIR = orig_docs_dir
            mod.INVENTORY_DOC_PATH = orig_inv_path

    def test_error_finding_returns_nonzero(self, tmp_path: Path) -> None:
        """A run yielding an ERROR finding must return a non-zero exit code."""
        docs_dir = tmp_path / "docs"
        _write(
            docs_dir,
            "governance_03_issue-and-uncertainty-management.md",
            "## Part 2:\n#### NC-1\n**Status:** resolved\n**Source File:** `example.md`\n",
        )
        # Declare "two required fields" but provide only one numbered item
        _write(
            docs_dir,
            "05_agent_example.md",
            "The following two required fields:\n1. **Field A**\n",
        )
        import tools.check_needs_confirmation_inventory as mod

        orig_docs_dir = mod.DOCS_DIR
        orig_inv_path = mod.INVENTORY_DOC_PATH
        try:
            mod.DOCS_DIR = docs_dir
            mod.INVENTORY_DOC_PATH = (
                docs_dir / "governance_03_issue-and-uncertainty-management.md"
            )
            result = mod.main()
            assert result != 0, (
                f"Expected non-zero exit code for ERROR finding, got {result}"
            )
        finally:
            mod.DOCS_DIR = orig_docs_dir
            mod.INVENTORY_DOC_PATH = orig_inv_path


class TestParseInventoryMarkers:
    """The extended parser reads the Last Reviewed / Priority / Blocking markers."""

    def test_three_markers_are_parsed(self) -> None:
        lines = [
            "## Part 2:",
            "#### NC-1",
            "**Status:** open",
            "**Source File:** `example.md`",
            "**Assigned To:** alice",
            "**Resolution Target:** 2026-12-01",
            "**Last Reviewed:** 2026-01-15",
            "**Priority:** High",
            "**Blocking:** NC-2",
            "#### NC-2",
            "**Status:** open",
        ]
        entries = _parse_inventory_entries(SimpleNamespace(lines=lines))
        assert len(entries) == 2
        nc1 = entries[0]
        assert nc1.last_reviewed == "2026-01-15"
        assert nc1.priority == "High"
        assert nc1.blocking == "NC-2"

    def test_absent_markers_map_to_none(self) -> None:
        lines = ["## Part 2:", "#### NC-1", "**Status:** open"]
        entries = _parse_inventory_entries(SimpleNamespace(lines=lines))
        assert len(entries) == 1
        nc1 = entries[0]
        assert nc1.last_reviewed is None
        assert nc1.priority is None
        assert nc1.blocking is None


class TestCheckLastReviewed:
    """check_last_reviewed enforces presence + ISO YYYY-MM-DD well-formedness."""

    def test_valid_iso_date_passes(self) -> None:
        entry = NcEntry(
            "NC-1", "example.md", "open", "alice", "2026-12-01", "2026-01-15"
        )
        assert check_last_reviewed([entry]) == []

    def test_missing_last_reviewed_is_flagged(self) -> None:
        entry = NcEntry("NC-1", "example.md", "open", "alice", "2026-12-01")
        issues = check_last_reviewed([entry])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert "Last Reviewed" in issues[0].message

    def test_malformed_date_is_flagged(self) -> None:
        entry = NcEntry(
            "NC-1", "example.md", "open", "alice", "2026-12-01", "01/15/2026"
        )
        issues = check_last_reviewed([entry])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert "ISO" in issues[0].message

    def test_non_open_entry_is_excluded(self) -> None:
        entry = NcEntry("NC-1", "example.md", "resolved", None, None, None)
        assert check_last_reviewed([entry]) == []


class TestCheckPriorityValid:
    """check_priority_valid enforces case-insensitive High/Medium/Low membership."""

    def test_valid_priority_passes(self) -> None:
        entry = NcEntry(
            "NC-1", "example.md", "open", "alice", "2026-12-01", priority="High"
        )
        assert check_priority_valid([entry]) == []

    def test_case_insensitive_priority_passes(self) -> None:
        entry = NcEntry(
            "NC-1", "example.md", "open", "alice", "2026-12-01", priority="low"
        )
        assert check_priority_valid([entry]) == []

    def test_missing_priority_is_flagged(self) -> None:
        entry = NcEntry("NC-1", "example.md", "open", "alice", "2026-12-01")
        issues = check_priority_valid([entry])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"

    def test_invalid_priority_is_flagged(self) -> None:
        entry = NcEntry(
            "NC-1", "example.md", "open", "alice", "2026-12-01", priority="Urgent"
        )
        issues = check_priority_valid([entry])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"

    def test_non_open_entry_is_excluded(self) -> None:
        entry = NcEntry("NC-1", "example.md", "resolved", None, None, priority="Urgent")
        assert check_priority_valid([entry]) == []


class TestCheckBlockingReference:
    """check_blocking_reference validates that Blocking names a real NC id."""

    def test_valid_blocking_reference_passes(self) -> None:
        e1 = NcEntry("NC-1", "example.md", "open", blocking="NC-2")
        e2 = NcEntry("NC-2", "example.md", "open")
        assert check_blocking_reference([e1, e2]) == []

    def test_invalid_blocking_reference_is_flagged(self) -> None:
        e1 = NcEntry("NC-1", "example.md", "open", blocking="NC-99")
        e2 = NcEntry("NC-2", "example.md", "open")
        issues = check_blocking_reference([e1, e2])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert "Blocking" in issues[0].message

    def test_unset_blocking_produces_no_issue(self) -> None:
        e1 = NcEntry("NC-1", "example.md", "open")
        assert check_blocking_reference([e1]) == []

    def test_non_open_entry_is_excluded(self) -> None:
        e1 = NcEntry("NC-1", "example.md", "resolved", blocking="NC-99")
        assert check_blocking_reference([e1]) == []
