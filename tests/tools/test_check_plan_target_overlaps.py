"""tests/tools/test_check_plan_target_overlaps.py
Tests for tools/check_plan_target_overlaps.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.check_plan_target_overlaps as cpto


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _plan_text(freeze_status: str, target_files: list[str]) -> str:
    rows = "\n".join(
        f"| {path} | Modify | reason | REQ-001 | evidence | tests | Verified |"
        for path in target_files
    )
    return (
        "# Sample Plan\n\n"
        "## Implementation Target Files\n"
        f"**Freeze status**: {freeze_status}\n\n"
        "| File Path | Change Responsibility | Reason for Modification | "
        "Related Requirement / Acceptance Criterion | Repository Evidence | "
        "Related Tests | Validation Status |\n"
        "|---|---|---|---|---|---|---|\n"
        f"{rows}\n\n"
        "## Reference Files\n\nN/A\n"
    )


class TestCrossPlanTargetOverlap:
    def test_two_frozen_plans_targeting_same_file_are_flagged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cpto, "ROOT_DIR", tmp_path)
        plans_dir = tmp_path / "plans"
        _write(
            plans_dir / "20260901-100000_plan.md",
            _plan_text("Frozen", ["scripts/eventbus/dlq.py"]),
        )
        _write(
            plans_dir / "20260902-100000_plan.md",
            _plan_text("Frozen", ["scripts/eventbus/dlq.py"]),
        )

        documents = cpto.discover_plan_documents(plans_dir)
        findings = cpto.find_cross_plan_target_overlaps(documents)

        assert len(findings) == 1
        assert findings[0]["category"] == "cross-plan-target-overlap"
        assert findings[0]["file"] == "scripts/eventbus/dlq.py"
        assert "20260901-100000_plan.md" in findings[0]["detail"]
        assert "20260902-100000_plan.md" in findings[0]["detail"]

    def test_single_plan_targeting_a_file_is_not_flagged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cpto, "ROOT_DIR", tmp_path)
        plans_dir = tmp_path / "plans"
        _write(
            plans_dir / "20260901-100000_plan.md",
            _plan_text("Frozen", ["scripts/eventbus/dlq.py"]),
        )

        documents = cpto.discover_plan_documents(plans_dir)
        findings = cpto.find_cross_plan_target_overlaps(documents)

        assert findings == []

    def test_draft_plan_overlap_is_not_flagged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`Implementation Target Files` is not canonical scope until
        `Frozen` -- a Draft's overlap is not yet a meaningful signal.
        """
        monkeypatch.setattr(cpto, "ROOT_DIR", tmp_path)
        plans_dir = tmp_path / "plans"
        _write(
            plans_dir / "20260901-100000_plan.md",
            _plan_text("Draft", ["scripts/eventbus/dlq.py"]),
        )
        _write(
            plans_dir / "20260902-100000_plan.md",
            _plan_text("Frozen", ["scripts/eventbus/dlq.py"]),
        )

        documents = cpto.discover_plan_documents(plans_dir)
        findings = cpto.find_cross_plan_target_overlaps(documents)

        assert findings == []

    def test_different_files_across_plans_are_not_flagged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cpto, "ROOT_DIR", tmp_path)
        plans_dir = tmp_path / "plans"
        _write(
            plans_dir / "20260901-100000_plan.md",
            _plan_text("Frozen", ["scripts/eventbus/dlq.py"]),
        )
        _write(
            plans_dir / "20260902-100000_plan.md",
            _plan_text("Frozen", ["scripts/eventbus/ack_route.py"]),
        )

        documents = cpto.discover_plan_documents(plans_dir)
        findings = cpto.find_cross_plan_target_overlaps(documents)

        assert findings == []


class TestPlanFilter:
    """`--plan PATH` keeps only findings that name a given Plan."""

    P1 = "20260901-100000_plan.md"
    P2 = "20260902-100000_plan.md"
    P3 = "20260903-100000_plan.md"

    def _setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        monkeypatch.setattr(cpto, "ROOT_DIR", tmp_path)
        plans_dir = tmp_path / "plans"
        shared = ["scripts/eventbus/dlq.py"]
        _write(plans_dir / self.P1, _plan_text("Frozen", shared))
        _write(plans_dir / self.P2, _plan_text("Frozen", shared))
        _write(plans_dir / self.P3, _plan_text("Frozen", ["scripts/other.py"]))
        original = cpto.discover_plan_documents
        monkeypatch.setattr(
            cpto, "discover_plan_documents", lambda: original(plans_dir)
        )
        return plans_dir

    def test_plan_keeps_findings_naming_it_in_every_format(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plans_dir = self._setup(tmp_path, monkeypatch)
        plan = str(plans_dir / self.P1)
        assert cpto.main(["--plan", plan]) == 0
        assert "scripts/eventbus/dlq.py" in capsys.readouterr().out
        assert cpto.main(["--plan", plan, "--format", "json"]) == 0
        assert '"scripts/eventbus/dlq.py"' in capsys.readouterr().out
        assert cpto.main(["--plan", plan, "--format", "csv"]) == 0
        assert "scripts/eventbus/dlq.py" in capsys.readouterr().out

    def test_plan_without_overlap_prints_the_empty_form(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        plans_dir = self._setup(tmp_path, monkeypatch)
        assert cpto.main(["--plan", str(plans_dir / self.P3)]) == 0
        assert capsys.readouterr().out == "No findings.\n"
        assert cpto.main(["--plan", str(plans_dir / self.P3), "--format", "json"]) == 0
        assert capsys.readouterr().out.strip() == "[]"

    def test_repeating_plan_keeps_the_union(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._setup(tmp_path, monkeypatch)
        findings = cpto.find_cross_plan_target_overlaps(cpto.discover_plan_documents())
        both = cpto.filter_findings_by_plans(
            findings, [f"plans/{self.P3}", f"plans/{self.P2}"]
        )
        assert both == findings
        assert cpto.filter_findings_by_plans(findings, [f"plans/{self.P3}"]) == []

    def test_absolute_and_relative_paths_match_alike(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plans_dir = self._setup(tmp_path, monkeypatch)
        monkeypatch.chdir(tmp_path)
        findings = cpto.find_cross_plan_target_overlaps(cpto.discover_plan_documents())
        by_abs = cpto.filter_findings_by_plans(findings, [str(plans_dir / self.P1)])
        by_rel = cpto.filter_findings_by_plans(findings, [f"plans/{self.P1}"])
        assert by_abs == by_rel == findings

    def test_a_prefix_of_a_listed_path_does_not_match(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._setup(tmp_path, monkeypatch)
        findings = cpto.find_cross_plan_target_overlaps(cpto.discover_plan_documents())
        assert (
            cpto.filter_findings_by_plans(findings, ["plans/20260901-100000_pl"]) == []
        )

    def test_unknown_plan_path_is_a_usage_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._setup(tmp_path, monkeypatch)
        assert cpto.main(["--plan", str(tmp_path / "plans" / "absent.md")]) == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "not a file" in captured.err

    def test_default_run_is_unchanged_without_plan(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._setup(tmp_path, monkeypatch)
        assert cpto.main([]) == 0
        out = capsys.readouterr().out
        assert "1 finding(s) total." in out
