"""tests/tools/test_run_cited_adr_tests.py
Tests for .github/run_cited_adr_tests.py (the cited-node CI runner).

The runner lives outside any importable package, so it is loaded by file path
in a fixture, mirroring how the runner itself loads the checker. Classification
cases monkeypatch `_run_pytest` with canned (rc, output) pairs; one end-to-end
case runs a real pytest process against a tmp package with a skip-marked test.
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_runner() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(
        "run_cited_adr_tests", REPO_ROOT / ".github" / "run_cited_adr_tests.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def runner() -> types.ModuleType:
    return _load_runner()


# ---------------------------------------------------------------------------
# Outcome classification (canned pytest outputs)
# ---------------------------------------------------------------------------


class TestClassifyOutcome:
    def test_classify_passed(self, runner: types.ModuleType) -> None:
        assert runner._classify_outcome(0, "5 passed in 0.10s") is None

    def test_classify_skipped(self, runner: types.ModuleType) -> None:
        output = "SKIPPED [1] tests/a/test_a.py:5: environment gate\n1 skipped in 0.01s"
        assert runner._classify_outcome(0, output) == "skipped"

    def test_classify_xfailed(self, runner: types.ModuleType) -> None:
        output = "XFAIL tests/a/test_a.py::test_x - known gap\n1 xfailed in 0.01s"
        assert runner._classify_outcome(0, output) == "xfailed"

    def test_classify_ignores_nonzero_exit(self, runner: types.ModuleType) -> None:
        output = "SKIPPED [1] tests/a/test_a.py:5: gate\n1 failed, 1 skipped"
        assert runner._classify_outcome(1, output) is None


def _canned(
    runner: types.ModuleType, monkeypatch: pytest.MonkeyPatch, rc: int, output: str
) -> None:
    monkeypatch.setattr(runner, "_run_pytest", lambda args: (rc, output))


class TestEvaluateCitation:
    def test_classify_passed_maps_to_passed(
        self, runner: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _canned(runner, monkeypatch, 0, "1 passed in 0.01s")
        assert runner.evaluate_citation("tests/a/test_a.py", "test_x") == (
            True,
            "passed",
        )

    def test_classify_skipped_citation(
        self, runner: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _canned(runner, monkeypatch, 0, "SKIPPED [1] tests/a/test_a.py:5: gate")
        assert runner.evaluate_citation("tests/a/test_a.py", "test_x") == (
            False,
            "skipped",
        )

    def test_classify_xfailed_citation(
        self, runner: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _canned(runner, monkeypatch, 0, "XFAIL tests/a/test_a.py::test_x - gap")
        assert runner.evaluate_citation("tests/a/test_a.py", "test_x") == (
            False,
            "xfailed",
        )

    def test_missing_citation(
        self, runner: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _canned(runner, monkeypatch, 5, "no tests ran")
        monkeypatch.setattr(runner, "_node_id_exists", lambda node_id: False)
        assert runner.evaluate_citation("tests/a/test_a.py", "test_x") == (
            False,
            "missing",
        )

    def test_integration_deselection(
        self, runner: types.ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _canned(runner, monkeypatch, 5, "3 deselected / no tests ran")
        monkeypatch.setattr(runner, "_node_id_exists", lambda node_id: True)
        assert runner.evaluate_citation("tests/a/test_a.py", "test_x") == (
            True,
            "integration-deselected",
        )


# ---------------------------------------------------------------------------
# Approved-exception parsing (grammar shared with the checker)
# ---------------------------------------------------------------------------


class TestCitedExceptions:
    def test_exception_line_approves_its_citations(
        self, runner: types.ModuleType
    ) -> None:
        lines = [
            "| ADR-001 INV-01 | s | Unit Test | CI | Blocking | "
            "Confirmed (`tests/a/test_a.py::test_x`, `tests/b/test_b.py::test_y`; "
            "Exception: EXC-001) |",
            "| ADR-002 INV-01 | s | Unit Test | CI | Blocking | "
            "Confirmed (`tests/c/test_c.py::test_z`) |",
        ]
        assert runner._cited_exceptions(lines) == {
            ("tests/a/test_a.py", "test_x"),
            ("tests/b/test_b.py", "test_y"),
        }

    def test_no_exception_lines_approves_nothing(
        self, runner: types.ModuleType
    ) -> None:
        lines = ["Confirmed (`tests/a/test_a.py::test_x`)"]
        assert runner._cited_exceptions(lines) == set()


# ---------------------------------------------------------------------------
# End-to-end: a real skipped citation fails, an approved one passes
# ---------------------------------------------------------------------------

_SKIP_MODULE = """\
import pytest


@pytest.mark.skip(reason="environment gate")
def test_skipped() -> None:
    pass
"""


@pytest.fixture
def e2e_repo(
    runner: types.ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """A tmp repo root whose cited matrix references one skip-marked test."""
    tests_dir = tmp_path / "tests_e2e"
    tests_dir.mkdir()
    (tests_dir / "test_skip_demo.py").write_text(_SKIP_MODULE, encoding="utf-8")
    monkeypatch.setattr(runner, "REPO_ROOT", tmp_path)
    return tmp_path


def _write_index(tmp_path: Path, status: str) -> None:
    index = tmp_path / "adr_01_index.md"
    index.write_text(
        "| ADR-099 INV-01 | s | Unit Test | CI | Blocking | "
        f"Confirmed (`tests_e2e/test_skip_demo.py::test_skipped`; {status}) |\n",
        encoding="utf-8",
    )


def test_end_to_end_skipped_citation_fails_without_exception(
    runner: types.ModuleType,
    e2e_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_index(e2e_repo, "passing")
    monkeypatch.setattr(runner, "ADR_INDEX", e2e_repo / "adr_01_index.md")
    assert runner.main() == 1
    out = capsys.readouterr().out
    assert "[FAIL] tests_e2e/test_skip_demo.py::test_skipped (skipped)" in out


def test_end_to_end_skipped_citation_passes_with_exception(
    runner: types.ModuleType,
    e2e_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_index(e2e_repo, "Exception: E2E-001")
    monkeypatch.setattr(runner, "ADR_INDEX", e2e_repo / "adr_01_index.md")
    assert runner.main() == 0
    out = capsys.readouterr().out
    assert (
        "[PASS] tests_e2e/test_skip_demo.py::test_skipped (skipped-approved-exception)"
        in out
    )
