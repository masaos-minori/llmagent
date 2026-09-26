"""tests/tools/test_check_needs_confirmation_inventory.py
Tests for tools/check_needs_confirmation_inventory.py.

Each scenario builds its own minimal fixture set under an isolated `tmp_path`
subdirectory and calls the tool's functions directly, matching
tests/tools/test_check_known_deviation_sync.py's tmp_path-fixture pattern.
"""

from __future__ import annotations

from pathlib import Path

from tools._docs_consistency_lib import discover_md_files
from tools.check_needs_confirmation_inventory import (
    _GOVERNANCE_META_DOCS,
    INVENTORY_DOC_PATH,
    NcEntry,
    check_missing_nc_fields,
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
            # Check both root level (legacy) and the target subfolder (post-reorg).
            if not (docs_dir / name).is_file():
                sub = name.split("_")[0] + "_" + name.split("_")[1]
                if not (docs_dir / sub / name).is_file():
                    missing.append(name)
        assert missing == [], (
            f"_GOVERNANCE_META_DOCS names non-existent files: {missing}"
        )

    def test_current_governance_filenames_are_covered(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        docs_dir = repo_root / "docs"
        real_governance_docs: set[str] = set()
        # Check root level (legacy) and the target subfolder (post-reorg).
        for p in docs_dir.glob("00_governance_*.md"):
            real_governance_docs.add(p.name)
        gov_subdir = docs_dir / "00_governance"
        if gov_subdir.is_dir():
            for p in gov_subdir.glob("00_governance_*.md"):
                real_governance_docs.add(p.name)
        assert real_governance_docs <= _GOVERNANCE_META_DOCS, (
            "A real docs/00_governance_*.md file is missing from "
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
            "00_governance_03_issue-and-uncertainty-management.md",
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
    """check_missing_nc_fields enforces GV-009: every *active* (open) NC item
    must carry both an 'Assigned To' owner (not empty / not 'Unassigned') and a
    non-empty 'Resolution Target'. Resolved/non-open items are skipped."""

    def _entry(self, **overrides) -> NcEntry:
        base = dict(
            nc_id="NC-100",
            source_file="governance_03_issue-and-uncertainty-management.md",
            status="open",
            assigned_to="alice",
            resolution_target="next review",
        )
        base.update(overrides)
        return NcEntry(**base)

    def test_complete_active_entry_produces_no_issues(self) -> None:
        issues = check_missing_nc_fields([self._entry()])
        assert issues == []

    def test_missing_assigned_to_is_flagged(self) -> None:
        issues = check_missing_nc_fields([self._entry(assigned_to=None)])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert issues[0].message == ("NC-100: missing required field 'Assigned To'")

    def test_missing_resolution_target_is_flagged(self) -> None:
        issues = check_missing_nc_fields([self._entry(resolution_target=None)])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert issues[0].message == (
            "NC-100: missing required field 'Resolution Target'"
        )

    def test_empty_assigned_to_is_flagged(self) -> None:
        issues = check_missing_nc_fields([self._entry(assigned_to="")])
        assert len(issues) == 1
        assert "Assigned To" in issues[0].message

    def test_unassigned_owner_is_flagged(self) -> None:
        issues = check_missing_nc_fields([self._entry(assigned_to="Unassigned")])
        assert len(issues) == 1
        assert "Assigned To" in issues[0].message

    def test_both_fields_missing_produces_two_issues(self) -> None:
        issues = check_missing_nc_fields(
            [self._entry(assigned_to=None, resolution_target=None)]
        )
        assert len(issues) == 2
        messages = {i.message for i in issues}
        assert "NC-100: missing required field 'Assigned To'" in messages
        assert "NC-100: missing required field 'Resolution Target'" in messages

    def test_non_open_item_is_excluded(self) -> None:
        for status in ("resolved", "fixed", "investigating", "deferred"):
            issues = check_missing_nc_fields(
                [self._entry(status=status, assigned_to=None, resolution_target=None)]
            )
            assert issues == [], f"{status} should be skipped"

    def test_mixed_entries_only_active_are_checked(self) -> None:
        active = self._entry(nc_id="NC-101", assigned_to=None)
        resolved = self._entry(
            nc_id="NC-102",
            status="resolved",
            assigned_to=None,
            resolution_target=None,
        )
        issues = check_missing_nc_fields([active, resolved])
        assert len(issues) == 1
        assert issues[0].message.startswith("NC-101:")
