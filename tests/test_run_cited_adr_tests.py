#!/usr/bin/env python3
"""Tests for .github/run_cited_adr_tests.py — the CI helper that runs the
pytest node ids cited in the ADR Invariant Verification Matrix (GV-012).

The helper lives outside ``tools/``/``scripts/`` so it is not covered by the
repo's tool linters; these tests pin its two pure behaviors: citation
extraction (dedup + ordering) and per-node-id outcome classification.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

_HELPER_PATH = (
    Path(__file__).resolve().parent.parent / ".github" / "run_cited_adr_tests.py"
)
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_helper() -> Any:
    spec = importlib.util.spec_from_file_location("run_cited_adr_tests", _HELPER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def helper() -> Any:
    return _load_helper()


def _fake_run(side_effect: Any) -> Any:
    """Return a stand-in for ``_run_pytest`` mapping arg-lists to exit codes."""

    def _run(args: list[str]) -> int:
        return int(side_effect(args))

    return _run


class TestExtractCitedNodeIds:
    def test_returns_file_and_node_id_pairs(self, helper: Any) -> None:
        lines = [
            "| INV-01 | desc | Unit Test | CI | Blocking | Confirmed (`tests/a/test_a.py::test_one`, passing) |"
        ]
        assert helper.extract_cited_node_ids(lines) == [
            ("tests/a/test_a.py", "test_one")
        ]

    def test_deduplicates_while_preserving_first_seen_order(self, helper: Any) -> None:
        lines = [
            "| INV-01 | a | | | | (`tests/a/x.py::t1`, x)",
            "| INV-02 | b | | | | (`tests/a/x.py::t1`, x) (`tests/b/y.py::t2`, y)",
        ]
        assert helper.extract_cited_node_ids(lines) == [
            ("tests/a/x.py", "t1"),
            ("tests/b/y.py", "t2"),
        ]

    def test_ignores_lines_without_citations(self, helper: Any) -> None:
        assert helper.extract_cited_node_ids(["no citations here", ""]) == []

    def test_requires_py_separator_not_bare_code_ref(self, helper: Any) -> None:
        # A bare code reference like `config_loader.py` (no ::) must not match.
        lines = ["| INV-01 | a | | | | (`config_loader.py`, x) |"]
        assert helper.extract_cited_node_ids(lines) == []


class TestEvaluateCitation:
    def test_passing_exit_is_ok(
        self, helper: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(helper, "_run_pytest", _fake_run(lambda _args: 0))
        ok, reason = helper.evaluate_citation("tests/a/x.py", "t1")
        assert ok is True
        assert reason == "passed"

    def test_failing_exit_is_not_ok(
        self, helper: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(helper, "_run_pytest", _fake_run(lambda _args: 1))
        ok, reason = helper.evaluate_citation("tests/a/x.py", "t1")
        assert ok is False
        assert reason == "failed"

    def test_no_tests_collected_but_node_exists_is_intentional(
        self, helper: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Exit 5 on the gated run (nothing ran) but the node resolves under a
        # marker-less collect-only -> integration-only citation, intentional.
        monkeypatch.setattr(
            helper,
            "_run_pytest",
            _fake_run(lambda args: 0 if "--collect-only" in args else 5),
        )
        ok, reason = helper.evaluate_citation("tests/a/x.py", "t1")
        assert ok is True
        assert reason == "integration-deselected"

    def test_no_tests_collected_and_node_missing_fails(
        self, helper: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Exit 5 on both the gated run and the collect-only -> missing citation.
        monkeypatch.setattr(helper, "_run_pytest", _fake_run(lambda _args: 5))
        ok, reason = helper.evaluate_citation("tests/a/x.py", "t1")
        assert ok is False
        assert reason == "missing"

    def test_usage_error_fails(
        self, helper: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(helper, "_run_pytest", _fake_run(lambda _args: 4))
        ok, reason = helper.evaluate_citation("tests/a/x.py", "t1")
        assert ok is False
        assert reason == "pytest-exit-4"


class TestRealMatrixRegression:
    def test_all_cited_files_exist_on_disk(self, helper: Any) -> None:
        lines = helper.ADR_INDEX.read_text(encoding="utf-8").splitlines()
        cited = helper.extract_cited_node_ids(lines)
        assert cited, "matrix should cite at least one node id"
        for file_part, _node_id in cited:
            assert (_REPO_ROOT / file_part).is_file(), (
                f"cited file missing: {file_part}"
            )

    def test_matrix_has_expected_unique_citation_count(self, helper: Any) -> None:
        # Pins the matrix size; a drift that adds/removes citations fails here.
        lines = helper.ADR_INDEX.read_text(encoding="utf-8").splitlines()
        assert len(helper.extract_cited_node_ids(lines)) == 42
