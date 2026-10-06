"""tests/rag/ingestion/test_crawl_persister_lang.py

Unit and integration tests for local-file ``lang="auto"`` resolution in
CrawlPersister.save() / WebCrawler.crawl_file(), and the ``file://`` + ``auto``
dispatch through WebCrawler.crawl().
"""

from __future__ import annotations

from pathlib import Path

import orjson
import pytest
from rag.ingestion.crawler import WebCrawler

# Japanese fixture >= 100 chars so detect_lang() is deterministic (CJK ratio >= threshold).
_JAPANESE_FIXTURE = (
    "日本語のテキストです。これはテストのために作成された文章です。"
    "一百文字以上あって、CJK判定が安定するように設計されています。"
    "日本語の文字が含まれているので、言語検出は明確に日本語と判断します。"
    "この文章は確実に一百文字を超えていて、検出が安定しています。"
)
# English fixture >= 100 chars so detect_lang() is deterministic (CJK ratio < threshold).
_ENGLISH_FIXTURE = (
    "This is an English test fixture created for language detection. "
    "It is long enough at over one hundred characters to produce a stable "
    "result from the CJK-ratio heuristic used by the crawler."
)
_SHORT_FIXTURE = "too short"


def _config(tmp_path: Path) -> dict:
    """Return a minimal WebCrawler config rooted at tmp_path."""
    return {
        "target_urls": [],
        "rag_src_dir": str(tmp_path / "rag-src"),
        "skip_external": True,
        "crawl_delay": 0,
        "max_depth": 1,
        "min_chunk": 10,
        "fetch_retry": 1,
    }


def _read_written_json(rag_src: Path) -> dict:
    """Return the parsed payload of the single JSON written into rag_src."""
    files = list(rag_src.glob("*.json"))
    assert len(files) == 1, f"expected exactly one JSON, found {len(files)}"
    parsed: dict[str, object] = orjson.loads(files[0].read_bytes())
    return parsed


class TestSaveAutoResolution:
    def test_auto_resolves_japanese(self, tmp_path: Path) -> None:
        crawler = WebCrawler(_config(tmp_path))
        target = tmp_path / "doc.txt"
        target.write_text(_JAPANESE_FIXTURE)

        result = crawler.crawl_file(target, "auto")

        assert result == 1
        payload = _read_written_json(tmp_path / "rag-src")
        assert payload["lang"] == "ja"

    def test_auto_resolves_english(self, tmp_path: Path) -> None:
        crawler = WebCrawler(_config(tmp_path))
        target = tmp_path / "doc.txt"
        target.write_text(_ENGLISH_FIXTURE)

        result = crawler.crawl_file(target, "auto")

        assert result == 1
        payload = _read_written_json(tmp_path / "rag-src")
        assert payload["lang"] == "en"

    def test_auto_short_text_falls_back_to_english(self, tmp_path: Path) -> None:
        crawler = WebCrawler(_config(tmp_path))
        target = tmp_path / "short.txt"
        target.write_text(_SHORT_FIXTURE)

        result = crawler.crawl_file(target, "auto")

        assert result == 1
        payload = _read_written_json(tmp_path / "rag-src")
        assert payload["lang"] == "en"

    def test_unsupported_lang_returns_zero_and_writes_nothing(
        self, tmp_path: Path
    ) -> None:
        crawler = WebCrawler(_config(tmp_path))
        target = tmp_path / "doc.txt"
        target.write_text(_ENGLISH_FIXTURE)

        result = crawler.crawl_file(target, "fr")

        assert result == 0
        assert not list((tmp_path / "rag-src").glob("*.json"))


class TestCrawlFilePlusAutoDispatch:
    @pytest.mark.asyncio
    async def test_file_target_auto_resolves_within_supported(
        self, tmp_path: Path
    ) -> None:
        crawler = WebCrawler(_config(tmp_path))
        target = tmp_path / "doc.txt"
        target.write_text(_JAPANESE_FIXTURE)
        await crawler.crawl([(f"file://{target.resolve()}", "auto")])

        files = list((tmp_path / "rag-src").glob("*.json"))
        assert len(files) == 1
        payload = orjson.loads(files[0].read_bytes())
        assert payload["lang"] in {"en", "ja"}
