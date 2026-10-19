"""Tests for tools/check_module_size.py baseline handling and exit codes."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.check_module_size import collect_sizes, load_baseline, main, write_baseline

LIMIT = 100


def _scripts(tmp_path: Path, files: dict[str, int]) -> Path:
    scripts = tmp_path / "scripts"
    for name, size in files.items():
        target = scripts / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x" * size, encoding="utf-8")
    return scripts


def test_collect_sizes_skips_pycache(tmp_path: Path) -> None:
    scripts = _scripts(tmp_path, {"a.py": 10})
    cached = scripts / "__pycache__" / "a.cpython-313.py"
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text("x" * 5000, encoding="utf-8")
    assert collect_sizes(scripts) == [("a.py", 10)]


def test_all_under_limit_passes_without_baseline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts = _scripts(tmp_path, {"a.py": 90, "b.py": 100})
    assert (
        main(
            [
                "--scripts-dir",
                str(scripts),
                "--limit",
                str(LIMIT),
                "--baseline",
                str(tmp_path / "absent-baseline.txt"),
            ]
        )
        == 0
    )
    assert "ALL OK" in capsys.readouterr().out


def test_new_over_limit_module_fails_when_not_baselined(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts = _scripts(tmp_path, {"big.py": 150, "small.py": 20})
    baseline = tmp_path / "baseline.txt"
    assert (
        main(
            [
                "--scripts-dir",
                str(scripts),
                "--limit",
                str(LIMIT),
                "--baseline",
                str(baseline),
            ]
        )
        == 1
    )
    out = capsys.readouterr().out
    assert "big.py: 150 B exceeds the 100 B limit" in out
    assert "small.py" not in out
    assert not baseline.exists()


def test_baselined_module_at_recorded_size_passes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts = _scripts(tmp_path, {"big.py": 150})
    baseline = tmp_path / "baseline.txt"
    write_baseline(baseline, {"big.py": 150})
    assert (
        main(
            [
                "--scripts-dir",
                str(scripts),
                "--limit",
                str(LIMIT),
                "--baseline",
                str(baseline),
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "OK - no new violations (1 baselined module(s)" in out
    assert "ISSUES FOUND" not in out


def test_baselined_module_that_grew_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts = _scripts(tmp_path, {"big.py": 180})
    baseline = tmp_path / "baseline.txt"
    write_baseline(baseline, {"big.py": 150})
    assert (
        main(
            [
                "--scripts-dir",
                str(scripts),
                "--limit",
                str(LIMIT),
                "--baseline",
                str(baseline),
            ]
        )
        == 1
    )
    assert "grew from 150 B to 180 B" in capsys.readouterr().out


def test_baselined_module_that_shrank_passes_and_reports_tightening(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts = _scripts(tmp_path, {"big.py": 120})
    baseline = tmp_path / "baseline.txt"
    write_baseline(baseline, {"big.py": 150})
    assert (
        main(
            [
                "--scripts-dir",
                str(scripts),
                "--limit",
                str(LIMIT),
                "--baseline",
                str(baseline),
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "IMPROVED BASELINE ENTRIES (1)" in out
    assert "big.py: 150 B -> 120 B" in out


def test_stale_entry_for_a_module_now_under_the_limit_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts = _scripts(tmp_path, {"fixed.py": 80})
    baseline = tmp_path / "baseline.txt"
    write_baseline(baseline, {"fixed.py": 150})
    assert (
        main(
            [
                "--scripts-dir",
                str(scripts),
                "--limit",
                str(LIMIT),
                "--baseline",
                str(baseline),
            ]
        )
        == 1
    )
    out = capsys.readouterr().out
    assert "STALE BASELINE ENTRIES (1)" in out
    assert "fixed.py: recorded 150 B but the file is now 80 B" in out


def test_stale_entry_for_a_deleted_module_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts = _scripts(tmp_path, {"kept.py": 10})
    baseline = tmp_path / "baseline.txt"
    write_baseline(baseline, {"gone.py": 150})
    assert (
        main(
            [
                "--scripts-dir",
                str(scripts),
                "--limit",
                str(LIMIT),
                "--baseline",
                str(baseline),
            ]
        )
        == 1
    )
    assert (
        "gone.py: recorded 150 B but the file no longer exists"
        in capsys.readouterr().out
    )


def test_no_baseline_reports_every_over_limit_module(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts = _scripts(tmp_path, {"a.py": 150, "b.py": 160})
    baseline = tmp_path / "baseline.txt"
    write_baseline(baseline, {"a.py": 150})
    assert (
        main(
            [
                "--scripts-dir",
                str(scripts),
                "--limit",
                str(LIMIT),
                "--baseline",
                str(baseline),
                "--no-baseline",
            ]
        )
        == 1
    )
    assert "ISSUES FOUND (2)" in capsys.readouterr().out


def test_update_baseline_writes_sorted_entries_with_sizes(tmp_path: Path) -> None:
    scripts = _scripts(tmp_path, {"z.py": 150, "a.py": 130, "ok.py": 40})
    baseline = tmp_path / "baseline.txt"
    assert (
        main(
            [
                "--scripts-dir",
                str(scripts),
                "--limit",
                str(LIMIT),
                "--baseline",
                str(baseline),
                "--update-baseline",
            ]
        )
        == 0
    )
    assert baseline.read_text(encoding="utf-8").splitlines() == [
        "a.py\t130",
        "z.py\t150",
    ]


def test_nested_paths_are_recorded_relative_to_scripts_dir(tmp_path: Path) -> None:
    scripts = _scripts(tmp_path, {"pkg/sub/mod.py": 150})
    baseline = tmp_path / "baseline.txt"
    assert (
        main(
            [
                "--scripts-dir",
                str(scripts),
                "--limit",
                str(LIMIT),
                "--baseline",
                str(baseline),
                "--update-baseline",
            ]
        )
        == 0
    )
    assert baseline.read_text(encoding="utf-8") == "pkg/sub/mod.py\t150\n"


def test_load_baseline_ignores_comments_and_blanks_and_drops_malformed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "baseline.txt"
    path.write_text(
        "# comment\n\nbig.py\t150\nno-tab-line\nbad-size\tabc\n",
        encoding="utf-8",
    )
    assert load_baseline(path) == {"big.py": 150}
    err = capsys.readouterr().err
    assert "malformed baseline line 4" in err
    assert "malformed baseline line 5" in err
    assert load_baseline(tmp_path / "absent.txt") == {}


def test_custom_limit_changes_what_counts_as_a_violation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts = _scripts(tmp_path, {"mid.py": 120})
    baseline = str(tmp_path / "absent-baseline.txt")
    assert (
        main(["--scripts-dir", str(scripts), "--limit", "200", "--baseline", baseline])
        == 0
    )
    assert (
        main(["--scripts-dir", str(scripts), "--limit", "100", "--baseline", baseline])
        == 1
    )
    assert "mid.py: 120 B exceeds the 100 B limit" in capsys.readouterr().out


def test_top_report_is_advisory_and_does_not_change_exit_status(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts = _scripts(tmp_path, {"a.py": 90, "b.py": 80})
    assert (
        main(
            [
                "--scripts-dir",
                str(scripts),
                "--limit",
                str(LIMIT),
                "--baseline",
                str(tmp_path / "absent-baseline.txt"),
                "--top",
                "2",
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "LARGEST MODULES (top 2):" in out
    assert "a.py: 90 B" in out


def test_missing_scripts_directory_fails_with_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--scripts-dir", str(tmp_path / "absent")]) == 1
    assert "scripts directory not found" in capsys.readouterr().err


def test_committed_baseline_is_honest_against_the_real_scripts_tree() -> None:
    """Regression guard for tools/check_module_size_baseline.txt itself.

    Runs with the defaults (repo scripts/ and the committed baseline), so a new
    over-limit module, a grown baselined module, or a stale baseline entry all
    fail here before CI does.
    """
    assert main([]) == 0
