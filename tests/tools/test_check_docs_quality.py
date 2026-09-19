#!/usr/bin/env python3
"""Tests for tools.check_docs_quality — alphabetic-suffix duplicate headings + content similarity."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tools.check_docs_quality import (
    _compute_section_similarity,
    check_content_similarity,
    check_duplicate_heading_numbers,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_DOCS_DIR = _ROOT_DIR / "docs"
_KNOWN_DEFECT_PATH = _DOCS_DIR / "90_shared_02_02_types_and_protocols-tool-and-execution-dto.md"


def _make_doc_file(content: str, path: Path | None = None) -> object:
    """Construct an object that behaves like DocFile for check functions."""
    class FakeDocFile:
        def __init__(self, content: str, path: Path | None = None) -> None:
            self.lines = content.splitlines()
            if path is not None:
                self.path = path
                self.rel_path = str(path.relative_to(_ROOT_DIR / "docs"))
            else:
                tmp = _ROOT_DIR / ".tmp_test_doc.md"
                tmp.write_text(content, encoding="utf-8")
                self.path = tmp
                self.rel_path = ".tmp_test_doc.md"

    return FakeDocFile(content, path)

# ---------------------------------------------------------------------------
# Tests for _compute_section_similarity
# ---------------------------------------------------------------------------

class TestComputeSectionSimilarity:
    def test_identical_sections(self):
        text = "hello world foo bar baz"
        assert _compute_section_similarity(text, text) is True

    def test_no_overlap(self):
        assert _compute_section_similarity("hello world", "foo bar baz") is False

    def test_partial_overlap_below_threshold(self):
        # Only 1 word overlap out of ~6 unique words → Jaccard ≈ 0.14 < 0.85
        assert _compute_section_similarity(
            "hello world foo bar",
            "hello baz qux quux",
        ) is False

    def test_custom_threshold(self):
        # With threshold=0.1, partial overlap should pass
        assert _compute_section_similarity(
            "hello world foo bar",
            "hello baz qux quux",
            threshold=0.1,
        ) is True

    def test_empty_body_returns_false(self):
        assert _compute_section_similarity("", "some text") is False
        assert _compute_section_similarity("some text", "") is False

    def test_code_blocks_are_stripped(self):
        text_with_code = "before ```code\nprint('hello')\n```\nafter"
        text_without_code = "before after"
        result = _compute_section_similarity(text_with_code, text_without_code)
        assert result is True

# ---------------------------------------------------------------------------
# Tests for alphabetic-suffix duplicate-heading detection
# ---------------------------------------------------------------------------

class TestAlphabeticSuffixDuplicateHeading:
    def test_true_positive_same_base_number(self):
        """Two headings with same base number and same level → expect Issue."""
        content = "# Title\n\n## 7a. First section\n\nSome text.\n\n## 7b. Second section\n\nMore text."
        doc = _make_doc_file(content)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])  # type: ignore[arg-type]
        assert len(issues) == 1
        assert "7a" in str(issues[0].message) or "7b" in str(issues[0].message)

    def test_true_positive_known_defect_case(self):
        """The known ## 7c. duplicate in docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md → expect Issue."""
        if not _KNOWN_DEFECT_PATH.exists():
            pytest.skip(f"Test file not found: {_KNOWN_DEFECT_PATH}")
        content = _KNOWN_DEFECT_PATH.read_text(encoding="utf-8")
        doc = _make_doc_file(content, path=_KNOWN_DEFECT_PATH)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])  # type: ignore[arg-type]
        assert len(issues) >= 1
        assert any("7c" in str(issue.message) for issue in issues)

    def test_false_positive_different_base_numbers(self):
        """Different base numbers at same level → no Issue."""
        content = "# Title\n\n## 7a. First section\n\nText A.\n\n## 8b. Second section\n\nText B."
        doc = _make_doc_file(content)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])  # type: ignore[arg-type]
        assert len(issues) == 0

    def test_false_positive_numeric_subsections(self):
        """Numeric subsections like 2.1, 2.2 → no Issue."""
        content = "# Title\n\n## 2.1 First subsection\n\nText A.\n\n## 2.2 Second subsection\n\nText B."
        doc = _make_doc_file(content)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])  # type: ignore[arg-type]
        assert len(issues) == 0

    def test_false_positive_different_levels(self):
        """Same heading number at different levels → no Issue."""
        content = "# Title\n\n## 7a. Level 2 section\n\nText A.\n\n####### 7a. Level 7 section\n\nText B."
        doc = _make_doc_file(content)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])  # type: ignore[arg-type]
        assert len(issues) == 0

