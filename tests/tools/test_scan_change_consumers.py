"""tests/tools/test_scan_change_consumers.py
Tests for tools/scan_change_consumers.py.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
from pathlib import Path

import orjson
import pytest

import tools.scan_change_consumers as scc

_NOW = 1_800_000_000.0
_DAY = 86400.0
_MODULE_TEXT = "def SEED() -> int:\n    return 1\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _files(root: Path) -> list[str]:
    return sorted(
        p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
    )


def _scan(root: Path, *seeds: str, now: float = _NOW) -> scc.Report:
    return scc.scan(root, _files(root), list(seeds), now=now)


def _paths(report: scc.Report, category: str) -> set[str]:
    return {c.path for c in report.candidates if c.category == category}


def _make_testmon(root: Path, *, tables: bool = True) -> Path:
    path = root / scc.TESTMON_FILE
    conn = sqlite3.connect(path)
    try:
        if tables:
            conn.executescript(
                "CREATE TABLE test_execution (id INTEGER PRIMARY KEY,"
                " environment_id INTEGER, test_name TEXT);"
                "CREATE TABLE file_fp (id INTEGER PRIMARY KEY, filename TEXT);"
                "CREATE TABLE test_execution_file_fp ("
                " test_execution_id INTEGER, fingerprint_id INTEGER);"
                "INSERT INTO test_execution VALUES (1, 1, 'tests/test_a.py::test_x');"
                "INSERT INTO test_execution VALUES (2, 1, 'tests/test_a.py::test_y');"
                "INSERT INTO file_fp VALUES (1, 'scripts/agent/mod.py');"
                "INSERT INTO test_execution_file_fp VALUES (1, 1);"
                "INSERT INTO test_execution_file_fp VALUES (2, 1);"
            )
        else:
            conn.execute("CREATE TABLE unrelated (x INTEGER)")
        conn.commit()
    finally:
        conn.close()
    return path


def _set_age(path: Path, days: float) -> None:
    stamp = _NOW - days * _DAY
    os.utime(path, (stamp, stamp))


def _snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        rel: ((root / rel).read_bytes(), (root / rel).stat().st_mtime_ns)
        for rel in _files(root)
    }


class TestSeedCategories:
    def test_direct_hits_in_each_scanned_directory(self, tmp_path: Path) -> None:
        for top in ("scripts", "tests", "tools", "deploy", "docs"):
            _write(tmp_path / top / "a.txt", "x = ZEBRA_CONST\n")
        _write(tmp_path / "other" / "a.txt", "x = ZEBRA_CONST\n")
        report = _scan(tmp_path, "ZEBRA_CONST")
        for top in ("scripts", "tests", "tools", "deploy", "docs"):
            assert _paths(report, f"direct:{top}") == {f"{top}/a.txt"}
        assert not any(c.path.startswith("other/") for c in report.candidates)

    def test_seed_matches_whole_names_only(self, tmp_path: Path) -> None:
        _write(tmp_path / "scripts" / "a.py", "SEED_EXTRA = 1\nmy_SEED = 2\n")
        assert _scan(tmp_path, "SEED").candidates == []

    def test_patch_target_and_import_consumers(self, tmp_path: Path) -> None:
        _write(tmp_path / "scripts" / "agent" / "mod.py", _MODULE_TEXT)
        _write(
            tmp_path / "tests" / "test_patch.py",
            'with patch("agent.mod.SEED"):\n    pass\n',
        )
        _write(tmp_path / "tests" / "test_imp.py", "from agent.mod import helper\n")
        _write(tmp_path / "tests" / "test_pkg.py", "from agent import mod\n")
        _write(tmp_path / "tests" / "test_none.py", "import agent.other\n")
        report = _scan(tmp_path, "SEED")
        assert _paths(report, scc.CAT_PATCH_IMPORT) == {
            "tests/test_patch.py",
            "tests/test_imp.py",
            "tests/test_pkg.py",
        }

    def test_tools_module_is_imported_by_dotted_name(self, tmp_path: Path) -> None:
        _write(tmp_path / "tools" / "x.py", "def SEED():\n    pass\n")
        _write(tmp_path / "tests" / "tools" / "test_x.py", "import tools.x as x\n")
        report = _scan(tmp_path, "SEED")
        assert _paths(report, scc.CAT_PATCH_IMPORT) == {"tests/tools/test_x.py"}

    def test_inventory_checker_and_baseline_file(self, tmp_path: Path) -> None:
        _write(tmp_path / "tools" / "check_x.py", 'OWNERSHIP = ("ZEBRA_COL",)\n')
        _write(tmp_path / "data" / "size_baseline.txt", "ZEBRA_COL 100\n")
        _write(tmp_path / "tools" / "helper.py", 'NAMES = ("ZEBRA_COL",)\n')
        report = _scan(tmp_path, "ZEBRA_COL")
        assert _paths(report, scc.CAT_INVENTORY) == {
            "tools/check_x.py",
            "data/size_baseline.txt",
        }

    def test_adr_citation_of_a_test_naming_the_seed(self, tmp_path: Path) -> None:
        _write(tmp_path / "tests" / "test_a.py", "def test_b():\n    SEED_X = 1\n")
        _write(tmp_path / "tests" / "test_c.py", "def test_d():\n    pass\n")
        _write(
            tmp_path / "docs" / "10_adr" / "adr_01.md",
            "| INV-1 | `tests/test_a.py::test_b` |\n| INV-2 | `tests/test_c.py::test_d` |\n",
        )
        report = _scan(tmp_path, "SEED_X")
        hits = [c for c in report.candidates if c.category == scc.CAT_ADR]
        assert [(c.path, c.line_no) for c in hits] == [("docs/10_adr/adr_01.md", 1)]
        assert "tests/test_a.py::test_b" in hits[0].text

    def test_unrelated_seed_reports_nothing(self, tmp_path: Path) -> None:
        _write(tmp_path / "scripts" / "agent" / "mod.py", _MODULE_TEXT)
        _write(tmp_path / "tests" / "test_a.py", "from agent.mod import SEED\n")
        report = _scan(tmp_path, "NOWHERE_AT_ALL")
        assert report.candidates == []
        assert report.categories() == {}

    def test_seed_without_defining_module_is_a_limit(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "d.md", "column ZEBRA_COL\n")
        report = _scan(tmp_path, "ZEBRA_COL")
        assert any("no defining Python module" in item for item in report.limits)
        assert _paths(report, "direct:docs") == {"docs/d.md"}

    def test_path_seed_matches_path_and_dotted_module(self, tmp_path: Path) -> None:
        _write(tmp_path / "scripts" / "agent" / "mod.py", _MODULE_TEXT)
        _write(tmp_path / "docs" / "d.md", "see scripts/agent/mod.py\n")
        _write(tmp_path / "tests" / "test_a.py", "import agent.mod\n")
        report = _scan(tmp_path, "scripts/agent/mod.py")
        assert _paths(report, "direct:docs") == {"docs/d.md"}
        assert _paths(report, "direct:tests") == {"tests/test_a.py"}
        assert _paths(report, scc.CAT_PATCH_IMPORT) == {"tests/test_a.py"}

    def test_oversized_and_binary_files_are_counted_as_a_limit(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "bin.dat").write_bytes(b"\xff\xfe\x00")
        _write(tmp_path / "docs" / "ok.md", "ZEBRA\n")
        report = _scan(tmp_path, "ZEBRA")
        assert any("1 files skipped" in item for item in report.limits)


class TestTestmonState:
    def test_absent(self, tmp_path: Path) -> None:
        assert scc.testmon_state(tmp_path, _NOW).state == scc.STATE_ABSENT

    def test_stale_file_is_not_opened(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = _make_testmon(tmp_path)
        _set_age(path, 30)

        def _boom(*args: object, **kwargs: object) -> None:
            raise AssertionError("a stale testmon file must not be opened")

        monkeypatch.setattr(scc.sqlite3, "connect", _boom)
        assert scc.testmon_state(tmp_path, _NOW).state == scc.STATE_STALE

    def test_fresh_file_is_used_and_lists_tests(self, tmp_path: Path) -> None:
        _write(tmp_path / "scripts" / "agent" / "mod.py", _MODULE_TEXT)
        path = _make_testmon(tmp_path)
        _set_age(path, 1)
        report = _scan(tmp_path, "SEED")
        assert report.testmon.state == scc.STATE_USED
        hits = [c for c in report.candidates if c.category == scc.CAT_TESTMON]
        assert [(c.path, c.line_no) for c in hits] == [("tests/test_a.py", 0)]
        assert "2 recorded test(s)" in hits[0].text

    def test_fresh_file_that_is_not_a_database_is_unrecognized(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / scc.TESTMON_FILE
        path.write_bytes(b"not a database" * 100)
        _set_age(path, 1)
        assert scc.testmon_state(tmp_path, _NOW).state == scc.STATE_UNRECOGNIZED

    def test_fresh_file_without_expected_tables_is_unrecognized(
        self, tmp_path: Path
    ) -> None:
        path = _make_testmon(tmp_path, tables=False)
        _set_age(path, 1)
        state = scc.testmon_state(tmp_path, _NOW)
        assert state.state == scc.STATE_UNRECOGNIZED
        assert "lacks tables" in state.detail

    def test_unrecognized_state_skips_the_testmon_category(
        self, tmp_path: Path
    ) -> None:
        _write(tmp_path / "scripts" / "agent" / "mod.py", _MODULE_TEXT)
        path = _make_testmon(tmp_path, tables=False)
        _set_age(path, 1)
        report = _scan(tmp_path, "SEED")
        assert report.testmon.state == scc.STATE_UNRECOGNIZED
        assert not _paths(report, scc.CAT_TESTMON)


class TestOutput:
    def _report(self, tmp_path: Path) -> scc.Report:
        _write(tmp_path / "docs" / "d.md", "ZEBRA\n")
        return _scan(tmp_path, "ZEBRA")

    def test_text_output_states_notice_and_testmon(self, tmp_path: Path) -> None:
        text = scc.render_text(self._report(tmp_path))
        assert scc.NOTICE in text
        assert "Testmon: absent" in text
        assert "[direct:docs] 1 candidate(s)" in text

    def test_text_output_for_no_candidates(self, tmp_path: Path) -> None:
        text = scc.render_text(_scan(tmp_path, "NOWHERE"))
        assert "No candidates found." in text
        assert scc.NOTICE in text

    def test_text_output_truncates_per_category(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "d.md", "ZEBRA\n" * 5)
        text = scc.render_text(_scan(tmp_path, "ZEBRA"), max_lines=2)
        assert "... 3 more" in text

    def test_json_output_has_documented_keys(self, tmp_path: Path) -> None:
        data = orjson.loads(scc.render_json(self._report(tmp_path)))
        assert set(data) == {
            "notice",
            "seeds",
            "testmon",
            "limits",
            "candidates",
            "categories",
        }
        assert data["notice"] == scc.NOTICE
        assert data["testmon"]["state"] == scc.STATE_ABSENT
        assert data["categories"] == {"direct:docs": 1}

    def test_main_writes_report_file_and_stdout(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        root = tmp_path / "repo"
        _write(root / "docs" / "d.md", "ZEBRA\n")
        monkeypatch.setattr(scc, "list_tracked_files", lambda r: _files(r))
        out = tmp_path / "out" / "report.json"
        out.parent.mkdir()
        code = scc.main(
            ["--root", str(root), "--seed", "ZEBRA", "--format", "json"]
            + ["--report", str(out)]
        )
        assert code == 0
        stdout = capsys.readouterr().out
        assert out.read_text(encoding="utf-8") == stdout
        assert orjson.loads(stdout)["categories"] == {"direct:docs": 1}

    def test_main_requires_a_seed(self) -> None:
        with pytest.raises(SystemExit) as excinfo:
            scc.main([])
        assert excinfo.value.code == 2


class TestReadOnly:
    def test_scan_changes_no_file_in_the_tree(self, tmp_path: Path) -> None:
        _write(tmp_path / "scripts" / "agent" / "mod.py", _MODULE_TEXT)
        _write(tmp_path / "tests" / "test_a.py", "from agent.mod import SEED\n")
        path = _make_testmon(tmp_path)
        _set_age(path, 1)
        before = _snapshot(tmp_path)
        report = _scan(tmp_path, "SEED")
        assert report.testmon.state == scc.STATE_USED
        assert _snapshot(tmp_path) == before

    def test_stale_and_absent_scans_change_nothing(self, tmp_path: Path) -> None:
        _write(tmp_path / "docs" / "d.md", "ZEBRA\n")
        before = _snapshot(tmp_path)
        _scan(tmp_path, "ZEBRA")
        assert _snapshot(tmp_path) == before


class TestListTrackedFiles:
    def test_only_tracked_files_are_listed(self, tmp_path: Path) -> None:
        _write(tmp_path / "tracked.txt", "a\n")
        _write(tmp_path / "untracked.txt", "b\n")
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
        subprocess.run(  # nosec B603 B607 — fixed git argv in a temp repository
            ["git", "init", "-q"], cwd=tmp_path, check=True
        )
        subprocess.run(  # nosec B603 B607 — fixed git argv in a temp repository
            [*git, "add", "tracked.txt"], cwd=tmp_path, check=True
        )
        assert scc.list_tracked_files(tmp_path) == ["tracked.txt"]

    def test_non_repository_exits_with_message(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as excinfo:
            scc.list_tracked_files(tmp_path)
        assert "git ls-files failed" in str(excinfo.value)
