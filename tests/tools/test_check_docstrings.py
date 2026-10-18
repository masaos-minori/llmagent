"""Tests for tools/check_docstrings.py baseline handling."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.check_docstrings import issue_kind, load_baseline, main, write_baseline

GOOD = '"""scripts/good.py — A valid description."""\n'
BAD = '"""Prose only."""\n'


def _scripts(tmp_path: Path, files: dict[str, str]) -> Path:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name, text in files.items():
        (scripts / name).write_text(text, encoding="utf-8")
    return scripts


def test_issue_kind_is_text_before_first_colon() -> None:
    assert issue_kind("missing separator: 'x: y'") == "missing separator"
    assert issue_kind("no docstring") == "no docstring"


def test_baseline_round_trip_ignores_comments_and_blanks(tmp_path: Path) -> None:
    path = tmp_path / "baseline.txt"
    write_baseline(path, {("b.py", "no docstring"), ("a.py", "missing separator")})
    assert path.read_text(encoding="utf-8").splitlines()[0].startswith("a.py\t")
    path.write_text("# note\n\n" + path.read_text(encoding="utf-8"), encoding="utf-8")
    assert load_baseline(path) == {
        ("a.py", "missing separator"),
        ("b.py", "no docstring"),
    }
    assert load_baseline(tmp_path / "absent.txt") == set()


def test_new_violation_fails_without_baseline_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts = _scripts(tmp_path, {"good.py": GOOD, "bad.py": BAD})
    baseline = tmp_path / "baseline.txt"
    assert main(["--scripts-dir", str(scripts), "--baseline", str(baseline)]) == 1
    assert "bad.py" in capsys.readouterr().out


def test_grandfathered_violation_passes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts = _scripts(tmp_path, {"good.py": GOOD, "bad.py": BAD})
    baseline = tmp_path / "baseline.txt"
    args = ["--scripts-dir", str(scripts), "--baseline", str(baseline)]
    assert main([*args, "--update-baseline"]) == 0
    assert main(args) == 0
    assert "1 grandfathered" in capsys.readouterr().out
    assert main([*args, "--no-baseline"]) == 1


def test_stale_baseline_entry_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts = _scripts(tmp_path, {"bad.py": BAD})
    baseline = tmp_path / "baseline.txt"
    args = ["--scripts-dir", str(scripts), "--baseline", str(baseline)]
    main([*args, "--update-baseline"])
    (scripts / "bad.py").write_text(
        '"""scripts/bad.py — Now fixed."""\n', encoding="utf-8"
    )
    assert main(args) == 1
    assert "STALE BASELINE" in capsys.readouterr().out


def test_different_kind_in_baselined_file_is_new(tmp_path: Path) -> None:
    scripts = _scripts(tmp_path, {"bad.py": BAD})
    baseline = tmp_path / "baseline.txt"
    args = ["--scripts-dir", str(scripts), "--baseline", str(baseline)]
    main([*args, "--update-baseline"])
    (scripts / "bad.py").write_text(
        '"""scripts/other.py — Wrong path."""\n', encoding="utf-8"
    )
    assert main(args) == 1
