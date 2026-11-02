"""tests/tools/test_amend_plan.py
Unit tests for tools/amend_plan.py over fixture Plans.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import tools.amend_plan as ap

NEW_ROW_FILE = "scripts/new_module.py"
EXISTING_FILE = "scripts/existing_helper.py"

_TARGET_HEADER = (
    "| File Path | Change Responsibility | Reason for Modification | "
    "Related Requirement / Acceptance Criterion | Repository Evidence | "
    "Related Tests | Validation Status |\n"
    "|---|---|---|---|---|---|---|\n"
)


def _plan_text(
    *,
    freeze: str = "Frozen (validated)",
    similar_path_first: bool = False,
    requirements: tuple[str, ...] = ("REQ-001", "REQ-002"),
    placeholder_work_items: bool = True,
    drop_heading: str | None = None,
) -> str:
    req_lines = "\n".join(f"- `{r}`: requirement text" for r in requirements)
    # A similar path in an unrelated earlier row must never be edited.
    earlier = (
        f"| `{NEW_ROW_FILE}.bak` | Modify | r | REQ-001 | e | t | Verified |\n"
        if similar_path_first
        else ""
    )
    work_rows = (
        "| — | — | — | — | — | — |\n"
        if placeholder_work_items
        else "| implementations/a.md | 1 | Procedure | Pending | — | — |\n"
    )
    text = (
        "## Goal\n- g\n\n"
        f"## Requirements\n{req_lines}\n\n"
        "## Implementation Target Files\n"
        f"**Freeze status**: {freeze}\n\n"
        "This table is canonical.\n\n"
        f"{_TARGET_HEADER}"
        f"{earlier}"
        "| `scripts/a.py` | Modify | reason | REQ-001 / AC-1 | ev | t | Verified |\n"
        "| `tests/test_a.py` | Modify | reason | REQ-001 / AC-1 | ev | t | Verified |\n"
        "\n## Reference Files\n"
        "| File Path | Why | Related |\n|---|---|---|\n"
        "| `scripts/ref_only.py` | read | REQ-001 |\n\n"
        "## Acceptance Criteria\n"
        "- AC-1 (`REQ-001`): works\n- AC-2 (`REQ-002`): also works\n\n"
        "## Affected areas\n"
        "| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |\n"
        "|---|---|---|---|---|---|\n"
        "| `scripts/a.py` | Modify | Low | 1 | N/A | not applicable |\n\n"
        "## Implementation steps\n"
        "1. **Phase 1: Core**\n"
        "   - [ ] do a (REQ-001; `scripts/a.py`)\n"
        "     continuation line of the checkbox\n"
        "   - [ ] do b (REQ-001; `tests/test_a.py`)\n"
        "2. **Phase 2: Docs**\n"
        "   - [ ] do c (REQ-002; `scripts/a.py`)\n\n"
        "### Release units\nN/A: no release unit\n\n"
        "## Execution Status\n\n### Execution Status\n"
        "| Step | Description | Status | Started | Completed | Notes |\n"
        "|---|---|---|---|---|---|\n| 1 | d | Pending | — | — | |\n\n"
        "### Work Items Created\n"
        "| Item ID | Related Step | Type | Status | Owner | Due Date |\n"
        "|---|---|---|---|---|---|\n"
        f"{work_rows}\n"
        "## Traceability\n"
        "- **Source issue**: issues/x.md\n"
        "- **Related target files**: `scripts/a.py`, `tests/test_a.py` — the list\n\n"
        "### Requirement Traceability\n"
        "| Requirement ID | Source | Target file | Step | AC | Test | Status |\n"
        "|---|---|---|---|---|---|---|\n"
        "| REQ-001 | s | `scripts/a.py` | 1 | AC-1 | t | Explicit in issue |\n"
    )
    if drop_heading is not None:
        text = text.replace(drop_heading + "\n", "X-removed-heading\n")
    return text


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "plans" / "done").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / EXISTING_FILE).write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(ap, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(ap, "PLANS_DIR", tmp_path / "plans")
    monkeypatch.setattr(ap, "_today", lambda: "2026-11-02")
    return tmp_path


@pytest.fixture
def fake_checks(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    calls: list[list[str]] = []

    def fake(argv: list[str]) -> tuple[int, str]:
        calls.append(argv)
        if any("check_plan_target_overlaps" in a for a in argv):
            return 0, "[cross-plan-target-overlap] other.py: unrelated.md"
        return 0, "ok"

    monkeypatch.setattr(ap, "_run_check", fake)
    return calls


def _write_plan(repo: Path, text: str, name: str = "p.md", done: bool = False) -> Path:
    path = repo / "plans" / ("done" if done else "") / name
    path.write_text(text, encoding="utf-8")
    return path


def _run(
    plan: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    file: str = EXISTING_FILE,
    responsibility: str = "Keep helper working",
    reason: str = "Calls the changed API",
    requirement: str = "REQ-001",
    evidence: str = "rg shows a caller in helper",
    step: str = "1",
    extra: list[str] | None = None,
) -> tuple[int, str]:
    argv = [
        str(plan),
        "--file",
        file,
        "--responsibility",
        responsibility,
        "--reason",
        reason,
        "--requirement",
        requirement,
        "--evidence",
        evidence,
        "--tests",
        "tests/test_helper.py",
        "--step",
        step,
        "--class",
        "fallout",
        *(extra or []),
    ]
    code = ap.main(argv)
    return code, capsys.readouterr().out


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    nxt = text.find("\n## ", start + 1)
    return text[start : nxt if nxt != -1 else len(text)]


class TestDryRun:
    def test_dry_run_prints_every_edit_and_changes_nothing(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text())
        before = plan.read_bytes()

        code, out = _run(
            plan, capsys, extra=["--dry-run", "--procedure", "implementations/n.md"]
        )

        assert code == 0
        assert plan.read_bytes() == before
        for label in (
            "Implementation Target Files: append row",
            "Freeze status: dated amendment line",
            "Requirement Traceability: append row",
            "Related target files",
            "Affected areas: append row",
            "Implementation steps: step 1 checkbox",
            "Work Items Created",
        ):
            assert label in out
        assert "nothing written" in out
        assert fake_checks == []

    def test_real_run_announces_nothing_and_prints_check_results(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text())

        code, out = _run(plan, capsys)

        assert code == 0
        assert len(fake_checks) == 3
        for name in (
            "check_workitem_structure",
            "audit_plan_target_paths",
            "check_plan_target_overlaps",
        ):
            assert f"[{name}] exit 0" in out
        assert "no overlap finding names plans/p.md" in out


class TestAppendOnly:
    def test_new_row_is_appended_after_the_last_row(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text())

        _run(plan, capsys)

        rows = [
            ln
            for ln in _section(
                plan.read_text(), "## Implementation Target Files"
            ).splitlines()
            if ln.startswith("| `")
        ]
        assert [r.split("|")[1].strip(" `") for r in rows] == [
            "scripts/a.py",
            "tests/test_a.py",
            EXISTING_FILE,
        ]
        assert rows[-1].rstrip().endswith("| Verified |")


class TestRefusals:
    def test_file_already_a_target_row(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text())
        before = plan.read_bytes()

        code, out = _run(plan, capsys, file="scripts/a.py")

        assert code == 1
        assert "already an Implementation Target Files row" in out
        assert plan.read_bytes() == before

    def test_file_already_a_reference_row(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text())
        before = plan.read_bytes()

        code, out = _run(plan, capsys, file="scripts/ref_only.py")

        assert code == 1
        assert "Reference Files row" in out
        assert plan.read_bytes() == before

    def test_archived_plan_is_refused(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text(), done=True)
        before = plan.read_bytes()

        code, out = _run(plan, capsys)

        assert code == 1
        assert "archived Plan" in out
        assert plan.read_bytes() == before

    def test_plan_outside_plans_is_refused(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        outside = repo / "elsewhere.md"
        outside.write_text(_plan_text(), encoding="utf-8")

        code, out = _run(outside, capsys)

        assert code == 1
        assert "directly under plans/" in out

    def test_plan_missing_a_required_section(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text(drop_heading="## Affected areas"))
        before = plan.read_bytes()

        code, out = _run(plan, capsys)

        assert code == 1
        assert "## Affected areas" in out
        assert plan.read_bytes() == before

    def test_duplicate_amendment_line(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        text = _plan_text().replace(
            "\nThis table is canonical.",
            f"\nAmended 2026-10-01 (fallout): added {EXISTING_FILE} — earlier\n"
            "\nThis table is canonical.",
        )
        plan = _write_plan(repo, text)
        before = plan.read_bytes()

        code, out = _run(plan, capsys)

        assert code == 1
        assert "amendment line" in out
        assert plan.read_bytes() == before

    @pytest.mark.parametrize("bad", ["scripts/", "scripts/*.py", "/abs/x.py", ""])
    def test_not_a_single_file_path(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
        bad: str,
    ) -> None:
        plan = _write_plan(repo, _plan_text())

        code, out = _run(plan, capsys, file=bad)

        assert code == 1
        assert "exact repository-relative file path" in out

    def test_unknown_step_is_refused(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text())
        before = plan.read_bytes()

        code, out = _run(plan, capsys, step="9")

        assert code == 1
        assert "step 9 not found" in out
        assert plan.read_bytes() == before


class TestEditLocations:
    def _amend(
        self, repo: Path, capsys: pytest.CaptureFixture[str], step: str = "1"
    ) -> str:
        plan = _write_plan(repo, _plan_text())
        _run(plan, capsys, step=step)
        return plan.read_text()

    def test_freeze_note_line_added_and_token_unchanged(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        text = self._amend(repo, capsys)

        section = _section(text, "## Implementation Target Files")
        assert "**Freeze status**: Frozen (validated)" in section
        assert (
            f"Amended 2026-11-02 (fallout): added {EXISTING_FILE} — Calls the changed API"
            in section
        )

    def test_requirement_traceability_row(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        text = self._amend(repo, capsys)

        last = text.rstrip().splitlines()[-1]
        assert last.startswith(
            "| REQ-001 | Amendment 2026-11-02: Calls the changed API"
        )
        assert EXISTING_FILE in last
        assert "Phase 1" in last
        assert last.endswith("| Confirmed by repository evidence |")

    def test_related_target_files_line_keeps_suffix(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        text = self._amend(repo, capsys)

        assert (
            f"- **Related target files**: `scripts/a.py`, `tests/test_a.py`, "
            f"`{EXISTING_FILE}` — the list" in text
        )

    def test_affected_areas_row(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        text = self._amend(repo, capsys)

        section = _section(text, "## Affected areas")
        assert f"| `{EXISTING_FILE}` | Modify |" in section

    def test_step_checkbox_after_last_checkbox_of_named_step_only(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        text = self._amend(repo, capsys, step="1")

        steps = _section(text, "## Implementation steps").splitlines()
        added = [i for i, ln in enumerate(steps) if EXISTING_FILE in ln]
        assert len(added) == 1
        assert steps[added[0]].startswith("   - [ ] Keep helper working")
        assert steps[added[0] - 1].startswith("   - [ ] do b")
        assert steps[added[0] + 1].startswith("2. **Phase 2")

    def test_work_items_row_replaces_placeholder(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text())
        _run(plan, capsys, extra=["--procedure", "implementations/n.md"])

        section = _section(plan.read_text(), "### Work Items Created")
        assert "| implementations/n.md | 1 | Procedure | Pending | — | — |" in section
        assert "| — | — | — | — | — | — |" not in section

    def test_work_items_row_appended_after_existing_row(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text(placeholder_work_items=False))
        _run(plan, capsys, extra=["--procedure", "implementations/n.md"])

        rows = [
            ln
            for ln in _section(plan.read_text(), "### Work Items Created").splitlines()
            if ln.startswith("| implementations")
        ]
        assert [r.split("|")[1].strip() for r in rows] == [
            "implementations/a.md",
            "implementations/n.md",
        ]

    def test_work_items_skipped_without_procedure(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text())

        _code, out = _run(plan, capsys)

        assert "Work Items Created: skipped" in out
        assert "| — | — | — | — | — | — |" in plan.read_text()

    def test_similar_path_earlier_in_file_is_not_touched(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        before = _plan_text(similar_path_first=True)
        plan = _write_plan(repo, before)

        _run(plan, capsys, file=NEW_ROW_FILE, responsibility="New file: module")

        text = plan.read_text()
        assert (
            f"| `{NEW_ROW_FILE}.bak` | Modify | r | REQ-001 | e | t | Verified |"
            in text
        )
        assert text.count(f"`{NEW_ROW_FILE}`") >= 3
        rows = [
            ln
            for ln in _section(text, "## Implementation Target Files").splitlines()
            if ln.startswith("| `")
        ]
        assert rows[0].startswith(f"| `{NEW_ROW_FILE}.bak`")
        assert rows[-1].startswith(f"| `{NEW_ROW_FILE}` |")


class TestFreezeCriteria:
    def test_all_criteria_pass_keeps_frozen_and_verified(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text())

        _code, out = _run(plan, capsys)

        text = plan.read_text()
        assert "**Freeze status**: Frozen" in text
        assert "Freeze re-check: passed" in out
        assert "| Needs confirmation |" not in text

    def test_declared_new_file_with_existing_directory_passes(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text())

        _run(plan, capsys, file=NEW_ROW_FILE, responsibility="New file: module")

        text = plan.read_text()
        assert "**Freeze status**: Frozen" in text
        row = next(
            ln for ln in text.splitlines() if ln.startswith(f"| `{NEW_ROW_FILE}`")
        )
        assert row.split("|")[2].strip().startswith("New file:")
        assert row.rstrip().endswith("| Verified |")

    def test_new_file_declared_only_in_reason_prefixes_the_responsibility_cell(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text())

        _run(plan, capsys, file=NEW_ROW_FILE, reason="New file; needed")

        row = next(
            ln
            for ln in plan.read_text().splitlines()
            if ln.startswith(f"| `{NEW_ROW_FILE}`")
        )
        assert row.split("|")[2].strip().startswith("New file: ")

    @pytest.mark.parametrize(
        ("kwargs", "needle"),
        [
            ({"file": "scripts/missing.py"}, "exists:"),
            (
                {"file": "nodir/new.py", "responsibility": "New file: x"},
                "containing directory",
            ),
            ({"reason": "  "}, "requires modification"),
            ({"evidence": ""}, "supporting evidence"),
            ({"requirement": "REQ-099"}, "REQ-099 is not defined"),
        ],
    )
    def test_each_failing_criterion_sets_draft_and_names_it(
        self,
        repo: Path,
        fake_checks: list[list[str]],
        capsys: pytest.CaptureFixture[str],
        kwargs: dict[str, Any],
        needle: str,
    ) -> None:
        plan = _write_plan(repo, _plan_text())

        code, out = _run(plan, capsys, **kwargs)

        text = plan.read_text()
        assert code == 0
        assert "**Freeze status**: Draft (validated)" in text
        assert (
            "Frozen"
            not in _section(text, "## Implementation Target Files").splitlines()[1]
        )
        assert "| Needs confirmation |" in text
        assert "Freeze re-check: FAILED" in out
        assert needle in out
        assert needle in text


class TestRealChecks:
    def test_real_audit_output_is_printed_and_failure_sets_exit(
        self,
        repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plan = _write_plan(repo, _plan_text())
        monkeypatch.setattr(
            ap,
            "_planned_checks",
            lambda p: [
                (
                    "audit_plan_target_paths",
                    [str(ap.TOOLS_DIR / "audit_plan_target_paths.py"), str(p)],
                )
            ],
        )

        code, out = _run(plan, capsys, file="scripts/missing.py")

        assert code == 1
        assert "[audit_plan_target_paths] exit 1" in out
        assert "missing target path: scripts/missing.py" in out
