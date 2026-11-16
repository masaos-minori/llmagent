"""Unit tests for tools/run_validation_gates.py.

Covers the four surfaces the plan's validation table exercises: path-to-gate selection
(REQ-002), result classification into the canonical vocabulary (REQ-005), fast-vs-full
mode gate sets (REQ-003), and the drift invariant against the real routing.md (REQ-006).

``run_gate`` results come from an injected runner callable rather than ``unittest.mock``,
so the mock-patch-targets checker never sees a module-level patch target to complain about.
"""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from tools.run_validation_gates import (
    COMMIT_ONLY_HOOKS,
    MODE_FAST,
    MODE_FULL,
    ROUTING_GATES,
    SOURCE_ROUTING,
    SOURCE_TOOLCHAIN,
    TOOLCHAIN_GATES,
    Gate,
    _checker_id_from_cell,
    _checker_id_from_command,
    _resolve_argv,
    _split_md_row,
    build_parser,
    classify,
    drift_report,
    parse_precommit_hooks,
    run_gate,
    run_gates,
    select_gates,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ROUTING_MD = REPO_ROOT / "routing.md"
PRECOMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"


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


def test_adr_edit_does_not_auto_select_preservation_check():
    """check_adr_preservation is content-based (routing.md: only for an ADR shortened or
    reworded without changing its decisions), so an ADR edit never selects it, while the
    gate keeps its routing mapping entry for the drift check."""
    adr_path = "docs/10_adr/adr_01_index.md"
    for mode in (MODE_FAST, MODE_FULL):
        names = {gate.name for gate in select_gates([adr_path], mode)}
        assert "check_docs_structure" in names
        assert "check_adr_preservation" not in names
    gate = next(g for g in ROUTING_GATES if g.name == "check_adr_preservation")
    assert gate.patterns == ()


def test_manage_frontmatter_gate_command_is_valid_subcommand():
    """The manage_frontmatter gate must invoke a valid report-only CLI subcommand.

    Regression guard for the ``add-missing|dedupe-lists`` argv token that made the
    gate a permanent argparse usage-error Fail (exit 2).
    """
    gate = next(g for g in ROUTING_GATES if g.name == "manage_frontmatter")
    valid_subcommands = {
        "add-missing",
        "dedupe-lists",
        "merge-related",
        "rename-category-to-area",
        "classify",
    }
    for argv in gate.command:
        subcommand = argv[argv.index("tools/manage_frontmatter.py") + 1]
        assert subcommand in valid_subcommands
        assert "|" not in subcommand
        assert "--fix" not in argv


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


# --- new gate triggers (REQ-002) ------------------------------------------------

_ADR_GATES = {
    "check_adr_invariant_matrix",
    "check_adr_reference",
    "check_adr_structure",
}
_PARITY_GATES = _ADR_GATES | {
    "check_known_deviation_sync",
    "check_plan_target_overlaps",
    "check_conftest_integrity",
    "check_workitem_traceability",
}


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("docs/10_adr/adr_01_index.md", {"check_known_deviation_sync"}),
        ("scripts/x.py", _ADR_GATES),
        ("routing.md", _ADR_GATES),
        ("tools/check_adr_structure.py", _ADR_GATES),
        ("docs/a.md", {"check_known_deviation_sync"}),
        ("docs/sub/a.md", {"check_known_deviation_sync"}),
        ("plans/p.md", {"check_plan_target_overlaps", "check_workitem_traceability"}),
        ("tests/conftest.py", {"check_conftest_integrity"}),
        ("tests/agent/conftest.py", {"check_conftest_integrity"}),
        ("issues/i.md", {"check_workitem_traceability"}),
        ("plans/done/p.md", {"check_workitem_traceability"}),
        ("implementations/i.md", {"check_workitem_traceability"}),
        ("assets/logo.png", set()),
    ],
)
def test_parity_gate_triggers_mirror_hook_filters(
    path: str, expected: set[str]
) -> None:
    """Each parity gate selects on its hook's filter (full mode sees every gate)."""
    names = {g.name for g in select_gates([path], MODE_FULL)} & _PARITY_GATES
    # Any .py or .md path also matches the ADR hooks' `types_or: [python, markdown]`.
    if path.endswith((".py", ".md")):
        expected = expected | _ADR_GATES
    assert names == expected


