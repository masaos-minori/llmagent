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


class TestMultiPathCli:
    """The CLI accepts several paths: validates all before writing, guards per
    path, and aggregates the per-path exit codes."""

    def _two_paths(self, tmp_path: Path, text: str = PROC_TEXT) -> tuple[Path, Path]:
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text(text, encoding="utf-8")
        b.write_text(text, encoding="utf-8")
        return a, b

    def test_list_reports_each_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a, b = self._two_paths(tmp_path)
        seen: list[str] = []

        def fake(_proc: Path) -> list[str]:
            seen.append(_proc.name)
            return ["REASON_OK"]

        monkeypatch.setattr(mps, "reported_missing_symbols", fake)

        rc = mps.main(["list", str(a), str(b)])

        assert rc == 0
        assert sorted(seen) == ["a.md", "b.md"]

    def test_mark_writes_to_every_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a, b = self._two_paths(tmp_path)
        monkeypatch.setattr(mps, "reported_missing_symbols", lambda _: ["REASON_OK"])

        rc = mps.main(["mark", str(a), str(b), "--symbols", "REASON_OK"])

        assert rc == 0
        assert a.read_text(encoding="utf-8").count("`REASON_OK` (new)") == 2
        assert b.read_text(encoding="utf-8").count("`REASON_OK` (new)") == 2

    def test_unusable_path_exits_two_before_any_write(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        good, _ = self._two_paths(tmp_path)
        good_before = good.read_bytes()

        rc = mps.main(["mark", str(good), str(tmp_path / "absent.md"), "--all"])

        assert rc == 2
        assert good.read_bytes() == good_before

    def test_refusal_applies_per_path_and_aggregates(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        a, b = self._two_paths(tmp_path)

        def fake(_proc: Path) -> list[str]:
            return ["REASON_OK"] if _proc.name == "a.md" else []

        monkeypatch.setattr(mps, "reported_missing_symbols", fake)

        rc = mps.main(["mark", str(a), str(b), "--symbols", "REASON_OK", "--dry-run"])

        out = capsys.readouterr().out
        assert rc == 1
        assert "REFUSED: 'REASON_OK'" in out
        assert "Nothing to mark." in out
        assert a.read_text(encoding="utf-8") == PROC_TEXT

    def test_all_paths_succeed_returns_zero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a, b = self._two_paths(tmp_path)
        monkeypatch.setattr(mps, "reported_missing_symbols", lambda _: ["REASON_OK"])

        rc = mps.main(["mark", str(a), str(b), "--symbols", "REASON_OK", "--dry-run"])

        assert rc == 0

    def test_real_run_writes_utf8_to_all_paths(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        text = "Create `alpha` and `beta`.\nSee existing 日本 ünï.\n"
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text(text, encoding="utf-8")
        b.write_text(text, encoding="utf-8")
        monkeypatch.setattr(mps, "reported_missing_symbols", lambda _: ["alpha"])

        rc = mps.main(["mark", str(a), str(b), "--symbols", "alpha"])

        expected = "Create `alpha` (new) and `beta`.\nSee existing 日本 ünï.\n"
        assert rc == 0
        assert a.read_bytes() == expected.encode("utf-8")
        assert b.read_bytes() == expected.encode("utf-8")

    def test_already_marked_name_left_alone_at_cli(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        doc = tmp_path / "p.md"
        original = "See `alpha` (new) and `beta`.\n"
        doc.write_text(original, encoding="utf-8")
        monkeypatch.setattr(mps, "reported_missing_symbols", lambda _: ["alpha"])

        rc = mps.main(["mark", str(doc), "--symbols", "alpha"])

        assert rc == 0
        assert doc.read_text(encoding="utf-8") == original
