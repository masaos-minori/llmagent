"""tests/tools/test_fix_docs_section_marks.py
Tests for tools/fix_docs_section_marks.py: default preview, `--dry-run`, `--apply`.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import tools.fix_docs_section_marks as fsm

ORIGINAL = "See §15 and §8a.\n日本 ünï\n"
FIXED = "See section 15 and section 8a.\n日本 ünï\n"


@pytest.fixture
def doc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(fsm, "REPO_ROOT", tmp_path)
    path = tmp_path / "docs" / "a.md"
    path.parent.mkdir()
    path.write_text(ORIGINAL, encoding="utf-8")
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_default_run_previews_without_writing(
    doc: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = _sha(doc)

    assert fsm.main(["--dir", "docs"]) == 0

    assert _sha(doc) == before
    assert "[DRY-RUN] docs/a.md: 2 occurrence(s) would be replaced" in (
        capsys.readouterr().out
    )


def test_explicit_dry_run_writes_nothing_and_prints_the_diff(
    doc: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = _sha(doc)

    assert fsm.main(["--dir", "docs", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert _sha(doc) == before
    assert "-See §15 and §8a." in out
    assert "+See section 15 and section 8a." in out


def test_apply_rewrites_the_file_as_utf8(doc: Path) -> None:
    assert fsm.main(["--dir", "docs", "--apply"]) == 0

    assert doc.read_bytes() == FIXED.encode()
    assert [p.name for p in doc.parent.iterdir()] == ["a.md"]


def test_apply_with_dry_run_is_rejected(doc: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        fsm.main(["--dir", "docs", "--apply", "--dry-run"])

    assert excinfo.value.code == 2


def test_clean_tree_returns_zero_in_every_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(fsm, "REPO_ROOT", tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("plain\n", encoding="utf-8")

    assert fsm.main(["--dir", "docs"]) == 0
    assert fsm.main(["--dir", "docs", "--dry-run"]) == 0
    assert fsm.main(["--dir", "docs", "--apply"]) == 0
