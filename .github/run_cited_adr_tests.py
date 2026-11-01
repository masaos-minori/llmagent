#!/usr/bin/env python3
"""Run the pytest node ids cited in the ADR Invariant Verification Matrix.

Citations are extracted from ``docs/10_adr/adr_01_index.md`` using the same
node-id regex as ``tools.check_adr_invariant_matrix`` (imported here for a
single source of truth). Each cited node id is executed with
``pytest <nodeid> -m "not integration" -rs -q``; the step fails when a citation
collects to zero tests (missing), fails, reports SKIPPED or XFAIL without an
approved ``Exception: <id>`` recorded in the citing matrix row, or is left with
nothing to run after integration tests are intentionally deselected.

This backs GV-012's behavioral verification in the CI ``lint`` job
(``.github/workflows/ci.yml``); the path-existence check in
``check_adr_invariant_matrix`` remains the structural gate.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

# Repo root is three levels up: .github/ -> repo root. Prepend it so the
# checker's own ``import tools._docs_consistency_lib`` resolves regardless of
# the directory this helper is invoked from (e.g. the CI checkout root, whose
# sys.path[0] is the script's own directory rather than the repo root).
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Load the checker by file path (rather than ``import tools.check_adr_invariant_matrix``)
# so the node-id regex and matrix index stay single-sourced from the checker
# without an import that ruff would flag for placement outside the top of file.
_checker_spec = importlib.util.spec_from_file_location(
    "check_adr_invariant_matrix",
    REPO_ROOT / "tools" / "check_adr_invariant_matrix.py",
)
if _checker_spec is None:  # pragma: no cover - path exists and is a valid module
    msg = f"cannot load checker module: {REPO_ROOT / 'tools' / 'check_adr_invariant_matrix.py'}"
    raise RuntimeError(msg)
_CHECKER = importlib.util.module_from_spec(_checker_spec)
if _checker_spec.loader is None:  # pragma: no cover - file always exists in repo
    msg = f"checker module has no loader: {REPO_ROOT / 'tools' / 'check_adr_invariant_matrix.py'}"
    raise RuntimeError(msg)
_checker_spec.loader.exec_module(_CHECKER)

_TEST_PATH_RE = _CHECKER._TEST_PATH_RE
_EXCEPTION_RE = _CHECKER._EXCEPTION_RE
ADR_INDEX = _CHECKER.ADR_INDEX

_PYTEST_EXIT = {
    "passed": 0,
    "failed": 1,
    "interrupted": 2,
    "usage_error": 4,
    "no_tests_collected": 5,
}


def extract_cited_node_ids(lines: list[str]) -> list[tuple[str, str]]:
    """Return ``(file_part, node_id)`` for every cited node id in `lines`.

    Order follows first appearance; duplicates are dropped keeping the first.
    """
    cited: list[tuple[str, str]] = []
    for line in lines:
        for match in _TEST_PATH_RE.finditer(line):
            if (match.group(1), match.group(2)) not in cited:
                cited.append((match.group(1), match.group(2)))
    return cited


def _run_pytest(args: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


def _node_id_exists(node_id: str) -> bool:
    """True if `node_id` resolves to at least one test (no marker filter)."""
    rc, _ = _run_pytest([node_id, "--collect-only", "-q", "-p", "no:cacheprovider"])
    return rc == _PYTEST_EXIT["passed"]


def _classify_outcome(returncode: int, output: str) -> str | None:
    """Classify a passing pytest run whose `-rs` short summary shows a skip-family
    outcome. Each cited node runs in its own pytest process, so a `SKIPPED [` or
    `XFAIL ` short-summary line in this output belongs to that node."""
    if returncode != _PYTEST_EXIT["passed"]:
        return None
    for line in output.splitlines():
        if line.startswith("SKIPPED"):
            return "skipped"
        if line.startswith("XFAIL"):
            return "xfailed"
    return None


def _cited_exceptions(lines: list[str]) -> set[tuple[str, str]]:
    """Return the cited `(file_part, node_id)` pairs whose matrix line records an
    approved `Exception: <id>` (grammar single-sourced from the checker)."""
    approved: set[tuple[str, str]] = set()
    for line in lines:
        if not _EXCEPTION_RE.search(line):
            continue
        for match in _TEST_PATH_RE.finditer(line):
            approved.add((match.group(1), match.group(2)))
    return approved


def evaluate_citation(file_part: str, node_id: str) -> tuple[bool, str]:
    """Run one cited node id and classify the outcome.

    Returns ``(ok, reason)``. `ok` is False for a missing, failing, skipped, or
    xfailed citation; True otherwise (including intentional integration
    deselection).
    """
    rc, output = _run_pytest(
        [f"{file_part}::{node_id}", "-m", "not integration", "-rs", "-q"]
    )
    outcome = _classify_outcome(rc, output)
    if outcome:
        return False, outcome
    if rc == _PYTEST_EXIT["passed"]:
        return True, "passed"
    if rc == _PYTEST_EXIT["failed"]:
        if output:
            print(output, file=sys.stderr)
        return False, "failed"
    if rc == _PYTEST_EXIT["no_tests_collected"]:
        # Empty after deselection: either an integration-only citation
        # (intentional) or a missing citation. Disambiguate by collecting
        # without the marker filter.
        if _node_id_exists(f"{file_part}::{node_id}"):
            return True, "integration-deselected"
        return False, "missing"
    return False, f"pytest-exit-{rc}"


def main() -> int:
    if not ADR_INDEX.exists():
        print(f"cited-test matrix not found: {ADR_INDEX}", file=sys.stderr)
        return 2

    lines = ADR_INDEX.read_text(encoding="utf-8").splitlines()
    # `extract_cited_node_ids` already drops duplicate citations; `unique` keeps
    # the existing name used by the run/report loops below.
    unique = extract_cited_node_ids(lines)
    if not unique:
        print("no cited node ids found in ADR invariant matrix", file=sys.stderr)
        return 2

    approved = _cited_exceptions(lines)
    failures: list[tuple[str, str, str]] = []
    for file_part, node_id in unique:
        ok, reason = evaluate_citation(file_part, node_id)
        if (
            not ok
            and reason in ("skipped", "xfailed")
            and (file_part, node_id) in approved
        ):
            ok = True
            reason = f"{reason}-approved-exception"
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {file_part}::{node_id} ({reason})")
        if not ok:
            failures.append((file_part, node_id, reason))

    if failures:
        print("\nCited ADR invariant tests that did not pass:", file=sys.stderr)
        for file_part, node_id, reason in failures:
            print(f"  {file_part}::{node_id} — {reason}", file=sys.stderr)
        return 1

    print(f"All {len(unique)} cited ADR invariant tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
