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
        repo_root = Path(__file__).resolve().parent.parent.parent
        docs_dir = repo_root / "docs"
        missing = [
            name for name in _GOVERNANCE_META_DOCS if not (docs_dir / name).is_file()
        ]
        assert missing == [], (
            f"_GOVERNANCE_META_DOCS names non-existent files: {missing}"
        )

    def test_current_governance_filenames_are_covered(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        docs_dir = repo_root / "docs"
        real_governance_docs = {p.name for p in docs_dir.glob("00_governance_*.md")}
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
