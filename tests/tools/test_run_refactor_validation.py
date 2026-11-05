"""Tests for tools/run_refactor_validation.py command construction and gate results."""

from __future__ import annotations

import pytest

from tools import run_refactor_validation as rrv

RUFF_FORMAT = ("uv", "run", "ruff", "format")
RUFF_CHECK = ("uv", "run", "ruff", "check")
MYPY = ("uv", "run", "mypy")
RADON = ("uv", "run", "radon", "cc")
PYTEST = ("uv", "run", "pytest")
COVERAGE_RUN = ("uv", "run", "coverage", "run")
COVERAGE_XML = ("uv", "run", "coverage", "xml")
DIFF_COVER = ("uv", "run", "diff-cover")


class _Recorder:
    """Stand-in for `_run`: records each command and answers by command prefix."""

    def __init__(self, responses: dict[tuple[str, ...], tuple[int, str]]) -> None:
        self.commands: list[list[str]] = []
        self._responses = responses

    def __call__(self, cmd: list[str]) -> tuple[int, str]:
        self.commands.append(cmd)
        for size in range(len(cmd), 0, -1):
            hit = self._responses.get(tuple(cmd[:size]))
            if hit is not None:
                return hit
        return 0, ""


def _install(
    monkeypatch: pytest.MonkeyPatch,
    responses: dict[tuple[str, ...], tuple[int, str]] | None = None,
) -> _Recorder:
    recorder = _Recorder(responses or {})
    monkeypatch.setattr(rrv, "_run", recorder)
    return recorder


def test_pytest_args_without_coverage() -> None:
    assert rrv._pytest_args(["t1.py", "t2.py"], coverage=False) == [
        "uv",
        "run",
        "pytest",
        "t1.py",
        "t2.py",
        "-q",
        "-p",
        "no:randomly",
    ]


def test_pytest_args_with_coverage() -> None:
    assert rrv._pytest_args(["t1.py"], coverage=True) == [
        "uv",
        "run",
        "coverage",
        "run",
        "-m",
        "pytest",
        "t1.py",
        "-q",
        "-p",
        "no:randomly",
    ]


def test_tail_keeps_last_non_empty_lines_and_handles_empty_text() -> None:
    text = "one\n\ntwo\nthree\nfour\nfive\n"
    assert rrv._tail(text) == "two | three | four | five"
    assert rrv._tail("  \n\n") == "no output"


def test_radon_gate_passes_at_grade_b(monkeypatch: pytest.MonkeyPatch) -> None:
    out = "a.py\n    F 1:0 f - B (7)\n    F 9:0 g - A (2)\n"
    recorder = _install(monkeypatch, {RADON: (0, out)})
    result = rrv._radon_gate(["a.py", "b.py"])
    assert result == rrv.StepResult("radon", True, "worst grade B (2 function(s))")
    assert recorder.commands == [["uv", "run", "radon", "cc", "a.py", "b.py", "-s"]]


def test_radon_gate_fails_at_grade_c(monkeypatch: pytest.MonkeyPatch) -> None:
    out = "a.py\n    F 1:0 f - B (7)\n    M 9:4 g - C (12)\n"
    _install(monkeypatch, {RADON: (0, out)})
    result = rrv._radon_gate(["a.py"])
    assert result == rrv.StepResult(
        "radon", False, "worst grade C: 1 function(s) at C or worse"
    )


def test_radon_gate_ignores_class_lines(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, {RADON: (0, "a.py\n    C 1:0 Foo - C (11)\n")})
    result = rrv._radon_gate(["a.py"])
    assert result == rrv.StepResult("radon", True, "worst grade A (0 function(s))")


def test_radon_gate_reports_tool_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, {RADON: (2, "radon exploded")})
    assert rrv._radon_gate(["a.py"]) == rrv.StepResult("radon", False, "radon exploded")


def test_diff_cover_gate_builds_the_three_commands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorder = _install(monkeypatch)
    results = rrv._diff_cover_gate(["a.py", "b.py"], ["t.py"], "master", 90)
    assert results == [rrv.StepResult("diff-cover", True, "no output")]
    assert recorder.commands == [
        rrv._pytest_args(["t.py"], coverage=True),
        ["uv", "run", "coverage", "xml"],
        [
            "uv",
            "run",
            "diff-cover",
            "coverage.xml",
            "--compare-branch=master",
            "--fail-under=90",
            "--include",
            "a.py",
            "b.py",
        ],
    ]


