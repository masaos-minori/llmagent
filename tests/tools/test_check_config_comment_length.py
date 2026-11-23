"""tests/tools/test_check_config_comment_length.py

Tests for tools/check_config_comment_length.py: comment-block detection, finding codes,
severity, exit codes and allowlist behavior. The live `config/` run is asserted clean
through the recorded exceptions exactly once, as a `repo_scan` test.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tools import check_config_comment_length as cl

_LONG_BLOCK = "# header\n# more\n# more\n# more\n# more\n# more\nvalue = 1\n"
_THRESHOLD_BLOCK = "# a\n# b\n# c\n# d\n# e\n"


def _entry(path: str, line: int, length: int) -> cl.ExceptionEntry:
    return cl.ExceptionEntry(
        path=path, line=line, length=length, reason="fixture exception"
    )


def test_comment_blocks_splits_runs_on_non_comment_lines() -> None:
    text = "# a\n# b\nvalue = 1\n# c\n# d\n# e\n"
    assert cl.comment_blocks(text) == [(1, 2), (4, 3)]


def test_comment_blocks_ignores_inline_comments() -> None:
    text = "value = 1  # inline comment\nother = 2  # inline\n"
    assert cl.comment_blocks(text) == []


def test_comment_blocks_counts_a_block_ending_at_eof() -> None:
    assert cl.comment_blocks("value = 1\n# a\n# b\n") == [(2, 2)]


def test_block_longer_than_the_threshold_reports_the_error_finding_code() -> None:
    findings = cl.check_file(Path("config/sample.toml"), _LONG_BLOCK, exceptions=())
    assert [f[0] for f in findings] == [cl.CODE_LONG_BLOCK]
    assert findings[0][1] == cl.SEVERITY_ERROR
    assert findings[0][2].startswith("config/sample.toml:1")


def test_block_at_the_threshold_reports_nothing() -> None:
    findings = cl.check_file(
        Path("config/sample.toml"), _THRESHOLD_BLOCK, exceptions=()
    )
    assert findings == []


def test_recorded_block_reports_the_warning_finding_code() -> None:
    entry = _entry("config/sample.toml", 1, 6)
    findings = cl.check_file(
        Path("config/sample.toml"), _LONG_BLOCK, exceptions=(entry,)
    )
    assert [(f[0], f[1]) for f in findings] == [
        (cl.CODE_ALLOWLISTED_BLOCK, cl.SEVERITY_WARNING)
    ]
    assert "fixture exception" in findings[0][2]


def test_stale_exception_is_an_error_finding() -> None:
    entry = _entry("config/sample.toml", 1, 12)
    findings = cl.check_file(
        Path("config/sample.toml"), "value = 1\n", exceptions=(entry,)
    )
    assert [(f[0], f[1]) for f in findings] == [
        (cl.CODE_STALE_EXCEPTION, cl.SEVERITY_ERROR)
    ]
    assert findings[0][2].startswith("config/sample.toml:1")


def test_main_exits_one_on_an_unrecorded_block(tmp_path: Path) -> None:
    fixture = tmp_path / "config" / "sample.toml"
    fixture.parent.mkdir()
    fixture.write_text(_LONG_BLOCK, encoding="utf-8")
    assert cl.main(["--root", str(fixture.parent)]) == 1


def test_main_exits_zero_when_only_recorded_exceptions_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = tmp_path / "config" / "sample.toml"
    fixture.parent.mkdir()
    fixture.write_text(_LONG_BLOCK, encoding="utf-8")
    monkeypatch.setattr(cl, "EXCEPTIONS", (_entry(cl.relative_path(fixture), 1, 6),))
    assert cl.main(["--root", str(fixture.parent)]) == 0


def test_main_exits_one_when_a_recorded_exception_goes_stale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = tmp_path / "config" / "sample.toml"
    fixture.parent.mkdir()
    fixture.write_text("value = 1\n", encoding="utf-8")
    monkeypatch.setattr(cl, "EXCEPTIONS", (_entry(cl.relative_path(fixture), 1, 6),))
    assert cl.main(["--root", str(fixture.parent)]) == 1


def test_every_recorded_exception_names_a_live_block() -> None:
    for entry in cl.EXCEPTIONS:
        path = cl.REPO_ROOT / entry.path
        assert path.is_file(), entry.path
        blocks = cl.comment_blocks(path.read_text(encoding="utf-8"))
        assert (entry.line, entry.length) in blocks, entry


# Scans the live config/ tree; local iteration and full runs deselect it.
@pytest.mark.repo_scan
def test_live_config_run_is_clean_through_the_recorded_exceptions() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(cl.REPO_ROOT / "tools" / "check_config_comment_length.py"),
        ],
        cwd=cl.REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert cl.CODE_LONG_BLOCK not in result.stderr
    assert cl.CODE_ALLOWLISTED_BLOCK in result.stderr
