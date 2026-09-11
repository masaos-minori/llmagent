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
