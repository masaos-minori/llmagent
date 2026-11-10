"""tests/rag/ingestion/test_crawl_persister_lang.py

Unit and integration tests for local-file ``lang="auto"`` resolution in
CrawlPersister.save() / WebCrawler.crawl_file(), and the ``file://`` + ``auto``
dispatch through WebCrawler.crawl().
"""

from __future__ import annotations

from pathlib import Path

import orjson
import pytest
from rag.ingestion.crawl_persister import CrawlPersister
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

# Two distinct URLs sharing an 80-character-or-longer common prefix. Their
# url_to_slug() outputs collapse to the same 80-char label, so without a
# per-URL uniqueness component they would collide within the same wall-clock
# second. The trailing /page-a vs /page-b suffix sits past the truncation point.
_LONG_PREFIX = "https://example.com/" + "x" * 100
_COLLIDING_URL_A = _LONG_PREFIX + "/page-a"
_COLLIDING_URL_B = _LONG_PREFIX + "/page-b"


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


class TestMakeCrawlFilePathUniqueness:
    def _persister(self, tmp_path: Path) -> CrawlPersister:
        return CrawlPersister({"rag_src_dir": str(tmp_path / "rag-src")})

    def test_long_prefix_urls_produce_distinct_paths(self, tmp_path: Path) -> None:
        persister = self._persister(tmp_path)

        path_a = persister.make_crawl_filepath(_COLLIDING_URL_A)
        path_b = persister.make_crawl_filepath(_COLLIDING_URL_B)

        assert path_a != path_b
        assert path_a.suffix == ".json"
        assert path_b.suffix == ".json"

    def test_simulated_save_writes_one_file_per_url(self, tmp_path: Path) -> None:
        rag_src = tmp_path / "rag-src"
        persister = self._persister(tmp_path)

        persister.save_http(
            _COLLIDING_URL_A, title="A", lang="en", content="content-a", code_blocks=[]
        )
        persister.save_http(
            _COLLIDING_URL_B, title="B", lang="en", content="content-b", code_blocks=[]
        )

        files = sorted(rag_src.glob("*.json"))
        assert len(files) == 2
        contents = {orjson.loads(f.read_bytes())["content"] for f in files}
        assert contents == {"content-a", "content-b"}


class TestSaveHttpSkipContract:
    def _persister(self, tmp_path: Path) -> CrawlPersister:
        return CrawlPersister({"rag_src_dir": str(tmp_path / "rag-src")})

    @pytest.mark.parametrize(
        ("lang", "content", "code_blocks"),
        [
            pytest.param("de", "some content", [], id="unsupported-lang"),
            pytest.param("en", "some content", "not-a-list", id="non-list-code-blocks"),
            pytest.param("en", "", [], id="empty-content"),
        ],
    )
    def test_skip_branches_return_none_and_write_nothing(
        self,
        tmp_path: Path,
        lang: str,
        content: str,
        code_blocks: object,
    ) -> None:
        persister = self._persister(tmp_path)

        result = persister.save_http(
            "https://example.com/skip",
            title="skip",
            lang=lang,
            content=content,
            code_blocks=code_blocks,
        )

        assert result is None
        assert not list((tmp_path / "rag-src").glob("*.json"))

    def test_normal_path_returns_existing_path(self, tmp_path: Path) -> None:
        persister = self._persister(tmp_path)

        result = persister.save_http(
            "https://example.com/ok",
            title="t",
            lang="en",
            content="x",
            code_blocks=[],
        )

        assert isinstance(result, Path)
        assert result.parent == tmp_path / "rag-src"
        assert result.exists()
