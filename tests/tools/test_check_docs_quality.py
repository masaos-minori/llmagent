#!/usr/bin/env python3
"""Tests for tools.check_docs_quality — alphabetic-suffix duplicate headings + content similarity."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from tools import check_docs_quality as cdq
from tools.check_docs_quality import (
    _compute_section_similarity,
    check_content_similarity,
    check_duplicate_heading_numbers,
)

# Baseline of within-file content-similarity pairs. Sections shorter than the
# within-file token threshold are not compared, so the docs tree currently has
# none; a new entry means real duplicated prose appeared inside one document.
EXPECTED_WITHIN_FILE_PAIRS: frozenset[str] = frozenset()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_DOCS_DIR = _ROOT_DIR / "docs"

# Long enough to clear the within-file token threshold.
_LONG_TEXT = (
    "This is boilerplate content that appears in many documents and describes the "
    "purpose and scope of the section in detail. It explains the responsibilities "
    "involved, the constraints that apply, the inputs that are accepted, the outputs "
    "that are produced and the failure behavior that callers should expect."
)


def _make_doc_file(
    content: str, path: Path | None = None, tmp_name: str = ".tmp_test_doc.md"
) -> object:
    """Construct an object that behaves like DocFile for check functions."""

    class FakeDocFile:
        def __init__(self, content: str, path: Path | None = None) -> None:
            self.lines = content.splitlines()
            if path is not None:
                self.path = path
                self.rel_path = str(path.relative_to(_ROOT_DIR / "docs"))
            else:
                tmp = _ROOT_DIR / tmp_name
                tmp.write_text(content, encoding="utf-8")
                self.path = tmp
                self.rel_path = tmp_name

    return FakeDocFile(content, path)


@pytest.fixture(autouse=True)
def _cleanup_tmp_test_doc() -> Iterator[None]:
    """Remove the .tmp_test_doc.md scratch file left by _make_doc_file after each test.

    _make_doc_file writes a scratch markdown file to the repo root when called
    without an explicit path (the check functions read it back from disk). This
    autouse fixture deletes the file once the test body finishes, so it never
    lingers in the working tree between or across test runs.
    """
    yield
    (_ROOT_DIR / ".tmp_test_doc.md").unlink(missing_ok=True)


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
        assert (
            _compute_section_similarity(
                "hello world foo bar",
                "hello baz qux quux",
            )
            is False
        )

    def test_custom_threshold(self):
        # With threshold=0.1, partial overlap should pass
        assert (
            _compute_section_similarity(
                "hello world foo bar",
                "hello baz qux quux",
                threshold=0.1,
            )
            is True
        )

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
    def test_true_positive_exact_duplicate_lettered_number(self):
        """The same lettered number twice at the same level → expect Issue."""
        content = "# Title\n\n## 7c. First section\n\nText.\n\n## 7c. Second section\n\nMore text."
        doc = _make_doc_file(content)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"
        assert "7c" in issues[0].message

    def test_distinct_suffixes_of_one_base_are_not_reported(self):
        """7a, 7b, 7c are a legitimate sub-numbering scheme → no Issue."""
        content = (
            "# Title\n\n## 7a. First\n\nA.\n\n## 7b. Second\n\nB.\n\n## 7c. Third\n\nC."
        )
        doc = _make_doc_file(content)
        assert check_duplicate_heading_numbers(_DOCS_DIR, [doc]) == []

    def test_false_positive_different_base_numbers(self):
        """Different base numbers at same level → no Issue."""
        content = "# Title\n\n## 7a. First section\n\nText A.\n\n## 8b. Second section\n\nText B."
        doc = _make_doc_file(content)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])
        assert len(issues) == 0

    def test_false_positive_numeric_subsections(self):
        """Numeric subsections like 2.1, 2.2 → no Issue."""
        content = "# Title\n\n## 2.1 First subsection\n\nText A.\n\n## 2.2 Second subsection\n\nText B."
        doc = _make_doc_file(content)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])
        assert len(issues) == 0

    def test_false_positive_different_levels(self):
        """Same heading number at different levels → no Issue."""
        content = "# Title\n\n## 7a. Level 2 section\n\nText A.\n\n####### 7a. Level 7 section\n\nText B."
        doc = _make_doc_file(content)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])
        assert len(issues) == 0

    def test_lettered_number_inside_fenced_block_is_ignored(self):
        content = "# Title\n\n## 7c. Real\n\n```md\n## 7c. Example\n```\n"
        doc = _make_doc_file(content)
        assert check_duplicate_heading_numbers(_DOCS_DIR, [doc]) == []


# ---------------------------------------------------------------------------
# Tests for content-similarity check
# ---------------------------------------------------------------------------


class TestContentSimilarity:
    def test_true_positive_overlapping_sections(self):
        """Two sections with heavily overlapping body text → expect Issue."""
        common_text = _LONG_TEXT
        content = f"# Title\n\n## Section One\n\n{common_text}\n\n## Section Two\n\n{common_text}"
        doc = _make_doc_file(content)
        issues = check_content_similarity(_DOCS_DIR, [doc])
        assert len(issues) >= 1
        assert any("similarity" in issue.message.lower() for issue in issues)

    def test_false_positive_templated_distinct_sections(self):
        """Two templated-but-distinct sections → no Issue."""
        verification_a = (
            "Verification: This item has been verified against the current source code."
        )
        verification_b = "Verification: This item has been validated against the latest documentation updates."
        content = f"# Title\n\n## Verification A\n\n{verification_a}\n\n## Verification B\n\n{verification_b}"
        doc = _make_doc_file(content)
        issues = check_content_similarity(_DOCS_DIR, [doc])
        assert len(issues) == 0

    def test_false_positive_short_unique_sections(self):
        """Short sections with minimal overlap → no Issue."""
        content = "# Title\n\n## Short A\n\nA.\n\n## Short B\n\nB."
        doc = _make_doc_file(content)
        issues = check_content_similarity(_DOCS_DIR, [doc])
        assert len(issues) == 0

    def test_content_similarity_across_multiple_sections(self):
        """Three sections where two share heavy overlap → expect one Issue."""
        shared = _LONG_TEXT
        content = f"# Title\n\n## Section One\n\n{shared}\n\n## Section Two\n\nUnique content here.\n\n## Section Three\n\n{shared}"
        doc = _make_doc_file(content)
        issues = check_content_similarity(_DOCS_DIR, [doc])
        assert len(issues) >= 1


class TestContentSimilarityCrossFile:
    def test_true_positive_cross_file_overlap(self):
        """Two different documents sharing a near-duplicate section body → expect cross-file Issue."""
        common_text = (
            "This is boilerplate content that appears in many documents. "
            "It describes the purpose and scope of the section."
        )
        content_a = f"# Title A\n\n## Section One\n\n{common_text}"
        content_b = f"# Title B\n\n## Section Two\n\n{common_text}"
        doc_a = _make_doc_file(content_a, tmp_name=".tmp_test_doc_a.md")
        doc_b = _make_doc_file(content_b, tmp_name=".tmp_test_doc_b.md")
        try:
            issues = check_content_similarity(_DOCS_DIR, [doc_a, doc_b])
            assert len(issues) >= 1
            assert any(
                doc_a.rel_path in issue.message and doc_b.rel_path in issue.message
                for issue in issues
            )
        finally:
            (_ROOT_DIR / ".tmp_test_doc_a.md").unlink(missing_ok=True)
            (_ROOT_DIR / ".tmp_test_doc_b.md").unlink(missing_ok=True)

    def test_false_positive_cross_file_unrelated(self):
        """Two different documents with unrelated content → no cross-file Issue."""
        content_a = (
            "# Title A\n\n## Section One\n\nCompletely unrelated discussion of widgets."
        )
        content_b = (
            "# Title B\n\n## Section Two\n\nA totally different discussion of gadgets."
        )
        doc_a = _make_doc_file(content_a, tmp_name=".tmp_test_doc_a.md")
        doc_b = _make_doc_file(content_b, tmp_name=".tmp_test_doc_b.md")
        try:
            issues = check_content_similarity(_DOCS_DIR, [doc_a, doc_b])
            assert issues == []
        finally:
            (_ROOT_DIR / ".tmp_test_doc_a.md").unlink(missing_ok=True)
            (_ROOT_DIR / ".tmp_test_doc_b.md").unlink(missing_ok=True)


class TestExtractSectionsFencedCode:
    def test_comment_line_in_fenced_block_is_not_a_heading(self):
        from tools.check_docs_quality import _extract_sections

        content = "# Title\n\n## Real\n\n```bash\n# a comment\necho hi\n```\n\nafter"
        headings = [s["heading"] for s in _extract_sections(content)]
        assert headings == ["Title", "Real"]


class TestWithinFileSizeThreshold:
    def test_short_parallel_sections_are_not_reported(self):
        body = "Returned when the request succeeds."
        content = f"# T\n\n## One\n\n{body}\n\n## Two\n\n{body}\n"
        doc = _make_doc_file(content)
        assert check_content_similarity(_DOCS_DIR, [doc]) == []

    def test_long_duplicated_sections_are_still_reported(self):
        body = " ".join(f"word{n}" for n in range(40))
        content = f"# T\n\n## One\n\n{body}\n\n## Two\n\n{body}\n"
        doc = _make_doc_file(content)
        assert len(check_content_similarity(_DOCS_DIR, [doc])) >= 1


class TestPlaceholderSections:
    def test_identical_placeholder_sections_in_one_file_are_not_reported(self):
        content = (
            "# T\n\n## Operational Notes\n\n- Unknown\n\n"
            "## Known Limitations\n\n- Unknown\n"
        )
        doc = _make_doc_file(content)
        assert check_content_similarity(_DOCS_DIR, [doc]) == []

    def test_identical_real_content_in_one_file_is_still_reported(self):
        body = _LONG_TEXT
        content = f"# T\n\n## One\n\n{body}\n\n## Two\n\n{body}\n"
        doc = _make_doc_file(content)
        assert len(check_content_similarity(_DOCS_DIR, [doc])) >= 1


class TestContentSimilarityTemplateSections:
    """Same-heading template sections between ADRs / area guides are exempt."""

    _COMMON = (
        "This is boilerplate content that appears in many documents. "
        "It describes the purpose and scope of the section."
    )

    def _run(self, name_a: str, heading_a: str, name_b: str, heading_b: str):
        return self._run_bodies(
            name_a, heading_a, self._COMMON, name_b, heading_b, self._COMMON
        )

    def _run_bodies(
        self,
        name_a: str,
        heading_a: str,
        body_a: str,
        name_b: str,
        heading_b: str,
        body_b: str,
    ):
        doc_a = _make_doc_file(f"# A\n\n## {heading_a}\n\n{body_a}", tmp_name=name_a)
        doc_b = _make_doc_file(f"# B\n\n## {heading_b}\n\n{body_b}", tmp_name=name_b)
        try:
            return check_content_similarity(_DOCS_DIR, [doc_a, doc_b])
        finally:
            (_ROOT_DIR / name_a).unlink(missing_ok=True)
            (_ROOT_DIR / name_b).unlink(missing_ok=True)

    def test_adr_template_section_is_exempt(self):
        issues = self._run(
            "ADR-901-a.md", "Approval Record", "ADR-902-b.md", "Approval Record"
        )
        assert issues == []

    def test_adr_non_template_section_is_still_reported(self):
        issues = self._run(
            "ADR-901-a.md", "Alternative A", "ADR-902-b.md", "Alternative A"
        )
        assert len(issues) >= 1

    def test_adr_template_heading_against_non_adr_is_still_reported(self):
        issues = self._run(
            "ADR-901-a.md", "Approval Record", "other_doc.md", "Approval Record"
        )
        assert len(issues) >= 1

    def test_navigation_sections_are_exempt(self):
        links = "- [a](a.md)\n- [b](b.md)\n- [c](c.md)\n- [d](d.md)\n- [e](e.md)"
        issues = self._run_bodies(
            "x.md", "See Also", links, "y.md", "Other Pointers", links
        )
        assert issues == []

    def test_non_navigation_similar_sections_are_still_reported(self):
        issues = self._run_bodies(
            "x.md", "Details", self._COMMON, "y.md", "Notes", self._COMMON
        )
        assert len(issues) >= 1

    def test_adr_companion_document_counts_as_adr(self):
        issues = self._run(
            "ADR-901-a.md",
            "Deployment Validation",
            "adr_91_supporting-sections.md",
            "Deployment Validation",
        )
        assert issues == []

    def test_guide_template_section_is_exempt(self):
        issues = self._run(
            "x_00_document-guide.md",
            "Canonical Sources",
            "y_00_document-guide.md",
            "Canonical Sources",
        )
        assert issues == []

    def test_guide_other_section_is_still_reported(self):
        issues = self._run(
            "x_00_document-guide.md", "Purpose", "y_00_document-guide.md", "Purpose"
        )
        assert len(issues) >= 1


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


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

        lines = result.stdout.split("\n") + result.stderr.split("\n")
        for line in lines:
            if ".1" in line or ".2" in line or ".3" in line:
                assert "duplicate" not in line.lower(), (
                    f"False positive on numeric subsection: {line}"
                )

    def test_cross_file_duplication_detected_on_full_docs_tree(self):
        """Run the checker against the full docs/ tree → confirm the set of
        within-file similarity pairs still matches the recorded baseline."""
        if not _DOCS_DIR.exists():
            pytest.skip(f"Docs directory not found: {_DOCS_DIR}")

        result = subprocess.run(
            [sys.executable, "-m", "tools.check_docs_quality"],
            capture_output=True,
            text=True,
            cwd=str(_ROOT_DIR),
        )
        output = result.stdout + result.stderr

        current_pairs: set[str] = set()
        for line in output.split("\n"):
            m = re.search(
                r"\[WARNING\] ([^:]+):\d+ — Content similarity detected between "
                r"sections '([^']+)' and '([^']+)'",
                line,
            )
            if m:
                file_path = m.group(1)
                section_a = m.group(2)
                section_b = m.group(3)
                current_pairs.add(
                    f"{file_path}:{repr(section_a)} <-> {repr(section_b)}"
                )

        assert current_pairs == EXPECTED_WITHIN_FILE_PAIRS, (
            f"Within-file content-similarity pairs changed:\n"
            f"Added: {current_pairs - EXPECTED_WITHIN_FILE_PAIRS}\n"
            f"Removed: {EXPECTED_WITHIN_FILE_PAIRS - current_pairs}"
        )


# ---------------------------------------------------------------------------
# Custom rules: history / uncertainty wording (config/doc_quality_rules.json)
# ---------------------------------------------------------------------------


def _run_live_rule(rule_name: str, lines: list[str]) -> list[cdq.Issue]:
    """Build the named rule from the real rules file and run it on `lines`."""
    cdq._CUSTOM_RULES.clear()
    cdq.load_custom_rules(_DOCS_DIR)
    try:
        doc = cdq.DocFile(path=Path("x.md"), rel_path="x.md", lines=lines)
        return cdq._CUSTOM_RULES[rule_name](_DOCS_DIR, [doc])
    finally:
        cdq._CUSTOM_RULES.clear()


class TestHistoryMarkerRule:
    @pytest.mark.parametrize(
        "line",
        [
            "Rule text. (Added 2026-09-02; see the issue.)",
            "- `implementations/done/20260829-134950_01_x.md`: Create module",
            "Fixed by REQ-001 in the strict default.",
            "### Impact of REQ-001",
            "- **Resolved**: the protected-branch short-circuit was fixed.",
            "- **Resolved Issue**: recovery treated UNKNOWN as corrupt.",
            "~~Orchestrator creates an unused runner~~",
            "## Traceability",
        ],
    )
    def test_marker_is_reported_even_with_historical_wording(self, line: str) -> None:
        issues = _run_live_rule("history_marker_in_active_doc", [line])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"

    def test_current_state_wording_is_not_reported(self) -> None:
        lines = [
            "`SecurityProfile` holds only PRODUCTION.",
            "Resolved server key names are cached after startup.",
        ]
        assert _run_live_rule("history_marker_in_active_doc", lines) == []


class TestUncertaintyPhraseRule:
    @pytest.mark.parametrize(
        "line",
        [
            "Retention policy is unresolved — requires verification against code.",
            "Latency may increase. To be verified.",
            "Threshold: TBD",
            "This behavior is not yet confirmed.",
            "Pending decision on the cleanup policy.",
        ],
    )
    def test_unverified_wording_is_reported(self, line: str) -> None:
        issues = _run_live_rule("uncertainty_phrase_outside_inventory", [line])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"

    def test_ordinary_wording_is_not_reported(self) -> None:
        lines = [
            "Unknown tool names raise ValueError.",
            "Verification is performed by the integration tests.",
        ]
        assert _run_live_rule("uncertainty_phrase_outside_inventory", lines) == []


class TestExemptHistoricalContextOption:
    def test_default_rule_skips_lines_with_historical_marker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        rules = tmp_path / "rules.json"
        rules.write_text(
            json.dumps(
                {
                    "rules": {
                        "default_rule": {"pattern": "FOO", "severity": "ERROR"},
                        "strict_rule": {
                            "pattern": "FOO",
                            "severity": "ERROR",
                            "exempt_historical_context": False,
                        },
                    }
                }
            )
        )
        monkeypatch.setattr(cdq, "CUSTOM_RULES_FILE", rules)
        cdq._CUSTOM_RULES.clear()
        cdq.load_custom_rules(_DOCS_DIR)
        try:
            doc = cdq.DocFile(
                path=Path("x.md"), rel_path="x.md", lines=["FOO was removed"]
            )
            assert cdq._CUSTOM_RULES["default_rule"](_DOCS_DIR, [doc]) == []
            assert len(cdq._CUSTOM_RULES["strict_rule"](_DOCS_DIR, [doc])) == 1
        finally:
            cdq._CUSTOM_RULES.clear()
