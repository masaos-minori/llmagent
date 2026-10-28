"""tests/tools/test_check_adr_reference.py
Tests for tools/check_adr_reference.py.

Each scenario builds an in-memory Matrix table (as a list of lines) and calls
parse_matrix_source_refs()/check_adr_reference() directly, then verifies file
existence/marker checks against real tmp_path fixture files -- matching
tests/tools/test_check_adr_invariant_matrix.py's direct-function-call pattern.
Live `docs/10_adr/adr_01_index.md` validation (AC-3) is exercised separately by running
the tool against the real repository, not duplicated here as a unit test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.check_adr_reference import (
    MatrixSourceRef,
    check_adr_reference,
    collect_issues,
    parse_matrix_source_refs,
)

_HEADER = "| Invariant | Statement | Type | Timing | Gate | Verification Status |"
_SEPARATOR = "|-----------|-----------|------|--------|------|---------------------|"


def _matrix(*rows: str, header: str = _HEADER) -> list[str]:
    return [
        "## ADR Invariant Verification Matrix",
        "",
        header,
        _SEPARATOR,
        *rows,
        "",
        "## Next Section",
        "unrelated content",
    ]


class TestParseMatrixSourceRefs:
    def test_scripts_path_without_double_colon_is_extracted(self) -> None:
        lines = _matrix(
            "| ADR-004 INV-07 | x | Startup Validation | Startup | Deployment Blocking | "
            "Confirmed in code structure (`scripts/agent/startup.py` routes these checks) |"
        )
        refs = parse_matrix_source_refs(lines)
        assert refs == [
            MatrixSourceRef(
                file_path="scripts/agent/startup.py", adr_id="ADR-004", line_no=5
            )
        ]

    def test_every_adr_id_of_the_invariant_cell_is_extracted(self) -> None:
        lines = _matrix(
            "| ADR-002 INV-01 and ADR-004 INV-07 | x | Unit Test | CI | Blocking | "
            "Confirmed (`scripts/agent/startup.py`) |"
        )
        refs = parse_matrix_source_refs(lines)
        assert [(r.adr_id, r.file_path) for r in refs] == [
            ("ADR-002", "scripts/agent/startup.py"),
            ("ADR-004", "scripts/agent/startup.py"),
        ]

    def test_columns_are_found_by_header_name(self) -> None:
        lines = _matrix(
            "| Confirmed (`scripts/agent/startup.py`) | ADR-004 INV-07 | x |",
            header="| Verification Status | Invariant | Statement |",
        )
        refs = parse_matrix_source_refs(lines)
        assert [(r.adr_id, r.file_path) for r in refs] == [
            ("ADR-004", "scripts/agent/startup.py")
        ]

    def test_test_node_reference_is_not_extracted(self) -> None:
        """A `tests/*.py::test_name` citation is check_adr_invariant_matrix.py's
        concern, not this check's."""
        lines = _matrix(
            "| ADR-001 INV-01 | x | Unit Test | CI | Blocking | "
            "Confirmed (`tests/agent/test_startup.py::test_aborts_on_missing_workflow_definition`) |"
        )
        assert parse_matrix_source_refs(lines) == []

    def test_bare_filename_without_scripts_prefix_is_not_extracted(self) -> None:
        """A bare `config_loader.py` reference (no `scripts/` path) is
        ambiguous and not resolvable — out of this check's scope."""
        lines = _matrix(
            "| ADR-002 INV-03 | x | Unit Test | CI | Blocking | "
            "Confirmed in code (`config_loader.py` `restrict_to()`); no test yet |"
        )
        assert parse_matrix_source_refs(lines) == []

    def test_malformed_adr_column_is_skipped(self) -> None:
        lines = _matrix(
            "| not-an-adr | x | Unit Test | CI | Blocking | "
            "Confirmed (`scripts/agent/startup.py`) |"
        )
        assert parse_matrix_source_refs(lines) == []


class TestCheckAdrReference:
    """check_adr_reference() resolves `file_path` against module-level
    REPO_ROOT, so each test patches it to `tmp_path` via monkeypatch."""

    @staticmethod
    def _check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source: str) -> list:
        (tmp_path / "startup.py").write_text(source)
        monkeypatch.setattr("tools.check_adr_reference.REPO_ROOT", tmp_path)
        ref = MatrixSourceRef(file_path="startup.py", adr_id="ADR-004", line_no=5)
        return check_adr_reference([ref])

    def test_file_with_adr_reference_produces_no_issue(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert self._check(tmp_path, monkeypatch, "# ADR-004: startup checks\n") == []

    def test_file_missing_adr_reference_produces_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        issues = self._check(tmp_path, monkeypatch, "# No ADR mentioned here\n")
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"
        assert issues[0].file == "startup.py"
        assert "ADR-004" in issues[0].message

    def test_prose_only_adr_mention_is_not_a_marker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        source = '"""Startup checks (ADR-004 INV-07)."""\n\nNOTE = "see ADR-004"\n'
        issues = self._check(tmp_path, monkeypatch, source)
        assert len(issues) == 1
        assert "comment marker" in issues[0].message

    def test_marker_after_other_comment_text_is_accepted_only_at_comment_start(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mid_comment = self._check(tmp_path, monkeypatch, "# see ADR-004 for details\n")
        assert len(mid_comment) == 1
        trailing = self._check(tmp_path, monkeypatch, "x = 1  # ADR-004: startup\n")
        assert trailing == []

    def test_longer_adr_number_is_not_a_marker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        issues = self._check(tmp_path, monkeypatch, "# ADR-0041: other decision\n")
        assert len(issues) == 1

    def test_unparseable_source_file_is_an_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        issues = self._check(tmp_path, monkeypatch, '"""never closed\n')
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"
        assert "cannot be tokenized" in issues[0].message

    def test_nonexistent_file_produces_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("tools.check_adr_reference.REPO_ROOT", tmp_path)
        ref = MatrixSourceRef(
            file_path="does_not_exist.py", adr_id="ADR-004", line_no=5
        )
        issues = check_adr_reference([ref])
        assert len(issues) == 1
        assert issues[0].file == "adr_01_index.md"
        assert "does not exist" in issues[0].message


class TestCollectIssues:
    def test_matrix_with_no_parsable_rows_is_an_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A table whose shape no longer matches must not let the check pass."""
        index = tmp_path / "adr_01_index.md"
        index.write_text(
            "\n".join(_matrix("| ADR-004 INV-07 | x |", header="| ID | Statement |"))
        )
        monkeypatch.setattr("tools.check_adr_reference.ADR_INDEX", index)
        issues = collect_issues()
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"
        assert "no source references" in issues[0].message