def test_diff_cover_gate_stops_when_the_coverage_run_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorder = _install(monkeypatch, {COVERAGE_RUN: (1, "tests failed")})
    results = rrv._diff_cover_gate(["a.py"], ["t.py"], "master", 90)
    assert results == [rrv.StepResult("coverage run", False, "tests failed")]
    assert len(recorder.commands) == 1


def test_diff_cover_gate_stops_when_the_xml_report_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorder = _install(monkeypatch, {COVERAGE_XML: (1, "no data")})
    results = rrv._diff_cover_gate(["a.py"], ["t.py"], "master", 90)
    assert results == [rrv.StepResult("coverage xml", False, "no data")]
    assert len(recorder.commands) == 2


def test_diff_cover_gate_reports_a_failing_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(monkeypatch, {DIFF_COVER: (1, "Total: 50%")})
    results = rrv._diff_cover_gate(["a.py"], ["t.py"], "master", 90)
    assert results == [rrv.StepResult("diff-cover", False, "Total: 50%")]


def test_validate_runs_every_step_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = _install(monkeypatch)
    results = rrv.validate(["a.py"], ["t.py"], "master", 90, set())
    assert [r.name for r in results] == [
        "ruff format",
        "ruff check",
        "mypy",
        "radon",
        "tests",
        "diff-cover",
    ]
    assert all(r.ok for r in results)
    assert recorder.commands[0] == ["uv", "run", "ruff", "format", "a.py", "t.py"]
    assert recorder.commands[1] == ["uv", "run", "ruff", "check", "a.py", "t.py"]
    assert recorder.commands[2] == [
        "uv",
        "run",
        "mypy",
        "--no-namespace-packages",
        "a.py",
    ]


def test_validate_marks_only_the_failing_step(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, {PYTEST: (1, "2 failed")})
    results = rrv.validate(["a.py"], ["t.py"], "master", 90, set())
    failed = [r for r in results if not r.ok]
    assert failed == [rrv.StepResult("tests", False, "2 failed")]


@pytest.mark.parametrize(
    ("skip", "dropped"),
    [
        ({"mypy"}, "mypy"),
        ({"radon"}, "radon"),
        ({"tests"}, "tests"),
        ({"diff-cover"}, "diff-cover"),
    ],
)
def test_skip_drops_exactly_its_own_step(
    skip: set[str], dropped: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install(monkeypatch)
    names = [r.name for r in rrv.validate(["a.py"], ["t.py"], "master", 90, skip)]
    assert dropped not in names
    assert len(names) == 5


def test_skipping_every_optional_step_leaves_the_two_ruff_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorder = _install(monkeypatch)
    skip = set(rrv._SKIP_CHOICES)
    results = rrv.validate(["a.py"], ["t.py"], "master", 90, skip)
    assert [r.name for r in results] == ["ruff format", "ruff check"]
    assert len(recorder.commands) == 2


def test_main_prints_pass_lines_and_returns_0(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch)
    assert rrv.main(["--src", "a.py", "--tests", "t.py"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "PASS  ruff format: no output"
    assert sum(line.startswith("PASS  ") for line in lines) == 6
    assert lines[-1] == "GATE PASSED"


def test_main_reports_the_failing_step_and_returns_1(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch, {MYPY: (1, "a.py:1: error: bad")})
    assert rrv.main(["--src", "a.py", "--tests", "t.py"]) == 1
    out = capsys.readouterr().out
    assert "FAIL  mypy: a.py:1: error: bad" in out
    assert out.splitlines()[-1] == "GATE FAILED: mypy"


def test_main_skip_option_removes_the_step(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch)
    argv = ["--src", "a.py", "--tests", "t.py", "--skip", "mypy", "--skip", "radon"]
    assert rrv.main(argv) == 0
    out = capsys.readouterr().out
    assert "mypy" not in out
    assert "radon" not in out


def test_main_passes_compare_branch_and_threshold_to_diff_cover(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorder = _install(monkeypatch)
    argv = ["--src", "a.py", "--tests", "t.py"]
    argv += ["--compare-branch", "develop", "--fail-under", "80"]
    assert rrv.main(argv) == 0
    diff_cover = recorder.commands[-1]
    assert "--compare-branch=develop" in diff_cover
    assert "--fail-under=80" in diff_cover


def test_main_rejects_an_unknown_skip_choice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorder = _install(monkeypatch)
    with pytest.raises(SystemExit) as excinfo:
        rrv.main(["--src", "a.py", "--tests", "t.py", "--skip", "bogus"])
    assert excinfo.value.code == 2
    assert recorder.commands == []


def test_main_requires_src_and_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = _install(monkeypatch)
    with pytest.raises(SystemExit) as excinfo:
        rrv.main([])
    assert excinfo.value.code == 2
    assert recorder.commands == []
