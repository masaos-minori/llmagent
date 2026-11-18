"""tests/tools/test_complete_doc_procedure.py
Tests for tools/complete_doc_procedure.py.

Characterization harness for plan wftoolfu002 (doc-procedure-archival): every test
except the shared-completed-constant test pins the behavior of the tool as it exists
today, so the seq 01 restructure cannot silently drop it. The shared-completed-constant
test is the sanctioned red state for the status vocabulary; it passes once the
COMPLETED_STATUS constant (already present in `tools/_workitem_status_table.py`) and the
tool change (seq 01) land.

The archival, refusal, and location families exercise the real repository layout: a
temporary Git repository with `implementations/` and `implementations/done/`, documents
under `implementations/`, and Git staging inspected through the index (the tool archives
through `move_to_done` with `stage_only=True`, so the move shows as a staged rename and
the tool never commits).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import git
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

# A document with only Pending rows: the tool stamps them all to Completed and archives.
# It must carry at least one Pending row (the tool refuses a document with no Pending
# rows) and no In Progress / Blocked row (that would trigger the unfinished-row refusal).
READY_TEXT = """## Implementation

1. Implement the change.
2. Run the validation sequence.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change | Pending | — | — | |
| 2 | Run the validation sequence | Pending | — | — | |
| 3 | Update documentation | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |
"""

# A document with a Pending row plus an In Progress row: stamping clears the Pending row,
# then the unfinished-row refusal catches the In Progress row that stamping skips.
IN_PROGRESS_TEXT = """## Implementation

1. Implement the change.
2. Run the validation sequence.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change | Pending | — | — | stamp |
| 2 | Run the validation sequence | In Progress | — | — | stuck |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |
"""

NO_PENDING_TEXT = DOC_TEXT.replace("| Pending |", "| Completed |")

NO_ANCHOR_TEXT = """## Implementation

1. Implement the change.

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |
"""

MEMO_TEXT = """# Memo

