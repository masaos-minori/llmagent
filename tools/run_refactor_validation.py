"""tools/run_refactor_validation.py — Run the refactor validation gate for changed source files.

Composes the per-file validation sequence from `rules/toolchain.md` (ruff format and
check, mypy, radon complexity gate, targeted tests, coverage plus diff-cover) so a
multi-file refactor program does not re-type the same command chain (AGENTS.md Global
Rule 7). Read-only: it runs checks and reports; it never edits source.

Usage:
    uv run python tools/run_refactor_validation.py \
        --src scripts/agent/http_lifecycle.py \
        --tests tests/agent/test_http_lifecycle.py
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 — invokes fixed repo tool commands, argv is a literal list
import sys
from dataclasses import dataclass

_RADON_BLOCK = re.compile(r"^\s+[MF] \d+:\d+ \S+ - ([A-Z]) \(\d+\)$")
_SKIP_CHOICES = ("mypy", "radon", "tests", "diff-cover")


@dataclass
class StepResult:
    """Outcome of one validation step."""

    name: str
    ok: bool
    detail: str


def _run(cmd: list[str]) -> tuple[int, str]:
    """Run *cmd* and return (returncode, combined stdout and stderr)."""
    proc = subprocess.run(  # nosec B603 — argv is a fixed tool list, no shell, no user-built command
        cmd,
        capture_output=True,
        text=True,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def _tail(text: str, lines: int = 4) -> str:
    """Return the last *lines* non-empty lines of *text* as one detail string."""
    kept = [line for line in text.splitlines() if line.strip()][-lines:]
    return " | ".join(kept) if kept else "no output"


def _pytest_args(tests: list[str], *, coverage: bool) -> list[str]:
    """Build the pytest invocation for the targeted-test run or the coverage run."""
    if coverage:
        return [
            "uv",
            "run",
            "coverage",
            "run",
            "-m",
            "pytest",
            *tests,
            "-q",
            "-p",
            "no:randomly",
        ]
    return ["uv", "run", "pytest", *tests, "-q", "-p", "no:randomly"]


def _radon_gate(src: list[str]) -> StepResult:
    """Fail when any function in *src* scores radon grade C or worse."""
    rc, out = _run(["uv", "run", "radon", "cc", *src, "-s"])
    if rc != 0:
        return StepResult("radon", False, _tail(out))
    grades = [
        match.group(1)
        for line in out.splitlines()
        if (match := _RADON_BLOCK.match(line))
    ]
    offenders = sorted(g for g in grades if g > "B")
    worst = max(grades, default="A")
    if offenders:
        count = len(offenders)
        return StepResult(
            "radon", False, f"worst grade {worst}: {count} function(s) at C or worse"
        )
    return StepResult("radon", True, f"worst grade {worst} ({len(grades)} function(s))")


def _diff_cover_gate(
    src: list[str],
    tests: list[str],
    compare_branch: str,
    fail_under: int,
) -> list[StepResult]:
    """Run coverage over *tests* and gate the changed lines of *src* with diff-cover.

    *src* is passed as ``--include`` so the gate scores only the files under refactor,
    not every uncommitted change in the working tree.
    """
    results: list[StepResult] = []
    rc, out = _run(_pytest_args(tests, coverage=True))
    if rc != 0:
        results.append(StepResult("coverage run", False, _tail(out)))
        return results
    rc, out = _run(["uv", "run", "coverage", "xml"])
    if rc != 0:
        results.append(StepResult("coverage xml", False, _tail(out)))
        return results
    cmd = [
        "uv",
        "run",
        "diff-cover",
        "coverage.xml",
        f"--compare-branch={compare_branch}",
        f"--fail-under={fail_under}",
        "--include",
        *src,
    ]
    rc, out = _run(cmd)
    results.append(StepResult("diff-cover", rc == 0, _tail(out, 6)))
    return results


def validate(
    src: list[str],
    tests: list[str],
    compare_branch: str,
    fail_under: int,
    skip: set[str],
) -> list[StepResult]:
    """Run the validation gate and return one result per step."""
    results: list[StepResult] = []
    all_files = [*src, *tests]

    rc, out = _run(["uv", "run", "ruff", "format", *all_files])
    results.append(StepResult("ruff format", rc == 0, _tail(out)))

    rc, out = _run(["uv", "run", "ruff", "check", *all_files])
    results.append(StepResult("ruff check", rc == 0, _tail(out)))

    if "mypy" not in skip:
        rc, out = _run(["uv", "run", "mypy", "--no-namespace-packages", *src])
        results.append(StepResult("mypy", rc == 0, _tail(out)))

    if "radon" not in skip:
        results.append(_radon_gate(src))

    if "tests" not in skip:
        rc, out = _run(_pytest_args(tests, coverage=False))
        results.append(StepResult("tests", rc == 0, _tail(out)))

    if "diff-cover" not in skip:
        results.extend(_diff_cover_gate(src, tests, compare_branch, fail_under))

    return results


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run the gate, print the summary, and return the exit code."""
    parser = argparse.ArgumentParser(
        description=(
            "Run the refactor validation gate (ruff, mypy, radon, targeted tests, "
            "diff-cover) for the given source files and test files."
        )
    )
    parser.add_argument(
        "--src",
        action="append",
        required=True,
        metavar="PATH",
        help="Changed source file under scripts/ (repeatable)",
    )
    parser.add_argument(
        "--tests",
        action="append",
        required=True,
        metavar="PATH",
        help="Test file that exercises the change (repeatable)",
    )
    parser.add_argument(
        "--compare-branch",
        default="master",
        help="diff-cover compare branch (default: master)",
    )
    parser.add_argument(
        "--fail-under",
        type=int,
        default=90,
        help="diff-cover minimum changed-line coverage percent (default: 90)",
    )
    parser.add_argument(
        "--skip",
        action="append",
        choices=_SKIP_CHOICES,
        default=[],
        help="Skip a gate step (repeatable)",
    )
    args = parser.parse_args(argv)

    results = validate(
        src=list(args.src),
        tests=list(args.tests),
        compare_branch=args.compare_branch,
        fail_under=args.fail_under,
        skip=set(args.skip),
    )
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        print(f"{status}  {result.name}: {result.detail}")

    failed = [result.name for result in results if not result.ok]
    if failed:
        print(f"GATE FAILED: {', '.join(failed)}")
        return 1
    print("GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
