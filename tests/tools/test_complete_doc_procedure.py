"""tests/tools/test_complete_doc_procedure.py
Tests for tools/complete_doc_procedure.py.

Characterization harness for plan wftool002 (plan Phase 1): every test except the
written-status test and the dry-run group pins the behavior of the tool as it exists
today, so the seq 01 restructure cannot silently drop it. The written-status test and
the dry-run group are the sanctioned Phase 1 red state; they pass once the
COMPLETED_STATUS constant (seq 02) and the tool change (seq 01) land.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

import tools.complete_doc_procedure as cdp

DOC_TEXT = """## Implementation

1. Implement the change.
2. Run the validation sequence.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change | Pending | — | — | land with row `2` |
| 2 | Run the validation sequence | Pending | 20261116-090000 | — | |
| 3 | Update documentation | Blocked | — | — | keep |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |
"""

MEMO_TEXT = """# Memo

- implementations/20261117-090000_other.md
- implementations/procedure.md
"""

NO_PENDING_TEXT = DOC_TEXT.replace("| Pending |", "| Completed |")

NO_ANCHOR_TEXT = """## Implementation

1. Implement the change.

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |
"""

FINDINGS_TEXT = DOC_TEXT.replace(
    "### Blocker Log",
    "### Verification Findings\n"
    "| Item | Finding | Action taken |\n"
    "|------|---------|--------------|\n"
    "| OLD | old finding | old action |\n"
    "\n### Blocker Log",
)


def _doc(path: Path, text: str = DOC_TEXT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _memo(path: Path, text: str = MEMO_TEXT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _done_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Repoint the tool's archive directory so the real implementations/done/ is untouched."""
    done = tmp_path / "done"
    done.mkdir(exist_ok=True)
    monkeypatch.setattr(cdp, "DONE_DIR", done)
    return done


