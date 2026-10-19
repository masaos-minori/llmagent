"""tests/tools/test_check_glossary_term_classification.py

Tests for tools/check_glossary_term_classification.py.

Each scenario builds small in-memory Markdown tables and calls the parser /
classifier / audit functions directly -- matching the direct-function-call
pattern used by tests/tools/test_check_auto_check_inventory.py. The real
repository corpus (the governance_02 glossary table) is asserted clean exactly
once here, per REQ-004; it is not duplicated as unit fixtures.
"""

from __future__ import annotations

from pathlib import Path

from tools.check_glossary_term_classification import (
    GOVERNANCE_02_REL,
    _find_section_index,
    _first_cell,
    _is_separator_row,
    audit,
    classify,
    main,
    parse_glossary_terms,
    resolve_governance_02,
)


def _row(*cells: str) -> str:
    return "|" + "|".join(f" {c} " for c in cells) + "|"


def _table(*rows: str) -> str:
    return "\n".join(rows) + "\n"


def _write_glossary(path: Path, rows: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_table(*rows), encoding="utf-8")
    return path


class TestHelpers:
    def test_first_cell_returns_raw_unstripped_cell(self) -> None:
        # Stripping is the caller's responsibility (parse_glossary_terms).
        assert (
            _first_cell("| Backward Compatibility | x |") == " Backward Compatibility "
        )
        assert _first_cell("no pipes here") == ""

    def test_separator_row_detection(self) -> None:
        assert _is_separator_row("|------|------------|") is True
        assert _is_separator_row("| Real row | desc |") is False

    def test_find_section_index_is_case_insensitive(self) -> None:
        idx = _find_section_index(
            ["### COMPATIBILITY AND LIFECYCLE TERMINOLOGY"],
            "compatibility and lifecycle terminology",
        )
        assert idx == 0
        assert _find_section_index(["unrelated heading"], "compatibility") is None


class TestParseGlossaryTerms:
    def test_returns_empty_when_file_missing(self, tmp_path: Path) -> None:
        assert parse_glossary_terms(tmp_path / "missing.md") == []

    def test_returns_empty_when_section_absent(self, tmp_path: Path) -> None:
        gov = _write_glossary(tmp_path / "docs" / "g.md", ["| Term | Definition |"])
        assert parse_glossary_terms(gov) == []

    def test_extracts_first_cell_of_each_data_row_with_line_numbers(
        self, tmp_path: Path
    ) -> None:
        gov = _write_glossary(
            tmp_path / "docs" / "g.md",
            [
                "### Compatibility and Lifecycle Terminology",
                "",
                "| Term | Definition | Example |",
                "|------|------------|---------|",
                _row("Backward Compatibility", "desc", "ex"),
                _row("Dead Code", "desc", "ex"),
                "",
                "## Next Section",
            ],
        )
        assert parse_glossary_terms(gov) == [
            ("Backward Compatibility", 5),
            ("Dead Code", 6),
        ]

    def test_section_match_is_case_insensitive(self, tmp_path: Path) -> None:
        gov = _write_glossary(
            tmp_path / "docs" / "g.md",
            [
                "### compatibility and lifecycle terminology",
                "| Term | Definition |",
                "|------|------------|",
                _row("Migration", "desc"),
            ],
        )
        assert parse_glossary_terms(gov) == [("Migration", 4)]


class TestClassify:
    def test_capitalized_term_is_project_specific(self) -> None:
        assert classify("Default") is False
        assert classify("Backward Compatibility") is False
        assert classify("Dead Code") is False

    def test_capitalized_domain_prefixed_term_is_project_specific(self) -> None:
        # Procedure 02 fixture: a capitalized, domain-prefixed term (GV-015).
        assert classify("GV-015") is False

    def test_american_spelling_exceptions_are_project_specific(self) -> None:
        # Documented capitalized exceptions are canonical, never flagged.
        assert classify("Authorization") is False
        assert classify("Behavior") is False
        assert classify("Standardization") is False

    def test_lowercase_common_word_is_flagged(self) -> None:
        # Procedure 02 fixture: a lowercase common English word (behavior).
        assert classify("behavior") is True
        assert classify("example") is True

    def test_lowercase_unknown_word_is_not_flagged(self) -> None:
        assert classify("workflowx") is False

    def test_empty_term_is_not_flagged(self) -> None:
        assert classify("") is False

    def test_project_domain_prefix_is_project_specific(self) -> None:
        assert classify("gv-something") is False


class TestAudit:
    def test_flagged_term_produces_warning(self) -> None:
        issues = audit([("example", 12)])
        assert len(issues) == 1
        finding = issues[0]
        assert finding.severity == "WARNING"
        assert finding.line_no == 12
        assert "example" in finding.message
        assert "GV-015" in finding.message

    def test_file_field_points_at_governance_02(self) -> None:
        issues = audit([("sample", 3)])
        assert issues[0].file == GOVERNANCE_02_REL

    def test_general_common_term_produces_warning(self) -> None:
        # Procedure 02 REQ-003: a general/common entry is flagged at Warning.
        issues = audit([("behavior", 7)])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert "behavior" in issues[0].message

    def test_project_specific_term_produces_no_finding(self) -> None:
        assert audit([("Backward Compatibility", 5)]) == []


class TestResolveGovernance02:
    def test_resolves_under_root(self, tmp_path: Path) -> None:
        resolved = resolve_governance_02(tmp_path)
        assert (
            resolved
            == tmp_path
            / "docs"
            / "00_governance"
            / "governance_02_documentation-metadata.md"
        )


class TestMain:
    def test_strict_exits_nonzero_on_warning(self, tmp_path: Path) -> None:
        gov = _write_glossary(
            tmp_path
            / "docs"
            / "00_governance"
            / "governance_02_documentation-metadata.md",
            [
                "### Compatibility and Lifecycle Terminology",
                "| Term | Definition |",
                "|------|------------|",
                _row("example", "a generic word"),
            ],
        )
        root = str(gov.parent.parent.parent)
        assert main(["--root", root, "--strict"]) == 1
        # Non-strict still exits 0 despite the warning (report-only contract).
        assert main(["--root", root]) == 0

    def test_real_corpus_yields_zero_findings(self) -> None:
        # REQ-004: the canonical glossary term set must not be flagged.
        assert main([]) == 0
