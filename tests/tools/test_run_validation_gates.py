"""Unit tests for tools/run_validation_gates.py.

Covers the four surfaces the plan's validation table exercises: path-to-gate selection
(REQ-002), result classification into the canonical vocabulary (REQ-005), fast-vs-full
mode gate sets (REQ-003), and the drift invariant against the real routing.md (REQ-006).

``run_gate`` results come from an injected runner callable rather than ``unittest.mock``,
so the mock-patch-targets checker never sees a module-level patch target to complain about.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools.run_validation_gates import (
    MODE_FAST,
    MODE_FULL,
    ROUTING_GATES,
    SOURCE_ROUTING,
    SOURCE_TOOLCHAIN,
    TOOLCHAIN_GATES,
    Gate,
    _checker_id_from_cell,
    _checker_id_from_command,
    _split_md_row,
    classify,
    drift_report,
    run_gate,
    select_gates,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ROUTING_MD = REPO_ROOT / "routing.md"


def _runner_for(*returncodes: int):
    """Return a fake ``Runner`` yielding ``returncodes`` in order (last repeats)."""
    sequence = list(returncodes)
    index = 0

    def _run(
        argv: list[str], env: dict[str, str] | None
    ) -> subprocess.CompletedProcess:
        nonlocal index
        if sequence:
            code = sequence[index] if index < len(sequence) else sequence[-1]
        else:
            code = 0
        index += 1
        return subprocess.CompletedProcess(args=argv, returncode=code)

    return _run


# --- id derivation (guards the relative-path regex fix) --------------------------


def test_checker_id_from_relative_tool_path():
    """A repo-relative ``tools/<name>.py`` token yields the basename, not the first argv."""
    got = _checker_id_from_command(
        ("uv", "run", "python", "tools/manage_workitem_stage.py", "detect-stale")
    )
    assert got == "manage_workitem_stage:detect-stale"


def test_checker_id_matches_across_sources():
    """Every mapping id equals the id derived from the equivalent routing.md Run cell."""
    for gate in ROUTING_GATES:
        command_line = " ".join(gate.command[0])
        from_cell = _checker_id_from_cell(f"`{command_line}`")
        assert gate.checker_id == from_cell


# --- markdown table row splitting (guards the escaped-pipe fix) ------------------


def test_split_md_row_keeps_escaped_pipe_inside_code_span():
    """Pipes inside a code span (or escaped as ``\\|``) do not split the row into cells."""
    row = r"| Trigger `a`\|`b` | `run --format json\|csv` | notes |"
    cells = _split_md_row(row.strip("|"))
    assert len(cells) == 3
    assert cells[1].strip() == "`run --format json|csv`"


# --- selection (REQ-002) --------------------------------------------------------


def test_selection_docs_only_fast_mode():
    """A docs-only diff selects docs-pattern routing gates and nothing else in fast mode."""
    selected = select_gates(["docs/pages/guide.md"], MODE_FAST)
    names = {gate.name for gate in selected}
    assert names >= {"check_docs_japanese", "manage_frontmatter"}
    # Fast mode never runs the toolchain sequence.
    assert not any(gate.source == SOURCE_TOOLCHAIN for gate in selected)
    # Patternless (manual/content-based) checkers are never auto-selected.
    assert "check_compat_shims" not in names
    assert "generate_reference_table_mcp" not in names


def test_selection_scripts_full_includes_toolchain():
    """A scripts/** diff selects scripts routing gates plus the full toolchain sequence."""
    selected = select_gates(["scripts/thing.py"], MODE_FULL)
    names = {gate.name for gate in selected}
    assert "check_docstrings" in names
    assert "check_mock_patch_targets" in names
    assert "mypy" in names
    assert "bandit" in names


def test_selection_scripts_fast_excludes_toolchain():
    """Fast mode selects the same routing gates but never the toolchain sequence."""
    selected = select_gates(["scripts/thing.py"], MODE_FAST)
    assert not any(gate.source == SOURCE_TOOLCHAIN for gate in selected)
    names = {gate.name for gate in selected}
    assert "check_docstrings" in names
    assert "check_mock_patch_targets" in names


def test_selection_no_match_fast_mode_empty():
    """A diff touching no mapped path selects no gates in fast mode."""
    assert select_gates(["assets/logo.png"], MODE_FAST) == []


# --- classification (REQ-005) ---------------------------------------------------

_CLASSIFY_CASES: list[tuple[int | None, bool, str]] = [
    (0, False, "Pass"),
    (1, False, "Fail"),
    (None, False, "Not available"),
    (0, True, "Not available"),
    (2, True, "Not available"),
]


@pytest.mark.parametrize(("returncode", "unavailable", "expected"), _CLASSIFY_CASES)
def test_classify_buckets(
    returncode: int | None, unavailable: bool, expected: str
) -> None:
    assert classify(returncode, unavailable=unavailable) == expected


def test_classify_unavailable_never_pass() -> None:
    """An unavailable gate is reported as ``Not available`` for every return code (REQ-005)."""
    for returncode in (0, 1, None):
        status = classify(returncode, unavailable=True)
        assert status == "Not available"
        assert status != "Pass"


# --- modes (REQ-003) ------------------------------------------------------------


def test_modes_full_adds_toolchain_sequence() -> None:
    """Full mode adds every toolchain gate on top of the fast-mode selection."""
    fast = select_gates(["scripts/thing.py"], MODE_FAST)
    full = select_gates(["scripts/thing.py"], MODE_FULL)
    fast_names = {gate.name for gate in fast}
    full_names = {gate.name for gate in full}
    assert not any(gate.source == SOURCE_TOOLCHAIN for gate in fast)
    assert {gate.name for gate in TOOLCHAIN_GATES} <= full_names
    # Fast-mode selection is a subset of full-mode selection.
    assert fast_names <= full_names


# --- drift (REQ-006) ------------------------------------------------------------


def test_drift_all_routing_checkers_mapped() -> None:
    """Every checker named in the real routing.md has a mapping entry."""
    text = ROUTING_MD.read_text(encoding="utf-8")
    count, errors = drift_report(text)
    assert count == 0, errors


def test_drift_reports_unmapped_checker() -> None:
    """A synthetic routing.md with an unmapped Run cell produces a drift error."""
    synthetic = (
        "### When to run which tool\n\n"
        "| Situation | Run | Notes |\n"
        "|---|---|---|\n"
        "| A trigger | `uv run python tools/nonexistent_checker_xyz.py` | notes |\n"
    )
    count, errors = drift_report(synthetic)
    assert count >= 1
    assert any("nonexistent_checker_xyz" in message for message in errors)


def test_drift_ignores_the_orchestrators_own_row() -> None:
    """The row naming run_validation_gates itself is not a checker, so it needs no mapping."""
    synthetic = (
        "### When to run which tool\n\n"
        "| Situation | Run | Notes |\n"
        "|---|---|---|\n"
        "| Run the gates | `uv run python tools/run_validation_gates.py` | notes |\n"
    )
    _, errors = drift_report(synthetic)
    assert not any("run_validation_gates" in message for message in errors)


# --- run_gate runner injection --------------------------------------------------


def test_run_gate_pass_and_fail_via_injected_runner() -> None:
    """A zero exit is ``Pass``; a non-zero exit is ``Fail`` with the exit code in the detail."""
    ok = Gate(name="ok", command=(("echo",),), source=SOURCE_ROUTING, mode=MODE_FAST)
    bad = Gate(name="bad", command=(("false",),), source=SOURCE_ROUTING, mode=MODE_FAST)
    assert run_gate(ok, runner=_runner_for(0)).status == "Pass"
    fail_result = run_gate(bad, runner=_runner_for(1))
    assert fail_result.status == "Fail"
    assert "exit code 1" in fail_result.detail


def test_run_gate_requires_context_is_not_available() -> None:
    """A gate whose command carries a runtime placeholder short-circuits to ``Not available``."""
    gate = Gate(
        name="needs-arg",
        command=(("uv", "run", "python", "tools/x.py", "--file", "<path>"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
    )
    assert gate.requires_context is True
    # The injected runner would report Pass; the placeholder short-circuit wins instead.
    assert run_gate(gate, runner=_runner_for(0)).status == "Not available"
