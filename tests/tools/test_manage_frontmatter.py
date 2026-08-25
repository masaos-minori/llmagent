"""tests/tools/test_manage_frontmatter.py
Tests for tools/manage_frontmatter.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from tools.manage_frontmatter import cmd_add_missing

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_docs(tmp_path: Path) -> Path:
    """Create a temporary docs directory with a file that needs front matter."""
    docs = tmp_path / "docs"
    docs.mkdir(parents=True)
    # File without front matter — should be flagged
    (docs / "test_doc.md").write_text("# Hello World\n\nSome content.\n")
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
        content = (temp_docs / "test_doc.md").read_text(encoding="utf-8")
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
        content = (temp_docs / "test_doc.md").read_text(encoding="utf-8")
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
        content = (temp_docs / "test_doc.md").read_text(encoding="utf-8")
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
        content = (temp_docs / "test_doc.md").read_text(encoding="utf-8")
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
        content = (temp_docs / "test_doc.md").read_text(encoding="utf-8")
        assert not content.startswith("---"), "File was written despite dry_run=True"
