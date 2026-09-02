"""tests/tools/test_check_adr_reference.py
Tests for tools/check_adr_reference.py.

Each scenario builds an in-memory Matrix table (as a list of lines) and calls
parse_matrix_source_refs()/check_adr_reference() directly, then verifies file
existence/content checks against real tmp_path fixture files -- matching
tests/tools/test_check_adr_invariant_matrix.py's direct-function-call pattern.
Live `docs/adr-index.md` validation (AC-3) is exercised separately by running
the tool against the real repository, not duplicated here as a unit test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.check_adr_reference import (
    MatrixSourceRef,
    check_adr_reference,
    parse_matrix_source_refs,
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


class TestParseMatrixSourceRefs:
    def test_scripts_path_without_double_colon_is_extracted(self) -> None:
        lines = _matrix(
            "| INV-011 | ADR-004 | x | Startup Validation | Startup | Deployment Blocking | "
            "Confirmed in code structure (`scripts/agent/startup.py` routes these checks) |"
        )
        refs = parse_matrix_source_refs(lines)
        assert refs == [
            MatrixSourceRef(
                file_path="scripts/agent/startup.py", adr_id="ADR-004", line_no=5
            )
        ]

    def test_test_node_reference_is_not_extracted(self) -> None:
        """A `tests/*.py::test_name` citation is check_adr_invariant_matrix.py's
        concern, not this check's."""
        lines = _matrix(
            "| INV-001 | ADR-001 | x | Unit Test | CI | Blocking | "
            "Confirmed (`tests/agent/test_startup.py::test_aborts_on_missing_workflow_definition`) |"
        )
        assert parse_matrix_source_refs(lines) == []

    def test_bare_filename_without_scripts_prefix_is_not_extracted(self) -> None:
        """A bare `config_loader.py` reference (no `scripts/` path) is
        ambiguous and not resolvable — out of this check's scope."""
        lines = _matrix(
            "| INV-003 | ADR-002 | x | Unit Test | CI | Blocking | "
            "Confirmed in code (`config_loader.py` `restrict_to()`); no test yet |"
        )
        assert parse_matrix_source_refs(lines) == []

    def test_malformed_adr_column_is_skipped(self) -> None:
        lines = _matrix(
            "| INV-001 | not-an-adr | x | Unit Test | CI | Blocking | "
            "Confirmed (`scripts/agent/startup.py`) |"
        )
        assert parse_matrix_source_refs(lines) == []


class TestCheckAdrReference:
    """check_adr_reference() resolves `file_path` against module-level
    REPO_ROOT, so each test patches it to `tmp_path` via monkeypatch."""

    def test_file_with_adr_reference_produces_no_issue(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / "startup.py").write_text("# Implements ADR-004 startup checks\n")
        monkeypatch.setattr("tools.check_adr_reference.REPO_ROOT", tmp_path)
        ref = MatrixSourceRef(file_path="startup.py", adr_id="ADR-004", line_no=5)
        assert check_adr_reference([ref]) == []

    def test_file_missing_adr_reference_produces_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / "startup.py").write_text("# No ADR mentioned here\n")
        monkeypatch.setattr("tools.check_adr_reference.REPO_ROOT", tmp_path)
        ref = MatrixSourceRef(file_path="startup.py", adr_id="ADR-004", line_no=5)
        issues = check_adr_reference([ref])
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"
        assert issues[0].file == "startup.py"
        assert "ADR-004" in issues[0].message

    def test_nonexistent_file_produces_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("tools.check_adr_reference.REPO_ROOT", tmp_path)
        ref = MatrixSourceRef(
            file_path="does_not_exist.py", adr_id="ADR-004", line_no=5
        )
        issues = check_adr_reference([ref])
        assert len(issues) == 1
        assert issues[0].file == "adr-index.md"
        assert "does not exist" in issues[0].message