def test_removed_adr_cited_test_selects_adr_gate_and_fails_on_checker_failure() -> None:
    """AC-3: an ADR change selects the invariant gate in fast mode; its failure is ``Fail``."""
    changed = ["docs/10_adr/adr_01_index.md"]
    gate = next(
        g
        for g in select_gates(changed, MODE_FAST)
        if g.name == "check_adr_invariant_matrix"
    )
    assert run_gate(gate, runner=_runner_for(1)).status == "Fail"
    assert run_gate(gate, runner=_runner_for(0)).status == "Pass"


def test_workitem_traceability_gate_id_matches_hook_id() -> None:
    """The gate carries --active-only, so its id equals the id derived from the hook."""
    gate = next(g for g in ROUTING_GATES if g.name == "check_workitem_traceability")
    hooks, _ = parse_precommit_hooks(PRECOMMIT_CONFIG.read_text(encoding="utf-8"))
    assert gate.checker_id == "check_workitem_traceability:--active-only"
    assert hooks["workitem-traceability"] == gate.checker_id


def test_full_mode_only_gate_is_absent_from_fast_selection() -> None:
    """A slow routing gate (mode=full) is skipped in fast mode and kept in full mode."""
    path = "issues/i.md"
    fast = {g.name for g in select_gates([path], MODE_FAST)}
    full = {g.name for g in select_gates([path], MODE_FULL)}
    assert "check_workitem_traceability" not in fast
    assert "check_workitem_traceability" in full
    gate = next(g for g in ROUTING_GATES if g.name == "check_workitem_traceability")
    assert gate.mode == MODE_FULL


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


# --- hook parity (REQ-001) ------------------------------------------------------

_EMPTY_ROUTING = (
    "### When to run which tool\n\n| Situation | Run | Notes |\n|---|---|---|\n"
)


def _hook_config(entry: str | None, hook_id: str = "demo-hook") -> str:
    """Build a one-hook pre-commit config; ``entry=None`` omits the ``entry`` key."""
    entry_line = f"        entry: {entry}\n" if entry is not None else ""
    return (
        "repos:\n  - repo: local\n    hooks:\n"
        f"      - id: {hook_id}\n        name: demo\n{entry_line}"
        "        language: system\n"
    )


def _hook_messages(config: str) -> list[str]:
    """Hook-parity messages only (drops routing and stale-allowlist noise)."""
    _, errors = drift_report(_EMPTY_ROUTING, config)
    return [m for m in errors if "pre-commit" in m or "unparseable" in m]


def test_drift_reports_unmapped_hook() -> None:
    """A tool-backed hook with no gate mapping and no allowlist entry is a drift error."""
    config = _hook_config("python -m tools.nonexistent_checker_xyz")
    count, errors = drift_report(_EMPTY_ROUTING, config)
    assert count >= 1
    assert any("demo-hook" in m and "nonexistent_checker_xyz" in m for m in errors)


def test_drift_allows_allowlisted_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    """The same hook is not reported once its id is in ``COMMIT_ONLY_HOOKS`` with a reason."""
    import tools.run_validation_gates as module

    config = _hook_config("python -m tools.nonexistent_checker_xyz")
    monkeypatch.setattr(
        module, "COMMIT_ONLY_HOOKS", (("demo-hook", "commit-only for the test"),)
    )
    count, errors = drift_report(_EMPTY_ROUTING, config)
    assert not any("demo-hook" in m for m in errors), errors
    assert count == len(errors)


def test_drift_rejects_blank_allowlist_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    """An allowlist entry without a reason is an error, not a silent default."""
    import tools.run_validation_gates as module

    config = _hook_config("python -m tools.nonexistent_checker_xyz")
    monkeypatch.setattr(module, "COMMIT_ONLY_HOOKS", (("demo-hook", "  "),))
    _, errors = drift_report(_EMPTY_ROUTING, config)
    assert any("has no reason" in m and "demo-hook" in m for m in errors)


