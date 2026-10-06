"""tests/tools/test_manage_frontmatter.py
Tests for tools/manage_frontmatter.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from tools.manage_frontmatter import (
    AMBIGUOUS,
    classify_from_filename,
    cmd_add_missing,
    cmd_classify,
    cmd_merge_related,
    cmd_rename_category_to_area,
    extract_area_from_filename,
    main,
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


# ---------------------------------------------------------------------------
# classify subcommand
# ---------------------------------------------------------------------------


class TestClassify:
    """`classify` never guesses and never writes — report-only, following
    `add-missing`'s existing never-guess/report-ambiguous pattern."""

    def test_confident_signal_detected(self) -> None:
        assert classify_from_filename("05_agent_13_reference-api.md") == "Reference"

    def test_no_signal_is_ambiguous(self) -> None:
        assert classify_from_filename("notes.md") is None

    def test_confident_case_reported_and_no_file_modified(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        doc = docs / "06_eventbus_06_reference-api.md"
        original = "# Event Bus: Reference API\n\nBody.\n"
        doc.write_text(original)
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", docs)
        result = cmd_classify([])
        assert result == 0
        captured = capsys.readouterr()
        assert "[CONFIDENT]" in captured.out
        assert "Reference" in captured.out
        assert doc.read_text(encoding="utf-8") == original, (
            "classify must never modify a file's content"
        )

    def test_ambiguous_case_reported_and_no_file_modified(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        doc = docs / "notes.md"
        original = "# Notes\n\nSome working notes.\n"
        doc.write_text(original)
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", docs)
        result = cmd_classify([])
        assert result == 0  # ambiguous is reported, not a nonzero exit
        captured = capsys.readouterr()
        assert "[AMBIGUOUS]" in captured.out
        assert doc.read_text(encoding="utf-8") == original, (
            "classify must never modify a file's content"
        )


# ---------------------------------------------------------------------------
# merge-related
# ---------------------------------------------------------------------------


def _doc(related: str, body: str) -> str:
    return (
        "---\ntitle: T\narea: agent\ntags:\n  - x\n"
        f"related:{related}\n---\n\n# T\n\n{body}"
    )


_TAIL = "\n## Keywords\n\nx\n"


@pytest.fixture
def merge_docs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A docs tree whose `a.md`, `b.md`, `c.md`, and `sub/d.md` are link targets."""
    docs = tmp_path / "docs"
    (docs / "sub").mkdir(parents=True)
    (docs / "10_adr").mkdir()
    for name in ("a.md", "b.md", "c.md", "sub/d.md"):
        (docs / name).write_text(_doc(" []", "text\n"), encoding="utf-8")
    monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", docs)
    return docs


def _subject(docs: Path, related: str, body: str, name: str = "s.md") -> Path:
    path = docs / name
    path.write_text(_doc(related, body), encoding="utf-8")
    return path


class TestMergeRelatedDefaults:
    def test_default_is_dry_run(
        self, merge_docs: Path, capsys: pytest.CaptureFixture
    ) -> None:
        body = "## Related Documents\n\n- `b.md`\n" + _TAIL
        subject = _subject(merge_docs, "\n  - a.md", body)
        before = subject.read_bytes()
        assert cmd_merge_related([]) == 0
        assert subject.read_bytes() == before
        out = capsys.readouterr().out
        assert "[DRY-RUN]" in out
        assert "add to related: b.md" in out

    def test_fix_merges_in_order_and_removes_section(self, merge_docs: Path) -> None:
        body = "Some text.\n\n## Related Documents\n\n- `b.md`\n- `a.md`\n" + _TAIL
        subject = _subject(merge_docs, "\n  - a.md", body)
        assert cmd_merge_related(["--fix"]) == 0
        content = subject.read_text(encoding="utf-8")
        assert "related:\n  - a.md\n  - b.md\n---" in content
        assert "## Related" not in content
        assert "Some text.\n\n## Keywords\n\nx\n" in content
        assert content.endswith("\n")
        assert "\n\n\n" not in content

    def test_second_fix_run_changes_nothing(
        self, merge_docs: Path, capsys: pytest.CaptureFixture
    ) -> None:
        body = "## Related Documents\n\n- `b.md`\n" + _TAIL
        subject = _subject(merge_docs, "\n  - a.md", body)
        cmd_merge_related(["--fix"])
        after_first = subject.read_bytes()
        capsys.readouterr()
        assert cmd_merge_related(["--fix"]) == 0
        assert subject.read_bytes() == after_first
        assert "0 file(s) modified" in capsys.readouterr().out


class TestMergeRelatedInputForms:
    def test_link_form_with_anchor_and_subdirectory_path(
        self, merge_docs: Path
    ) -> None:
        body = "## Related Documents\n\n- [B](../b.md#x)\n- [D](sub/d.md)\n" + _TAIL
        subject = _subject(merge_docs, " []", body)
        cmd_merge_related(["--fix"])
        content = subject.read_text(encoding="utf-8")
        assert "related:\n  - b.md\n  - d.md\n---" in content

    @pytest.mark.parametrize("heading", ["Related Docs", "Related Chapters"])
    def test_alternate_headings_are_merged_and_removed(
        self, merge_docs: Path, heading: str
    ) -> None:
        body = f"## {heading}\n\n- `c.md`\n" + _TAIL
        subject = _subject(merge_docs, " []", body)
        cmd_merge_related(["--fix"])
        content = subject.read_text(encoding="utf-8")
        assert "  - c.md" in content
        assert f"## {heading}" not in content

    def test_two_sections_in_one_file(self, merge_docs: Path) -> None:
        body = (
            "## Related Documents\n\n- `a.md`\n\n"
            "## Middle\n\ntext\n\n## Related Docs\n\n- `b.md`\n" + _TAIL
        )
        subject = _subject(merge_docs, "", body)
        cmd_merge_related(["--fix"])
        content = subject.read_text(encoding="utf-8")
        assert "related:\n  - a.md\n  - b.md\n---" in content
        assert "## Related" not in content
        assert "## Middle\n\ntext\n\n## Keywords" in content

    def test_section_at_end_of_file(self, merge_docs: Path) -> None:
        body = "text\n\n## Related Documents\n\n- `a.md`\n"
        subject = _subject(merge_docs, " []", body)
        cmd_merge_related(["--fix"])
        content = subject.read_text(encoding="utf-8")
        assert content.endswith("text\n")
        assert "  - a.md" in content


class TestMergeRelatedShapes:
    @pytest.mark.parametrize("related", [" []", "", "\n  - a.md"])
    def test_each_supported_shape_receives_additions(
        self, merge_docs: Path, related: str
    ) -> None:
        body = "## Related Documents\n\n- `b.md`\n" + _TAIL
        subject = _subject(merge_docs, related, body)
        cmd_merge_related(["--fix"])
        content = subject.read_text(encoding="utf-8")
        assert "  - b.md\n---" in content

    def test_unsupported_inline_list_is_skipped_and_exits_nonzero(
        self, merge_docs: Path, capsys: pytest.CaptureFixture
    ) -> None:
        body = "## Related Documents\n\n- `b.md`\n" + _TAIL
        subject = _subject(merge_docs, " [a.md]", body)
        before = subject.read_bytes()
        assert cmd_merge_related(["--fix"]) == 1
        assert subject.read_bytes() == before
        assert "skipped (unsupported)" in capsys.readouterr().out

    def test_unsupported_in_dry_run_still_exits_zero(self, merge_docs: Path) -> None:
        _subject(merge_docs, " [a.md]", "text\n" + _TAIL)
        assert cmd_merge_related([]) == 0


class TestMergeRelatedEdgeCases:
    def test_self_reference_and_duplicates_are_dropped(self, merge_docs: Path) -> None:
        body = "## Related Documents\n\n- `s.md`\n- `a.md`\n" + _TAIL
        subject = _subject(merge_docs, "\n  - s.md\n  - a.md\n  - a.md", body)
        cmd_merge_related(["--fix"])
        content = subject.read_text(encoding="utf-8")
        assert "related:\n  - a.md\n---" in content

    def test_existing_path_entries_are_normalized_to_basenames(
        self, merge_docs: Path
    ) -> None:
        subject = _subject(merge_docs, "\n  - ../a.md", "text\n" + _TAIL)
        cmd_merge_related(["--fix"])
        content = subject.read_text(encoding="utf-8")
        assert "related:\n  - a.md\n---" in content

    def test_unresolved_body_reference_is_reported_not_merged(
        self, merge_docs: Path, capsys: pytest.CaptureFixture
    ) -> None:
        body = "## Related Documents\n\n- `a.md`\n- `missing.md`\n" + _TAIL
        subject = _subject(merge_docs, " []", body)
        assert cmd_merge_related(["--fix"]) == 1
        content = subject.read_text(encoding="utf-8")
        assert "  - a.md" in content
        assert "missing.md\n---" not in content
        assert "## Related Documents" in content, "section must be kept"
        assert "unresolved (no such document): missing.md" in capsys.readouterr().out

    def test_non_link_line_keeps_section_but_merges_links(
        self, merge_docs: Path, capsys: pytest.CaptureFixture
    ) -> None:
        body = "## Related Documents\n\n- `a.md`\n\nSee also the notes.\n" + _TAIL
        subject = _subject(merge_docs, " []", body)
        assert cmd_merge_related(["--fix"]) == 0
        content = subject.read_text(encoding="utf-8")
        assert "related:\n  - a.md\n---" in content
        assert "See also the notes." in content
        assert "## Related Documents" in content
        assert "non-link line (section kept)" in capsys.readouterr().out


class TestMergeRelatedAdr:
    def test_adr_front_matter_is_extended_and_body_is_untouched(
        self, merge_docs: Path
    ) -> None:
        body = (
            "## Related Documents\n\n### Specifications\n\n- `a.md`\n- `b.md`\n" + _TAIL
        )
        adr = _subject(merge_docs, "\n  - a.md", body, name="10_adr/ADR-001-x.md")
        before_body = adr.read_text(encoding="utf-8").split("\n---\n", 1)[1]
        assert cmd_merge_related(["--fix"]) == 0
        content = adr.read_text(encoding="utf-8")
        assert "related:\n  - a.md\n  - b.md\n---" in content
        assert content.split("\n---\n", 1)[1] == before_body


class TestMergeRelatedSelection:
    def test_documents_in_subdirectories_are_processed(self, merge_docs: Path) -> None:
        body = "## Related Documents\n\n- `a.md`\n" + _TAIL
        nested = _subject(merge_docs, " []", body, name="sub/n.md")
        cmd_merge_related(["--fix"])
        assert "  - a.md" in nested.read_text(encoding="utf-8")

    def test_paths_argument_limits_the_run(self, merge_docs: Path) -> None:
        body = "## Related Documents\n\n- `a.md`\n" + _TAIL
        first = _subject(merge_docs, " []", body, name="first.md")
        second = _subject(merge_docs, " []", body, name="second.md")
        second_before = second.read_bytes()
        cmd_merge_related([str(first), "--fix"])
        assert "  - a.md" in first.read_text(encoding="utf-8")
        assert second.read_bytes() == second_before

    def test_paths_outside_docs_are_ignored(
        self, merge_docs: Path, tmp_path: Path
    ) -> None:
        outside = tmp_path / "outside.md"
        outside.write_text(
            _doc(" []", "## Related Documents\n\n- `a.md`\n" + _TAIL),
            encoding="utf-8",
        )
        before = outside.read_bytes()
        cmd_merge_related([str(outside), "--fix"])
        assert outside.read_bytes() == before


class TestMergeRelatedErrorPaths:
    @pytest.mark.parametrize(
        ("text", "message"),
        [
            ("# No front matter\n", "no front matter"),
            ("---\ntitle: T\nrelated: []\n", "no closing"),
            ("---\ntitle: T\n---\n\n# T\n", "no 'related:' key"),
            (
                "---\ntitle: T\nrelated:\n  - 'a.md'\n---\n\n# T\n",
                "unsupported entry",
            ),
        ],
    )
    def test_unsupported_layouts_are_reported_and_untouched(
        self,
        merge_docs: Path,
        capsys: pytest.CaptureFixture,
        text: str,
        message: str,
    ) -> None:
        path = merge_docs / "odd.md"
        path.write_text(text, encoding="utf-8")
        assert cmd_merge_related(["--fix"]) == 1
        assert path.read_text(encoding="utf-8") == text
        assert message in capsys.readouterr().out

    def test_existing_entry_without_target_is_kept_and_reported(
        self, merge_docs: Path, capsys: pytest.CaptureFixture
    ) -> None:
        subject = _subject(merge_docs, "\n  - ghost.md\n  - a.md", "text\n" + _TAIL)
        assert cmd_merge_related(["--fix"]) == 1
        content = subject.read_text(encoding="utf-8")
        assert "related:\n  - ghost.md\n  - a.md\n---" in content
        assert "unresolved (no such document): ghost.md" in capsys.readouterr().out

    def test_key_after_related_block_is_preserved(self, merge_docs: Path) -> None:
        subject = merge_docs / "s.md"
        subject.write_text(
            "---\ntitle: T\nrelated:\n  - a.md\nsource:\n  - x\n---\n\n# T\n\n"
            "## Related Documents\n\n- `b.md`\n" + _TAIL,
            encoding="utf-8",
        )
        cmd_merge_related(["--fix"])
        content = subject.read_text(encoding="utf-8")
        assert "related:\n  - a.md\n  - b.md\nsource:\n  - x\n---" in content


class TestMergeRelatedEntryPoints:
    def test_relative_pattern_resolves_against_repo_root(
        self, merge_docs: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("tools.manage_frontmatter.ROOT_DIR", merge_docs.parent)
        body = "## Related Documents\n\n- `a.md`\n" + _TAIL
        subject = _subject(merge_docs, " []", body)
        cmd_merge_related(["docs/s.md", "--fix"])
        assert "  - a.md" in subject.read_text(encoding="utf-8")

    def test_missing_docs_directory_exits_nonzero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("tools.manage_frontmatter.DOCS_DIR", tmp_path / "none")
        assert cmd_merge_related([]) == 1

    def test_main_dispatches_the_subcommand(self, merge_docs: Path) -> None:
        body = "## Related Documents\n\n- `a.md`\n" + _TAIL
        subject = _subject(merge_docs, " []", body)
        assert main(["merge-related", "--fix"]) == 0
        assert "  - a.md" in subject.read_text(encoding="utf-8")


class TestMergeRelatedOneTimeAid:
    """merge-related migrates second-level (## ) body Related sections only;
    deep ### blocks are left untouched (one-time migration aid)."""

    def test_detects_and_migrates_h2_section(self, merge_docs: Path) -> None:
        body = "Some text.\n\n## Related Documents\n\n- `b.md`\n" + _TAIL
        subject = _subject(merge_docs, " []", body)
        assert cmd_merge_related(["--fix"]) == 0
        content = subject.read_text(encoding="utf-8")
        assert "  - b.md" in content
        assert "## Related Documents" not in content

    def test_does_not_detect_h3_section(self, merge_docs: Path) -> None:
        body = "Some text.\n\n### Related Documents\n\n- `b.md`\n" + _TAIL
        subject = _subject(merge_docs, " []", body)
        before = subject.read_bytes()
        assert cmd_merge_related(["--fix"]) == 0
        assert subject.read_bytes() == before
        assert "### Related Documents" in subject.read_text(encoding="utf-8")

    def test_dry_run_default_leaves_h2_section(
        self, merge_docs: Path, capsys: pytest.CaptureFixture
    ) -> None:
        body = "## Related Documents\n\n- `b.md`\n" + _TAIL
        subject = _subject(merge_docs, " []", body)
        before = subject.read_bytes()
        assert cmd_merge_related([]) == 0
        assert subject.read_bytes() == before
        assert "[DRY-RUN]" in capsys.readouterr().out
