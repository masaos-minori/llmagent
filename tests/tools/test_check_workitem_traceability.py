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

    @pytest.mark.parametrize(
        "target_file_value",
        [
            "`scripts/eventbus/db.py`.",
            "\\`scripts/eventbus/db.py\\`",
            "`scripts/eventbus/db.py`, then verify",
            "- `scripts/eventbus/db.py` (new)",
        ],
        ids=[
            "trailing-period",
            "escaped-backticks",
            "trailing-prose",
            "leading-bullet",
        ],
    )
    def test_formatting_variants_of_the_same_path_report_no_finding(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        target_file_value: str,
    ) -> None:
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)
        self._write_implementation(
            tmp_path, "scripts/eventbus/db.py", target_file_value
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


class TestActiveOnly:
    """`--active-only` drops findings located under `done/` directories."""

    def test_is_archived_finding_matches_done_directory_only(self) -> None:
        assert cwt.is_archived_finding({"file": "plans/done/20260101_plan.md"})
        assert not cwt.is_archived_finding({"file": "plans/20260101_plan.md"})
        assert not cwt.is_archived_finding({"file": "plans/done.md"})

    def test_main_ignores_archived_gating_findings(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)
        _write(
            tmp_path / "plans" / "done" / "20260801-110000_plan.md",
            "# Plan\n\n## Traceability\n- **Source issue**: issues/gone.md\n",
        )

        assert cwt.main([]) == 1
        capsys.readouterr()
        assert cwt.main(["--active-only"]) == 0


class TestBacktickedNotApplicable:
    """A backtick-wrapped `N/A: ...` value (the form `templates/issue.md` uses)
    is not applicable, not a path to a missing file."""

    @pytest.mark.parametrize(
        "value",
        [
            "`N/A: not filed from a Plan`",
            "N/A: not filed from a Plan",
            "`n/a`",
        ],
    )
    def test_na_values_are_recognized(self, value: str) -> None:
        assert cwt._is_na(value)

    def test_real_path_is_not_treated_as_na(self) -> None:
        assert not cwt._is_na("`plans/20260801-110000_plan.md`")

    def test_backticked_na_source_plan_reports_no_missing_source(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)
        _write(
            tmp_path / "issues" / "20260801-100000_i_sample.md",
            "# Sample\n\n## Traceability\n"
            "- **Source plan**: `N/A: not filed from a Plan`\n"
            "- **Source implementation procedure**: "
            "`N/A: not filed from an implementation procedure`\n",
        )

        documents = cwt.discover_documents()

        assert cwt.find_missing_source_files(documents) == []


CODE = "scripts/agent/foo.py"
TEST_A = "tests/agent/test_foo.py"
TEST_B = "tests/agent/test_foo_edge.py"
PLAN_NAME = "20261101-100000_plan.md"


def _write_plan(root: Path, rows: list[tuple[str, str]], *, done: bool = False) -> Path:
    """Write a Plan with an `Implementation Target Files` table of
    `(File Path, Related Tests)` rows and return its repository-relative path.
    """
    rel = Path("plans") / "done" / PLAN_NAME if done else Path("plans") / PLAN_NAME
    table = "\n".join(f"| `{path}` | A change | {tests} |" for path, tests in rows)
    _write(
        root / rel,
        "# Plan\n\n## Implementation Target Files\n"
        "| File Path | Change Responsibility | Related Tests |\n"
        "|---|---|---|\n"
        f"{table}\n\n## Reference Files\n| File Path |\n|---|\n| `other.py` |\n",
    )
    return rel


def _write_procedure(
    root: Path,
    name: str,
    target: str,
    companions: list[str],
    related: str | None = None,
    plan: str = PLAN_NAME,
) -> Path:
    """Write a procedure document with an optional companion section."""
    body = f"### Target file\n`{target}`\n\n### Details\n- x\n\n"
    if companions:
        body += "### Companion test files\n"
        for companion in companions:
            body += (
                f"- `{companion}` (new)\n  - Procedure: add tests\n"
                "  - Validation: run them\n"
            )
        body += "\n"
    if related is None:
        related = ", ".join(f"`{path}`" for path in [target, *companions])
    path = root / "implementations" / name
    _write(
        path,
        f"# Procedure\n\n## Implementation\n{body}## Traceability\n"
        f"- **Source plan**: `plans/{plan}`\n"
        f"- **Related target files**: {related}\n",
    )
    return path


def _categories(findings: list[dict[str, str]]) -> list[str]:
    return [finding["category"] for finding in findings]


class TestCompanionEquality:
    """`Related target files` lists the target first, then each companion."""

    @pytest.fixture(autouse=True)
    def _root(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)
        self.root = tmp_path

    def _mismatches(self) -> list[dict[str, str]]:
        return cwt.find_target_file_mismatches(cwt.discover_documents())

    def test_extract_related_target_files_list_reads_backticked_paths(self) -> None:
        text = f"## Traceability\n- **Related target files**: `{CODE}`, `{TEST_A}`\n"

        assert cwt.extract_related_target_files_list(text) == [CODE, TEST_A]

    def test_extract_related_target_files_list_falls_back_to_first_token(self) -> None:
        text = f"## Traceability\n- **Related target files**: {CODE}\n"

        assert cwt.extract_related_target_files_list(text) == [CODE]

    def test_extract_related_target_files_list_empty_for_na_and_absent(self) -> None:
        assert (
            cwt.extract_related_target_files_list(
                "## Traceability\n- **Related target files**: N/A\n"
            )
            == []
        )
        assert cwt.extract_related_target_files_list("# no traceability\n") == []

    def test_extract_companion_files_reads_top_level_bullets_only(self) -> None:
        text = (
            "### Companion test files\n"
            f"- `{TEST_A}` (new)\n  - Procedure: `not/a/companion.py`\n"
            f"- `{TEST_B}`\n\n## Next\n- `ignored.py`\n"
        )

        assert cwt.extract_companion_files(text) == [TEST_A, TEST_B]

    def test_extract_companion_files_empty_without_section(self) -> None:
        assert cwt.extract_companion_files("### Target file\n`a.py`\n") == []

    def test_list_equal_to_target_and_companions_reports_no_finding(self) -> None:
        _write_procedure(self.root, "20261101-100001_01_foo.md", CODE, [TEST_A, TEST_B])

        assert self._mismatches() == []

    def test_list_missing_a_companion_is_reported(self) -> None:
        _write_procedure(
            self.root,
            "20261101-100001_01_foo.md",
            CODE,
            [TEST_A, TEST_B],
            related=f"`{CODE}`, `{TEST_A}`",
        )

        findings = self._mismatches()

        assert _categories(findings) == ["target-file-mismatch"]
        assert TEST_B in findings[0]["detail"]

    def test_list_with_an_extra_path_is_reported(self) -> None:
        _write_procedure(
            self.root,
            "20261101-100001_01_foo.md",
            CODE,
            [TEST_A],
            related=f"`{CODE}`, `{TEST_A}`, `tests/extra.py`",
        )

        assert _categories(self._mismatches()) == ["target-file-mismatch"]

    def test_first_path_not_the_target_is_reported(self) -> None:
        _write_procedure(
            self.root,
            "20261101-100001_01_foo.md",
            CODE,
            [TEST_A],
            related=f"`{TEST_A}`, `{CODE}`",
        )

        assert _categories(self._mismatches()) == ["target-file-mismatch"]

    def test_document_without_companions_keeps_first_token_check(self) -> None:
        _write_procedure(self.root, "20261101-100001_01_foo.md", CODE, [])
        _write_procedure(
            self.root, "20261101-100001_02_bar.md", "scripts/bar.py", [], related="x.py"
        )

        findings = self._mismatches()

        assert _categories(findings) == ["target-file-mismatch"]
        assert findings[0]["file"].endswith("_02_bar.md")


class TestPlanCoverage:
    """`find_plan_coverage_findings` and the `--plan-coverage` option."""

    @pytest.fixture(autouse=True)
    def _root(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cwt, "ROOT_DIR", tmp_path)
        self.root = tmp_path
        self.plan = _write_plan(
            tmp_path,
            [
                (CODE, f"`{TEST_A}`, `{TEST_B}`"),
                (TEST_A, "itself"),
                (TEST_B, "itself"),
            ],
        )

    def _findings(self) -> list[dict[str, str]]:
        return cwt.find_plan_coverage_findings(self.plan, cwt.discover_documents())

    def test_plan_table_rows_are_read_by_header(self) -> None:
        text = (self.root / self.plan).read_text(encoding="utf-8")

        assert cwt._plan_target_rows(text) == [
            (CODE, f"`{TEST_A}`, `{TEST_B}`"),
            (TEST_A, "itself"),
            (TEST_B, "itself"),
        ]

    def test_code_document_with_two_companions_covers_all_rows(self) -> None:
        _write_procedure(self.root, "20261101-100001_01_foo.md", CODE, [TEST_A, TEST_B])

        assert self._findings() == []

    def test_removing_a_companion_leaves_its_row_uncovered(self) -> None:
        _write_procedure(self.root, "20261101-100001_01_foo.md", CODE, [TEST_A])

        findings = self._findings()

        assert _categories(findings) == ["row-uncovered"]
        assert TEST_B in findings[0]["detail"]

    def test_test_file_listed_by_two_documents_is_covered_twice(self) -> None:
        _write_procedure(self.root, "20261101-100001_01_foo.md", CODE, [TEST_A, TEST_B])
        _write_procedure(self.root, "20261101-100001_02_foo.md", TEST_A, [])

        findings = self._findings()

        assert _categories(findings) == ["path-covered-twice"]
        assert TEST_A in findings[0]["detail"]

    def test_companion_named_in_two_rows_is_multi_row(self) -> None:
        self.plan = _write_plan(
            self.root,
            [
                (CODE, f"`{TEST_A}`"),
                ("scripts/agent/bar.py", f"`{TEST_A}`"),
                (TEST_A, "itself"),
            ],
        )
        _write_procedure(self.root, "20261101-100001_01_foo.md", CODE, [TEST_A])
        _write_procedure(
            self.root, "20261101-100001_02_bar.md", "scripts/agent/bar.py", []
        )

        findings = self._findings()

        assert "companion-multi-row" in _categories(findings)
        multi = next(f for f in findings if f["category"] == "companion-multi-row")
        assert TEST_A in multi["detail"]

    def test_companion_not_a_plan_row_is_not_eligible(self) -> None:
        _write_procedure(
            self.root, "20261101-100001_01_foo.md", CODE, [TEST_A, TEST_B, "tests/x.py"]
        )

        findings = self._findings()

        assert _categories(findings) == ["companion-not-eligible"]
        assert "tests/x.py" in findings[0]["detail"]

    def test_companion_outside_tests_is_not_eligible(self) -> None:
        self.plan = _write_plan(
            self.root, [(CODE, "`scripts/helper.py`"), ("scripts/helper.py", "itself")]
        )
        _write_procedure(
            self.root, "20261101-100001_01_foo.md", CODE, ["scripts/helper.py"]
        )

        findings = self._findings()

        assert _categories(findings) == ["companion-not-eligible"]
        assert "not under tests/" in findings[0]["detail"]

    def test_companion_not_named_in_its_target_row_is_not_eligible(self) -> None:
        self.plan = _write_plan(self.root, [(CODE, "itself"), (TEST_A, "itself")])
        _write_procedure(self.root, "20261101-100001_01_foo.md", CODE, [TEST_A])

        findings = self._findings()

        assert _categories(findings) == ["companion-not-eligible"]
        assert "Related Tests" in findings[0]["detail"]

    def test_document_of_another_plan_is_ignored(self) -> None:
        _write_procedure(
            self.root,
            "20261101-100001_01_foo.md",
            CODE,
            [TEST_A, TEST_B],
            plan="20261101-999999_other.md",
        )

        assert _categories(self._findings()) == ["row-uncovered"] * 3

    def test_done_plan_matches_by_basename(self) -> None:
        self.plan = _write_plan(
            self.root,
            [(CODE, f"`{TEST_A}`, `{TEST_B}`"), (TEST_A, "x"), (TEST_B, "x")],
            done=True,
        )
        _write_procedure(self.root, "20261101-100001_01_foo.md", CODE, [TEST_A, TEST_B])

        assert self._findings() == []

    def test_main_returns_1_on_a_finding_and_skips_default_categories(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # A missing-source-file finding would exit 1 under the default scan;
        # here only coverage findings count, so a covered Plan exits 0.
        _write_procedure(self.root, "20261101-100001_01_foo.md", CODE, [TEST_A])
        _write(
            self.root / "plans" / "20261101-110000_bad.md",
            "# P\n\n## Traceability\n- **Source issue**: issues/gone.md\n",
        )

        assert cwt.main(["--plan-coverage", str(self.plan)]) == 1
        assert "row-uncovered" in capsys.readouterr().out

        _write_procedure(self.root, "20261101-100001_01_foo.md", CODE, [TEST_A, TEST_B])

        assert cwt.main(["--plan-coverage", str(self.plan)]) == 0
        assert "gone.md" not in capsys.readouterr().out

    def test_main_rejects_a_missing_plan_file(self) -> None:
        with pytest.raises(SystemExit) as excinfo:
            cwt.main(["--plan-coverage", "plans/absent.md"])

        assert excinfo.value.code == 2
