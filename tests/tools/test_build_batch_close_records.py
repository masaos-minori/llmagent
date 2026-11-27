"""tests/tools/test_build_batch_close_records.py
Tests for tools/build_batch_close_records.py: the records file built from a procedure's
`### Execution Status` rows.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools import build_batch_close_records as bcr

TOOL = (
    Path(__file__).resolve().parent.parent.parent
    / "tools"
    / "build_batch_close_records.py"
)

SUITE = "full suite: 15938 passed, 6 known baseline failures, 5 skipped; diff-cover 95%"


def _procedure(tmp_path: Path, rows: list[str]) -> Path:
    path = tmp_path / "proc.md"
    body = "\n".join(
        [
            "### Execution Status",
            "| Step | Description | Status | Started | Completed | Notes |",
            "|---|---|---|---|---|---|",
        ]
        + rows
    )
    path.write_text(body + "\n", encoding="utf-8")
    return path


def test_unfinished_rows_become_completed_and_row_4_is_na(tmp_path: Path) -> None:
    proc = _procedure(
        tmp_path,
        [
            "| 1 | Implement | In Progress | 20261127-000000 | — | kept note |",
            "| 2 | Add tests | Pending | — | — | — |",
            "| 3 | Run the validation gates | In Progress | — | — | gates pass |",
            "| 4 | Update documentation, if in scope | Pending | — | — | — |",
        ],
    )

    records = bcr.build(proc, SUITE)

    assert [r["status"] for r in records] == [
        "Completed",
        "Completed",
        "Completed",
        "N/A",
    ]
    assert records[0]["notes"] == "kept note"
    assert records[1]["notes"] == ""
    assert records[2]["notes"] == f"gates pass; {SUITE}"
    assert [r["step"] for r in records] == [1, 2, 3, 4]
    assert all(
        r["path"] == str(proc) and r["kind"] == "implementation-procedure"
        for r in records
    )


def test_the_pending_placeholder_is_replaced_by_the_suite_result(
    tmp_path: Path,
) -> None:
    proc = _procedure(
        tmp_path,
        [
            "| 3 | Run the validation gates | In Progress | — | — | gates pass; awaiting end-of-batch full suite |"
        ],
    )

    assert bcr.build(proc, SUITE)[0]["notes"] == f"gates pass; {SUITE}"


def test_finished_rows_are_skipped(tmp_path: Path) -> None:
    proc = _procedure(
        tmp_path, ["| 1 | Implement | Completed | — | 20261127-000000 | done |"]
    )

    assert bcr.build(proc, SUITE) == []


def test_missing_file_raises_oserror(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        bcr.build(tmp_path / "absent.md", SUITE)


def test_cli_writes_the_records_file(tmp_path: Path) -> None:
    proc = _procedure(tmp_path, ["| 1 | Implement | In Progress | — | — | — |"])
    out = tmp_path / "records.json"

    code = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--out",
            str(out),
            "--suite",
            SUITE,
            str(proc),
        ],
        capture_output=True,
        text=True,
    )

    assert code.returncode == 0
    assert json.loads(out.read_text(encoding="utf-8")) == [
        {
            "path": str(proc),
            "kind": "implementation-procedure",
            "step": 1,
            "status": "Completed",
            "notes": "",
        }
    ]


def test_cli_exit_1_when_a_procedure_has_no_unfinished_row(tmp_path: Path) -> None:
    proc = _procedure(
        tmp_path, ["| 1 | Implement | Completed | — | 20261127-000000 | done |"]
    )
    out = tmp_path / "records.json"

    code = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--out",
            str(out),
            "--suite",
            SUITE,
            str(proc),
        ],
        capture_output=True,
        text=True,
    )

    assert code.returncode == 1
    assert "no unfinished row" in code.stderr
    assert not out.exists()
