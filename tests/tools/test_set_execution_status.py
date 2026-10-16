"""tests/tools/test_set_execution_status.py
Tests for tools/set_execution_status.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.set_execution_status as ses

DOC_TEXT = """## Implementation

1. Remove the import.
2. Update the docstrings.
3. Run the validation sequence.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the import | Pending | \u2014 | \u2014 | land with row `20` |
| 2 | Update the docstrings | Pending | \u2014 | \u2014 | |
| 3 | Run the validation sequence | Pending | 2026-10-16 | \u2014 | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| \u2014 | \u2014 | \u2014 | \u2014 |
"""


def _doc(tmp_path: Path, text: str = DOC_TEXT) -> Path:
    path = tmp_path / "procedure.md"
    path.write_text(text)
    return path


def _rows(path: Path) -> list[list[str]]:
    """Return the Execution Status data rows of a document as cell lists."""
    lines = path.read_text().splitlines()
    start, end = ses.find_table(lines)
    return [ses.split_row(line) for line in lines[start:end]]


class TestFindTable:
    """find_table locates the data rows and nothing else."""

    def test_locates_only_the_execution_status_rows(self, tmp_path: Path) -> None:
        lines = DOC_TEXT.splitlines()
        start, end = ses.find_table(lines)

        assert [line.strip().startswith("|") for line in lines[start:end]] == [True] * 3
        assert "Blocker Description" not in "\n".join(lines[start:end])

    def test_missing_heading_is_an_error(self, tmp_path: Path) -> None:
        with pytest.raises(ses.ExecutionStatusError, match="heading"):
            ses.find_table("## Implementation\n\n| a | b |\n".splitlines())

    def test_malformed_row_is_an_error(self, tmp_path: Path) -> None:
        broken = DOC_TEXT.replace(
            "| 3 | Run the validation sequence | Pending | 2026-10-16 | \u2014 | |",
            "| 3 | Run the validation sequence | Pending |",
        )
        with pytest.raises(ses.ExecutionStatusError, match="cells"):
            ses.update_document(_doc(tmp_path, broken), None, {}, "2026-10-17")


class TestMarkingRows:
    """Selected rows become Completed; unselected rows keep their state."""

    def test_all_marks_every_row(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path)
        code = ses.main([str(doc), "--all", "--date", "2026-10-17"])

        assert code == 0
        rows = _rows(doc)
        assert [row[2] for row in rows] == ["Completed"] * 3
        assert [row[4] for row in rows] == ["2026-10-17"] * 3

    def test_step_selects_only_named_rows(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path)
        ses.main([str(doc), "--step", "1,3", "--date", "2026-10-17"])

        rows = _rows(doc)
        assert [row[2] for row in rows] == ["Completed", "Pending", "Completed"]

    def test_description_column_is_never_rewritten(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path)
        ses.main([str(doc), "--all", "--date", "2026-10-17"])

        assert [row[1] for row in _rows(doc)] == [
            "Remove the import",
            "Update the docstrings",
            "Run the validation sequence",
        ]

    def test_existing_started_date_is_preserved(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path)
        ses.main([str(doc), "--step", "3", "--date", "2026-10-17"])

        assert _rows(doc)[2][3] == "2026-10-16"

    def test_empty_started_cell_gets_the_date(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path)
        ses.main([str(doc), "--step", "1", "--date", "2026-10-17"])

        assert _rows(doc)[0][3] == "2026-10-17"

    def test_notes_are_replaced_only_when_supplied(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path)
        ses.main(
            [
                str(doc),
                "--all",
                "--date",
                "2026-10-17",
                "--note",
                "2:no audit names remain",
            ]
        )

        rows = _rows(doc)
        assert rows[0][5] == "land with row `20`"
        assert rows[1][5] == "no audit names remain"

    def test_other_tables_are_left_untouched(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path)
        ses.main([str(doc), "--all", "--date", "2026-10-17"])

        assert "| \u2014 | \u2014 | \u2014 | \u2014 |" in doc.read_text()


class TestRefusals:
    """A typo in the step list fails instead of silently skipping a step."""

    def test_unknown_step_is_refused(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path)
        code = ses.main([str(doc), "--step", "9", "--date", "2026-10-17"])

        assert code == 1
        assert "Pending" in doc.read_text()

    def test_note_for_an_unselected_step_is_refused(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path)
        code = ses.main([str(doc), "--step", "1", "--note", "3:wrong row"])

        assert code == 1
        assert _rows(doc)[2][5] == ""

    def test_missing_document_is_refused(self, tmp_path: Path) -> None:
        code = ses.main([str(tmp_path / "absent.md"), "--all"])

        assert code == 1
