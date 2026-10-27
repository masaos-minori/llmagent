"""tests/tools/test_check_adr_invariant_matrix.py
Tests for tools/check_adr_invariant_matrix.py.

Each scenario builds an in-memory Matrix table (as a list of lines) and calls
check_invariant_matrix_test_paths() directly, matching
tests/tools/test_check_known_deviation_sync.py's direct-function-call pattern.
Live `docs/10_adr/adr_01_index.md` validation (AC-1) is exercised separately by running
the tool against the real repository, not duplicated here as a unit test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.check_adr_invariant_matrix as checker
from tools.check_adr_invariant_matrix import (
    check_adr_body_evidence_cells,
    check_body_index_agreement,
    check_invariant_matrix_test_paths,
)

_HEADER = "| INV | ADR | Invariant | Type | Timing | Gate | Verification Status |"
_SEPARATOR = "|-----|-----|-----------|------|--------|------|---------------------|"


def _matrix(*rows: str) -> list[str]:
    return [
        "## ADR Invariant Verification Matrix",
        "",
        _HEADER,
        _SEPARATOR,
        *rows,
        "",
        "## Next Section",
        "unrelated content",
    ]


class TestResolvableTestPath:
    def test_existing_test_path_produces_no_issue(self) -> None:
        lines = _matrix(
            "| INV-001 | ADR-001 | x | Unit Test | CI | Blocking | "
            "Confirmed (`tests/agent/test_startup.py::test_aborts_on_missing_workflow_definition`, passing) |"
        )
        assert check_invariant_matrix_test_paths(lines) == []


class TestUnresolvableTestPath:
    def test_missing_file_produces_error(self) -> None:
        lines = _matrix(
            "| INV-999 | ADR-999 | x | Unit Test | CI | Blocking | "
            "Confirmed (`tests/nonexistent/test_fake.py::test_fake_thing`) |"
        )
        issues = check_invariant_matrix_test_paths(lines)
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"
        assert issues[0].file == "adr_01_index.md"
        assert "tests/nonexistent/test_fake.py::test_fake_thing" in issues[0].message


class TestCodeReferenceCellIsNotATestPath:
    """A cell like INV-003's `config_loader.py` `restrict_to()` has no `::`
    separator and must not be misread as a pytest node id."""

    def test_code_reference_without_double_colon_is_skipped(self) -> None:
        lines = _matrix(
            "| INV-003 | ADR-002 | x | Unit Test | CI | Blocking | "
            "Confirmed in code (`config_loader.py` `restrict_to()`); no test yet |"
        )
        assert check_invariant_matrix_test_paths(lines) == []


class TestNoTestYetRow:
    def test_row_with_no_backtick_path_is_skipped(self) -> None:
        lines = _matrix(
            "| INV-009 | ADR-009 | x | Integration Test | CI | Blocking | Not verified |"
        )
        assert check_invariant_matrix_test_paths(lines) == []


class TestMultipleRows:
    def test_only_the_broken_row_is_flagged(self) -> None:
        lines = _matrix(
            "| INV-001 | ADR-001 | x | Unit Test | CI | Blocking | "
            "Confirmed (`tests/agent/test_startup.py::test_aborts_on_missing_workflow_definition`) |",
            "| INV-999 | ADR-999 | x | Unit Test | CI | Blocking | "
            "Confirmed (`tests/nonexistent/test_fake.py::test_fake_thing`) |",
        )
        issues = check_invariant_matrix_test_paths(lines)
        assert len(issues) == 1
        assert (
            "INV-999" not in issues[0].message
        )  # message cites the path, not the INV id
        assert "tests/nonexistent" in issues[0].message


class TestMissingMatrixHeading:
    def test_no_heading_returns_no_issues(self) -> None:
        lines = ["## Some Other Section", "content with no matrix table"]
        assert check_invariant_matrix_test_paths(lines) == []


# ---------------------------------------------------------------------------
# Rules that read the ADR bodies (WARNING severity)
# ---------------------------------------------------------------------------

_BODY_HEADER = "| Test | Verifies | Type | Blocking | Implementation |"
_BODY_SEPARATOR = "|---|---|---|---|---|"
_INDEX_HEADER = "| Invariant | Statement | Type | Timing | Gate | Verification Status |"
_INDEX_SEPARATOR = "|---|---|---|---|---|---|"


def _body(*rows: str, header: str = _BODY_HEADER) -> list[str]:
    """Build an ADR body with an `### Automated Tests` table from `rows`."""
    return [
        "## Verification",
        "",
        "### Automated Tests",
        "",
        header,
        _BODY_SEPARATOR,
        *rows,
        "",
        "### Startup Validation",
        "- unrelated content",
    ]


def _row(inv: str, implementation: str) -> str:
    return f"| a test | {inv} | Unit | Yes | {implementation} |"


def _index(*rows: str) -> list[str]:
    """Build an index matrix with the real six-column header from `rows`."""
    return [
        "## ADR Invariant Verification Matrix",
        "",
        _INDEX_HEADER,
        _INDEX_SEPARATOR,
        *rows,
        "",
        "## Next Section",
    ]


def _index_row(invariant: str, status: str) -> str:
    return f"| {invariant} | statement | Unit Test | CI | Blocking | {status} |"


class TestBodyEmptyCellWithoutMarker:
    @pytest.mark.parametrize("cell", ["-", "", "\u2014"])
    def test_empty_implementation_cell_is_reported(self, cell: str) -> None:
        issues = check_adr_body_evidence_cells("adr_x.md", _body(_row("INV-03", cell)))
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert issues[0].file == "adr_x.md"
        assert "INV-03" in issues[0].message

    def test_line_number_points_at_the_row(self) -> None:
        issues = check_adr_body_evidence_cells("adr_x.md", _body(_row("INV-01", "-")))
        assert issues[0].line_no == 7  # heading, blank, header, separator, first row

    def test_two_invariants_in_one_row_are_both_named(self) -> None:
        issues = check_adr_body_evidence_cells(
            "adr_x.md", _body(_row("INV-01 and INV-02", "-"))
        )
        assert "INV-01" in issues[0].message
        assert "INV-02" in issues[0].message


class TestBodyEmptyCellWithMarker:
    def test_not_verified_marker_is_an_explicit_status(self) -> None:
        lines = _body(_row("INV-03", "Not verified (no automated test exists)"))
        assert check_adr_body_evidence_cells("adr_x.md", lines) == []

    def test_cited_test_is_an_explicit_status(self) -> None:
        lines = _body(_row("INV-01", "`tests/agent/test_startup.py::test_a`"))
        assert check_adr_body_evidence_cells("adr_x.md", lines) == []


class TestBodyIndexAgreement:
    def test_equal_file_sets_produce_no_issue(self) -> None:
        index = _index(
            _index_row("ADR-001 INV-01", "Confirmed (`tests/agent/test_a.py::test_x`)")
        )
        bodies = {"001": _body(_row("INV-01", "`tests/agent/test_a.py::test_x`"))}
        assert check_body_index_agreement(index, bodies) == []

    def test_bare_file_and_node_id_count_as_the_same_file(self) -> None:
        index = _index(_index_row("ADR-001 INV-01", "Confirmed (`tests/a/test_a.py`)"))
        bodies = {"001": _body(_row("INV-01", "`tests/a/test_a.py::TestX::test_y`"))}
        assert check_body_index_agreement(index, bodies) == []

    def test_rows_naming_two_adrs_are_split(self) -> None:
        index = _index(
            _index_row(
                "ADR-002 INV-01, INV-02 and ADR-004 INV-07, INV-10",
                "Confirmed (`tests/a/test_a.py::t`)",
            )
        )
        bodies = {
            "002": _body(_row("INV-01", "`tests/a/test_a.py::t`")),
            "004": _body(_row("INV-07", "`tests/a/test_a.py::t`")),
        }
        assert check_body_index_agreement(index, bodies) == []


class TestBodyIndexDisagreement:
    def test_different_file_sets_produce_one_warning(self) -> None:
        index = _index(
            _index_row("ADR-001 INV-01", "Confirmed (`tests/a/test_a.py::test_x`)")
        )
        bodies = {"001": _body(_row("INV-01", "`tests/b/test_b.py::test_y`"))}
        issues = check_body_index_agreement(index, bodies)
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert issues[0].file == "adr_01_index.md"
        assert issues[0].line_no == 5
        assert "ADR-001 INV-01" in issues[0].message

    def test_body_with_union_over_several_rows_is_compared_as_a_union(self) -> None:
        index = _index(
            _index_row(
                "ADR-001 INV-01",
                "Confirmed (`tests/a/test_a.py::x`, `tests/b/test_b.py::y`)",
            )
        )
        bodies = {
            "001": _body(
                _row("INV-01", "`tests/a/test_a.py::x`"),
                _row("INV-01", "`tests/b/test_b.py::y`"),
            )
        }
        assert check_body_index_agreement(index, bodies) == []

    def test_only_the_disagreeing_adr_of_a_multi_adr_row_is_reported(self) -> None:
        index = _index(
            _index_row(
                "ADR-002 INV-01 and ADR-004 INV-07",
                "Confirmed (`tests/a/test_a.py::t`)",
            )
        )
        bodies = {
            "002": _body(_row("INV-01", "`tests/a/test_a.py::t`")),
            "004": _body(_row("INV-07", "`tests/z/test_z.py::t`")),
        }
        issues = check_body_index_agreement(index, bodies)
        assert [("ADR-004 INV-07" in i.message) for i in issues] == [True]

    def test_no_finding_when_the_body_cites_no_test_file(self) -> None:
        index = _index(
            _index_row("ADR-001 INV-01", "Confirmed (`tests/a/test_a.py::t`)")
        )
        bodies = {"001": _body(_row("INV-01", "Not verified (no test)"))}
        assert check_body_index_agreement(index, bodies) == []

    def test_source_file_references_are_not_test_evidence(self) -> None:
        index = _index(_index_row("ADR-001 INV-01", "`scripts/agent/orchestrator.py`"))
        bodies = {"001": _body(_row("INV-01", "`tests/a/test_a.py::t`"))}
        assert check_body_index_agreement(index, bodies) == []


class TestBodyTableBoundaries:
    def test_first_and_last_rows_are_both_parsed(self) -> None:
        lines = _body(
            _row("INV-01", "-"),
            _row("INV-02", "`tests/a/test_a.py::t`"),
            _row("INV-03", "-"),
        )
        issues = check_adr_body_evidence_cells("adr_x.md", lines)
        assert sorted("INV-01" in i.message for i in issues) == [False, True]
        assert {i.line_no for i in issues} == {7, 9}

    def test_table_without_implementation_column_is_skipped(self) -> None:
        header = "| Test | Verifies | Type | Blocking |"
        lines = _body("| a test | INV-01 | Unit | Yes |", header=header)
        assert check_adr_body_evidence_cells("adr_x.md", lines) == []

    def test_missing_table_returns_no_issue(self) -> None:
        assert (
            check_adr_body_evidence_cells("adr_x.md", ["## Verification", "text"]) == []
        )

    def test_row_with_wrong_cell_count_is_skipped(self) -> None:
        lines = _body("| a test | INV-01 | Unit |")
        assert check_adr_body_evidence_cells("adr_x.md", lines) == []


class TestExistingRuleUnchanged:
    def test_missing_cited_path_is_still_an_error(self) -> None:
        lines = _matrix(
            "| INV-999 | ADR-999 | x | Unit Test | CI | Blocking | "
            "Confirmed (`tests/nonexistent/test_fake.py::test_fake_thing`) |"
        )
        issues = check_invariant_matrix_test_paths(lines)
        assert [i.severity for i in issues] == ["ERROR"]


class TestCollectIssues:
    """collect_issues() against a minimal repository built under tmp_path."""

    _INDEX = """\
