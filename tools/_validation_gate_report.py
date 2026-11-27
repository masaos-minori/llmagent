#!/usr/bin/env python3
"""tools/_validation_gate_report.py - the gate-summary renderer for run_validation_gates.

Default output hides gates whose command needs a runtime argument (reason
``runtime-argument``) and prints one count line naming the count and the ``--verbose``
flag that shows them; every other row, including the other ``Not available`` reasons,
stays visible (rules/ai-execution.md item 12: an unrun check is never reported as
passed). ``verbose=True`` prints every row. The header names the base ref the run
actually used. ``failures_only=True`` prints the changed-file count, only the rows whose
status is not ``Pass``, and a final ``Result:`` line (the exit code is unchanged).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.run_validation_gates import GateResult

# The only reason the default summary hides; a missing-tool or os-error row is a check
# that did not run and stays visible.
HIDE_REASON = "runtime-argument"


def _print_header(changed: list[str], mode: str, base: str) -> None:
    """Print the mode/base header line, the changed-file list, and the blank line."""
    print(
        f"Validation gates — mode: {mode}, base: {base}, changed files: {len(changed)}"
    )
    if changed:
        print(", ".join(changed))
    print()


def _print_rows(results: list[GateResult]) -> None:
    """Print one aligned row per result, with the detail indented under the row."""
    name_width = max((len(res.name) for res in results), default=0)
    status_width = max((len(res.status) for res in results), default=0)
    for res in results:
        name = res.name.ljust(name_width)
        status = res.status.ljust(status_width)
        print(f"  {name}  {status}  {res.command}")
        if res.detail:
            print(f"          ({res.detail})")


def _print_count_header(changed: list[str], mode: str, base: str) -> None:
    """Print the header with the changed-file count only, then a blank line."""
    print(
        f"Validation gates — mode: {mode}, base: {base}, changed files: {len(changed)}"
    )
    print()


def _render_failures_only(
    results: list[GateResult],
    changed: list[str],
    mode: str,
    base: str,
    verbose: bool,
) -> None:
    """Print the count header, the non-``Pass`` rows, and the final ``Result:`` line."""
    _print_count_header(changed, mode, base)
    failing = sum(1 for res in results if res.status == "Fail")
    if not results:
        print("No gates selected for these changed files.")
    else:
        unfinished = [res for res in results if res.status != "Pass"]
        shown = (
            unfinished
            if verbose
            else [res for res in unfinished if res.reason != HIDE_REASON]
        )
        _print_rows(shown)
        hidden_count = len(unfinished) - len(shown)
        if hidden_count:
            print(
                f"  ({hidden_count} gate(s) hidden: their commands need a runtime "
                "argument; pass --verbose to show them)"
            )
    print(
        "Result: Pass" if failing == 0 else f"Result: Fail ({failing} failing gate(s))"
    )


def render_summary(
    results: list[GateResult],
    changed: list[str],
    mode: str,
    base: str,
    verbose: bool = False,
    failures_only: bool = False,
) -> None:
    """Print the per-gate summary table and the changed-file/mode/base header.

    Without ``verbose``, rows whose reason is ``runtime-argument`` are dropped and one
    count line names them; with it, every row prints with its detail. The canonical
    Pass/Fail/Partial/Not available/Blocked row framing is unchanged.
    """
    if failures_only:
        _render_failures_only(results, changed, mode, base, verbose)
        return
    _print_header(changed, mode, base)
    if not results:
        print("No gates selected for these changed files.")
        return
    visible = (
        list(results)
        if verbose
        else [res for res in results if res.reason != HIDE_REASON]
    )
    _print_rows(visible)
    hidden_count = len(results) - len(visible)
    if hidden_count:
        print(
            f"  ({hidden_count} gate(s) hidden: their commands need a runtime argument;"
            " pass --verbose to show them)"
        )