def _rows(path: Path) -> list[list[str]]:
    """Return the Execution Status data rows of a document as cell lists."""
    lines = path.read_text(encoding="utf-8").splitlines()
    head = next(i for i, ln in enumerate(lines) if ln.strip() == "### Execution Status")
    rows: list[list[str]] = []
    for line in lines[head + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r"-+", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestStatusRows:
    """Only `Pending` rows are rewritten, with one shared stamp and the given step notes."""

    def test_only_pending_rows_are_rewritten(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path / "procedure.md")

        code = cdp.main([str(doc), "--no-archive"])

        assert code == 0
        rows = _rows(doc)
        assert rows[0][2] != "Pending"
        assert rows[1][2] != "Pending"
        assert rows[2] == ["3", "Update documentation", "Blocked", "—", "—", "keep"]

    def test_descriptions_are_never_rewritten(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path / "procedure.md")

        cdp.main([str(doc), "--no-archive"])

        assert [row[1] for row in _rows(doc)] == [
            "Implement the change",
            "Run the validation sequence",
            "Update documentation",
        ]

    def test_step_notes_fill_notes_and_unmatched_steps_are_empty(
        self, tmp_path: Path
    ) -> None:
        doc = _doc(tmp_path / "procedure.md")

        cdp.main(
            [str(doc), "--no-archive", "--step1-note", "doc edit", "--step3-note", "x"]
        )

        rows = _rows(doc)
        assert rows[0][5] == "doc edit"
        assert rows[1][5] == ""

    def test_rewritten_rows_share_one_stamp_in_started_and_completed(
        self, tmp_path: Path
    ) -> None:
        doc = _doc(tmp_path / "procedure.md")

        cdp.main([str(doc), "--no-archive"])

        rows = _rows(doc)
        stamps = {row[3] for row in rows[:2]} | {row[4] for row in rows[:2]}
        assert len(stamps) == 1
        (stamp,) = stamps
        assert stamp.strip() != ""
        assert stamp != "20261116-090000"

    def test_row_with_too_few_cells_is_skipped(self, tmp_path: Path) -> None:
        broken_row = "| 2 | Run the validation sequence | Pending |"
        doc = _doc(
            tmp_path / "procedure.md",
            DOC_TEXT.replace(
                "| 2 | Run the validation sequence | Pending | 20261116-090000 | — | |",
                broken_row,
            ),
        )

        code = cdp.main([str(doc), "--no-archive"])

        assert code == 0
        assert broken_row in doc.read_text(encoding="utf-8")
        assert _rows(doc)[0][2] != "Pending"

    def test_missing_status_anchor_is_exit_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        doc = _doc(tmp_path / "procedure.md", NO_ANCHOR_TEXT)
        before = _digest(doc)

        code = cdp.main([str(doc), "--no-archive"])

        assert code == 1
        assert "anchor not found: ### Execution Status" in capsys.readouterr().err
        assert _digest(doc) == before

    def test_no_pending_rows_is_exit_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        doc = _doc(tmp_path / "procedure.md", NO_PENDING_TEXT)
        before = _digest(doc)

        code = cdp.main([str(doc), "--no-archive"])

        assert code == 1
        assert "no Pending rows found in Execution Status" in capsys.readouterr().err
        assert _digest(doc) == before

    def test_missing_procedure_doc_is_exit_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = cdp.main([str(tmp_path / "absent.md")])

        assert code == 2
        assert "procedure doc not found" in capsys.readouterr().err

    def test_written_status_is_the_shared_completed_constant(
        self, tmp_path: Path
    ) -> None:
        from tools._workitem_status_table import (
            _VALID_STATUSES,
            COMPLETED_STATUS,
            parse_execution_status_rows,
        )

        doc = _doc(tmp_path / "procedure.md")

        code = cdp.main([str(doc), "--no-archive"])

        assert code == 0
        assert [row[2] for row in _rows(doc)] == [
            COMPLETED_STATUS,
            COMPLETED_STATUS,
            "Blocked",
        ]
        parsed = parse_execution_status_rows(doc.read_text(encoding="utf-8"))
        assert parsed is not None
        assert [row["Status"] for row in parsed] == [
            COMPLETED_STATUS,
            COMPLETED_STATUS,
            "Blocked",
        ]
        assert all(row["Status"] in _VALID_STATUSES for row in parsed)
        assert "Done" not in _VALID_STATUSES


class TestVerificationFindings:
    """The findings table is inserted once, before `### Blocker Log`, from `--vf` rows."""

    def test_absent_section_is_created_before_blocker_log(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path / "procedure.md")

        code = cdp.main(
            [str(doc), "--no-archive", "--vf", "VF-1|finding one|action one"]
        )

        assert code == 0
        text = doc.read_text(encoding="utf-8")
        assert text.count("### Verification Findings") == 1
        assert "| VF-1 | finding one | action one |" in text
        assert text.index("### Verification Findings") < text.index("### Blocker Log")

    def test_existing_section_is_left_untouched(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path / "procedure.md", FINDINGS_TEXT)

        code = cdp.main([str(doc), "--no-archive", "--vf", "VF-1|new finding|action"])

        assert code == 0
        text = doc.read_text(encoding="utf-8")
        assert text.count("### Verification Findings") == 1
        assert "| OLD | old finding | old action |" in text
        assert "new finding" not in text

    def test_malformed_vf_row_is_exit_2_and_writes_nothing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        doc = _doc(tmp_path / "procedure.md")
        before = _digest(doc)

        code = cdp.main([str(doc), "--no-archive", "--vf", "bad-row"])

        assert code == 2
        assert "--vf needs ITEM|FINDING|ACTION: bad-row" in capsys.readouterr().err
        assert _digest(doc) == before

    def test_missing_blocker_log_anchor_is_exit_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        doc = _doc(
            tmp_path / "procedure.md", DOC_TEXT.replace("### Blocker Log", "### Notes")
        )
        before = _digest(doc)

        code = cdp.main([str(doc), "--no-archive", "--vf", "VF-1|finding|action"])

        assert code == 1
        assert "anchor not found: ### Blocker Log" in capsys.readouterr().err
        assert _digest(doc) == before


class TestUsage:
    """Usage errors exit 2 with the tool's own messages, never a traceback."""

    def test_no_arguments_is_exit_2(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = cdp.main([])

        assert code == 2
        assert "Usage:" in capsys.readouterr().err

    def test_unknown_option_is_exit_2(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        doc = _doc(tmp_path / "procedure.md")

        code = cdp.main([str(doc), "--bogus"])

        assert code == 2
        assert "unknown option: --bogus" in capsys.readouterr().err

    def test_entry_point_returns_an_int(self, tmp_path: Path) -> None:
        doc = _doc(tmp_path / "procedure.md")

        assert isinstance(cdp.main([str(doc), "--no-archive"]), int)


class TestMemoAndArchive:
    """The memo line is matched by filename and the archive refuses a taken destination."""

    def test_memo_line_is_removed_by_filename(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        doc = _doc(tmp_path / "procedure.md")
        memo = _memo(tmp_path / "memo.md")
        done = _done_dir(monkeypatch, tmp_path)

        code = cdp.main([str(doc), "--memo", str(memo)])

        assert code == 0
        kept = memo.read_text(encoding="utf-8")
        assert "procedure.md" not in kept
        assert "20261117-090000_other.md" in kept
        assert not doc.exists()
        archived = done / "procedure.md"
        assert archived.is_file()
        assert "| Blocked |" in archived.read_text(encoding="utf-8")

    def test_no_memo_line_match_is_exit_1(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        doc = _doc(tmp_path / "procedure.md")
        memo = _memo(tmp_path / "memo.md", "# Memo\n\n- implementations/other.md\n")
        done = _done_dir(monkeypatch, tmp_path)

        code = cdp.main([str(doc), "--memo", str(memo)])

        assert code == 1
        assert "no memo line matched: procedure.md" in capsys.readouterr().err
        assert (
            memo.read_text(encoding="utf-8") == "# Memo\n\n- implementations/other.md\n"
        )
        assert list(done.iterdir()) == []

    def test_absent_memo_is_skipped_with_exit_0(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        doc = _doc(tmp_path / "procedure.md")
        done = _done_dir(monkeypatch, tmp_path)
        missing = tmp_path / "absent-memo.md"

        code = cdp.main([str(doc), "--memo", str(missing)])

        assert code == 0
        assert "memo not found, skipped" in capsys.readouterr().err
        assert not missing.exists()
        assert (done / "procedure.md").is_file()

    def test_taken_archive_destination_is_exit_1(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        doc = _doc(tmp_path / "procedure.md")
        memo = _memo(tmp_path / "memo.md")
        done = _done_dir(monkeypatch, tmp_path)
        (done / "procedure.md").write_text("existing\n", encoding="utf-8")

        code = cdp.main([str(doc), "--memo", str(memo)])

        assert code == 1
        assert "archive destination exists" in capsys.readouterr().err
        assert doc.is_file()
        assert (done / "procedure.md").read_text(encoding="utf-8") == "existing\n"
        assert "procedure.md" in memo.read_text(encoding="utf-8")

    def test_no_archive_leaves_the_file_and_memo_in_place(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        doc = _doc(tmp_path / "procedure.md")
        memo = _memo(tmp_path / "memo.md")
        done = _done_dir(monkeypatch, tmp_path)

        code = cdp.main([str(doc), "--memo", str(memo), "--no-archive"])

        assert code == 0
        assert doc.is_file()
        assert list(done.iterdir()) == []
        assert "procedure.md" in memo.read_text(encoding="utf-8")


class TestDryRun:
    """`--dry-run` previews the diff and writes, renames, and edits nothing (AC-2)."""

    def test_dry_run_prints_the_diff_and_writes_nothing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        doc = _doc(tmp_path / "procedure.md")
        memo = _memo(tmp_path / "memo.md")
        done = _done_dir(monkeypatch, tmp_path)
        before = (_digest(doc), _digest(memo))

        code = cdp.main([str(doc), "--memo", str(memo), "--dry-run"])
        out = capsys.readouterr().out

        assert code == 0
        assert (_digest(doc), _digest(memo)) == before
        assert doc.is_file()
        assert list(done.iterdir()) == []
        assert {path.name for path in tmp_path.iterdir()} == {
            "procedure.md",
            "memo.md",
            "done",
        }
        assert "+|" in out

    def test_dry_run_leaves_a_real_run_result_untouched(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        doc = _doc(tmp_path / "procedure.md")
        memo = _memo(tmp_path / "memo.md")
        _done_dir(monkeypatch, tmp_path)
        before = (_digest(doc), _digest(memo))

        code = cdp.main([str(doc), "--memo", str(memo), "--dry-run"])

        assert code == 0
        assert (_digest(doc), _digest(memo)) == before

    def test_dry_run_returns_the_exit_codes_of_the_real_runs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        done = _done_dir(monkeypatch, tmp_path)
        cases: list[tuple[int, list[str]]] = []

        anchor_doc = _doc(tmp_path / "anchor" / "procedure.md", NO_ANCHOR_TEXT)
        cases.append((1, [str(anchor_doc), "--dry-run"]))

        taken_doc = _doc(tmp_path / "taken" / "procedure.md")
        (done / "procedure.md").write_text("existing\n", encoding="utf-8")
        cases.append(
            (
                1,
                [
                    str(taken_doc),
                    "--memo",
                    str(_memo(tmp_path / "taken" / "memo.md")),
                    "--dry-run",
                ],
            )
        )

        nomemo_doc = _doc(tmp_path / "nomemo" / "procedure.md")
        cases.append(
            (
                1,
                [
                    str(nomemo_doc),
                    "--memo",
                    str(
                        _memo(tmp_path / "nomemo" / "memo.md", "# Memo\n\n- other.md\n")
                    ),
                    "--dry-run",
                ],
            )
        )

        unknown_doc = _doc(tmp_path / "unknown" / "procedure.md")
        cases.append((2, [str(unknown_doc), "--bogus", "--dry-run"]))

        for expected, argv in cases:
            assert cdp.main(argv) == expected
