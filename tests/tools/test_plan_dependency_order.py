"""tests/tools/test_plan_dependency_order.py
Tests for tools/plan_dependency_order.py.
"""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

import orjson
import pytest

import tools.plan_dependency_order as pdo

PLAN_A = "plans/20261101-000001_a_plan.md"
PLAN_B = "plans/20261101-000002_b_plan.md"
PLAN_C = "plans/20261101-000003_c_plan.md"
PLAN_D = "plans/20261101-000004_d_plan.md"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _plan_text(
    scope_lines: list[str],
    targets: list[str] | None = None,
    status_rows: list[tuple[str, str]] | None = None,
) -> str:
    rows = "\n".join(
        f"| {path} | Modify | reason | REQ-001 | evidence | tests | Verified |"
        for path in targets or []
    )
    status = "\n".join(
        f"| {step} | step {step} | {state} | — | — | |"
        for step, state in status_rows or []
    )
    return (
        "# Sample Plan\n\n"
        "## Scope\n"
        "- **In-Scope**:\n  - something\n"
        + "\n".join(scope_lines)
        + "\n\n## Implementation Target Files\n"
        "**Freeze status**: Frozen\n\n"
        "| File Path | Change Responsibility | Reason for Modification | "
        "Related Requirement / Acceptance Criterion | Repository Evidence | "
        "Related Tests | Validation Status |\n"
        "|---|---|---|---|---|---|---|\n"
        f"{rows}\n\n"
        "## Execution Status\n\n"
        "### Execution Status\n"
        "| Step | Description | Status | Started | Completed | Notes |\n"
        "|------|-------------|--------|---------|-----------|-------|\n"
        f"{status}\n\n"
        "### Blocker Log\n"
    )


def _plan(
    root: Path,
    rel: str,
    scope_lines: list[str] | None = None,
    targets: list[str] | None = None,
    status_rows: list[tuple[str, str]] | None = None,
) -> None:
    _write(root / rel, _plan_text(scope_lines or [], targets, status_rows))


def _depends(path: str, phase: str = "all", reason: str = "needs it") -> str:
    return f"- **Depends on**: {path} | phase {phase} | {reason}"


def _readiness(root: Path, rel: str) -> pdo.Readiness:
    nodes, _ = pdo.load_plans(root)
    plans = {node.path: node for node in nodes}
    return pdo.readiness(plans[rel], root, plans)


class TestParseDependencies:
    def test_structured_line_yields_path_phase_reason_without_warning(self) -> None:
        text = _plan_text([_depends("plans/x.md", "3", "schema first")])
        deps, warnings = pdo.parse_dependencies(text)
        assert deps == [pdo.Dependency("plans/x.md", 3, "schema first", True)]
        assert warnings == []

    def test_nested_structured_line_under_dependencies_is_read(self) -> None:
        text = _plan_text(
            [
                "- **Dependencies**: see below",
                "  " + _depends("plans/x.md", "2", "nested"),
            ]
        )
        deps, warnings = pdo.parse_dependencies(text)
        assert deps == [pdo.Dependency("plans/x.md", 2, "nested", True)]
        assert warnings == []

    def test_phase_all_stays_a_string(self) -> None:
        deps, _ = pdo.parse_dependencies(_plan_text([_depends("issues/x.md")]))
        assert deps[0].phase == "all"

    def test_na_none_yields_nothing(self) -> None:
        text = _plan_text(["- **Dependencies**: `N/A: none`"])
        assert pdo.parse_dependencies(text) == ([], [])

    def test_prose_fallback_reads_paths_with_warning(self) -> None:
        text = _plan_text(
            [
                "- **Dependencies**: Implement after `plans/x.md` and "
                "`issues/y.md`; again plans/x.md.",
                "- **Other**: text",
            ]
        )
        deps, warnings = pdo.parse_dependencies(text)
        assert [d.path for d in deps] == ["plans/x.md", "issues/y.md"]
        assert all(d.phase == "all" and not d.declared for d in deps)
        assert warnings == [
            "prose-dependency: plans/x.md",
            "prose-dependency: issues/y.md",
        ]

    def test_prose_fallback_reads_continuation_lines(self) -> None:
        text = _plan_text(["- **Dependencies**:", "  - see `issues/z.md`"])
        deps, _ = pdo.parse_dependencies(text)
        assert [d.path for d in deps] == ["issues/z.md"]

    def test_structured_line_wins_over_prose(self) -> None:
        text = _plan_text(
            [
                "- **Dependencies**: also `plans/prose.md`",
                _depends("plans/x.md", "1"),
            ]
        )
        deps, warnings = pdo.parse_dependencies(text)
        assert [d.path for d in deps] == ["plans/x.md"]
        assert warnings == []

    def test_no_scope_section(self) -> None:
        assert pdo.parse_dependencies("# Plan\n\n## Goal\n- x\n") == ([], [])