- implementations/20261117-090000_other.md
- implementations/procedure.md
"""

FINDINGS_TEXT = DOC_TEXT.replace(
    "### Blocker Log",
    "### Verification Findings\n"
    "| Item | Finding | Action taken |\n"
    "|------|---------|--------------|\n"
    "| OLD | old finding | old action |\n"
    "\n### Blocker Log",
)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> git.Repo:
    """A temporary Git repository with the real `implementations/` layout.

    Creates `implementations/` and `implementations/done/`, commits a seed file so the
    repository has a HEAD, and repoints the tool's `IMPLEMENTATIONS_DIR`/`DONE_DIR` at it
    so the real repository is untouched. Returns the `git.Repo`.
    """
    (tmp_path / "implementations" / "done").mkdir(parents=True)
    impl = tmp_path / "implementations"
    git_repo = git.Repo.init(tmp_path)
    with git_repo.config_writer() as writer:
        writer.set_value("user", "name", "Test User")
        writer.set_value("user", "email", "test@example.com")
    seed = tmp_path / ".gitkeep"
    seed.write_text("", encoding="utf-8")
    git_repo.index.add([str(seed)])
    git_repo.index.commit("initial commit")
    monkeypatch.setattr(cdp, "DONE_DIR", impl / "done")
    # `raising=False` sets the attribute even before seq 01 adds it, and restores
    # (removes) it after the test; seq 01's real constant is overwritten by the patch.
    monkeypatch.setattr(cdp, "IMPLEMENTATIONS_DIR", impl, raising=False)
    return git_repo


def _doc(repo: git.Repo, name: str, text: str = DOC_TEXT) -> Path:
    """Write a procedure under `implementations/` and commit it so the archive move
    shows as a rename in the index. Caller selects the fixture via `text`."""
    proc = cdp.IMPLEMENTATIONS_DIR / name
    proc.write_text(text, encoding="utf-8")
    repo.index.add([str(proc)])
    repo.index.commit(f"add {name}")
    return proc


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

    def test_only_pending_rows_are_rewritten(
        self, repo: git.Repo, tmp_path: Path
    ) -> None:
        doc = _doc(repo, "procedure.md")

        code = cdp.main([str(doc), "--no-archive"])

        assert code == 0
        rows = _rows(doc)
        assert rows[0][2] != "Pending"
        assert rows[1][2] != "Pending"
        assert rows[2] == ["3", "Update documentation", "Blocked", "—", "—", "keep"]

    def test_descriptions_are_never_rewritten(
        self, repo: git.Repo, tmp_path: Path
    ) -> None:
        doc = _doc(repo, "procedure.md")

        cdp.main([str(doc), "--no-archive"])

        assert [row[1] for row in _rows(doc)] == [
            "Implement the change",
            "Run the validation sequence",
            "Update documentation",
        ]

    def test_step_notes_fill_notes_and_unmatched_steps_are_empty(
        self, repo: git.Repo, tmp_path: Path
    ) -> None:
        doc = _doc(repo, "procedure.md")

        cdp.main(
            [str(doc), "--no-archive", "--step1-note", "doc edit", "--step3-note", "x"]
        )

        rows = _rows(doc)
        assert rows[0][5] == "doc edit"
        assert rows[1][5] == ""

    def test_rewritten_rows_share_one_stamp_in_started_and_completed(
        self, repo: git.Repo, tmp_path: Path
    ) -> None:
        doc = _doc(repo, "procedure.md")

        cdp.main([str(doc), "--no-archive"])

        rows = _rows(doc)
        stamps = {row[3] for row in rows[:2]} | {row[4] for row in rows[:2]}
        assert len(stamps) == 1
        (stamp,) = stamps
        assert stamp.strip() != ""
        assert stamp != "20261116-090000"

    def test_row_with_too_few_cells_is_skipped(
        self, repo: git.Repo, tmp_path: Path
    ) -> None:
        broken_row = "| 2 | Run the validation sequence | Pending |"
        doc = _doc(
            repo,
            "procedure.md",
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
        self, repo: git.Repo, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        doc = _doc(repo, "procedure.md", NO_ANCHOR_TEXT)
        before = _digest(doc)

        code = cdp.main([str(doc), "--no-archive"])

        assert code == 1
        assert "anchor not found: ### Execution Status" in capsys.readouterr().err
        assert _digest(doc) == before

    def test_no_pending_rows_is_exit_1(
        self, repo: git.Repo, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        doc = _doc(repo, "procedure.md", NO_PENDING_TEXT)
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
        self, repo: git.Repo, tmp_path: Path
    ) -> None:
        from tools._workitem_status_table import (
            _VALID_STATUSES,
            COMPLETED_STATUS,
            parse_execution_status_rows,
        )

        doc = _doc(repo, "procedure.md")

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

    def test_absent_section_is_created_before_blocker_log(
        self, repo: git.Repo, tmp_path: Path
    ) -> None:
        doc = _doc(repo, "procedure.md")

        code = cdp.main(
            [str(doc), "--no-archive", "--vf", "VF-1|finding one|action one"]
        )

        assert code == 0
        text = doc.read_text(encoding="utf-8")
        assert text.count("### Verification Findings") == 1
        assert "| VF-1 | finding one | action one |" in text
        assert text.index("### Verification Findings") < text.index("### Blocker Log")

    def test_existing_section_is_left_untouched(
        self, repo: git.Repo, tmp_path: Path
    ) -> None:
        doc = _doc(repo, "procedure.md", FINDINGS_TEXT)

        code = cdp.main([str(doc), "--no-archive", "--vf", "VF-1|new finding|action"])

        assert code == 0
        text = doc.read_text(encoding="utf-8")
        assert text.count("### Verification Findings") == 1
        assert "| OLD | old finding | old action |" in text
        assert "new finding" not in text

    def test_malformed_vf_row_is_exit_2_and_writes_nothing(
        self, repo: git.Repo, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        doc = _doc(repo, "procedure.md")
        before = _digest(doc)

        code = cdp.main([str(doc), "--no-archive", "--vf", "bad-row"])

        assert code == 2
        assert "--vf needs ITEM|FINDING|ACTION: bad-row" in capsys.readouterr().err
        assert _digest(doc) == before

    def test_missing_blocker_log_anchor_is_exit_1(
        self, repo: git.Repo, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        doc = _doc(
            repo, "procedure.md", DOC_TEXT.replace("### Blocker Log", "### Notes")
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
        self, repo: git.Repo, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        doc = _doc(repo, "procedure.md")

        code = cdp.main([str(doc), "--bogus"])

        assert code == 2
        assert "unknown option: --bogus" in capsys.readouterr().err

    def test_entry_point_returns_an_int(self, repo: git.Repo, tmp_path: Path) -> None:
        doc = _doc(repo, "procedure.md")

        assert isinstance(cdp.main([str(doc), "--no-archive"]), int)


class TestUnfinishedRefusal:
    """Archiving a document that still carries an unfinished row exits 1 with nothing written."""

    def _refused(
        self, repo: git.Repo, text: str, capsys: pytest.CaptureFixture[str]
    ) -> Path:
        doc = _doc(repo, "procedure.md", text)
        before = _digest(doc)
        done = cdp.DONE_DIR

        code = cdp.main([str(doc)])

        assert code == 1
        assert _digest(doc) == before
        assert list(done.iterdir()) == []
        return doc

    def test_blocked_row_refused_on_archive(
        self, repo: git.Repo, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        self._refused(repo, DOC_TEXT, capsys)
        message = capsys.readouterr().err
        # The Blocked row (step 3) survives the stamping of the Pending rows and is named.
        assert "3" in message
        assert "Blocked" in message

    def test_in_progress_row_refused_on_archive(
        self, repo: git.Repo, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        doc = self._refused(repo, IN_PROGRESS_TEXT, capsys)
        message = capsys.readouterr().err
        assert "2" in message
        assert "In Progress" in message
        assert doc.read_text(encoding="utf-8").count("In Progress") == 1

    def test_dry_run_refuses_unfinished_like_real_run(
        self, repo: git.Repo, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        doc = _doc(repo, "procedure.md", DOC_TEXT)
        memo = _memo(tmp_path / "memo.md")
        before = (_digest(doc), _digest(memo))

        code = cdp.main([str(doc), "--memo", str(memo), "--dry-run"])

        assert code == 1
        assert (_digest(doc), _digest(memo)) == before
        assert cdp.DONE_DIR is not None
        assert list(cdp.DONE_DIR.iterdir()) == []
        assert "procedure.md" in memo.read_text(encoding="utf-8")


class TestMemoAndArchive:
    """The memo line is matched by filename and the archive refuses a taken destination."""

    def test_memo_line_is_removed_by_filename(
        self, repo: git.Repo, tmp_path: Path
    ) -> None:
        doc = _doc(repo, "procedure.md", READY_TEXT)
        memo = _memo(tmp_path / "memo.md")

        code = cdp.main([str(doc), "--memo", str(memo)])

        assert code == 0
        kept = memo.read_text(encoding="utf-8")
        assert "procedure.md" not in kept
        assert "20261117-090000_other.md" in kept
        assert not doc.exists()
        archived = cdp.DONE_DIR / "procedure.md"
        assert archived.is_file()
        # READY_TEXT had only Pending rows; they are stamped to the shared Completed status.
        assert "| Blocked |" not in archived.read_text(encoding="utf-8")
        assert all("| Completed |" in chunk for chunk in _chunks(archived))

    def test_no_memo_line_match_is_exit_1(
        self,
        repo: git.Repo,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        doc = _doc(repo, "procedure.md", READY_TEXT)
        memo = _memo(tmp_path / "memo.md", "# Memo\n\n- implementations/other.md\n")

        code = cdp.main([str(doc), "--memo", str(memo)])

        assert code == 1
        assert "no memo line matched: procedure.md" in capsys.readouterr().err
        assert (
            memo.read_text(encoding="utf-8") == "# Memo\n\n- implementations/other.md\n"
        )
        assert doc.is_file()
        assert list(cdp.DONE_DIR.iterdir()) == []

    def test_absent_memo_is_skipped_with_exit_0(
        self,
        repo: git.Repo,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        doc = _doc(repo, "procedure.md", READY_TEXT)
        missing = tmp_path / "absent-memo.md"

        code = cdp.main([str(doc), "--memo", str(missing)])

        assert code == 0
        assert "memo not found, skipped" in capsys.readouterr().err
        assert not missing.exists()
        assert (cdp.DONE_DIR / "procedure.md").is_file()

    def test_taken_archive_destination_is_exit_1(
        self,
        repo: git.Repo,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        doc = _doc(repo, "procedure.md", READY_TEXT)
        memo = _memo(tmp_path / "memo.md")
        (cdp.DONE_DIR / "procedure.md").write_text("existing\n", encoding="utf-8")

        code = cdp.main([str(doc), "--memo", str(memo)])

        assert code == 1
        assert "archive destination exists" in capsys.readouterr().err
        assert doc.is_file()
        assert (cdp.DONE_DIR / "procedure.md").read_text(
            encoding="utf-8"
        ) == "existing\n"
        assert "procedure.md" in memo.read_text(encoding="utf-8")

    def test_no_archive_leaves_the_file_and_memo_in_place(
        self, repo: git.Repo, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        doc = _doc(repo, "procedure.md", READY_TEXT)
        memo = _memo(tmp_path / "memo.md")

        code = cdp.main([str(doc), "--memo", str(memo), "--no-archive"])

        assert code == 0
        assert doc.is_file()
        assert list(cdp.DONE_DIR.iterdir()) == []
        assert "procedure.md" in memo.read_text(encoding="utf-8")


class TestSanctionedArchival:
    """A finished document archives through `move_to_done` as a staged rename (AC-1)."""

    def test_archival_is_a_staged_rename_into_done(
        self, repo: git.Repo, tmp_path: Path
    ) -> None:
        doc = _doc(repo, "procedure.md", READY_TEXT)
        memo = _memo(tmp_path / "memo.md")
        before_head = repo.head.commit.hexsha

        code = cdp.main([str(doc), "--memo", str(memo)])

        assert code == 0
        assert not doc.exists()
        dest = cdp.DONE_DIR / "procedure.md"
        assert dest.is_file()
        # The stamped rows survive into the archived copy.
        assert all("| Completed |" in chunk for chunk in _chunks(dest))
        # The move shows as a staged rename; the tool never commits.
        assert repo.head.commit.hexsha == before_head
        name_status = repo.git.diff("--cached", "--name-status")
        assert any(
            part.startswith("R")
            for line in name_status.splitlines()
            for part in line.split()
        )

    def test_location_refusal_at_root_is_exit_2(
        self, repo: git.Repo, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        proc = tmp_path / "root_proc.md"
        proc.write_text(DOC_TEXT, encoding="utf-8")
        before = _digest(proc)

        code = cdp.main([str(proc)])

        assert code == 2
        assert str(proc) in capsys.readouterr().err
        assert _digest(proc) == before
        assert list(cdp.DONE_DIR.iterdir()) == []

    def test_location_refusal_inside_done_is_exit_2(
        self, repo: git.Repo, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        inside = cdp.DONE_DIR / "inside.md"
        inside.write_text(READY_TEXT, encoding="utf-8")
        before = _digest(inside)

        code = cdp.main([str(inside)])

        assert code == 2
        assert str(inside) in capsys.readouterr().err
        assert _digest(inside) == before


class TestDryRun:
    """`--dry-run` previews the diff and writes, renames, and edits nothing (AC-4)."""

    def test_dry_run_prints_the_diff_and_writes_nothing(
        self,
        repo: git.Repo,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        doc = _doc(repo, "procedure.md", READY_TEXT)
        memo = _memo(tmp_path / "memo.md")
        before = (_digest(doc), _digest(memo))

        code = cdp.main([str(doc), "--memo", str(memo), "--dry-run"])
        out = capsys.readouterr().out

        assert code == 0
        assert (_digest(doc), _digest(memo)) == before
        assert doc.is_file()
        assert list(cdp.DONE_DIR.iterdir()) == []
        assert "+|" in out

    def test_dry_run_leaves_a_real_run_result_untouched(
        self, repo: git.Repo, tmp_path: Path
    ) -> None:
        doc = _doc(repo, "procedure.md", READY_TEXT)
        memo = _memo(tmp_path / "memo.md")
        before = (_digest(doc), _digest(memo))

        code = cdp.main([str(doc), "--memo", str(memo), "--dry-run"])

        assert code == 0
        assert (_digest(doc), _digest(memo)) == before

    def test_dry_run_returns_the_exit_codes_of_the_real_runs(
        self, repo: git.Repo, tmp_path: Path
    ) -> None:
        cases: list[tuple[int, list[str]]] = []

        anchor_doc = _doc(repo, "anchor.md", NO_ANCHOR_TEXT)
        cases.append((1, [str(anchor_doc), "--dry-run"]))

        taken_doc = _doc(repo, "taken.md", READY_TEXT)
        (cdp.DONE_DIR / "taken.md").write_text("existing\n", encoding="utf-8")
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

        unfinished_doc = _doc(repo, "unfinished.md", DOC_TEXT)
        cases.append(
            (
                1,
                [
                    str(unfinished_doc),
                    "--memo",
                    str(_memo(tmp_path / "unfinished" / "memo.md")),
                    "--dry-run",
                ],
            )
        )

        unknown_doc = _doc(repo, "unknown.md", READY_TEXT)
        cases.append((2, [str(unknown_doc), "--bogus", "--dry-run"]))

        for expected, argv in cases:
            assert cdp.main(argv) == expected


def _memo(path: Path, text: str = MEMO_TEXT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _chunks(path: Path) -> list[str]:
    """The Execution Status data rows of a document as full lines (for substring asserts)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    head = next(i for i, ln in enumerate(lines) if ln.strip() == "### Execution Status")
    chunks: list[str] = []
    for line in lines[head + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r"-+", cell) for cell in cells):
            continue
        chunks.append(line)
    return chunks
