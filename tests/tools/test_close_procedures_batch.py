"""tests/tools/test_close_procedures_batch.py
Tests for tools/close_procedures_batch.py.
"""

from __future__ import annotations

from pathlib import Path

import git
import pytest

from tools import close_procedures_batch as cpb
from tools.close_procedures_batch import (
    PlanStep,
    check_step_marking,
    main,
    parse_plan_steps,
    parse_related_targets,
    parse_source_plan,
    parse_target_paths,
    update_work_items,
    verify_procedure,
)
from tools.manage_workitem_stage import MoveResult

PLAN_NAME = "20260101-000000_plan_x.md"
PLAN_REL = f"plans/done/{PLAN_NAME}"
PROC_A = "implementations/20260101-000001_01_tools_a.py.md"
PROC_B = "implementations/20260101-000001_02_tools_b.py.md"
PROC_C = "implementations/20260101-000001_03_tools_c.py.md"


def procedure_text(
    rows: list[tuple[str, str]],
    *,
    related: str = "tools/a.py",
    source_plan: str = f"plans/{PLAN_NAME}",
) -> str:
    """Build a procedure with one Execution Status row per (status, notes) pair."""
    body = "\n".join(
        f"| {i} | Do part {i} | {status} | — | — | {notes} |"
        for i, (status, notes) in enumerate(rows, start=1)
    )
    return (
        "## Goal\n- fixture\n\n## Execution Status\n\n### Execution Status\n"
        "| Step | Description | Status | Started | Completed | Notes |\n"
        "|------|-------------|--------|---------|-----------|-------|\n"
        f"{body}\n\n### Blocker Log\n| Step | Blocker Description |\n|---|---|\n"
        "| — | — |\n\n## Traceability\n"
        f"- **Source plan**: {source_plan}\n"
        f"- **Related target files**: {related}\n"
    )


