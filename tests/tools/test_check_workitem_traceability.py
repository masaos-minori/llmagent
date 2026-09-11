"""tests/tools/test_check_workitem_traceability.py
Tests for tools/check_workitem_traceability.py.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from freezegun import freeze_time

import tools.check_workitem_traceability as cwt

# Fixed reference "now" for the age-threshold boundary tests — see this
# implementation procedure's Assumptions/Details for why freezegun is used
# here instead of a "now" function parameter (no such parameter exists on
# `find_no_plan_yet`/`find_no_procedure_yet` in current source).
FROZEN_NOW = datetime(2026, 9, 1, 12, 0, 0)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestValidChain:
    """A complete issue -> plan -> implementation-procedure chain, all
    present, reports zero missing-source-file, no-plan-yet, and
    no-procedure-yet findings.
    """

    def test_valid_chain_reports_no_findings(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)

        issue_path = tmp_path / "issues" / "20260801-100000_i_sample.md"
        _write(
            issue_path,
            "# Sample Issue\n\n## Traceability\n- **Requirement ID**: N/A\n",
        )
        plan_path = tmp_path / "plans" / "20260801-110000_plan.md"
        _write(
            plan_path,
            "# Sample Plan\n\n## Traceability\n"
            "- **Source issue**: `issues/20260801-100000_i_sample.md`\n",
        )
        impl_path = tmp_path / "implementations" / "20260801-120000_01_sample.md"
        _write(
            impl_path,
            "# Sample Implementation Procedure\n\n## Traceability\n"
            "- **Source plan**: `plans/20260801-110000_plan.md`\n",
        )

        documents = cwt.discover_documents()

        assert cwt.find_missing_source_files(documents) == []
        assert cwt.find_no_plan_yet(documents, cwt.DEFAULT_AGE_THRESHOLD_DAYS) == []
        assert (
            cwt.find_no_procedure_yet(documents, cwt.DEFAULT_AGE_THRESHOLD_DAYS) == []
        )


class TestMissingSourceFile:
    """A `Source *` field pointing at a path that does not exist in the
    fixture tree is reported with the exact referenced path.
    """

    def test_missing_source_file_is_reported_with_exact_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)

        missing_value = "issues/20260101-000000_i_missing.md"
        plan_path = tmp_path / "plans" / "20260801-110000_plan.md"
        _write(
            plan_path,
            "# Sample Plan\n\n## Traceability\n"
            f"- **Source issue**: `{missing_value}`\n",
        )

        documents = cwt.discover_documents()
        findings = cwt.find_missing_source_files(documents)

        assert len(findings) == 1
        assert findings[0]["category"] == "missing-source-file"
        assert findings[0]["file"] == "plans/20260801-110000_plan.md"
        assert missing_value in findings[0]["detail"]

    def test_missing_source_file_not_reported_once_moved_to_done(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A `Source *` value recorded before the referenced document's
        lifecycle move into `done/` must not be reported as missing — see
        `_source_path_exists`'s done-segment tolerance.
        """
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)

        referenced_value = "issues/20260101-000000_i_moved.md"
        done_issue_path = tmp_path / "issues" / "done" / "20260101-000000_i_moved.md"
        _write(
            done_issue_path,
            "# Moved Issue\n\n## Traceability\n- **Requirement ID**: N/A\n",
        )
        plan_path = tmp_path / "plans" / "20260801-110000_plan.md"
        _write(
            plan_path,
            "# Sample Plan\n\n## Traceability\n"
            f"- **Source issue**: `{referenced_value}`\n",
        )

        documents = cwt.discover_documents()
        findings = cwt.find_missing_source_files(documents)

        assert findings == []


class TestNoPlanYet:
    """An issue with no referencing plan is reported once it is older than
    the age threshold; a fresher unreferenced issue is not.
    """

    def test_old_unreferenced_issue_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)
        age_threshold_days = cwt.DEFAULT_AGE_THRESHOLD_DAYS
        old_ts = (FROZEN_NOW - timedelta(days=age_threshold_days + 10)).strftime(
            "%Y%m%d-%H%M%S"
        )
        issue_path = tmp_path / "issues" / f"{old_ts}_i_old.md"
        _write(
            issue_path,
            "# Old Issue\n\n## Traceability\n- **Requirement ID**: N/A\n",
        )

        with freeze_time(FROZEN_NOW):
            documents = cwt.discover_documents()
            findings = cwt.find_no_plan_yet(documents, age_threshold_days)

        assert any(f["file"] == f"issues/{old_ts}_i_old.md" for f in findings)

    def test_young_unreferenced_issue_is_not_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)
        age_threshold_days = cwt.DEFAULT_AGE_THRESHOLD_DAYS
        young_ts = (FROZEN_NOW - timedelta(days=age_threshold_days - 25)).strftime(
            "%Y%m%d-%H%M%S"
        )
        issue_path = tmp_path / "issues" / f"{young_ts}_i_young.md"
        _write(
            issue_path,
            "# Young Issue\n\n## Traceability\n- **Requirement ID**: N/A\n",
        )

        with freeze_time(FROZEN_NOW):
            documents = cwt.discover_documents()
            findings = cwt.find_no_plan_yet(documents, age_threshold_days)

        assert findings == []


