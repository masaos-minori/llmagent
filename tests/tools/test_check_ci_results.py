"""tests/tools/test_check_ci_results.py
Tests for tools/check_ci_results.py (Plan 20261025-090535, REQ-007 / AC-5).

Covers the four Plan validation groups over fixed sample data with an injected
fake runner (no network, no `gh`): run grouping, `FAILED <nodeid>` log parsing,
the read-only gh allowlist, and the 0/1/2 exit codes; plus the `--before`
filter and the report's skill pointer.
"""

from __future__ import annotations

import json
import subprocess

import pytest

import tools.check_ci_results as ccr
from tools.check_ci_results import RunRecord, group_repeats, parse_failed_tests

_LOG_TS = "2026-10-23T03:36:19.7416937Z"
_SHA = "abcdef1234567890abcdef1234567890abcdef12"
_TS_NEWEST = "2026-10-24T03:00:00Z"
_TS_MID = "2026-10-23T03:00:00Z"
_TS_OLD = "2026-10-22T03:00:00Z"
_POINTER = "skills/python-test-and-fix/SKILL.md"


def _run_json(
    run_id: int,
    conclusion: str | None,
    status: str,
    created_at: str,
    head_sha: str = _SHA,
) -> dict[str, object]:
    """One gh run-list entry with the Plan's fixed --json field set."""
    return {
        "databaseId": run_id,
        "conclusion": conclusion,
        "status": status,
        "createdAt": created_at,
        "headSha": head_sha,
        "workflowName": "CI",
    }


def _log(job: str, step: str, lines: list[str]) -> str:
    """Build a `gh run view --log-failed` body with the real line prefix."""
    return "".join(f"{job}\t{step}\t{_LOG_TS} {line}\n" for line in lines)


def _completed(
    stdout: str, stderr: str, returncode: int
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["gh"], returncode=returncode, stdout=stdout, stderr=stderr
    )


class FakeGh:
    """Stand-in for the module's only process-spawn point; records every vector."""

    def __init__(
        self,
        runs: list[dict[str, object]] | str | None = None,
        logs: dict[int, str] | None = None,
        list_rc: int = 0,
        list_stderr: str = "",
        view_rc: int = 0,
        missing_binary: bool = False,
    ) -> None:
        self.calls: list[list[str]] = []
        self.list_stdout = runs if isinstance(runs, str) else json.dumps(runs or [])
        self.logs = logs or {}
        self.list_rc = list_rc
        self.list_stderr = list_stderr
        self.view_rc = view_rc
        self.missing_binary = missing_binary

    def __call__(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(args))
        if self.missing_binary:
            raise FileNotFoundError("gh")
        if self.list_rc and (args[0], args[1]) == ("run", "list"):
            return _completed("", self.list_stderr, self.list_rc)
        if (args[0], args[1]) == ("run", "list"):
            return _completed(self.list_stdout, "", 0)
        if (args[0], args[1]) == ("run", "view"):
            if self.view_rc:
                return _completed("", "gh: could not fetch log", self.view_rc)
            return _completed(self.logs.get(int(args[2]), ""), "", 0)
        raise AssertionError(f"unexpected vector reached the tool layer: {args}")


def _install(monkeypatch: pytest.MonkeyPatch, fake: FakeGh) -> None:
    monkeypatch.setattr(ccr, "_run_gh", fake)