## ADR List

| ID | Title | Status | Group | File |
|----|-------|--------|-------|------|
| ADR-001 | First | Accepted | g | `10_adr/adr_a.md` |
| ADR-002 | Second | Accepted | g | `10_adr/adr_missing.md` |

## ADR Invariant Verification Matrix

| Invariant | Statement | Type | Timing | Gate | Verification Status |
|---|---|---|---|---|---|
| ADR-001 INV-01 | s | Unit Test | CI | Blocking | Confirmed (`tests/a/test_a.py::t`) |
| ADR-003 INV-01 | s | Unit Test | CI | Blocking | Not verified |

## Next Section
"""

    def _repo(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        adr_dir = tmp_path / "docs" / "10_adr"
        adr_dir.mkdir(parents=True)
        (adr_dir / "adr_01_index.md").write_text(self._INDEX, encoding="utf-8")
        body = "\n".join(_body(_row("INV-01", "-"), _row("INV-02", "Not verified (x)")))
        (adr_dir / "adr_a.md").write_text(body, encoding="utf-8")
        cited = tmp_path / "tests" / "a" / "test_a.py"
        cited.parent.mkdir(parents=True)
        cited.write_text("", encoding="utf-8")  # the cited file must exist for rule 0
        monkeypatch.setattr(checker, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(checker, "ADR_INDEX", adr_dir / "adr_01_index.md")

    def test_all_body_rules_report_warnings_only(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._repo(tmp_path, monkeypatch)
        issues = checker.collect_issues()
        assert {i.severity for i in issues} == {"WARNING"}
        messages = " | ".join(i.message for i in issues)
        assert "INV-01: Implementation cell is empty" in messages
        assert "ADR-002 file cannot be read" in messages
        assert "ADR-003 is named in the matrix but not in the ADR List" in messages

    def test_missing_index_is_still_an_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(checker, "ADR_INDEX", tmp_path / "absent.md")
        issues = checker.collect_issues()
        assert [i.severity for i in issues] == ["ERROR"]
