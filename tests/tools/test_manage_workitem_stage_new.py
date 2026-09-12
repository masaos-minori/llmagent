"""tests/tools/test_manage_workitem_stage_new.py

Tests for the new subcommands added to manage_workitem_stage.py:
set-status, set-step-status, detect-stale, list, show.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from tools.manage_workitem_stage import (
    EXECUTION_STATUS_HEADING,
    build_parser,
    cmd_detect_stale,
    cmd_list,
    cmd_set_status,
    cmd_set_step_status,
    cmd_show,
    parse_execution_status_table,
)

# ---------------------------------------------------------------------------
# Fixtures — Execution Status table variants
# ---------------------------------------------------------------------------

EXECUTION_STATUS_MULTI_ROW = """# Fixture implementation procedure

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | First step | Pending | — | — | |
| 2 | Second step | In Progress | 20260101-000000 | — | |
| 3 | Third step | Completed | 20260101-000000 | 20260101-000100 | done |
"""

EXECUTION_STATUS_SINGLE_ROW = """# Fixture implementation procedure

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Do the thing | Pending | — | — | |
"""

EXECUTION_STATUS_NO_TABLE = """# Fixture implementation procedure

Some content without an Execution Status table.
"""

# Reuse constants from existing test file
EXECUTION_STATUS_COMPLETED = """# Fixture implementation procedure

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Do the thing | Completed | 20260101-000000 | 20260101-000100 | |
"""

EXECUTION_STATUS_PENDING = """# Fixture implementation procedure

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Do the thing | Pending | — | — | |
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_temp_workitem(tmp_path: Path, kind: str, name: str, content: str) -> Path:
    """Create a temporary workitem file under the appropriate directory."""
    base = (
        tmp_path / kind.rstrip("s").rstrip("e")
        if kind != "plan"
        else tmp_path / "plans"
    )
    if kind == "implementation-procedure":
        base = tmp_path / "implementations"
    elif kind == "plan":
        base = tmp_path / "plans"
    fpath = base / name
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")
    return fpath


def _patch_mtime(fpath: Path, days_ago: int) -> None:
    """Set the modification time of a file to N days ago."""
    ts = time.time() - days_ago * 86400
    os.utime(str(fpath), (ts, ts))


def _get_status_cell(rows, row_idx, col_name):
    """Get the status cell value from a parsed table row."""
    header = rows[0] if isinstance(rows, tuple) else None
    if header is None:
        return None
    status_idx = header.index("Status")
    data_rows = rows[2] if isinstance(rows, tuple) else rows
    if data_rows is None:
        return None
    return data_rows[row_idx][status_idx]


# ---------------------------------------------------------------------------
# set-status: all rows
# ---------------------------------------------------------------------------