def _recorded_args(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[list[str], dict[str, object]]]:
    """Patch `subprocess.run` inside the tool module and record what reaches it."""
    recorded: list[tuple[list[str], dict[str, object]]] = []

    def _record(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        recorded.append((list(argv), kwargs))
        return _completed("[]", "", 0)

    monkeypatch.setattr(ccr.subprocess, "run", _record)
    return recorded


class TestParsing:
    def test_prefixed_summary_lines_yield_exact_identifiers(self) -> None:
        log = _log(
            "build",
            "Run tests",
            [
                "tests/agent/test_x.py::test_ok PASSED [ 50%]",
                "FAILED tests/agent/test_x.py::test_bad - AssertionError: 1 != 2",
            ],
        )
        assert parse_failed_tests(log) == ["tests/agent/test_x.py::test_bad"]

    def test_verbose_progress_lines_are_not_counted(self) -> None:
        log = _log(
            "build",
            "Run tests",
            [
                "tests/x.py::t1 FAILED [  6%]",
                "tests/x.py::t2 FAILED [ 12%]",
                "=========================== short test summary info ============================",
                "FAILED tests/x.py::t2 - assert False",
            ],
        )
        assert parse_failed_tests(log) == ["tests/x.py::t2"]

    def test_duplicate_summary_lines_dedupe_per_run(self) -> None:
        log = _log(
            "build",
            "Run tests",
            [
                "FAILED tests/x.py::t1 - first message",
                "FAILED tests/x.py::t1 - repeated message",
            ],
        )
        assert parse_failed_tests(log) == ["tests/x.py::t1"]

    def test_red_run_without_summary_yields_no_identifiers(self) -> None:
        log = _log("lint", "Run ruff", ["ruff failed: 2 errors found"])
        assert parse_failed_tests(log) == []

    def test_unprefixed_summary_line_still_matches(self) -> None:
        assert parse_failed_tests("FAILED tests/x.py::t9 - plain\n") == [
            "tests/x.py::t9"
        ]


class TestGrouping:
    @staticmethod
    def _record(run_id: int, tests: list[str], status: str = "completed") -> RunRecord:
        conclusion = "failure" if tests else "success"
        return RunRecord(
            run_id=run_id,
            head_sha=_SHA,
            conclusion=conclusion,
            status=status,
            created_at=_TS_MID,
            failed_tests=list(tests),
        )

    def test_single_red_run_lists_its_tests(self) -> None:
        counts = group_repeats([self._record(1, ["tests/x.py::a", "tests/y.py::b"])])
        assert counts["tests/x.py::a"] == 1
        assert counts["tests/y.py::b"] == 1

    def test_repeat_across_runs_is_counted_once_per_run(self) -> None:
        runs = [
            self._record(3, ["tests/x.py::a", "tests/x.py::a", "tests/y.py::b"]),
            self._record(2, ["tests/x.py::a"]),
            self._record(1, []),
        ]
        counts = group_repeats(runs)
        assert counts["tests/x.py::a"] == 2
        assert counts["tests/y.py::b"] == 1

    def test_green_window_contributes_nothing(self) -> None:
        assert group_repeats([self._record(2, []), self._record(1, [])]) == {}

    def test_in_progress_runs_never_contribute(self) -> None:
        running = self._record(3, [], status="in_progress")
        counts = group_repeats([running, self._record(2, ["tests/x.py::a"])])
        assert counts == {"tests/x.py::a": 1}


class TestAllowlist:
    def test_read_only_vectors_reach_subprocess_as_gh_argv(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        recorded = _recorded_args(monkeypatch)
        ccr._run_gh(["run", "list", "--limit", "10"])
        ccr._run_gh(["run", "view", "123", "--log-failed"])
        assert [argv for argv, _ in recorded] == [
            ["gh", "run", "list", "--limit", "10"],
            ["gh", "run", "view", "123", "--log-failed"],
        ]
        for argv, kwargs in recorded:
            assert kwargs.get("shell") is not True

    @pytest.mark.parametrize(
        "vector",
        [
            ["run", "rerun", "123"],
            ["workflow", "run", "CI"],
            ["api", "repos/owner/repo/runs"],
            ["run"],
            ["view", "123"],
            [],
        ],
    )
    def test_forbidden_vectors_raise_before_any_spawn(
        self, monkeypatch: pytest.MonkeyPatch, vector: list[str]
    ) -> None:
        recorded = _recorded_args(monkeypatch)
        with pytest.raises(ValueError, match="not allowlisted"):
            ccr._run_gh(vector)
        assert recorded == []

    def test_main_records_only_allowed_shapes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake = FakeGh(
            runs=[_run_json(101, "failure", "completed", _TS_NEWEST)],
            logs={
                101: _log("unit-tests", "Run tests", ["FAILED tests/x.py::a - boom"])
            },
        )
        _install(monkeypatch, fake)
        assert ccr.main([]) == 1
        shapes = [(args[0], args[1]) for args in fake.calls]
        assert shapes == [("run", "list"), ("run", "view")]
        assert all("--repo" not in args for args in fake.calls)
        assert fake.calls[1] == ["run", "view", "101", "--log-failed"]


class TestExitCodes:
    def test_all_green_exits_zero_without_pointer(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake = FakeGh(
            runs=[
                _run_json(101, "success", "completed", _TS_NEWEST),
                _run_json(100, "success", "completed", _TS_MID),
            ]
        )
        _install(monkeypatch, fake)
        assert ccr.main([]) == 0
        out = capsys.readouterr().out
        assert "green" in out
        assert _POINTER not in out

    def test_red_latest_completed_exits_one_and_reports(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake = FakeGh(
            runs=[
                _run_json(101, "failure", "completed", _TS_NEWEST),
                _run_json(100, "success", "completed", _TS_MID),
            ],
            logs={
                101: _log(
                    "unit-tests",
                    "Run tests",
                    ["FAILED tests/agent/test_x.py::test_a - AssertionError: boom"],
                )
            },
        )
        _install(monkeypatch, fake)
        assert ccr.main([]) == 1
        captured = capsys.readouterr()
        assert "run 101" in captured.out
        assert _SHA[:7] in captured.out
        assert "job: unit-tests" in captured.out
        assert "failed test: tests/agent/test_x.py::test_a" in captured.out
        assert _POINTER in captured.out
        assert captured.err == ""

    def test_green_latest_with_repeat_exits_one(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        log = _log("unit-tests", "Run tests", ["FAILED tests/x.py::a - boom"])
        fake = FakeGh(
            runs=[
                _run_json(103, "success", "completed", _TS_NEWEST),
                _run_json(102, "failure", "completed", _TS_MID),
                _run_json(101, "failure", "completed", _TS_OLD),
            ],
            logs={102: log, 101: log},
        )
        _install(monkeypatch, fake)
        assert ccr.main([]) == 1
        out = capsys.readouterr().out
        assert "Repeated failures" in out
        assert "tests/x.py::a  2 runs" in out

    def test_older_failure_green_latest_without_repeat_exits_zero(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake = FakeGh(
            runs=[
                _run_json(102, "success", "completed", _TS_NEWEST),
                _run_json(101, "failure", "completed", _TS_MID),
            ],
            logs={
                101: _log("unit-tests", "Run tests", ["FAILED tests/x.py::a - boom"])
            },
        )
        _install(monkeypatch, fake)
        assert ccr.main([]) == 0
        out = capsys.readouterr().out
        assert "green" in out
        assert "Repeated" not in out

    def test_in_progress_runs_are_listed_but_never_decide(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake = FakeGh(runs=[_run_json(104, None, "in_progress", _TS_NEWEST)])
        _install(monkeypatch, fake)
        assert ccr.main([]) == 0
        out = capsys.readouterr().out
        assert "in_progress" in out
        assert "No completed runs" in out

    def test_missing_binary_exits_two(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _install(monkeypatch, FakeGh(missing_binary=True))
        assert ccr.main([]) == 2
        assert "gh binary not found" in capsys.readouterr().err

    def test_gh_list_failure_exits_two(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _install(
            monkeypatch, FakeGh(list_rc=1, list_stderr="gh: HTTP 500 server error")
        )
        assert ccr.main([]) == 2
        captured = capsys.readouterr()
        assert "gh run list failed" in captured.err
        assert captured.err.count("\n") == 1

    def test_unparsable_json_exits_two(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _install(monkeypatch, FakeGh(runs="not json"))
        assert ccr.main([]) == 2
        assert "unparsable JSON" in capsys.readouterr().err

    def test_run_view_failure_exits_two(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake = FakeGh(
            runs=[_run_json(101, "failure", "completed", _TS_NEWEST)],
            view_rc=1,
        )
        _install(monkeypatch, fake)
        assert ccr.main([]) == 2
        assert "gh run view failed" in capsys.readouterr().err


class TestBeforeFilter:
    def test_before_drops_newer_runs_without_fetching_their_logs(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake = FakeGh(
            runs=[
                _run_json(101, "failure", "completed", _TS_NEWEST),
                _run_json(100, "success", "completed", _TS_MID),
            ],
            logs={
                101: _log("unit-tests", "Run tests", ["FAILED tests/x.py::a - boom"])
            },
        )
        _install(monkeypatch, fake)
        assert ccr.main(["--before", _TS_NEWEST]) == 0
        assert [tuple(args[:2]) for args in fake.calls] == [("run", "list")]

    def test_invalid_before_is_a_usage_error(self) -> None:
        with pytest.raises(SystemExit) as excinfo:
            ccr.main(["--before", "not-a-timestamp"])
        assert excinfo.value.code == 2

    def test_limit_below_one_is_a_usage_error(self) -> None:
        with pytest.raises(SystemExit) as excinfo:
            ccr.main(["--limit", "0"])
        assert excinfo.value.code == 2