class TestReadiness:
    def test_open_issue_gates_and_names_the_path(self, tmp_path: Path) -> None:
        _write(tmp_path / "issues/i.md", "issue")
        _plan(tmp_path, PLAN_A, [_depends("issues/i.md")])
        result = _readiness(tmp_path, PLAN_A)
        assert (result.status, result.label) == ("gated", "gated")
        assert result.blocking == ["issues/i.md phase all"]

    def test_closed_issue_is_ready(self, tmp_path: Path) -> None:
        _write(tmp_path / "issues/done/i.md", "issue")
        _plan(tmp_path, PLAN_A, [_depends("issues/i.md")])
        assert _readiness(tmp_path, PLAN_A).status == "ready"

    @pytest.mark.parametrize(
        ("row_status", "expected"),
        [("Pending", "gated"), ("In Progress", "gated"), ("Completed", "ready")],
    )
    def test_open_plan_phase_row(
        self, tmp_path: Path, row_status: str, expected: str
    ) -> None:
        _plan(tmp_path, PLAN_A, [], status_rows=[("1", "Completed"), ("2", row_status)])
        _plan(tmp_path, PLAN_B, [_depends(PLAN_A, "2")])
        result = _readiness(tmp_path, PLAN_B)
        assert result.status == expected
        if expected == "gated":
            assert result.blocking == [f"{PLAN_A} phase 2"]

    def test_open_plan_phase_all_gates(self, tmp_path: Path) -> None:
        _plan(tmp_path, PLAN_A, [], status_rows=[("1", "Completed")])
        _plan(tmp_path, PLAN_B, [_depends(PLAN_A)])
        assert _readiness(tmp_path, PLAN_B).status == "gated"

    def test_plan_in_done_is_ready(self, tmp_path: Path) -> None:
        _plan(tmp_path, "plans/done/20261101-000001_a_plan.md")
        _plan(tmp_path, PLAN_B, [_depends(PLAN_A)])
        assert _readiness(tmp_path, PLAN_B).status == "ready"

    def test_missing_path_needs_confirmation_and_does_not_gate(
        self, tmp_path: Path
    ) -> None:
        _plan(tmp_path, PLAN_A, [_depends("plans/ghost.md", "2")])
        result = _readiness(tmp_path, PLAN_A)
        assert result.status == "ready"
        assert len(result.confirmations) == 1
        assert result.confirmations[0].startswith(
            "Needs confirmation: plans/ghost.md phase 2"
        )

    def test_unmatched_phase_row_needs_confirmation(self, tmp_path: Path) -> None:
        _plan(tmp_path, PLAN_A, [], status_rows=[("1", "Pending")])
        _plan(tmp_path, PLAN_B, [_depends(PLAN_A, "9")])
        result = _readiness(tmp_path, PLAN_B)
        assert result.status == "ready"
        assert "no Execution Status row 9" in result.confirmations[0]

    def test_path_escaping_the_root_is_not_read(self, tmp_path: Path) -> None:
        outside = tmp_path / "outside.md"
        _write(outside, "secret")
        root = tmp_path / "repo"
        _plan(root, PLAN_A, [_depends("plans/../../outside.md")])
        result = _readiness(root, PLAN_A)
        assert result.status == "ready"
        assert "outside plans/ and issues/" in result.confirmations[0]

    def test_path_outside_plans_and_issues_is_not_read(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs/x.md", "doc")
        _plan(tmp_path, PLAN_A, [_depends("docs/x.md")])
        assert (
            "outside plans/ and issues/"
            in _readiness(tmp_path, PLAN_A).confirmations[0]
        )

    def test_prose_dependency_is_labelled_gated_prose(self, tmp_path: Path) -> None:
        _write(tmp_path / "issues/i.md", "issue")
        _plan(tmp_path, PLAN_A, ["- **Dependencies**: after `issues/i.md`"])
        result = _readiness(tmp_path, PLAN_A)
        assert (result.status, result.label) == ("gated", "gated (prose)")

    def test_declared_open_dependency_beats_prose_label(self, tmp_path: Path) -> None:
        _write(tmp_path / "issues/i.md", "issue")
        _plan(tmp_path, PLAN_A, [_depends("issues/i.md")])
        assert _readiness(tmp_path, PLAN_A).label == "gated"


class TestOrderAndCycles:
    def test_chain_is_ordered_dependency_first(self, tmp_path: Path) -> None:
        _plan(tmp_path, PLAN_A, [_depends(PLAN_B)])
        _plan(tmp_path, PLAN_B, [_depends(PLAN_C)])
        _plan(tmp_path, PLAN_C)
        nodes, _ = pdo.load_plans(tmp_path)
        order, cyclic = pdo.recommended_order(nodes)
        assert order == [PLAN_C, PLAN_B, PLAN_A]
        assert cyclic == []

    def test_independent_plans_follow_filename_timestamp(self, tmp_path: Path) -> None:
        for rel in (PLAN_C, PLAN_A, PLAN_B):
            _plan(tmp_path, rel)
        nodes, _ = pdo.load_plans(tmp_path)
        assert pdo.recommended_order(nodes)[0] == [PLAN_A, PLAN_B, PLAN_C]

    def test_unrelated_plan_keeps_timestamp_position(self, tmp_path: Path) -> None:
        _plan(tmp_path, PLAN_A, [_depends(PLAN_C)])
        _plan(tmp_path, PLAN_B)
        _plan(tmp_path, PLAN_C)
        nodes, _ = pdo.load_plans(tmp_path)
        assert pdo.recommended_order(nodes)[0] == [PLAN_B, PLAN_C, PLAN_A]

    def test_two_plan_cycle_reported_with_path(self, tmp_path: Path) -> None:
        _plan(tmp_path, PLAN_A, [_depends(PLAN_B)])
        _plan(tmp_path, PLAN_B, [_depends(PLAN_A)])
        nodes, _ = pdo.load_plans(tmp_path)
        assert pdo.find_cycles(nodes) == [[PLAN_A, PLAN_B, PLAN_A]]
        order, cyclic = pdo.recommended_order(nodes)
        assert order == [PLAN_A, PLAN_B]
        assert cyclic == [PLAN_A, PLAN_B]

    def test_three_plan_loop_reported_once(self, tmp_path: Path) -> None:
        _plan(tmp_path, PLAN_A, [_depends(PLAN_B)])
        _plan(tmp_path, PLAN_B, [_depends(PLAN_C)])
        _plan(tmp_path, PLAN_C, [_depends(PLAN_A)])
        _plan(tmp_path, PLAN_D)
        nodes, _ = pdo.load_plans(tmp_path)
        cycles = pdo.find_cycles(nodes)
        assert len(cycles) == 1
        assert set(cycles[0]) == {PLAN_A, PLAN_B, PLAN_C}
        assert cycles[0][0] == cycles[0][-1]
        assert pdo.recommended_order(nodes)[0][0] == PLAN_D

    def test_self_dependency_is_ignored(self, tmp_path: Path) -> None:
        _plan(tmp_path, PLAN_A, [_depends(PLAN_A)])
        nodes, _ = pdo.load_plans(tmp_path)
        assert pdo.find_cycles(nodes) == []

    def test_shared_target_is_an_overlap_note_and_no_edge(self, tmp_path: Path) -> None:
        _plan(tmp_path, PLAN_A, targets=["tools/x.py"])
        _plan(tmp_path, PLAN_B, targets=["tools/x.py"])
        nodes, _ = pdo.load_plans(tmp_path)
        overlaps = pdo.find_overlaps(nodes)
        assert [o["file"] for o in overlaps] == ["tools/x.py"]
        assert PLAN_A in overlaps[0]["detail"]
        assert PLAN_B in overlaps[0]["detail"]
        assert pdo.recommended_order(nodes)[0] == [PLAN_A, PLAN_B]
        assert all(
            _readiness(tmp_path, rel).status == "ready" for rel in (PLAN_A, PLAN_B)
        )

    def test_plans_done_are_not_open_plans(self, tmp_path: Path) -> None:
        _plan(tmp_path, PLAN_A)
        _plan(tmp_path, "plans/done/20261101-000009_z_plan.md")
        nodes, _ = pdo.load_plans(tmp_path)
        assert [n.path for n in nodes] == [PLAN_A]


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        digest.update(str(path.relative_to(root)).encode())
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


class TestMain:
    def _repo(self, root: Path) -> None:
        _write(root / "issues/i.md", "issue")
        _plan(root, PLAN_A, [_depends("issues/i.md", "all", "needs i")])
        _plan(root, PLAN_B, ["- **Dependencies**: after `plans/missing.md`"])

    def test_text_report_is_read_only_and_states_owner_decides(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        self._repo(tmp_path)
        before = _tree_hash(tmp_path)
        assert pdo.main(["--root", str(tmp_path)]) == 0
        out = capsys.readouterr().out
        assert _tree_hash(tmp_path) == before
        assert "The owner decides the order" in out
        assert f"{PLAN_A}: gated, blocked by issues/i.md phase all" in out
        assert "Needs confirmation" in out
        assert f"{PLAN_B}: prose-dependency: plans/missing.md" in out

    def test_cycle_still_exits_zero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _plan(tmp_path, PLAN_A, [_depends(PLAN_B)])
        _plan(tmp_path, PLAN_B, [_depends(PLAN_A)])
        assert pdo.main(["--root", str(tmp_path)]) == 0
        assert f"cycle: {PLAN_A} -> {PLAN_B} -> {PLAN_A}" in capsys.readouterr().out

    def test_json_output_parses(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        self._repo(tmp_path)
        assert pdo.main(["--root", str(tmp_path), "--format", "json"]) == 0
        data = orjson.loads(capsys.readouterr().out)
        statuses = {r["plan"]: r["status"] for r in data["results"]}
        assert statuses == {PLAN_A: "gated", PLAN_B: "ready"}
        assert data["order"] == [PLAN_A, PLAN_B]

    def test_plan_option_limits_the_report(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        self._repo(tmp_path)
        assert pdo.main(["--root", str(tmp_path), "--plan", PLAN_B]) == 0
        out = capsys.readouterr().out
        assert "Gated:\n  (none)" in out
        assert f"{PLAN_A}: gated" not in out

    def test_plan_option_accepts_an_archived_plan(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        self._repo(tmp_path)
        archived = "plans/done/20261101-000009_z_plan.md"
        _plan(tmp_path, archived, [_depends("issues/i.md")])
        assert pdo.main(["--root", str(tmp_path), "--plan", archived]) == 0
        out = capsys.readouterr().out
        assert f"{archived}: gated, blocked by issues/i.md phase all" in out
        assert f"{PLAN_A}: gated" not in out

    def test_missing_plan_path_returns_one(self, tmp_path: Path) -> None:
        self._repo(tmp_path)
        assert pdo.main(["--root", str(tmp_path), "--plan", "plans/nope.md"]) == 1

    def test_unreadable_plans_directory_returns_one(self, tmp_path: Path) -> None:
        assert pdo.main(["--root", str(tmp_path)]) == 1


def _procedure(root: Path, rel: str, source_plan: str, status: str) -> None:
    """Write a done procedure under `rel` naming `source_plan` as its
    `**Source plan**` with a single `### Execution Status` row in `status`."""
    body = (
        "# Procedure\n\n"
        "## Traceability\n"
        f"- **Source plan**: `{source_plan}`\n\n"
        "## Execution Status\n\n"
        "### Execution Status\n"
        "| Step | Description | Status | Started | Completed | Notes |\n"
        "|------|-------------|--------|---------|-----------|-------|\n"
        f"| 1 | step 1 | {status} | — | — | |\n"
    )
    _write(root / rel, body)


class TestIncompleteProcedures:
    def test_uncompleted_procedure_is_flagged_non_blocking(
        self, tmp_path: Path
    ) -> None:
        _plan(tmp_path, PLAN_A)
        _procedure(tmp_path, "implementations/done/20261107_x.md", PLAN_A, "Pending")
        report = pdo.build_report(tmp_path)
        assert report.incomplete == [PLAN_A]
        text = pdo.render_text(report)
        assert "Incomplete procedures (non-blocking):" in text
        assert PLAN_A in text

    def test_json_reports_incomplete(self, tmp_path: Path) -> None:
        _plan(tmp_path, PLAN_A)
        _procedure(
            tmp_path, "implementations/done/20261107_x.md", PLAN_A, "In Progress"
        )
        data = orjson.loads(pdo.render_json(pdo.build_report(tmp_path)))
        assert data["incomplete"] == [PLAN_A]

    def test_ready_gated_unchanged_with_uncompleted_procedure(
        self, tmp_path: Path
    ) -> None:
        # Regression guard (REQ-003): a leaked uncompleted procedure must not
        # change the dependency-driven ready/gated classification.
        _plan(tmp_path, PLAN_A, [], status_rows=[("1", "Completed")])
        _plan(tmp_path, PLAN_B, [_depends(PLAN_A)])
        before = {r.plan: r.status for r in pdo.build_report(tmp_path).results}
        _procedure(tmp_path, "implementations/done/20261107_x.md", PLAN_A, "Blocked")
        after = {r.plan: r.status for r in pdo.build_report(tmp_path).results}
        assert before == after == {PLAN_A: "ready", PLAN_B: "gated"}

    def test_completed_procedure_is_not_flagged(self, tmp_path: Path) -> None:
        _plan(tmp_path, PLAN_A)
        _procedure(tmp_path, "implementations/done/20261107_x.md", PLAN_A, "Completed")
        assert pdo.build_report(tmp_path).incomplete == []

    def test_old_procedure_outside_window_is_not_flagged(self, tmp_path: Path) -> None:
        _plan(tmp_path, PLAN_A)
        rel = "implementations/done/20260101_old.md"
        _procedure(tmp_path, rel, PLAN_A, "Pending")
        old = time.time() - 30 * 86_400
        os.utime(tmp_path / rel, (old, old))
        assert pdo.build_report(tmp_path).incomplete == []

    def test_missing_done_directory_yields_empty(self, tmp_path: Path) -> None:
        _plan(tmp_path, PLAN_A)
        assert pdo.build_report(tmp_path).incomplete == []
