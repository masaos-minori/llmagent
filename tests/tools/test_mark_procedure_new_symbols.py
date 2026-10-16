"""tests/tools/test_mark_procedure_new_symbols.py
Tests for tools/mark_procedure_new_symbols.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.mark_procedure_new_symbols as mps

PROC_TEXT = """## Procedure

1. Define `SecurityCheckStatus` (new) as a `StrEnum`.
2. Define `SECURITY_REASON_CODES` and `REASON_OK`.
3. Keep `REASON_OK` out of `message`.
"""


class TestMarkNames:
    """mark_names inserts the marker only where one is absent."""

    def test_marks_unmarked_occurrences(self) -> None:
        rewritten, counts = mps.mark_names(
            PROC_TEXT, ["SECURITY_REASON_CODES", "REASON_OK"]
        )

        assert counts == {"SECURITY_REASON_CODES": 1, "REASON_OK": 2}
        assert "`SECURITY_REASON_CODES` (new)" in rewritten
        assert rewritten.count("`REASON_OK` (new)") == 2

    def test_already_marked_occurrence_is_left_alone(self) -> None:
        rewritten, counts = mps.mark_names(PROC_TEXT, ["SecurityCheckStatus"])

        assert counts == {"SecurityCheckStatus": 0}
        assert rewritten == PROC_TEXT

    def test_is_idempotent(self) -> None:
        first, _ = mps.mark_names(PROC_TEXT, ["REASON_OK"])
        second, counts = mps.mark_names(first, ["REASON_OK"])

        assert second == first
        assert counts == {"REASON_OK": 0}

    def test_name_is_matched_as_a_whole_backticked_token(self) -> None:
        text = "`REASON_OK_EXTRA` and `REASON_OK`\n"
        rewritten, counts = mps.mark_names(text, ["REASON_OK"])

        assert counts == {"REASON_OK": 1}
        assert "`REASON_OK_EXTRA`" in rewritten
        assert "`REASON_OK` (new)" in rewritten


class TestUnmarkedLines:
    """unmarked_lines reports 1-based line numbers of unmarked occurrences."""

    def test_reports_lines_and_skips_marked_ones(self) -> None:
        assert mps.unmarked_lines(PROC_TEXT, "REASON_OK") == [4, 5]
        assert mps.unmarked_lines(PROC_TEXT, "SecurityCheckStatus") == []


class TestPrintMark:
    """A name stale_detector does not report as missing is refused."""

    def test_refuses_an_existing_symbol(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        proc = tmp_path / "proc.md"
        proc.write_text(PROC_TEXT, encoding="utf-8")
        monkeypatch.setattr(mps, "reported_missing_symbols", lambda _: ["REASON_OK"])

        rc = mps._print_mark(
            proc, ["REASON_OK", "audit_security_defaults"], dry_run=True
        )

        out = capsys.readouterr().out
        assert rc == 0
        assert "REFUSED: 'audit_security_defaults'" in out
        assert "DRY RUN: 2 marker(s)" in out
        assert proc.read_text(encoding="utf-8") == PROC_TEXT

    def test_dry_run_does_not_write(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        proc = tmp_path / "proc.md"
        proc.write_text(PROC_TEXT, encoding="utf-8")
        monkeypatch.setattr(mps, "reported_missing_symbols", lambda _: ["REASON_OK"])

        rc = mps._print_mark(proc, ["REASON_OK"], dry_run=True)

        assert rc == 0
        assert proc.read_text(encoding="utf-8") == PROC_TEXT

    def test_writes_when_not_dry_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        proc = tmp_path / "proc.md"
        proc.write_text(PROC_TEXT, encoding="utf-8")
        monkeypatch.setattr(mps, "reported_missing_symbols", lambda _: ["REASON_OK"])

        rc = mps._print_mark(proc, ["REASON_OK"], dry_run=False)

        assert rc == 0
        assert proc.read_text(encoding="utf-8").count("`REASON_OK` (new)") == 2

    def test_all_requested_names_refused_returns_nonzero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        proc = tmp_path / "proc.md"
        proc.write_text(PROC_TEXT, encoding="utf-8")
        monkeypatch.setattr(mps, "reported_missing_symbols", lambda _: [])

        rc = mps._print_mark(proc, ["audit_security_defaults"], dry_run=True)

        assert rc == 1


class TestCli:
    """The CLI resolves a missing file and the --symbols/--all contract."""

    def test_missing_file_is_an_error(self, tmp_path: Path) -> None:
        assert mps.main(["mark", str(tmp_path / "absent.md"), "--all"]) == 2

    def test_mark_requires_symbols_or_all(self, tmp_path: Path) -> None:
        proc = tmp_path / "proc.md"
        proc.write_text(PROC_TEXT, encoding="utf-8")

        assert mps.main(["mark", str(proc)]) == 2

    def test_mark_with_symbols(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        proc = tmp_path / "proc.md"
        proc.write_text(PROC_TEXT, encoding="utf-8")
        monkeypatch.setattr(mps, "reported_missing_symbols", lambda _: ["REASON_OK"])

        rc = mps.main(["mark", str(proc), "--symbols", "REASON_OK", "--dry-run"])

        assert rc == 0