class TestNoProcedureYet:
    """Symmetric to TestNoPlanYet, for a plan with no referencing
    implementation procedure.
    """

    def test_old_unreferenced_plan_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)
        age_threshold_days = cwt.DEFAULT_AGE_THRESHOLD_DAYS
        old_ts = (FROZEN_NOW - timedelta(days=age_threshold_days + 10)).strftime(
            "%Y%m%d-%H%M%S"
        )
        plan_path = tmp_path / "plans" / f"{old_ts}_plan.md"
        _write(
            plan_path,
            "# Old Plan\n\n## Traceability\n"
            "- **Source issue**: N/A: synthetic fixture plan\n",
        )

        with freeze_time(FROZEN_NOW):
            documents = cwt.discover_documents()
            findings = cwt.find_no_procedure_yet(documents, age_threshold_days)

        assert any(f["file"] == f"plans/{old_ts}_plan.md" for f in findings)

    def test_young_unreferenced_plan_is_not_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)
        age_threshold_days = cwt.DEFAULT_AGE_THRESHOLD_DAYS
        young_ts = (FROZEN_NOW - timedelta(days=age_threshold_days - 25)).strftime(
            "%Y%m%d-%H%M%S"
        )
        plan_path = tmp_path / "plans" / f"{young_ts}_plan.md"
        _write(
            plan_path,
            "# Young Plan\n\n## Traceability\n"
            "- **Source issue**: N/A: synthetic fixture plan\n",
        )

        with freeze_time(FROZEN_NOW):
            documents = cwt.discover_documents()
            findings = cwt.find_no_procedure_yet(documents, age_threshold_days)

        assert findings == []


class TestTargetFileMismatch:
    """`implementation`-kind documents: the Traceability `Related target
    files` value must equal the body's `### Target file` value.
    """

    def _write_implementation(
        self, tmp_path: Path, traceability_value: str, target_file_value: str
    ) -> Path:
        impl_path = tmp_path / "implementations" / "20260801-120000_01_sample.md"
        _write(
            impl_path,
            "# Sample Implementation Procedure\n\n"
            "### Target file\n"
            f"{target_file_value}\n\n"
            "## Traceability\n"
            f"- **Related target files**: {traceability_value}\n",
        )
        return impl_path

    def test_matching_values_report_no_finding(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)
        self._write_implementation(
            tmp_path, "scripts/eventbus/db.py", "scripts/eventbus/db.py"
        )

        documents = cwt.discover_documents()

        assert cwt.find_target_file_mismatches(documents) == []

    def test_mismatched_values_are_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)
        self._write_implementation(
            tmp_path, "scripts/eventbus/config.py", "scripts/eventbus/broker.py"
        )

        documents = cwt.discover_documents()
        findings = cwt.find_target_file_mismatches(documents)

        assert len(findings) == 1
        assert findings[0]["category"] == "target-file-mismatch"
        assert findings[0]["file"] == "implementations/20260801-120000_01_sample.md"
        assert "scripts/eventbus/config.py" in findings[0]["detail"]
        assert "scripts/eventbus/broker.py" in findings[0]["detail"]

    def test_plan_kind_multi_path_value_is_not_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A `plan`-kind document's `Related target files` legitimately
        holds a multi-path list or prose — this check must not fire there.
        """
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)
        plan_path = tmp_path / "plans" / "20260801-110000_plan.md"
        _write(
            plan_path,
            "# Sample Plan\n\n## Traceability\n"
            "- **Related target files**: see Target Files or Areas above\n",
        )

        documents = cwt.discover_documents()

        assert cwt.find_target_file_mismatches(documents) == []

    def test_missing_target_file_heading_is_not_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Neither value present (or one absent) is a "no data" case, not a
        mismatch — only two present-and-differing values are a finding.
        """
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)
        impl_path = tmp_path / "implementations" / "20260801-120000_01_sample.md"
        _write(
            impl_path,
            "# Sample Implementation Procedure\n\n"
            "## Traceability\n"
            "- **Related target files**: scripts/eventbus/db.py\n",
        )

        documents = cwt.discover_documents()

        assert cwt.find_target_file_mismatches(documents) == []
