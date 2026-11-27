"""tests/tools/test_check_skill_size.py

Tests for tools/check_skill_size.py: covered-file collection, the limit and baseline
semantics (violation, regression, stale entry, shrunk file), the update and no-baseline
modes, exit codes, and a malformed baseline line. The live repository is checked exactly
once, as a `repo_scan` test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools import check_skill_size as cs


def _write(root: Path, relpath: str, size: int) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x" * size, encoding="utf-8")


def _tree(root: Path) -> None:
    _write(root, "skills/a/workflow.md", 150)
    _write(root, "skills/a/SKILL.md", 40)
    _write(root, "rules/r.md", 60)
    _write(root, "prompts/p.md", 10)
    _write(root, "templates/t.md", 10)
    _write(root, "routing.md", 10)
    _write(root, "AGENTS.md", 10)
    _write(root, "other/ignored.md", 5000)
    _write(root, "docs/ignored.md", 5000)


def _run(root: Path, baseline: Path, *extra: str) -> int:
    return cs.main(
        ["--root", str(root), "--baseline", str(baseline), "--limit", "100", *extra]
    )


def test_collect_covered_finds_only_covered_patterns_sorted(tmp_path: Path) -> None:
    _tree(tmp_path)
    sizes = cs.collect_covered(tmp_path)
    relpaths = [relpath for relpath, _ in sizes]
    assert relpaths == sorted(relpaths)
    assert "skills/a/workflow.md" in relpaths
    assert "routing.md" in relpaths
    assert "other/ignored.md" not in relpaths
    assert "docs/ignored.md" not in relpaths


def test_evaluate_within_limit_is_clean() -> None:
    result = cs.evaluate([("a.md", 50), ("b.md", 100)], {}, 100)
    assert not result.failed
    assert result.violations == []


def test_evaluate_new_file_over_limit_is_a_violation() -> None:
    result = cs.evaluate([("a.md", 101)], {}, 100)
    assert result.failed
    assert "a.md" in result.violations[0]
    assert "not in the baseline" in result.violations[0]


def test_evaluate_baselined_file_growth_is_a_regression() -> None:
    result = cs.evaluate([("a.md", 150)], {"a.md": 120}, 100)
    assert result.failed
    assert "grew from 120 B to 150 B" in result.violations[0]


def test_evaluate_baselined_file_at_ceiling_is_grandfathered() -> None:
    result = cs.evaluate([("a.md", 120)], {"a.md": 120}, 100)
    assert not result.failed
    assert result.grandfathered == 1
    assert result.shrunk == []


def test_evaluate_shrunk_file_is_advisory_only() -> None:
    result = cs.evaluate([("a.md", 110)], {"a.md": 120}, 100)
    assert not result.failed
    assert result.shrunk == ["a.md: 120 B -> 110 B"]


def test_evaluate_stale_entry_for_a_missing_file_fails() -> None:
    result = cs.evaluate([("b.md", 10)], {"gone.md": 200}, 100)
    assert result.failed
    assert "gone.md" in result.stale[0]


def test_evaluate_stale_entry_for_a_file_back_under_the_limit_fails() -> None:
    result = cs.evaluate([("a.md", 100)], {"a.md": 200}, 100)
    assert result.failed
    assert "a.md" in result.stale[0]


def test_main_clean_tree_exits_zero(tmp_path: Path, capsys) -> None:
    _write(tmp_path, "rules/r.md", 50)
    assert _run(tmp_path, tmp_path / "baseline.txt") == 0
    assert "OK" in capsys.readouterr().out


def test_main_violation_exits_one(tmp_path: Path, capsys) -> None:
    _tree(tmp_path)
    assert _run(tmp_path, tmp_path / "baseline.txt") == 1
    err = capsys.readouterr().err
    assert "skills/a/workflow.md" in err
    assert "SIZE VIOLATIONS" in err


def test_main_missing_root_exits_two(tmp_path: Path, capsys) -> None:
    assert _run(tmp_path / "nope", tmp_path / "baseline.txt") == 2
    assert "root directory not found" in capsys.readouterr().err


def test_main_update_baseline_records_over_limit_files_and_passes(
    tmp_path: Path,
) -> None:
    _tree(tmp_path)
    baseline = tmp_path / "baseline.txt"
    assert _run(tmp_path, baseline, "--update-baseline") == 0
    assert baseline.read_text(encoding="utf-8") == "skills/a/workflow.md\t150\n"
    assert _run(tmp_path, baseline) == 0


def test_main_growth_after_baseline_exits_one(tmp_path: Path) -> None:
    _tree(tmp_path)
    baseline = tmp_path / "baseline.txt"
    _run(tmp_path, baseline, "--update-baseline")
    _write(tmp_path, "skills/a/workflow.md", 151)
    assert _run(tmp_path, baseline) == 1


def test_main_stale_entry_exits_one(tmp_path: Path) -> None:
    _tree(tmp_path)
    baseline = tmp_path / "baseline.txt"
    _run(tmp_path, baseline, "--update-baseline")
    _write(tmp_path, "skills/a/workflow.md", 90)
    assert _run(tmp_path, baseline) == 1


def test_main_shrunk_file_passes_and_prints_advisory(tmp_path: Path, capsys) -> None:
    _tree(tmp_path)
    baseline = tmp_path / "baseline.txt"
    _run(tmp_path, baseline, "--update-baseline")
    _write(tmp_path, "skills/a/workflow.md", 120)
    assert _run(tmp_path, baseline) == 0
    assert "SHRUNK" in capsys.readouterr().out


def test_main_no_baseline_reports_every_over_limit_file(tmp_path: Path) -> None:
    _tree(tmp_path)
    baseline = tmp_path / "baseline.txt"
    _run(tmp_path, baseline, "--update-baseline")
    assert _run(tmp_path, baseline, "--no-baseline") == 1


def test_main_malformed_baseline_line_cannot_grandfather(
    tmp_path: Path, capsys
) -> None:
    _tree(tmp_path)
    baseline = tmp_path / "baseline.txt"
    baseline.write_text("skills/a/workflow.md 150\n", encoding="utf-8")
    assert _run(tmp_path, baseline) == 1
    assert "malformed baseline line" in capsys.readouterr().err


def test_main_top_prints_the_largest_files(tmp_path: Path, capsys) -> None:
    _tree(tmp_path)
    _run(tmp_path, tmp_path / "baseline.txt", "--top", "2")
    out = capsys.readouterr().out
    assert "LARGEST FILES (top 2)" in out
    assert out.index("skills/a/workflow.md") < out.index("rules/r.md")


@pytest.mark.repo_scan
def _headroom(
    root: Path, baseline: Path, *paths: str, extra: tuple[str, ...] = ()
) -> int:
    return cs.main(
        [
            "--root",
            str(root),
            "--baseline",
            str(baseline),
            "--limit",
            "100",
            *extra,
            "--headroom",
            *paths,
        ]
    )


def test_headroom_prints_baseline_limit_and_negative_headroom(
    tmp_path: Path, capsys
) -> None:
    _tree(tmp_path)
    baseline = tmp_path / "baseline.txt"
    baseline.write_text("skills/a/workflow.md\t160\n", encoding="utf-8")
    assert _headroom(tmp_path, baseline, "skills/a/workflow.md", "rules/r.md") == 0
    out = capsys.readouterr().out.splitlines()
    assert out == [
        "skills/a/workflow.md: 150 B, ceiling 160 B (baseline), headroom 10 B",
        "rules/r.md: 60 B, ceiling 100 B (limit), headroom 40 B",
    ]
    _write(tmp_path, "skills/a/workflow.md", 170)
    assert _headroom(tmp_path, baseline, "skills/a/workflow.md") == 0
    assert "headroom -10 B" in capsys.readouterr().out


def test_headroom_uncovered_path_and_absolute_path(tmp_path: Path, capsys) -> None:
    _tree(tmp_path)
    baseline = tmp_path / "baseline.txt"
    absolute = str(tmp_path / "rules" / "r.md")
    assert _headroom(tmp_path, baseline, "docs/ignored.md", absolute, "rules/r.md") == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "docs/ignored.md: not covered by the size gate"
    assert lines[1] == lines[2]


def test_headroom_missing_path_exits_two_without_output(tmp_path: Path, capsys) -> None:
    _tree(tmp_path)
    assert _headroom(tmp_path, tmp_path / "baseline.txt", "rules/r.md", "nope.md") == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "path not found: nope.md" in captured.err


def test_headroom_is_report_only_and_does_not_run_the_gate(
    tmp_path: Path, capsys
) -> None:
    _tree(tmp_path)  # skills/a/workflow.md is over the limit and not baselined
    baseline = tmp_path / "baseline.txt"
    before = {p: p.read_bytes() for p in tmp_path.rglob("*.md")}
    assert _headroom(tmp_path, baseline, "rules/r.md") == 0
    capsys.readouterr()
    assert not baseline.exists()
    assert {p: p.read_bytes() for p in tmp_path.rglob("*.md")} == before
    assert _run(tmp_path, baseline) == 1  # the gate itself still fails


def test_headroom_honors_no_baseline(tmp_path: Path, capsys) -> None:
    _tree(tmp_path)
    baseline = tmp_path / "baseline.txt"
    baseline.write_text("skills/a/workflow.md\t160\n", encoding="utf-8")
    assert (
        _headroom(tmp_path, baseline, "skills/a/workflow.md", extra=("--no-baseline",))
        == 0
    )
    assert "ceiling 100 B (limit), headroom -50 B" in capsys.readouterr().out


def test_headroom_with_update_baseline_is_a_usage_error(tmp_path: Path) -> None:
    _tree(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        _headroom(
            tmp_path,
            tmp_path / "baseline.txt",
            "rules/r.md",
            extra=("--update-baseline",),
        )
    assert excinfo.value.code == 2


def test_clean_tree_default_output_is_pinned(tmp_path: Path, capsys) -> None:
    _write(tmp_path, "rules/r.md", 50)
    assert _run(tmp_path, tmp_path / "baseline.txt") == 0
    assert capsys.readouterr().out == (
        "OK - no new violations (0 baselined file(s) at or below their recorded size)\n"
    )


def test_live_repository_passes_with_the_recorded_baseline() -> None:
    assert cs.main([]) == 0
