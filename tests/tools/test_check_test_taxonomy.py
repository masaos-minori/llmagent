"""tests/tools/test_check_test_taxonomy.py
Tests for tools/check_test_taxonomy.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.check_test_taxonomy as ctt

REASON = "issues/done/20261119-145310_cliplc012_characterization-test-split.md"

REGISTERED_PYPROJECT = (
    '[tool.pytest.ini_options]\nmarkers = ["characterization", "contract"]\n'
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture_root(root: Path) -> Path:
    """A repository fixture with the registered markers and the classified areas."""
    _write(root / "pyproject.toml", REGISTERED_PYPROJECT)
    (root / "tests" / "agent").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "shared").mkdir(parents=True, exist_ok=True)
    return root


def _baseline(root: Path, entries: list[str]) -> Path:
    path = root / "baseline.txt"
    _write(path, "".join(f"{line}\n" for line in entries))
    return path


def _run(root: Path, baseline: Path, *extra: str) -> int:
    return ctt.main(["--root", str(root), "--baseline", str(baseline), *extra])


class TestUnclassifiedModule:
    def test_module_in_a_classified_area_without_a_marker_is_reported(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py", "def test_a():\n    assert True\n"
        )

        assert _run(root, _baseline(root, [])) == 1
        assert "unclassified-module: tests/agent/test_x.py" in capsys.readouterr().out

    def test_module_outside_the_classified_areas_is_not_reported(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "tools" / "test_y.py", "def test_a():\n    assert True\n"
        )

        assert _run(root, _baseline(root, [])) == 0
        assert "no findings" in capsys.readouterr().out

    def test_baseline_entry_exempts_a_module_in_a_classified_area(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py", "def test_a():\n    assert True\n"
        )

        assert _run(root, _baseline(root, [f"tests/agent/test_x.py\t{REASON}"])) == 0
        assert "no findings" in capsys.readouterr().out

    def test_a_baseline_module_that_now_has_a_marker_is_reported(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py",
            "import pytest\n\npytestmark = pytest.mark.contract\n\n"
            "def test_a():\n    assert True\n",
        )
        baseline = _baseline(root, [f"tests/agent/test_x.py\t{REASON}"])

        assert _run(root, baseline) == 1
        assert (
            "baseline-entry-classified: tests/agent/test_x.py"
            in capsys.readouterr().out
        )


class TestRequirementCitation:
    def test_contract_module_without_a_citation_is_reported(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py",
            "import pytest\n\npytestmark = pytest.mark.contract\n\n"
            "def test_a():\n    assert True\n",
        )

        assert _run(root, _baseline(root, [])) == 1
        assert (
            "contract-without-citation: tests/agent/test_x.py"
            in capsys.readouterr().out
        )

    def test_a_requirement_number_counts_as_a_citation(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py",
            '"""Verifies REQ-003."""\nimport pytest\n\npytestmark = pytest.mark.contract\n\n'
            "def test_a():\n    assert True\n",
        )

        assert _run(root, _baseline(root, [])) == 0
        assert "no findings" in capsys.readouterr().out

    def test_an_archived_issue_path_counts_as_a_citation(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py",
            f'"""Source: {REASON}."""\nimport pytest\n\npytestmark = pytest.mark.contract\n\n'
            "def test_a():\n    assert True\n",
        )

        assert _run(root, _baseline(root, [])) == 0
        assert "no findings" in capsys.readouterr().out

    def test_a_registry_path_counts_as_a_citation(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "config" / "documentation_canonical_sources.toml",
            'version = "1"\n\n[[canonical_sources]]\n'
            'decision_target = "x.y"\nclaim_type = "runtime-behavior"\n'
            'source_paths = ["scripts/agent/stdin_reader.py"]\narea = "Agent"\n',
        )
        _write(
            root / "tests" / "agent" / "test_x.py",
            '"""Verifies scripts/agent/stdin_reader.py."""\n'
            "import pytest\n\npytestmark = pytest.mark.contract\n\n"
            "def test_a():\n    assert True\n",
        )

        assert _run(root, _baseline(root, [])) == 0
        assert "no findings" in capsys.readouterr().out

    def test_characterization_module_needs_no_citation(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py",
            "import pytest\n\npytestmark = pytest.mark.characterization\n\n"
            "def test_a():\n    assert True\n",
        )

        assert _run(root, _baseline(root, [])) == 0
        assert "no findings" in capsys.readouterr().out


class TestBothKinds:
    def test_module_level_both_kinds_is_reported(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py",
            "import pytest\n\npytestmark = [pytest.mark.characterization, pytest.mark.contract]\n\n"
            "def test_a():\n    assert True\n",
        )

        assert _run(root, _baseline(root, [])) == 1
        out = capsys.readouterr().out
        assert "module-level-both-kinds: tests/agent/test_x.py" in out

    def test_a_mixed_module_is_allowed_through_per_test_markers(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py",
            '"""REQ-003."""\nimport pytest\n\npytestmark = pytest.mark.characterization\n\n'
            "@pytest.mark.contract\n"
            "def test_a():\n    assert True\n",
        )

        assert _run(root, _baseline(root, [])) == 0
        assert "no findings" in capsys.readouterr().out

    def test_a_test_claiming_both_kinds_is_reported(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py",
            '"""REQ-003."""\nimport pytest\n\npytestmark = pytest.mark.characterization\n\n'
            "@pytest.mark.contract\n@pytest.mark.characterization\n"
            "def test_a():\n    assert True\n",
        )

        assert _run(root, _baseline(root, [])) == 1
        assert (
            "test-claims-both-kinds: tests/agent/test_x.py" in capsys.readouterr().out
        )


class TestRegisteredMarkers:
    def test_marker_not_registered_in_pyproject_is_reported(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "pyproject.toml",
            '[tool.pytest.ini_options]\nmarkers = ["contract"]\n',
        )
        _write(
            root / "tests" / "agent" / "test_x.py",
            '"""REQ-003."""\nimport pytest\n\npytestmark = pytest.mark.characterization\n\n'
            "def test_a():\n    assert True\n",
        )

        assert _run(root, _baseline(root, [])) == 1
        assert "marker-not-registered: tests/agent/test_x.py" in capsys.readouterr().out


class TestReadOnly:
    def test_a_module_that_raises_at_import_time_is_still_scanned(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py",
            '"""REQ-003."""\nimport pytest\n\npytestmark = pytest.mark.contract\nraise RuntimeError\n',
        )

        assert _run(root, _baseline(root, [])) == 0
        assert "no findings" in capsys.readouterr().out


class TestBaselineInputErrors:
    def test_a_line_without_an_issue_path_is_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        baseline = _baseline(root, ["tests/agent/test_x.py\tlegacy behavior"])

        assert _run(root, baseline) == 2
        assert "must name an issue path" in capsys.readouterr().err

    def test_a_line_without_a_tab_is_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        baseline = _baseline(root, [f"tests/agent/test_x.py {REASON}"])

        assert _run(root, baseline) == 2
        assert "expected" in capsys.readouterr().err


class TestReportMode:
    def _junit(self, root: Path, cases: list[tuple[str, str, bool]]) -> Path:
        lines = [f'<testsuites><testsuite name="pytest" tests="{len(cases)}">']
        for classname, name, failed in cases:
            case = f'<testcase classname="{classname}" name="{name}">'
            if failed:
                case += '<failure message="boom">trace</failure>'
            lines.append(case + "</testcase>")
        lines.append("</testsuite></testsuites>")
        path = root / "report.xml"
        _write(path, "".join(lines))
        return path

    def test_report_groups_counts_by_module(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py",
            '"""REQ-003."""\nimport pytest\n\npytestmark = pytest.mark.contract\n\n'
            "def test_a():\n    assert True\n",
        )
        report = self._junit(root, [("tests.agent.test_x", "test_a", False)])

        assert _run(root, _baseline(root, []), "--junit-xml", str(report)) == 0
        out = capsys.readouterr().out
        assert "contract: 1 tests, 0 failure(s)" in out

    def test_characterization_failure_is_report_only(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py",
            "import pytest\n\npytestmark = pytest.mark.characterization\n\n"
            "def test_a():\n    assert True\n",
        )
        report = self._junit(root, [("tests.agent.test_x", "test_a", True)])

        assert _run(root, _baseline(root, []), "--junit-xml", str(report)) == 0
        out = capsys.readouterr().out
        assert "characterization: 1 tests, 1 failure(s)" in out
        assert "tests/agent/test_x.py: 1 failure(s)" in out

    def test_contract_failure_exits_non_zero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py",
            '"""REQ-003."""\nimport pytest\n\npytestmark = pytest.mark.contract\n\n'
            "def test_a():\n    assert True\n",
        )
        report = self._junit(root, [("tests.agent.test_x", "test_a", True)])

        assert _run(root, _baseline(root, []), "--junit-xml", str(report)) == 1
        assert "contract: 1 tests, 1 failure(s)" in capsys.readouterr().out

    def test_failure_in_a_baseline_module_exits_non_zero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py", "def test_a():\n    assert True\n"
        )
        baseline = _baseline(root, [f"tests/agent/test_x.py\t{REASON}"])
        report = self._junit(root, [("tests.agent.test_x", "test_a", True)])

        assert _run(root, baseline, "--junit-xml", str(report)) == 1
        assert "unclassified: 1 tests, 1 failure(s)" in capsys.readouterr().out

    def test_a_parametrized_id_falls_back_to_the_module_kind(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        _write(
            root / "tests" / "agent" / "test_x.py",
            '"""REQ-003."""\nimport pytest\n\npytestmark = pytest.mark.contract\n\n'
            "def test_a():\n    assert True\n",
        )
        report = self._junit(root, [("tests.agent.test_x", "test_a[case-1]", False)])

        assert _run(root, _baseline(root, []), "--junit-xml", str(report)) == 0
        assert "contract: 1 tests, 0 failure(s)" in capsys.readouterr().out

    def test_an_empty_run_is_an_input_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _fixture_root(tmp_path)
        report = self._junit(root, [])

        assert _run(root, _baseline(root, []), "--junit-xml", str(report)) == 2
        assert "no testcase found" in capsys.readouterr().err