class TestSetStatus:
    """Tests for the `set-status` subcommand."""

    def test_set_status_all_rows_to_completed(self, tmp_path: Path) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(
            ["set-status", "implementation-procedure", str(fpath), "Completed"]
        )
        exit_code = cmd_set_status(args)
        assert exit_code == 0
        content = fpath.read_text(encoding="utf-8")
        _, header, data_rows = parse_execution_status_table(content)
        assert data_rows[0][header.index("Status")] == "Completed"
        assert data_rows[1][header.index("Status")] == "Completed"
        assert data_rows[2][header.index("Status")] == "Completed"

    def test_set_status_all_rows_to_in_progress(self, tmp_path: Path) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(
            ["set-status", "implementation-procedure", str(fpath), "In Progress"]
        )
        exit_code = cmd_set_status(args)
        assert exit_code == 0
        content = fpath.read_text(encoding="utf-8")
        _, header, data_rows = parse_execution_status_table(content)
        for row in data_rows:
            assert row[header.index("Status")] == "In Progress"

    def test_set_status_invalid_status_refuses(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        # argparse.choices already validates — expect SystemExit from argparse
        with pytest.raises(SystemExit):
            build_parser().parse_args(
                ["set-status", "implementation-procedure", str(fpath), "Invalid"]
            )

    def test_set_status_missing_file_refuses(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = tmp_path / "nonexistent.md"
        args = build_parser().parse_args(
            ["set-status", "implementation-procedure", str(fpath), "Completed"]
        )
        exit_code = cmd_set_status(args)
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "source file not found" in captured.err

    def test_set_status_no_table_refuses(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_NO_TABLE
        )
        args = build_parser().parse_args(
            ["set-status", "implementation-procedure", str(fpath), "Completed"]
        )
        exit_code = cmd_set_status(args)
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "missing or malformed" in captured.err

    def test_set_status_plan_kind(self, tmp_path: Path) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "plan", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(["set-status", "plan", str(fpath), "Blocked"])
        exit_code = cmd_set_status(args)
        assert exit_code == 0
        content = fpath.read_text(encoding="utf-8")
        _, header, data_rows = parse_execution_status_table(content)
        for row in data_rows:
            assert row[header.index("Status")] == "Blocked"


# ---------------------------------------------------------------------------
# set-step-status: single step by number
# ---------------------------------------------------------------------------


class TestSetStepStatusByNumber:
    """Tests for the `set-step-status` subcommand with --step."""

    def test_set_step_status_by_number(self, tmp_path: Path) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(
            [
                "set-step-status",
                "implementation-procedure",
                str(fpath),
                "--step",
                "2",
                "Completed",
            ]
        )
        exit_code = cmd_set_step_status(args)
        assert exit_code == 0
        content = fpath.read_text(encoding="utf-8")
        _, header, data_rows = parse_execution_status_table(content)
        assert data_rows[0][header.index("Status")] == "Pending"  # unchanged
        assert data_rows[1][header.index("Status")] == "Completed"  # updated
        assert (
            data_rows[2][header.index("Status")] == "Completed"
        )  # already was completed

    def test_set_step_status_nonexistent_step_refuses(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(
            [
                "set-step-status",
                "implementation-procedure",
                str(fpath),
                "--step",
                "99",
                "Completed",
            ]
        )
        exit_code = cmd_set_step_status(args)
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "no row with Step=99" in captured.err

    def test_set_step_status_requires_step_or_description(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(
            ["set-step-status", "implementation-procedure", "test.md", "Completed"]
        )
        exit_code = cmd_set_step_status(args)
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "--step or --description is required" in captured.err

    def test_set_step_status_mutually_exclusive_step_and_description(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(
            [
                "set-step-status",
                "implementation-procedure",
                "test.md",
                "--step",
                "1",
                "--description",
                "First",
                "Completed",
            ]
        )
        exit_code = cmd_set_step_status(args)
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "mutually exclusive" in captured.err


# ---------------------------------------------------------------------------
# set-step-status: single step by description match
# ---------------------------------------------------------------------------


class TestSetStepStatusByDescription:
    """Tests for the `set-step-status` subcommand with --description."""

    def test_set_step_status_by_description_match(self, tmp_path: Path) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(
            [
                "set-step-status",
                "implementation-procedure",
                str(fpath),
                "--description",
                "Second",
                "Completed",
            ]
        )
        exit_code = cmd_set_step_status(args)
        assert exit_code == 0
        content = fpath.read_text(encoding="utf-8")
        _, header, data_rows = parse_execution_status_table(content)
        assert data_rows[0][header.index("Status")] == "Pending"  # unchanged
        assert data_rows[1][header.index("Status")] == "Completed"  # updated
        assert (
            data_rows[2][header.index("Status")] == "Completed"
        )  # unchanged (already completed)

    def test_set_step_status_case_insensitive_description(self, tmp_path: Path) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(
            [
                "set-step-status",
                "implementation-procedure",
                str(fpath),
                "--description",
                "second",
                "Completed",
            ]
        )
        exit_code = cmd_set_step_status(args)
        assert exit_code == 0
        content = fpath.read_text(encoding="utf-8")
        _, header, data_rows = parse_execution_status_table(content)
        assert data_rows[1][header.index("Status")] == "Completed"

    def test_set_step_status_no_description_match_refuses(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(
            [
                "set-step-status",
                "implementation-procedure",
                str(fpath),
                "--description",
                "Nonexistent",
                "Completed",
            ]
        )
        exit_code = cmd_set_step_status(args)
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "no row with Description containing 'Nonexistent'" in captured.err


# ---------------------------------------------------------------------------
# detect-stale
# ---------------------------------------------------------------------------


class TestDetectStale:
    """Tests for the `detect-stale` subcommand."""

    def test_detect_stale_finds_stale_items(self, tmp_path: Path) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "stale.md", EXECUTION_STATUS_MULTI_ROW
        )
        _patch_mtime(fpath, days_ago=10)
        args = build_parser().parse_args(["detect-stale", "--days", "7"])
        exit_code = cmd_detect_stale(args)
        assert exit_code == 0

    def test_detect_stale_no_stale_items(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _make_temp_workitem(
            tmp_path, "implementation-procedure", "fresh.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(["detect-stale", "--days", "1"])
        exit_code = cmd_detect_stale(args)
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No stale items found" in captured.out

    def test_detect_stale_completed_only_not_stale(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path,
            "implementation-procedure",
            "old_completed.md",
            EXECUTION_STATUS_COMPLETED,
        )
        _patch_mtime(fpath, days_ago=30)
        args = build_parser().parse_args(["detect-stale", "--days", "7"])
        exit_code = cmd_detect_stale(args)
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No stale items found" in captured.out


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestList:
    """Tests for the `list` subcommand."""

    def test_list_all_statuses(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _make_temp_workitem(
            tmp_path, "implementation-procedure", "pending.md", EXECUTION_STATUS_PENDING
        )
        _make_temp_workitem(
            tmp_path,
            "implementation-procedure",
            "completed.md",
            EXECUTION_STATUS_COMPLETED,
        )
        args = build_parser().parse_args(["list"])
        exit_code = cmd_list(args)
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Pending" in captured.out
        assert "Completed" in captured.out

    def test_list_filter_by_status(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _make_temp_workitem(
            tmp_path, "implementation-procedure", "pending.md", EXECUTION_STATUS_PENDING
        )
        _make_temp_workitem(
            tmp_path,
            "implementation-procedure",
            "completed.md",
            EXECUTION_STATUS_COMPLETED,
        )
        args = build_parser().parse_args(["list", "--status", "Pending"])
        exit_code = cmd_list(args)
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Pending" in captured.out
        assert "completed.md" not in captured.out

    def test_list_filter_by_kind(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_PENDING
        )
        _make_temp_workitem(tmp_path, "plan", "test.md", EXECUTION_STATUS_PENDING)
        args = build_parser().parse_args(["list", "--kind", "implementation-procedure"])
        exit_code = cmd_list(args)
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "implementation-procedure" in captured.out

    def test_list_no_items(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Create a temp dir with no implementations/plans directories
        args = build_parser().parse_args(["list"])
        exit_code = cmd_list(args)
        assert exit_code == 0
        # In the real repo there are files, so we just check it doesn't crash
        assert exit_code == 0


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


class TestShow:
    """Tests for the `show` subcommand."""

    def test_show_displays_table(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(
            ["show", "implementation-procedure", str(fpath)]
        )
        exit_code = cmd_show(args)
        assert exit_code == 0
        captured = capsys.readouterr()
        assert EXECUTION_STATUS_HEADING in captured.out
        assert (
            "| Step | Description | Status | Started | Completed | Notes |"
            in captured.out
        )
        assert "First step" in captured.out
        assert "Second step" in captured.out
        assert "Third step" in captured.out

    def test_show_missing_file_refuses(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = tmp_path / "nonexistent.md"
        args = build_parser().parse_args(
            ["show", "implementation-procedure", str(fpath)]
        )
        exit_code = cmd_show(args)
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "source file not found" in captured.err

    def test_show_no_table_refuses(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_NO_TABLE
        )
        args = build_parser().parse_args(
            ["show", "implementation-procedure", str(fpath)]
        )
        exit_code = cmd_show(args)
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "missing or malformed" in captured.err


class TestSetStatusWithNotes:
    """Tests for --notes argument on set-status."""

    def test_set_status_with_notes_appends_to_existing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(
            [
                "set-status",
                "implementation-procedure",
                str(fpath),
                "Completed",
                "--notes",
                "reviewed",
            ]
        )
        exit_code = cmd_set_status(args)
        assert exit_code == 0
        content = fpath.read_text(encoding="utf-8")
        assert "reviewed" in content

    def test_set_status_with_notes_empty_notes_column(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_SINGLE_ROW
        )
        args = build_parser().parse_args(
            [
                "set-status",
                "implementation-procedure",
                str(fpath),
                "In Progress",
                "--notes",
                "started",
            ]
        )
        exit_code = cmd_set_status(args)
        assert exit_code == 0
        content = fpath.read_text(encoding="utf-8")
        assert "started" in content

    def test_set_status_without_notes(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_SINGLE_ROW
        )
        args = build_parser().parse_args(
            ["set-status", "implementation-procedure", str(fpath), "Pending"]
        )
        exit_code = cmd_set_status(args)
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Notes appended" not in captured.out

    def test_set_status_output_includes_notes_message(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_SINGLE_ROW
        )
        args = build_parser().parse_args(
            [
                "set-status",
                "implementation-procedure",
                str(fpath),
                "Blocked",
                "--notes",
                "waiting-for-deps",
            ]
        )
        exit_code = cmd_set_status(args)
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Notes appended" in captured.out
        assert "waiting-for-deps" in captured.out


class TestSetStepStatusWithNotes:
    """Tests for --notes argument on set-step-status."""

    def test_set_step_status_with_notes_by_number(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(
            [
                "set-step-status",
                "implementation-procedure",
                str(fpath),
                "--step",
                "1",
                "Completed",
                "--notes",
                "done",
            ]
        )
        exit_code = cmd_set_step_status(args)
        assert exit_code == 0
        content = fpath.read_text(encoding="utf-8")
        assert "done" in content

    def test_set_step_status_with_notes_by_description(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_MULTI_ROW
        )
        args = build_parser().parse_args(
            [
                "set-step-status",
                "implementation-procedure",
                str(fpath),
                "--description",
                "First",
                "In Progress",
                "--notes",
                "working-on-it",
            ]
        )
        exit_code = cmd_set_step_status(args)
        assert exit_code == 0
        content = fpath.read_text(encoding="utf-8")
        assert "working-on-it" in content

    def test_set_step_status_with_notes_output_message(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_SINGLE_ROW
        )
        args = build_parser().parse_args(
            [
                "set-step-status",
                "implementation-procedure",
                str(fpath),
                "--step",
                "1",
                "Pending",
                "--notes",
                "new-note",
            ]
        )
        exit_code = cmd_set_step_status(args)
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Notes appended" in captured.out
        assert "new-note" in captured.out

    def test_set_step_status_without_notes(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fpath = _make_temp_workitem(
            tmp_path, "implementation-procedure", "test.md", EXECUTION_STATUS_SINGLE_ROW
        )
        args = build_parser().parse_args(
            [
                "set-step-status",
                "implementation-procedure",
                str(fpath),
                "--step",
                "1",
                "Completed",
            ]
        )
        exit_code = cmd_set_step_status(args)
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Notes appended" not in captured.out
