"""Tests for tools/check_docs_japanese.py."""

from __future__ import annotations

from pathlib import Path

from tools.check_docs_japanese import contains_japanese, find_japanese_files


def test_contains_japanese_detects_each_script() -> None:
    assert contains_japanese("ひらがな")
    assert contains_japanese("カタカナ")
    assert contains_japanese("漢字")
    assert not contains_japanese("English only, 123 -- symbols")


def test_find_japanese_files_lists_only_matching_markdown(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.md").write_text("plain English\n", encoding="utf-8")
    (tmp_path / "sub" / "b.md").write_text("混在 text\n", encoding="utf-8")
    (tmp_path / "c.txt").write_text("日本語\n", encoding="utf-8")

    assert find_japanese_files(tmp_path) == [tmp_path / "sub" / "b.md"]