def test_drift_rejects_allowlist_entry_without_hook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An allowlist entry naming no tool-backed hook in the config is stale."""
    import tools.run_validation_gates as module

    monkeypatch.setattr(module, "COMMIT_ONLY_HOOKS", (("ghost-hook", "reason"),))
    _, errors = drift_report(_EMPTY_ROUTING, _hook_config("bash -c true"))
    assert any("ghost-hook" in m for m in errors)


@pytest.mark.parametrize(
    "config",
    ["repos: [", "just a string", "other: 1\n"],
    ids=["malformed-yaml", "non-mapping", "no-repos"],
)
def test_drift_reports_malformed_config(config: str) -> None:
    """A malformed or repo-less config yields an error instead of passing silently."""
    count, errors = drift_report(_EMPTY_ROUTING, config)
    assert count >= 1
    assert any("pre-commit-config.yaml" in m for m in errors)


@pytest.mark.parametrize(
    "entry",
    [
        "bash -c 'true'",
        "uv run mypy --no-incremental",
        None,
    ],
    ids=["bash", "uv-run-mypy", "no-entry"],
)
def test_drift_ignores_non_tool_hooks(entry: str | None) -> None:
    """Non-tool hooks and hooks without an ``entry`` are not parity candidates."""
    hooks, errors = parse_precommit_hooks(_hook_config(entry))
    assert hooks == {}
    assert errors == []


def test_drift_skips_the_orchestrators_own_hook() -> None:
    """The drift hook runs this tool, so it must not be compared with the mapping."""
    config = _hook_config("python -m tools.run_validation_gates drift")
    hooks, errors = parse_precommit_hooks(config)
    assert hooks == {}
    assert errors == []


def test_drift_reports_unparseable_tool_entry() -> None:
    """A tool-looking token that matches neither the module nor the path form is an error."""
    assert any(
        "unparseable" in m for m in _hook_messages(_hook_config("python tools/x"))
    )


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        ("python -m tools.check_docs_quality", "check_docs_quality"),
        ("uv run python -m tools.check_docs_quality", "check_docs_quality"),
        (
            "python -m tools.check_workitem_traceability --active-only",
            "check_workitem_traceability:--active-only",
        ),
        ("python tools/check_docs_quality.py", "check_docs_quality"),
    ],
)
def test_hook_entry_forms_derive_gate_ids(entry: str, expected: str) -> None:
    """Each entry form present in the live config reduces to the gate id form."""
    hooks, errors = parse_precommit_hooks(_hook_config(entry))
    assert errors == []
    assert hooks == {"demo-hook": expected}


def test_live_precommit_config_has_no_drift() -> None:
    """The real hook config and routing.md produce zero drift errors (AC-1)."""
    routing = ROUTING_MD.read_text(encoding="utf-8")
    config = PRECOMMIT_CONFIG.read_text(encoding="utf-8")
    count, errors = drift_report(routing, config)
    assert count == 0, errors


def test_commit_only_hooks_all_carry_a_reason() -> None:
    """Every reviewed allowlist entry records a non-blank reason."""
    assert all(
        hook_id.strip() and reason.strip() for hook_id, reason in COMMIT_ONLY_HOOKS
    )


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


def test_requires_context_ignores_plain_dots_but_flags_ellipsis() -> None:
    """A ``.py`` path or ``--flag=1.5`` is concrete; only ``<``, ``[``, ``]`` and ``...`` mark a placeholder."""
    concrete = Gate(
        name="concrete",
        command=(("uv", "run", "python", "tools/check_skills_references.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
    )
    ellipsis = Gate(
        name="ellipsis",
        command=(("uv", "run", "python", "tools/x.py", "[glob ...]"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
    )
    assert concrete.requires_context is False
    assert ellipsis.requires_context is True


def test_tools_size_gate_is_mapped_with_its_own_checker_id() -> None:
    gate = next(g for g in ROUTING_GATES if g.name == "check_module_size_tools")

    assert gate.checker_id == "check_module_size:tools"
    assert "tools/*.py" in gate.patterns
    assert gate.source == SOURCE_ROUTING
    assert gate.mode == MODE_FAST


def test_tools_size_gate_is_selected_by_a_tool_change() -> None:
    selected = {g.name for g in select_gates(["tools/classify_changes.py"], MODE_FAST)}

    assert "check_module_size_tools" in selected
    assert "check_module_size" not in selected


def test_reexported_gate_definitions_are_the_same_objects() -> None:
    import tools._validation_gate_defs as defs
    import tools.run_validation_gates as entry

    assert entry.Gate is defs.Gate
    assert entry.ROUTING_GATES is defs.ROUTING_GATES
    assert entry.TOOLCHAIN_GATES is defs.TOOLCHAIN_GATES
    assert entry._checker_id_from_command is defs._checker_id_from_command


# --- concurrent execution --------------------------------------------------------


def _named_gate(name: str, *, exclusive: bool = False) -> Gate:
    return Gate(
        name=name,
        command=((name,),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        exclusive=exclusive,
    )


def test_run_gates_runs_independent_gates_at_the_same_time() -> None:
    """Both runners wait for each other; a serial run would time the barrier out."""
    barrier = threading.Barrier(2)

    def _run(
        argv: list[str], env: dict[str, str] | None
    ) -> subprocess.CompletedProcess:
        barrier.wait(timeout=10)
        return subprocess.CompletedProcess(args=argv, returncode=0)

    results = run_gates([_named_gate("a"), _named_gate("b")], jobs=2, runner=_run)

    assert [r.name for r in results] == ["a", "b"]
    assert [r.status for r in results] == ["Pass", "Pass"]


def test_run_gates_keeps_input_order_when_a_later_gate_finishes_first() -> None:
    def _run(
        argv: list[str], env: dict[str, str] | None
    ) -> subprocess.CompletedProcess:
        if argv[0] == "slow":
            time.sleep(0.2)
        return subprocess.CompletedProcess(
            args=argv, returncode=1 if argv[0] == "fast" else 0
        )

    results = run_gates([_named_gate("slow"), _named_gate("fast")], runner=_run)

    assert [(r.name, r.status) for r in results] == [("slow", "Pass"), ("fast", "Fail")]


def test_run_gates_runs_an_exclusive_gate_alone_between_the_batches() -> None:
    lock = threading.Lock()
    events: list[tuple[str, str]] = []

    def _run(
        argv: list[str], env: dict[str, str] | None
    ) -> subprocess.CompletedProcess:
        with lock:
            events.append(("start", argv[0]))
        time.sleep(0.05)
        with lock:
            events.append(("end", argv[0]))
        return subprocess.CompletedProcess(args=argv, returncode=0)

    gates = [
        _named_gate("a"),
        _named_gate("b"),
        _named_gate("w", exclusive=True),
        _named_gate("c"),
        _named_gate("d"),
    ]
    results = run_gates(gates, jobs=4, runner=_run)

    assert [r.name for r in results] == ["a", "b", "w", "c", "d"]
    at = {event: index for index, event in enumerate(events)}
    assert max(at[("end", name)] for name in "ab") < at[("start", "w")]
    assert at[("end", "w")] < min(at[("start", name)] for name in "cd")


def test_run_gates_with_one_job_never_overlaps() -> None:
    lock = threading.Lock()
    running = 0
    peak = 0

    def _run(
        argv: list[str], env: dict[str, str] | None
    ) -> subprocess.CompletedProcess:
        nonlocal running, peak
        with lock:
            running += 1
            peak = max(peak, running)
        time.sleep(0.02)
        with lock:
            running -= 1
        return subprocess.CompletedProcess(args=argv, returncode=0)

    run_gates([_named_gate(n) for n in "abcd"], jobs=1, runner=_run)

    assert peak == 1


def test_run_gates_of_nothing_is_empty() -> None:
    assert run_gates([], runner=_runner_for(0)) == []


@pytest.mark.parametrize("value", ["0", "-2"])
def test_jobs_option_rejects_less_than_one(value: str) -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--jobs", value])


def test_jobs_option_defaults_to_cpu_count() -> None:
    assert build_parser().parse_args([]).jobs is None
    assert build_parser().parse_args(["--jobs", "3"]).jobs == 3


# --- interpreter resolution ------------------------------------------------------


def test_resolve_argv_uses_the_running_interpreter_inside_the_project_venv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "prefix", str(REPO_ROOT / ".venv"))

    argv = _resolve_argv(("uv", "run", "python", "tools/x.py", "--flag"))

    assert argv == [sys.executable, "tools/x.py", "--flag"]


def test_resolve_argv_keeps_uv_run_outside_the_project_venv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "prefix", "/somewhere/else")
    command = ("uv", "run", "python", "tools/x.py")

    assert _resolve_argv(command) == list(command)


def test_resolve_argv_leaves_other_commands_alone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "prefix", str(REPO_ROOT / ".venv"))

    assert _resolve_argv(("uv", "run", "ruff", "check")) == [
        "uv",
        "run",
        "ruff",
        "check",
    ]
    assert _resolve_argv(("git", "diff")) == ["git", "diff"]


def test_run_gate_executes_the_resolved_argv_but_displays_the_documented_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "prefix", str(REPO_ROOT / ".venv"))
    seen: list[list[str]] = []

    def _run(
        argv: list[str], env: dict[str, str] | None
    ) -> subprocess.CompletedProcess:
        seen.append(argv)
        return subprocess.CompletedProcess(args=argv, returncode=0)

    gate = Gate(
        name="tool",
        command=(("uv", "run", "python", "tools/x.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
    )
    result = run_gate(gate, runner=_run)

    assert seen == [[sys.executable, "tools/x.py"]]
    assert result.command == "uv run python tools/x.py"


# --- gate definitions ------------------------------------------------------------


def test_exclusive_gates_are_the_writers_and_the_cpu_heavy_gates() -> None:
    exclusive = {g.name for g in (*ROUTING_GATES, *TOOLCHAIN_GATES) if g.exclusive}

    assert exclusive == {
        "ruff-format-lint",
        "pytest",
        "diff-cover",
        "pre-commit",
        "generate_adr_authority",
        "generate_reference_table_mcp",
        "generate_reference_table_rag",
        "generate_reference_table_deployment",
    }


def test_full_mode_runs_the_test_suite_once_and_diff_cover_reuses_its_coverage() -> (
    None
):
    by_name = {g.name: g for g in TOOLCHAIN_GATES}
    suite = by_name["pytest"].command[0]
    coverage_commands = by_name["diff-cover"].command

    assert {"-n", "logical", "--cov=scripts"} <= set(suite)
    assert all("pytest" not in command for command in coverage_commands)
    assert [command[2] for command in coverage_commands] == ["coverage", "diff-cover"]


def _ruff_gate():
    return next(g for g in ROUTING_GATES if g.name == "ruff_format_check_changed")


def test_ruff_gate_passes_on_clean_changed_file() -> None:
    """A clean changed scripts/ file yields Pass (AC-002)."""
    gate = _ruff_gate()
    assert gate.mode == MODE_FAST
    result = run_gate(gate, runner=_runner_for(0), changed_files=["scripts/clean.py"])
    assert result.status == "Pass"


def test_ruff_gate_fails_on_i001_changed_file() -> None:
    """A non-zero ruff exit on a changed scripts/ file yields Fail naming the file (AC-001)."""
    gate = _ruff_gate()
    result = run_gate(gate, runner=_runner_for(1), changed_files=["scripts/bad.py"])
    assert result.status == "Fail"
    assert "bad.py" in result.detail or "exit code 1" in result.detail


def test_ruff_gate_scopes_argv_to_changed_paths() -> None:
    """The ruff argv carries the changed scripts/ paths, not a bare scripts/ directory."""
    gate = _ruff_gate()
    captured: dict[str, list[str]] = {}

    def _capture(argv: list[str], env: dict[str, str] | None):
        captured["argv"] = argv
        return subprocess.CompletedProcess(args=argv, returncode=0)

    result = run_gate(
        gate,
        runner=_capture,
        changed_files=["scripts/a.py", "scripts/sub/b.py"],
    )
    assert result.status == "Pass"
    argv = captured["argv"]
    assert "scripts/a.py" in argv
    assert "scripts/sub/b.py" in argv
    # Not a bare directory argument.
    assert "scripts/" not in argv
    # Runs via the pinned uv ruff, format then check.
    assert argv[0:3] == ["uv", "run", "ruff"]


def test_drift_still_passes_after_ruff_gate_added() -> None:
    """After the routing.md row is added, every checker is still mapped (AC-005)."""
    text = ROUTING_MD.read_text(encoding="utf-8")
    count, errors = drift_report(text)
    assert count == 0, errors
    assert any(g.checker_id == "uv" for g in ROUTING_GATES)
