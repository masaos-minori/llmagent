"""tests/tools/test_check_adr_invariant_matrix.py
Tests for tools/check_adr_invariant_matrix.py.

Each scenario builds an in-memory Matrix table (as a list of lines) and calls
check_invariant_matrix_test_paths() directly, matching
tests/tools/test_check_known_deviation_sync.py's direct-function-call pattern.
Live `docs/adr-index.md` validation (AC-1) is exercised separately by running
the tool against the real repository, not duplicated here as a unit test.
"""

from __future__ import annotations

from tools.check_adr_invariant_matrix import check_invariant_matrix_test_paths

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
        assert issues[0].file == "adr-index.md"
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
