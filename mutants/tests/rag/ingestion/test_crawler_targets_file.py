"""Tests for --targets-file feature: parse_targets_file(), crawl() file:// dispatch, and CLI argument handling."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from rag.ingestion.crawler import WebCrawler, main
from rag.ingestion.crawler_utils import parse_targets_file

# --- parse_targets_file tests ---


def test_parse_targets_file_http(tmp_path: Path) -> None:
    """A valid TOML file with an http:// URL is parsed correctly."""
    targets_file = tmp_path / "targets.toml"
    targets_file.write_text(
        'target_urls = [["https://example.com/", "en"]]', encoding="utf-8"
    )
    result = parse_targets_file(targets_file)
    assert result == [("https://example.com/", "en")]


def test_parse_targets_file_file_url(tmp_path: Path) -> None:
    """A file:// URL is accepted and parsed."""
    targets_file = tmp_path / "targets.toml"
    targets_file.write_text(
        'target_urls = [["file:///path/to/file.py", "en"]]', encoding="utf-8"
    )
    result = parse_targets_file(targets_file)
    assert result == [("file:///path/to/file.py", "en")]


def test_parse_targets_file_invalid_scheme(tmp_path: Path) -> None:
    """An unsupported URL scheme raises ValueError."""
    targets_file = tmp_path / "targets.toml"
    targets_file.write_text(
        'target_urls = [["ftp://example.com/file.txt", "en"]]', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="unsupported URL scheme"):
        parse_targets_file(targets_file)


def test_parse_targets_file_invalid_lang(tmp_path: Path) -> None:
    """An unsupported lang value raises ValueError."""
    targets_file = tmp_path / "targets.toml"
    targets_file.write_text(
        'target_urls = [["https://example.com/", "zh"]]', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="unsupported lang"):
        parse_targets_file(targets_file)


def test_parse_targets_file_missing_file(tmp_path: Path) -> None:
    """A nonexistent path raises FileNotFoundError."""
    targets_file = tmp_path / "nonexistent.toml"
    with pytest.raises(FileNotFoundError):
        parse_targets_file(targets_file)


# --- main() conflict tests ---


def test_main_url_and_targets_file_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Passing both --url and --targets-file causes SystemExit(2)."""
    targets_file = tmp_path / "targets.toml"
    targets_file.write_text(
        'target_urls = [["https://example.com/", "en"]]', encoding="utf-8"
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "crawler.py",
            "--url",
            "https://example.com/",
            "--targets-file",
            str(targets_file),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 2


# --- CLI help tests ---


def test_crawler_help_no_force(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """--force does not appear in the crawler's help output."""
    monkeypatch.setattr(sys, "argv", ["crawler.py", "--help"])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr().out
    assert "--force" not in captured


# --- crawl() dispatch tests ---


def test_crawl_dispatches_file_url_to_crawl_file(tmp_path: Path) -> None:
    """WebCrawler.crawl() dispatches a file:// target to crawl_file(), not crawl_site()."""
    config = {
        "rag_src_dir": str(tmp_path),
        "crawl_delay": 0,
        "max_depth": 1,
        "min_chunk": 40,
        "fetch_retry": 1,
        "fetch_timeout": 5,
        "crawl_concurrency": 1,
        "max_pages": 10,
        "target_urls": [],
        "skip_nofollow": False,
        "skip_external": True,
    }
    crawler = WebCrawler(config=config)

    with patch.object(crawler, "crawl_file") as mock_crawl_file:
        targets = [("file:///tmp/some_file.py", "en")]
        asyncio.run(crawler.crawl(targets))

    mock_crawl_file.assert_called_once()
    call_args = mock_crawl_file.call_args
    assert call_args[0][0] == Path("/tmp/some_file.py")
    assert call_args[0][1] == "en"
