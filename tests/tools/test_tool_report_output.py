"""tests/tools/test_tool_report_output.py
Golden output (text, JSON, CSV) and determinism of the four checkers that share the
reporting layer. Expected strings were recorded from the tools before they were moved
onto `tools/_report.py` and are never regenerated from migrated code.

The finding sources are replaced (crafted findings, or a temporary work item tree), so
only the output layer is under test.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

import tools.check_adr_authority as authority
import tools.check_adr_invariant_matrix as matrix
import tools.check_adr_reference as reference
import tools.check_workitem_traceability as traceability
from tools._adr_authority_core import Finding
from tools._docs_consistency_lib import Issue

Result = tuple[int, str, str]

AUTHORITY_FINDINGS = [
    Finding("B_CODE", "loc/b.md", "second ünï"),
    Finding("A_CODE", "loc/z.md", "msg z"),
    Finding("A_CODE", "loc/a.md", "msg a"),
]
ISSUES = [
    Issue("b.md", 3, "WARNING", "w ünï"),
    Issue("a.md", 10, "ERROR", "e10"),
    Issue("a.md", 2, "ERROR", "e2"),
]


def _run(
    main: Callable[[list[str] | None], int],
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> Result:
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _authority(
    findings: list[Finding],
    argv: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> Result:
    monkeypatch.setattr(authority, "collect_findings", lambda *_: findings)
    return _run(authority.main, argv, capsys)


def _issues(
    module: ModuleType,
    issues: list[Issue],
    argv: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> Result:
    monkeypatch.setattr(module, "collect_issues", lambda: issues)
    return _run(module.main, argv, capsys)


AGE = ["--age-threshold-days", "100000"]


def _workitems(
    root: Path,
    argv: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *,
    populate: bool = True,
) -> Result:
    monkeypatch.setattr(traceability, "ROOT_DIR", root)
    (root / "plans").mkdir(parents=True)
    (root / "issues").mkdir(parents=True)
    if populate:
        (root / "plans" / "20260801-110000_plan.md").write_text(
            "## Traceability\n- **Source issue**: issues/missing_ünï.md\n",
            encoding="utf-8",
        )
        (root / "issues" / "20200101-000000_old_issue.md").write_text(
            "# raw issue\n", encoding="utf-8"
        )
    return _run(traceability.main, argv, capsys)


EXPECTED: dict[str, Result] = {
    "authority_text": (
        1,
        "[A_CODE] loc/a.md: msg a\n[A_CODE] loc/z.md: msg z\n[B_CODE] loc/b.md: second ünï\n",
        "\nFound 3 finding(s).\n",
    ),
    "authority_empty_text": (0, "Authority model OK: no findings.\n", ""),
    "reference_text": (
        1,
        "[ERROR] a.md:2: e2\n[ERROR] a.md:10: e10\n[WARNING] b.md:3: w ünï\n",
        "\nFound 2 error(s), 1 warning(s).\n",
    ),
    "reference_empty_text": (0, "No issues found.\n", ""),
    "matrix_text": (
        1,
        "[ERROR] a.md:2: e2\n[ERROR] a.md:10: e10\n[WARNING] b.md:3: w ünï\n",
        "\nFound 2 error(s), 1 warning(s).\n",
    ),
    "matrix_empty_text": (0, "No issues found.\n", ""),
    "authority_json": (
        1,
        '[\n  {\n    "code": "A_CODE",\n    "location": "loc/a.md",\n    "message": "msg a"\n  },\n  {\n    "code": "A_CODE",\n    "location": "loc/z.md",\n    "message": "msg z"\n  },\n  {\n    "code": "B_CODE",\n    "location": "loc/b.md",\n    "message": "second ünï"\n  }\n]\n',
        "",
    ),
    "authority_empty_json": (0, "[]\n", ""),
    "reference_json": (
        1,
        '[\n  {\n    "file": "a.md",\n    "line_no": 2,\n    "severity": "ERROR",\n    "message": "e2"\n  },\n  {\n    "file": "a.md",\n    "line_no": 10,\n    "severity": "ERROR",\n    "message": "e10"\n  },\n  {\n    "file": "b.md",\n    "line_no": 3,\n    "severity": "WARNING",\n    "message": "w ünï"\n  }\n]\n',
        "",
    ),
    "reference_empty_json": (0, "[]\n", ""),
    "matrix_json": (
        1,
        '[\n  {\n    "file": "a.md",\n    "line_no": 2,\n    "severity": "ERROR",\n    "message": "e2"\n  },\n  {\n    "file": "a.md",\n    "line_no": 10,\n    "severity": "ERROR",\n    "message": "e10"\n  },\n  {\n    "file": "b.md",\n    "line_no": 3,\n    "severity": "WARNING",\n    "message": "w ünï"\n  }\n]\n',
        "",
    ),
    "matrix_empty_json": (0, "[]\n", ""),
    "workitem_text": (
        1,
        "[parse-error] (1)\n  issues/20200101-000000_old_issue.md: no '## Traceability' heading found\n[missing-source-file] (1)\n  plans/20260801-110000_plan.md: Source issue target does not exist: issues/missing_ünï.md\n\n2 finding(s) total.\n",
        "",
    ),
    "workitem_json": (
        1,
        '[\n  {\n    "category": "parse-error",\n    "detail": "no \'## Traceability\' heading found",\n    "file": "issues/20200101-000000_old_issue.md"\n  },\n  {\n    "category": "missing-source-file",\n    "detail": "Source issue target does not exist: issues/missing_ünï.md",\n    "file": "plans/20260801-110000_plan.md"\n  }\n]\n',
        "",
    ),
    "workitem_csv": (
        1,
        "category,file,detail\r\nparse-error,issues/20200101-000000_old_issue.md,no '## Traceability' heading found\r\nmissing-source-file,plans/20260801-110000_plan.md,Source issue target does not exist: issues/missing_ünï.md\r\n",
        "",
    ),
    "workitem_empty_text": (0, "No findings.\n", ""),
    "workitem_empty_json": (0, "[]\n", ""),
}

JSON = ["--format", "json"]
CSV = ["--format", "csv"]
CASES: dict[str, Callable[..., Result]] = {}
for _fmt, _argv in (("text", []), ("json", JSON)):
    CASES[f"authority_{_fmt}"] = lambda mp, cap, root, a=_argv: _authority(
        AUTHORITY_FINDINGS, a, mp, cap
    )
    CASES[f"authority_empty_{_fmt}"] = lambda mp, cap, root, a=_argv: _authority(
        [], a, mp, cap
    )
    for _name, _module in (("reference", reference), ("matrix", matrix)):
        CASES[f"{_name}_{_fmt}"] = lambda mp, cap, root, m=_module, a=_argv: _issues(
            m, ISSUES, a, mp, cap
        )
        CASES[f"{_name}_empty_{_fmt}"] = lambda mp, cap, root, m=_module, a=_argv: (
            _issues(m, [], a, mp, cap)
        )
for _fmt, _argv in (("text", []), ("json", JSON), ("csv", CSV)):
    CASES[f"workitem_{_fmt}"] = lambda mp, cap, root, a=_argv: _workitems(
        root, AGE + a, mp, cap
    )
for _fmt, _argv in (("text", []), ("json", JSON)):
    CASES[f"workitem_empty_{_fmt}"] = lambda mp, cap, root, a=_argv: _workitems(
        root, a, mp, cap, populate=False
    )


def test_every_recorded_case_has_a_runner() -> None:
    assert set(CASES) == set(EXPECTED)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_output_matches_the_recorded_golden(
    name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert CASES[name](monkeypatch, capsys, tmp_path / "root") == EXPECTED[name]


@pytest.mark.parametrize("name", sorted(n for n in EXPECTED if "json" in n))
def test_json_output_is_deterministic(
    name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first = CASES[name](monkeypatch, capsys, tmp_path / "one")
    second = CASES[name](monkeypatch, capsys, tmp_path / "two")

    assert first == second
