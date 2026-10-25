"""tools/check_ci_results.py
Read-only CI result reporter: queries recent GitHub Actions runs with the `gh`
CLI, groups tests that failed in two or more examined runs, and reports to
stdout.

Read-only contract: `_run_gh` is the only place that spawns a process. It
accepts an argument vector only when the first two elements are ("run", "list")
or ("run", "view") and raises ValueError before subprocess.run otherwise. No
write-capable vector (`run rerun`, `workflow run`, `api`) can reach a process
spawn. Nothing is written to disk, nothing is retried, and no repository
content is sent to any service beyond the read-only `gh` queries.

Report output is stdout only; stderr carries only `gh` failure lines.

Usage:
    python tools/check_ci_results.py
    python tools/check_ci_results.py --limit 100 --before 2026-10-23T03:44:13Z
    python tools/check_ci_results.py --workflow CI --branch master

Exit codes:
    0 - latest completed run is green and no test failed in 2+ examined runs
    1 - latest completed run is not green, or a test failed in 2+ examined runs
    2 - any gh read failure (missing binary, non-zero gh exit, unparsable JSON)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 — gh is a trusted local CLI; argv is validated against a fixed allowlist
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime

# The only gh vectors this tool may ever spawn: read-only run queries.
_ALLOWED_VECTORS: tuple[tuple[str, str], ...] = (("run", "list"), ("run", "view"))
_RUN_LIST_FIELDS = "databaseId,conclusion,status,createdAt,headSha,workflowName"
# pytest's `short test summary info` line: `FAILED <nodeid> - <message>`
# (pyproject addopts `-v --tb=short` keeps this block present and stable).
_FAILED_RE = re.compile(r"^FAILED (\S+)(?: - .*)?$")
_SKILL_POINTER = "skills/python-test-and-fix/SKILL.md"


@dataclass
class RunRecord:
    """One examined CI run with its failed jobs and failed test identifiers."""

    run_id: int
    head_sha: str
    conclusion: str
    status: str
    created_at: str
    failed_jobs: list[str] = field(default_factory=list)
    failed_tests: list[str] = field(default_factory=list)


def _run_gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run one allowlisted read-only gh command; the only process spawn point."""
    if len(args) < 2 or (args[0], args[1]) not in _ALLOWED_VECTORS:
        raise ValueError(f"gh argument vector not allowlisted: {args[:2]!r}")
    return subprocess.run(  # nosec B603 B607 — argv validated against the fixed allowlist above; no shell
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _split_prefixed(line: str) -> tuple[str | None, str]:
    """Split a gh log line into (job, content), stripping the prefix.

    gh prefixes log lines with `<job>\\t<step>\\t<timestamp> `; the timestamp is
    a single space-free token. Lines without the prefix yield (None, line).
    """
    parts = line.split("\t", 2)
    if len(parts) == 3:
        rest = parts[2].split(" ", 1)
        return parts[0], rest[1] if len(rest) == 2 else ""
    return None, line


def _log_line_content(line: str) -> str:
    """Strip the `<job>\\t<step>\\t<timestamp> ` prefix gh adds to log lines."""
    return _split_prefixed(line)[1]


def _nodeid_from_line(line: str) -> str | None:
    """Return the failed-test nodeid of a summary line, or None."""
    match = _FAILED_RE.match(_log_line_content(line))
    return match.group(1) if match else None


def parse_failed_tests(log: str) -> list[str]:
    """Extract `FAILED <nodeid>` test identifiers from a `gh run view --log-failed` log.

    Only the fixed `short test summary info` block is counted; verbose progress
    lines never match. Everything after ` - ` is a message and is dropped. A run
    with no summary match yields an empty list (still reported red).
    Identifiers are returned deduplicated, in order of first appearance.
    """
    identifiers: list[str] = []
    seen: set[str] = set()
    for line in log.splitlines():
        nodeid = _nodeid_from_line(line)
        if nodeid is None or nodeid in seen:
            continue
        seen.add(nodeid)
        identifiers.append(nodeid)
    return identifiers


def _failed_job_names(log: str) -> list[str]:
    """Collect the distinct job names that produced FAILED summary lines."""
    jobs: list[str] = []
    seen: set[str] = set()
    for line in log.splitlines():
        job, content = _split_prefixed(line)
        if job is not None and _FAILED_RE.match(content) and job not in seen:
            seen.add(job)
            jobs.append(job)
    return jobs


def group_repeats(runs: list[RunRecord]) -> Counter[str]:
    """Count how many examined runs each failed test identifier appears in.

    A test counts once per run (Counter over each run's *set* of identifiers);
    in-progress runs carry no identifiers and never contribute.
    """
    counter: Counter[str] = Counter()
    for run in runs:
        counter.update(set(run.failed_tests))
    return counter


def _parse_iso_utc(value: str) -> datetime:
    """Parse an ISO-8601 timestamp, treating a naive value as UTC."""
    ts = datetime.fromisoformat(value)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts


def _first_line(text: str) -> str:
    return text.splitlines()[0] if text.strip() else "(no stderr output)"


def main(argv: list[str] | None = None) -> int:
    """Query runs, parse failures, group repeats, report, and pick the exit code."""
    parser = argparse.ArgumentParser(
        description="Read-only CI result reporter: group tests failing in 2+ recent runs."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="number of recent runs to examine (default 10)",
    )
    parser.add_argument(
        "--workflow", default="CI", help="workflow name or file to filter (default CI)"
    )
    parser.add_argument(
        "--branch", default="master", help="branch to filter (default master)"
    )
    parser.add_argument(
        "--before",
        default=None,
        help="ISO-8601 timestamp; drop runs created at or after it (client-side filter)",
    )
    args = parser.parse_args(argv)
    if args.limit < 1:
        parser.error("--limit must be >= 1")
    before: datetime | None = None
    if args.before is not None:
        try:
            before = _parse_iso_utc(args.before)
        except ValueError:
            parser.error(f"--before is not ISO-8601: {args.before!r}")

    # REQ-002: query recent runs (allowlisted read-only gh call).
    try:
        listed = _run_gh(
            [
                "run",
                "list",
                "--workflow",
                args.workflow,
                "--branch",
                args.branch,
                "--limit",
                str(args.limit),
                "--json",
                _RUN_LIST_FIELDS,
            ]
        )
    except FileNotFoundError:
        print("gh binary not found on PATH", file=sys.stderr)
        return 2
    if listed.returncode != 0:
        print(
            f"gh run list failed (exit {listed.returncode}): {_first_line(listed.stderr)}",
            file=sys.stderr,
        )
        return 2
    try:
        raw_runs = json.loads(listed.stdout)
    except json.JSONDecodeError:
        print("gh run list returned unparsable JSON", file=sys.stderr)
        return 2

    if before is not None:
        try:
            raw_runs = [
                r for r in raw_runs if _parse_iso_utc(str(r["createdAt"])) < before
            ]
        except (KeyError, TypeError, ValueError):
            print("gh run list returned unparsable run data", file=sys.stderr)
            return 2

    # REQ-003: fetch failed logs for red runs and extract test identifiers.
    runs: list[RunRecord] = []
    for raw in raw_runs:
        try:
            record = RunRecord(
                run_id=int(raw["databaseId"]),
                head_sha=str(raw["headSha"]),
                conclusion=str(raw["conclusion"] or ""),
                status=str(raw["status"]),
                created_at=str(raw["createdAt"]),
            )
        except (KeyError, TypeError, ValueError):
            print("gh run list returned unparsable run data", file=sys.stderr)
            return 2
        if record.conclusion == "failure":
            view = _run_gh(["run", "view", str(record.run_id), "--log-failed"])
            if view.returncode != 0:
                print(
                    f"gh run view failed (exit {view.returncode}): {_first_line(view.stderr)}",
                    file=sys.stderr,
                )
                return 2
            record.failed_tests = parse_failed_tests(view.stdout)
            record.failed_jobs = _failed_job_names(view.stdout)
        runs.append(record)

    repeats = group_repeats(runs)
    repeated = {nodeid: count for nodeid, count in repeats.items() if count >= 2}
    completed = [run for run in runs if run.status == "completed"]
    red_runs = [run for run in completed if run.conclusion == "failure"]

    # REQ-005: stdout-only report. Red runs first, then repeated failures.
    window = f"workflow={args.workflow} branch={args.branch} limit={args.limit}"
    if args.before is not None:
        window += f" before={args.before}"
    print(f"CI runs ({window}):")
    for run in runs:
        state = run.conclusion if run.conclusion else run.status
        print(f"  run {run.run_id}  {run.head_sha[:7]}  {state}  {run.created_at}")
        for job in run.failed_jobs:
            print(f"    job: {job}")
        for nodeid in run.failed_tests:
            print(f"    failed test: {nodeid}")
    if repeated:
        print("Repeated failures (failed in 2+ examined runs):")
        for nodeid, count in sorted(repeated.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {nodeid}  {count} runs")

    # Exit-code selection; in-progress runs never decide.
    exit_code = 0
    if not completed:
        print("No completed runs in window; nothing to judge.")
    else:
        latest = completed[0]
        if latest.conclusion == "success":
            print("Latest completed run is green.")
        else:
            print(
                f"Latest completed run (run {latest.run_id}) is not green: {latest.conclusion or latest.status}"
            )
            exit_code = 1
    if repeated:
        exit_code = 1
    if red_runs or repeated:
        print(f"Next: {_SKILL_POINTER}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