def plan_text(
    *,
    steps: list[tuple[str, list[str]]],
    items: list[str],
    targets: list[str],
    step_statuses: list[str] | None = None,
) -> str:
    """Build a Plan with targets, numbered steps, status rows, and work item rows."""
    target_rows = "\n".join(f"| `{t}` | change |" for t in targets)
    step_lines = "\n".join(
        f"{i}. **{title}**\n"
        + "\n".join(f"   - [ ] edit (`REQ-001`; `{path}`)" for path in cited)
        for i, (title, cited) in enumerate(steps, start=1)
    )
    statuses = step_statuses or ["Pending"] * len(steps)
    status_rows = "\n".join(
        f"| {i} | {steps[i - 1][0]} | {status} | — | — | |"
        for i, status in enumerate(statuses, start=1)
    )
    item_rows = "\n".join(f"| `{p}` | 1 | Procedure | Pending | — | — |" for p in items)
    return (
        "## Goal\n- fixture\n\n## Implementation Target Files\n"
        "| File Path | Change |\n|---|---|\n"
        f"{target_rows}\n\n## Implementation steps\n{step_lines}\n\n"
        "## Execution Status\n\n### Execution Status\n"
        "| Step | Description | Status | Started | Completed | Notes |\n"
        "|------|-------------|--------|---------|-----------|-------|\n"
        f"{status_rows}\n\n### Work Items Created\n"
        "| Item ID | Related Step | Type | Status | Owner | Due Date |\n"
        "|---------|--------------|------|--------|-------|----------|\n"
        f"{item_rows}\n\n## Traceability\n- **Related target files**: x\n"
    )


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A throwaway git repository that is also the working directory."""
    git.Repo.init(tmp_path)
    for name in ("plans/done", "implementations/done"):
        (tmp_path / name).mkdir(parents=True)
        (tmp_path / name / ".gitkeep").write_text("")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def write(repo: Path, rel: str, text: str) -> None:
    (repo / rel).write_text(text, encoding="utf-8")


def commit_all(repo: Path) -> str:
    handle = git.Repo(repo)
    handle.git.add("-A")
    handle.git.commit("-m", "fixture", "--no-verify")
    return handle.head.commit.hexsha


def standard_plan() -> str:
    return plan_text(
        steps=[("Build", ["tools/a.py", "tools/b.py"]), ("Check", ["tools/a.py"])],
        items=[PROC_A, PROC_B],
        targets=["tools/a.py", "tools/b.py"],
    )


def setup_batch(repo: Path, *, a: list[tuple[str, str]], b: list[tuple[str, str]]):
    write(repo, PLAN_REL, standard_plan())
    write(repo, PROC_A, procedure_text(a, related="tools/a.py"))
    write(repo, PROC_B, procedure_text(b, related="tools/b.py"))
    return commit_all(repo)


DONE = [("Completed", "")]


def status_lines(repo: Path, rel: str) -> list[str]:
    return [
        line
        for line in (repo / rel).read_text().splitlines()
        if line.startswith("| ") and "Do part" in line
    ]


class TestParsing:
    def test_related_targets_comma_list_with_backticks(self) -> None:
        text = "- **Related target files**: `tools/a.py`, tests/test_a.py\n"
        assert parse_related_targets(text) == ["tools/a.py", "tests/test_a.py"]

    def test_related_targets_drops_trailer_and_na(self) -> None:
        text = "- **Related target files**: tools/a.py — the full list\n"
        assert parse_related_targets(text) == ["tools/a.py"]
        assert parse_related_targets("- **Related target files**: N/A\n") == []

    def test_source_plan(self) -> None:
        assert parse_source_plan("- **Source plan**: plans/x.md\n") == "plans/x.md"
        assert parse_source_plan("- **Source plan**: N/A: none\n") is None
        assert parse_source_plan("nothing here") is None

    def test_plan_steps_cite_only_target_paths(self) -> None:
        text = plan_text(
            steps=[("One", ["tools/a.py"]), ("Two", [])],
            items=[],
            targets=["tools/a.py"],
        )
        steps = parse_plan_steps(text, parse_target_paths(text))
        assert [s.number for s in steps] == [1, 2]
        assert steps[0].cited == ("tools/a.py",)
        assert steps[1].cited == ()

    def test_check_step_marking(self) -> None:
        step = PlanStep(1, "s", ("tools/a.py", "tools/b.py"))
        assert check_step_marking(step, {"tools/a.py", "tools/b.py"}) is None
        assert "tools/b.py" in (check_step_marking(step, {"tools/a.py"}) or "")
        assert check_step_marking(PlanStep(2, "s", ()), set()) is not None


class TestVerifyRefusals:
    def test_pending_row_refused_and_named(self, repo: Path) -> None:
        setup_batch(repo, a=[("Completed", ""), ("Pending", "")], b=DONE)
        check = verify_procedure(
            Path(PROC_A), complete_rows=False, plan_path=Path(PLAN_REL)
        )
        assert check.refusal is not None
        assert "Step 2 is Pending" in check.refusal

    @pytest.mark.parametrize("status", ["Blocked", "In Progress"])
    def test_blocked_and_in_progress_refused(self, repo: Path, status: str) -> None:
        setup_batch(repo, a=[(status, "")], b=DONE)
        for complete_rows in (False, True):
            check = verify_procedure(
                Path(PROC_A), complete_rows=complete_rows, plan_path=Path(PLAN_REL)
            )
            assert check.refusal is not None
            assert f"Step 1 is {status}" in check.refusal

    def test_na_row_accepted(self, repo: Path) -> None:
        setup_batch(repo, a=[("Completed", ""), ("N/A", "")], b=DONE)
        check = verify_procedure(
            Path(PROC_A), complete_rows=False, plan_path=Path(PLAN_REL)
        )
        assert check.refusal is None

    def test_destination_exists_refused(self, repo: Path) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        write(repo, PROC_A.replace("implementations/", "implementations/done/"), "x")
        check = verify_procedure(
            Path(PROC_A), complete_rows=False, plan_path=Path(PLAN_REL)
        )
        assert check.refusal is not None
        assert "destination exists" in check.refusal

    def test_plan_not_found_refused(self, repo: Path) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        check = verify_procedure(Path(PROC_A), complete_rows=False, plan_path=None)
        assert check.refusal == "Plan not found"

    def test_gated_pending_row_refused_with_complete_rows(self, repo: Path) -> None:
        setup_batch(repo, a=[("Pending", "Gated: plans/x.md phase 1 - wait")], b=DONE)
        check = verify_procedure(
            Path(PROC_A), complete_rows=True, plan_path=Path(PLAN_REL)
        )
        assert check.refusal is not None
        assert "Gated" in check.refusal

    def test_path_outside_implementations_refused(self, repo: Path) -> None:
        write(repo, "elsewhere.md", procedure_text(DONE))
        check = verify_procedure(
            Path("elsewhere.md"), complete_rows=False, plan_path=Path(PLAN_REL)
        )
        assert check.refusal is not None
        assert "not a file directly under" in check.refusal

    def test_missing_table_refused(self, repo: Path) -> None:
        write(repo, PROC_A, "## Goal\n- no table\n")
        check = verify_procedure(
            Path(PROC_A), complete_rows=False, plan_path=Path(PLAN_REL)
        )
        assert check.refusal is not None
        assert "Execution Status table" in check.refusal


class TestMainRefusals:
    def test_refused_procedure_changes_no_file(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        commit = setup_batch(repo, a=[("Pending", "")], b=DONE)
        before = {rel: (repo / rel).read_bytes() for rel in (PROC_A, PLAN_REL)}
        code = main([PROC_A])
        out = capsys.readouterr().out
        assert code == 1
        assert f"refused {PROC_A}: Step 1 is Pending" in out
        assert {rel: (repo / rel).read_bytes() for rel in before} == before
        assert (repo / PROC_A).is_file()
        assert git.Repo(repo).head.commit.hexsha == commit

    def test_plan_not_found_changes_nothing(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        write(repo, PROC_A, procedure_text(DONE, source_plan="plans/missing.md"))
        commit_all(repo)
        code = main([PROC_A])
        assert code == 1
        assert "Plan not found" in capsys.readouterr().out
        assert (repo / PROC_A).is_file()

    def test_complete_rows_requires_note(self, repo: Path) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        with pytest.raises(SystemExit) as exc:
            main([PROC_A, "--complete-rows"])
        assert exc.value.code == 2

    def test_note_without_complete_rows_is_usage_error(self, repo: Path) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        with pytest.raises(SystemExit) as exc:
            main([PROC_A, "--note", "why"])
        assert exc.value.code == 2

    def test_note_with_pipe_rejected(self, repo: Path) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        with pytest.raises(SystemExit) as exc:
            main([PROC_A, "--complete-rows", "--note", "a|b"])
        assert exc.value.code == 2

    def test_different_source_plans_is_usage_error(self, repo: Path) -> None:
        write(repo, PROC_A, procedure_text(DONE, source_plan="plans/one.md"))
        write(repo, PROC_B, procedure_text(DONE, source_plan="plans/two.md"))
        with pytest.raises(SystemExit) as exc:
            main([PROC_A, PROC_B])
        assert exc.value.code == 2


class TestCompleteRows:
    def test_only_pending_rows_completed_with_note(self, repo: Path) -> None:
        setup_batch(
            repo,
            a=[("Pending", ""), ("N/A", "kept"), ("Completed", "done")],
            b=DONE,
        )
        code = main([PROC_A, "--complete-rows", "--note", "landed with batch"])
        assert code == 0
        archived = repo / "implementations/done" / Path(PROC_A).name
        lines = status_lines(repo, archived.relative_to(repo).as_posix())
        assert "| Completed |" in lines[0] and "landed with batch" in lines[0]
        assert "| N/A |" in lines[1] and "kept" in lines[1]
        assert "| Completed |" in lines[2] and "done" in lines[2]

    def test_blocked_row_never_overwritten(self, repo: Path) -> None:
        setup_batch(repo, a=[("Pending", ""), ("Blocked", "waiting")], b=DONE)
        before = (repo / PROC_A).read_bytes()
        code = main([PROC_A, "--complete-rows", "--note", "n"])
        assert code == 1
        assert (repo / PROC_A).read_bytes() == before


class TestDryRunAndArchive:
    def test_dry_run_changes_nothing_then_real_run_applies_the_same(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        setup_batch(repo, a=[("Pending", "")], b=DONE)
        git_repo = git.Repo(repo)
        status_before = git_repo.git.status("--porcelain")
        files_before = {
            rel: (repo / rel).read_bytes() for rel in (PROC_A, PROC_B, PLAN_REL)
        }
        args = [PROC_A, PROC_B, "--complete-rows", "--note", "n", "--plan-steps", "1"]
        assert main([*args, "--dry-run"]) == 0
        dry = capsys.readouterr().out
        assert git_repo.git.status("--porcelain") == status_before
        assert {rel: (repo / rel).read_bytes() for rel in files_before} == files_before
        assert f"would archive {PROC_A} (complete rows: 1)" in dry
        assert f"would archive {PROC_B}" in dry
        assert f"work item {PROC_A}: would set Completed" in dry
        assert "step 1: would mark Completed" in dry
        assert dry.strip().endswith(
            "dry run: verified=2 refused=0 archived=2 failed=0 "
            "steps_marked=1 steps_left=0"
        )

        assert main(args) == 0
        real = capsys.readouterr().out
        assert f"archived {PROC_A} (complete rows: 1)" in real
        assert "step 1: marked Completed" in real
        assert real.strip().endswith(
            "verified=2 refused=0 archived=2 failed=0 steps_marked=1 steps_left=0"
        )
        assert not (repo / PROC_A).exists()
        assert (repo / "implementations/done" / Path(PROC_B).name).is_file()

    def test_renames_staged_and_nothing_committed(self, repo: Path) -> None:
        commit = setup_batch(repo, a=DONE, b=DONE)
        assert main([PROC_A, PROC_B]) == 0
        git_repo = git.Repo(repo)
        assert git_repo.head.commit.hexsha == commit
        staged = git_repo.git.diff("--cached", "--name-status", "-M").splitlines()
        renames = [line for line in staged if line.startswith("R")]
        assert len(renames) == 2
        assert all("implementations/done/" in line for line in renames)

    def test_one_failed_archive_does_not_stop_the_others(
        self,
        repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        real_move = cpb.move_to_done

        def flaky_move(source: Path, *, kind: str, stage_only: bool) -> MoveResult:
            if source.name == Path(PROC_A).name:
                return MoveResult(success=False, error="boom")
            return real_move(source, kind=kind, stage_only=stage_only)

        monkeypatch.setattr(cpb, "move_to_done", flaky_move)
        code = main([PROC_A, PROC_B])
        out = capsys.readouterr().out
        assert code == 1
        assert f"failed {PROC_A}: archive failed: boom" in out
        assert (repo / PROC_A).is_file()
        assert not (repo / PROC_B).exists()
        assert "verified=2 refused=0 archived=1 failed=1" in out
        text = (repo / PLAN_REL).read_text()
        assert f"| `{PROC_A}` | 1 | Procedure | Pending" in text
        assert f"| `{PROC_B}` | 1 | Procedure | Completed" in text

    def test_absolute_path_is_accepted(self, repo: Path) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        assert main([str(repo / PROC_A)]) == 0
        assert (repo / "implementations/done" / Path(PROC_A).name).is_file()


class TestPlanSteps:
    def test_step_with_one_of_two_files_archived_left_unchanged(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        code = main([PROC_A, "--plan-steps", "1"])
        out = capsys.readouterr().out
        assert code == 0
        assert "step 1: left unchanged - cited file without an archived" in out
        assert "tools/b.py" in out
        assert "steps_marked=0 steps_left=1" in out
        assert "| 1 | Build | Pending |" in (repo / PLAN_REL).read_text()

    def test_named_step_with_all_files_archived_is_marked(self, repo: Path) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        assert main([PROC_A, PROC_B, "--plan-steps", "1"]) == 0
        text = (repo / PLAN_REL).read_text()
        assert "| 1 | Build | Completed |" in text
        assert "| 2 | Check | Pending |" in text

    def test_files_archived_in_an_earlier_run_count(self, repo: Path) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        assert main([PROC_A]) == 0
        assert main([PROC_B, "--plan-steps", "1,2"]) == 0
        text = (repo / PLAN_REL).read_text()
        assert "| 1 | Build | Completed |" in text
        assert "| 2 | Check | Completed |" in text

    def test_no_step_named_lists_candidates_and_changes_none(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        assert main([PROC_A]) == 0
        out = capsys.readouterr().out
        assert "candidate steps (none changed; pass --plan-steps): 2" in out
        text = (repo / PLAN_REL).read_text()
        assert "| 2 | Check | Pending |" in text

    def test_check_only_step_is_not_marked_unless_named(self, repo: Path) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        assert main([PROC_A, PROC_B, "--plan-steps", "1"]) == 0
        assert "| 2 | Check | Pending |" in (repo / PLAN_REL).read_text()

    def test_unparseable_and_unknown_steps_are_refused(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        write(
            repo,
            PLAN_REL,
            plan_text(
                steps=[("Verify", [])],
                items=[PROC_A],
                targets=["tools/a.py"],
            ),
        )
        write(repo, PROC_A, procedure_text(DONE))
        commit_all(repo)
        assert main([PROC_A, "--plan-steps", "1,5"]) == 0
        out = capsys.readouterr().out
        assert "step 1: left unchanged - cites no Implementation Target Files" in out
        assert "step 5: left unchanged - no such Implementation steps item" in out
        assert "| 1 | Verify | Pending |" in (repo / PLAN_REL).read_text()

    def test_already_completed_step_is_reported_not_rewritten(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        write(
            repo,
            PLAN_REL,
            plan_text(
                steps=[("Build", ["tools/a.py"])],
                items=[PROC_A],
                targets=["tools/a.py"],
                step_statuses=["Completed"],
            ),
        )
        write(repo, PROC_A, procedure_text(DONE))
        commit_all(repo)
        assert main([PROC_A, "--plan-steps", "1"]) == 0
        assert "step 1: left unchanged - already Completed" in capsys.readouterr().out

    def test_companion_test_path_counts_for_both_targets(self, repo: Path) -> None:
        write(
            repo,
            PLAN_REL,
            plan_text(
                steps=[("Code", ["tools/a.py"]), ("Tests", ["tests/test_a.py"])],
                items=[PROC_A],
                targets=["tools/a.py", "tests/test_a.py"],
            ),
        )
        write(
            repo,
            PROC_A,
            procedure_text(DONE, related="`tools/a.py`, `tests/test_a.py`"),
        )
        commit_all(repo)
        assert main([PROC_A, "--plan-steps", "1,2"]) == 0
        text = (repo / PLAN_REL).read_text()
        assert "| 1 | Code | Completed |" in text
        assert "| 2 | Tests | Completed |" in text

    def test_procedure_of_another_plan_does_not_count(self, repo: Path) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        other = "implementations/done/20260101-000009_01_tools_b.py.md"
        write(
            repo,
            other,
            procedure_text(DONE, related="tools/b.py", source_plan="plans/other.md"),
        )
        commit_all(repo)
        assert main([PROC_A, "--plan-steps", "1"]) == 0
        assert "| 1 | Build | Pending |" in (repo / PLAN_REL).read_text()


class TestWorkItems:
    def test_matching_row_becomes_completed(self) -> None:
        text = plan_text(steps=[("S", [])], items=[PROC_A, PROC_B], targets=[])
        new, matched, unmatched = update_work_items(text, [PROC_A])
        assert matched == [PROC_A] and unmatched == []
        assert f"| `{PROC_A}` | 1 | Procedure | Completed |" in new
        assert f"| `{PROC_B}` | 1 | Procedure | Pending |" in new

    def test_longer_name_sharing_a_prefix_is_not_matched(self) -> None:
        text = plan_text(steps=[("S", [])], items=[PROC_A + ".md"], targets=[])
        new, matched, unmatched = update_work_items(text, [PROC_A])
        assert new == text and matched == [] and unmatched == [PROC_A]

    def test_plan_without_row_or_table_is_handled(self) -> None:
        text = plan_text(steps=[("S", [])], items=[], targets=[])
        assert update_work_items(text, [PROC_A])[2] == [PROC_A]
        assert update_work_items("## Goal\n- none\n", [PROC_A]) == (
            "## Goal\n- none\n",
            [],
            [PROC_A],
        )

    def test_unmatched_document_reported_without_failure(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        setup_batch(repo, a=DONE, b=DONE)
        write(
            repo,
            PLAN_REL,
            plan_text(
                steps=[("S", ["tools/a.py"])], items=[PROC_B], targets=["tools/a.py"]
            ),
        )
        commit_all(repo)
        assert main([PROC_A]) == 0
        out = capsys.readouterr().out
        assert f"work item {PROC_A}: no row in {PLAN_REL} (not failed)" in out

    def test_refused_document_row_is_untouched(self, repo: Path) -> None:
        setup_batch(repo, a=[("Pending", "")], b=DONE)
        assert main([PROC_A, PROC_B]) == 1
        text = (repo / PLAN_REL).read_text()
        assert f"| `{PROC_A}` | 1 | Procedure | Pending" in text
        assert f"| `{PROC_B}` | 1 | Procedure | Completed" in text