# ---------------------------------------------------------------------------
# Tests for content-similarity check
# ---------------------------------------------------------------------------

class TestContentSimilarity:
    def test_true_positive_overlapping_sections(self):
        """Two sections with heavily overlapping body text → expect Issue."""
        common_text = ("This is boilerplate content that appears in many documents. "
                       "It describes the purpose and scope of the section.")
        content = f"# Title\n\n## Section One\n\n{common_text}\n\n## Section Two\n\n{common_text}"
        doc = _make_doc_file(content)
        issues = check_content_similarity(_DOCS_DIR, [doc])  # type: ignore[arg-type]
        assert len(issues) >= 1
        assert any("similarity" in issue.message.lower() for issue in issues)

    def test_false_positive_templated_distinct_sections(self):
        """Two templated-but-distinct sections → no Issue."""
        verification_a = "Verification: This item has been verified against the current source code."
        verification_b = "Verification: This item has been validated against the latest documentation updates."
        content = f"# Title\n\n## Verification A\n\n{verification_a}\n\n## Verification B\n\n{verification_b}"
        doc = _make_doc_file(content)
        issues = check_content_similarity(_DOCS_DIR, [doc])  # type: ignore[arg-type]
        assert len(issues) == 0

    def test_false_positive_short_unique_sections(self):
        """Short sections with minimal overlap → no Issue."""
        content = "# Title\n\n## Short A\n\nA.\n\n## Short B\n\nB."
        doc = _make_doc_file(content)
        issues = check_content_similarity(_DOCS_DIR, [doc])  # type: ignore[arg-type]
        assert len(issues) == 0

    def test_content_similarity_across_multiple_sections(self):
        """Three sections where two share heavy overlap → expect one Issue."""
        shared = "Shared content between sections one and three."
        content = f"# Title\n\n## Section One\n\n{shared}\n\n## Section Two\n\nUnique content here.\n\n## Section Three\n\n{shared}"
        doc = _make_doc_file(content)
        issues = check_content_similarity(_DOCS_DIR, [doc])  # type: ignore[arg-type]
        assert len(issues) >= 1

# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

class TestIntegrationKnownDefect:
    def test_run_checker_against_known_duplicate(self):
        """Run checker against the known defect file → expect '7c' in output."""
        if not _KNOWN_DEFECT_PATH.exists():
            pytest.skip(f"Test file not found: {_KNOWN_DEFECT_PATH}")

        result = subprocess.run(
            [sys.executable, "-m", "tools.check_docs_quality", "--only",
             "duplicate_heading_numbers", str(_KNOWN_DEFECT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(_ROOT_DIR),
        )

        # Warnings don't trigger non-zero exit; check output content instead
        assert "7c" in result.stdout or "7c" in result.stderr

class TestRegressionFullDocsTree:
    def test_no_new_false_positives_on_full_docs_tree(self):
        """Run checker against full docs/ tree → confirm no false-positive noise on numeric subsections."""
        if not _DOCS_DIR.exists():
            pytest.skip(f"Docs directory not found: {_DOCS_DIR}")

        result = subprocess.run(
            [sys.executable, "-m", "tools.check_docs_quality"],
            capture_output=True,
            text=True,
            cwd=str(_ROOT_DIR),
        )

        lines = result.stdout.split('\n') + result.stderr.split('\n')
        for line in lines:
            if ".1" in line or ".2" in line or ".3" in line:
                assert "duplicate" not in line.lower(), (
                    f"False positive on numeric subsection: {line}"
                )
