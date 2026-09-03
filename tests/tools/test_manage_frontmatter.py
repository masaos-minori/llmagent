"""tests/tools/test_manage_frontmatter.py
Tests for tools/manage_frontmatter.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from tools.manage_frontmatter import (
    AMBIGUOUS,
    cmd_add_missing,
    cmd_rename_category_to_area,
    extract_area_from_filename,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# "05_agent_..." unambiguously resolves to area "agent" via AREA_PREFIX_MAP —
# chosen so these fixtures exercise dry-run/--fix mechanics without also
# depending on ambiguous-area handling (see TestAmbiguousArea below for that).
_UNAMBIGUOUS_FILENAME = "05_agent_test_doc.md"


@pytest.fixture
def temp_docs(tmp_path: Path) -> Path:
    """Create a temporary docs directory with a file that needs front matter."""
    docs = tmp_path / "docs"
    docs.mkdir(parents=True)
    # File without front matter — should be flagged
    (docs / _UNAMBIGUOUS_FILENAME).write_text("# Hello World\n\nSome content.\n")
    return docs


# ---------------------------------------------------------------------------
# No-flag path: should NOT write anything
# ---------------------------------------------------------------------------


class TestNoFlagPath:
    """No-flag invocation must be non-destructive (report-only)."""

    def test_no_flag_does_not_write(
        self, temp_docs: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", temp_docs)
        result = cmd_add_missing([])
        assert result == 0  # no issues reported for files without ANY front matter
        content = (temp_docs / _UNAMBIGUOUS_FILENAME).read_text(encoding="utf-8")
        assert not content.startswith("---"), "File was written despite no --fix flag"

    def test_no_flag_prints_preview(
        self,
        temp_docs: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", temp_docs)
        cmd_add_missing([])
        captured = capsys.readouterr()
        assert "[DRY-RUN]" in captured.out


# ---------------------------------------------------------------------------
# --dry-run path: should NOT write anything
# ---------------------------------------------------------------------------


class TestDryRunPath:
    """--dry-run invocation must be non-destructive."""

    def test_dry_run_does_not_write(
        self, temp_docs: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", temp_docs)
        result = cmd_add_missing(["--dry-run"])
        assert result == 0  # no issues after dry-run (file untouched)
        content = (temp_docs / _UNAMBIGUOUS_FILENAME).read_text(encoding="utf-8")
        assert not content.startswith("---"), "File was written despite --dry-run flag"

    def test_dry_run_prints_preview(
        self,
        temp_docs: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", temp_docs)
        cmd_add_missing(["--dry-run"])
        captured = capsys.readouterr()
        assert "[DRY-RUN]" in captured.out


# ---------------------------------------------------------------------------
# --fix path: SHOULD write
# ---------------------------------------------------------------------------


class TestFixPath:
    """--fix invocation must perform actual writes."""

    def test_fix_writes_front_matter(
        self, temp_docs: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", temp_docs)
        result = cmd_add_missing(["--fix"])
        assert result == 0  # issues resolved after write
        content = (temp_docs / _UNAMBIGUOUS_FILENAME).read_text(encoding="utf-8")
        assert content.startswith("---"), (
            "Front matter was not added despite --fix flag"
        )

    def test_fix_exits_nonzero_when_issues_found(
        self, temp_docs: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", temp_docs)
        result = cmd_add_missing(["--fix"])
        assert result == 0  # issues resolved after write


# ---------------------------------------------------------------------------
# Namespace argument hand-off
# ---------------------------------------------------------------------------


class TestNamespaceHandoff:
    """cmd_add_missing must accept Namespace objects directly."""

    def test_accepts_namespace_directly(
        self, temp_docs: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", temp_docs)
        ns = argparse.Namespace(dry_run=False, fix=True)
        result = cmd_add_missing(ns)
        assert result == 0  # issues resolved after write
        content = (temp_docs / _UNAMBIGUOUS_FILENAME).read_text(encoding="utf-8")
        assert content.startswith("---"), (
            "Front matter was not added when passing Namespace"
        )

    def test_namespace_dry_run_does_not_write(
        self, temp_docs: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", temp_docs)
        ns = argparse.Namespace(dry_run=True, fix=False)
        result = cmd_add_missing(ns)
        assert result == 0  # no issues after dry-run (file untouched)
        content = (temp_docs / _UNAMBIGUOUS_FILENAME).read_text(encoding="utf-8")
        assert not content.startswith("---"), "File was written despite dry_run=True"


# ---------------------------------------------------------------------------
# Ambiguous area inference — must never guess (REQ: never guess ambiguous
# metadata during Front Matter migration)
# ---------------------------------------------------------------------------


class TestAmbiguousArea:
    """A filename with no confident area-prefix/digit match is reported as
    ambiguous and left untouched, in both --dry-run and --fix mode — never
    silently defaulted to a guessed area (e.g. the old 'overview' fallback)."""

    def test_extract_area_returns_ambiguous_sentinel(self) -> None:
        assert extract_area_from_filename("totally-unrecognized-name.md") is AMBIGUOUS

    def test_dry_run_reports_ambiguous_and_does_not_write(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "totally-unrecognized-name.md").write_text("# Title\n\nBody.\n")
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", docs)
        result = cmd_add_missing(["--dry-run"])
        assert result == 1  # ambiguous cases are reported as non-clean, not silent
        content = (docs / "totally-unrecognized-name.md").read_text(encoding="utf-8")
        assert not content.startswith("---")

    def test_fix_reports_ambiguous_and_does_not_write(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "totally-unrecognized-name.md").write_text("# Title\n\nBody.\n")
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", docs)
        result = cmd_add_missing(["--fix"])
        assert result == 1
        content = (docs / "totally-unrecognized-name.md").read_text(encoding="utf-8")
        assert not content.startswith("---"), (
            "An ambiguous-area file must never be written even with --fix"
        )


# ---------------------------------------------------------------------------
# AREA_PREFIX_MAP: 06_eventbus regression (was silently mapped to "overview")
# ---------------------------------------------------------------------------


class TestEventbusAreaInference:
    """06_eventbus_*.md files (this repository's real EventBus doc prefix)
    must resolve to area 'eventbus', not fall through to ambiguous/overview.
    Regression test for a confirmed bug: AREA_PREFIX_MAP previously mapped
    the never-used '06_config'/'91_eventbus' prefixes instead of the actual
    '06_eventbus' prefix real files use."""

    def test_06_eventbus_prefix_resolves_to_eventbus(self) -> None:
        assert (
            extract_area_from_filename("06_eventbus_00_document-guide.md") == "eventbus"
        )

    def test_dead_prefixes_no_longer_present(self) -> None:
        from tools.manage_frontmatter import AREA_PREFIX_MAP

        assert "91_eventbus" not in AREA_PREFIX_MAP
        assert "06_config" not in AREA_PREFIX_MAP
        assert AREA_PREFIX_MAP["06_eventbus"] == "eventbus"


# ---------------------------------------------------------------------------
# rename-category-to-area subcommand
# ---------------------------------------------------------------------------


class TestRenameCategoryToArea:
    def test_dry_run_does_not_write(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        doc = docs / "01_overview-example.md"
        doc.write_text(
            '---\ntitle: "Example"\ncategory: overview\ntags:\n  - x\n---\n\nBody.\n'
        )
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", docs)
        result = cmd_rename_category_to_area(["--dry-run"])
        assert result == 0
        content = doc.read_text(encoding="utf-8")
        assert "category: overview" in content
        assert "area:" not in content

    def test_fix_renames_key_preserving_value(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        doc = docs / "01_overview-example.md"
        doc.write_text(
            '---\ntitle: "Example"\ncategory: overview\ntags:\n  - x\n---\n\nBody.\n'
        )
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", docs)
        result = cmd_rename_category_to_area(["--fix"])
        assert result == 0
        content = doc.read_text(encoding="utf-8")
        assert "area: overview" in content
        assert "category:" not in content
        assert "Body." in content, "Body content must be untouched"

    def test_both_category_and_area_present_is_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        doc = docs / "01_overview-example.md"
        original = (
            '---\ntitle: "Example"\ncategory: overview\narea: overview\n---\n\nBody.\n'
        )
        doc.write_text(original)
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", docs)
        result = cmd_rename_category_to_area(["--fix"])
        assert result == 1  # ambiguous case reported, not silently resolved
        assert doc.read_text(encoding="utf-8") == original, (
            "File with both keys must be left untouched"
        )

    def test_missing_front_matter_fence_is_not_renamed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A file with an unfenced pseudo-YAML block (no opening '---') is
        add-missing's job, not this subcommand's — it must be left alone."""
        docs = tmp_path / "docs"
        docs.mkdir()
        doc = docs / "04_mcp_unfenced-example.md"
        original = 'title: "Example"\ncategory: mcp\ntags:\n  - x\n'
        doc.write_text(original)
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", docs)
        result = cmd_rename_category_to_area(["--fix"])
        assert result == 0
        assert doc.read_text(encoding="utf-8") == original
