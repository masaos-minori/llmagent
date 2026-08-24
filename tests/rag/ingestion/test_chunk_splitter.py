"""tests/test_chunk_splitter.py
Behavior-lock tests for ChunkSplitter._is_markdown_source(), chunking_strategy in chunk JSON,
and fetched_at propagation across all written chunk files.
"""

from __future__ import annotations

from pathlib import Path

import orjson
from rag.ingestion.chunk_splitter import ChunkSplitter
from rag.models_data import ChunkDocument


def _make_splitter(md_index_enable: bool = False) -> ChunkSplitter:
    splitter = object.__new__(ChunkSplitter)
    splitter._md_index_enable = md_index_enable
    return splitter


def _make_chunk_doc(url: str, content: str = "") -> ChunkDocument:
    return ChunkDocument(
        url=url,
        title="",
        lang="en",
        content=content,
        code_blocks=[],
        etag=None,
        last_modified=None,
        chunking_strategy="text",
        normalized_content=None,
        chunk_index=0,
        source_file="",
        chunk_type="",
        fetched_at="2024-01-01T00:00:00Z",
    )


class TestIsMarkdownSource:
    def test_md_extension_returns_true_regardless_of_flag(self) -> None:
        splitter = _make_splitter(md_index_enable=False)
        doc = _make_chunk_doc("https://example.com/README.md")
        assert splitter._is_markdown_source(doc) is True

    def test_markdown_extension_returns_true(self) -> None:
        splitter = _make_splitter(md_index_enable=False)
        doc = _make_chunk_doc("docs/guide.markdown")
        assert splitter._is_markdown_source(doc) is True

    def test_mdx_extension_returns_true(self) -> None:
        splitter = _make_splitter(md_index_enable=False)
        doc = _make_chunk_doc("component.mdx")
        assert splitter._is_markdown_source(doc) is True

    def test_non_md_url_returns_false_when_flag_disabled(self) -> None:
        splitter = _make_splitter(md_index_enable=False)
        doc = _make_chunk_doc("https://example.com/page.html")
        assert splitter._is_markdown_source(doc) is False

    def test_non_md_url_heuristic_when_flag_enabled(self) -> None:
        splitter = _make_splitter(md_index_enable=True)
        content = "# Heading 1\nsome text\n## Heading 2\nmore text"
        doc = _make_chunk_doc("page.html", content=content)
        assert splitter._is_markdown_source(doc) is True

    def test_non_md_no_headings_returns_false_even_when_flag_enabled(self) -> None:
        splitter = _make_splitter(md_index_enable=True)
        doc = _make_chunk_doc("page.html", content="plain text")
        assert splitter._is_markdown_source(doc) is False


# ── Helpers for fetched_at propagation tests ───────────────────────────────────

_FAKE_EMBEDDING = [0.1] * 384

_CRAWL_PAYLOAD_BASE = {
    "url": "http://example.com/page",
    "title": "Test Page",
    "lang": "en",
    "etag": None,
    "last_modified": None,
    "fetched_at": "2026-01-01T00:00:00Z",
}

_CHUNK_JSON_TEMPLATE = {
    "schema_version": "1",
    "artifact_type": "chunk",
    "created_by": "chunk_splitter",
    "url": "http://example.com/page",
    "title": "Test Page",
    "lang": "en",
    "content": "",
    "chunking_strategy": "heading",
    "normalized_content": None,
    "chunk_index": 0,
    "etag": None,
    "last_modified": None,
    "fetched_at": "2026-01-01T00:00:00Z",
    "chunk_type": "",
    "source_file": "",
    "code_blocks": [],
}

_CRAWL_CONFIG = {
    "rag_src_dir": "",
    "min_chunk": 40,
    "max_chunk": 500,
    "chunk_overlap": 50,
    "en_stopwords": [
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "if",
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "having",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "i",
        "you",
        "he",
        "she",
        "we",
        "they",
        "them",
        "their",
        "our",
        "your",
        "my",
        "his",
        "her",
        "not",
        "no",
        "nor",
        "so",
        "yet",
        "both",
        "either",
        "each",
        "other",
        "such",
        "into",
        "through",
        "about",
        "than",
        "then",
        "when",
        "where",
        "who",
        "which",
        "what",
        "how",
        "all",
        "any",
        "more",
        "most",
        "also",
        "up",
        "out",
        "as",
        "just",
        "over",
        "after",
        "before",
        "while",
        "since",
        "because",
        "although",
        "however",
        "therefore",
        "thus",
        "hence",
        "whether",
        "once",
        "only",
        "even",
        "still",
        "now",
        "here",
        "there",
        "very",
        "too",
        "much",
        "many",
        "some",
        "few",
        "must",
        "let",
        "get",
        "got",
        "make",
        "made",
        "use",
        "used",
        "using",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "new",
        "old",
        "first",
        "last",
        "long",
        "great",
        "little",
        "own",
        "right",
        "big",
        "high",
        "small",
        "large",
        "next",
        "early",
        "young",
        "important",
        "public",
        "private",
        "real",
        "best",
        "free",
        "same",
        "different",
    ],
    "ja_stop_pos": ["助詞", "助動詞", "補助記号", "空白", "感動詞", "接続詞"],
}

# Long single-paragraph content exceeding max_chunk=500 so English chunking
# splits it at sentence boundaries into >=2 chunks.
_LONG_SINGLE = (
    "The quick brown fox jumps over the lazy dog near the riverbank today with great enthusiasm and determination. "
    "A swift white rabbit hops across the meadow while the sun sets behind the hills casting long shadows. "
    "The ancient castle stands atop the mountain overlooking the valley below where streams flow. "
    "Deep within the forest a small stream winds its way toward the distant ocean beyond the horizon. "
    "Birds sing their morning songs as the dew drops glisten on every leaf and blade of grass. "
    "Mountains rise majestically above the clouds creating a breathtaking panorama for all to see. "
    "Rivers carve through stone over millennia forming deep canyons and dramatic waterfalls along their paths. "
    "Forests stretch endlessly across the landscape providing shelter for countless species of wildlife. "
    "Oceans cover most of the earth surface with waves crashing against rocky shores and sandy beaches. "
    "Deserts expand and contract with changing seasons revealing hidden oases and ancient ruins beneath sand."
)

_CODE_BLOCK = "def foo():\n    return 42\n\ndef bar():\n    return 99"

_CRAWL_WITH_MULTI_PARAGRAPHS = dict(_CRAWL_PAYLOAD_BASE)
_CRAWL_WITH_MULTI_PARAGRAPHS["content"] = _LONG_SINGLE
_CRAWL_WITH_MULTI_PARAGRAPHS["code_blocks"] = []

_CRAWL_WITH_TEXT_AND_CODE = dict(_CRAWL_PAYLOAD_BASE)
_CRAWL_WITH_TEXT_AND_CODE["content"] = _LONG_SINGLE
_CRAWL_WITH_TEXT_AND_CODE["code_blocks"] = [_CODE_BLOCK]

_CRAWL_WITH_LONG_SINGLE = dict(_CRAWL_PAYLOAD_BASE)
_CRAWL_WITH_LONG_SINGLE["content"] = (
    "The quick brown fox jumps over the lazy dog near the riverbank today."
)
_CRAWL_WITH_LONG_SINGLE["code_blocks"] = []

_CRAWL_WITH_CODE_ONLY = dict(_CRAWL_PAYLOAD_BASE)
_CRAWL_WITH_CODE_ONLY["content"] = ""
_CRAWL_WITH_CODE_ONLY["code_blocks"] = [_CODE_BLOCK]

_CRAWL_WITH_MD_HEADINGS = dict(_CRAWL_PAYLOAD_BASE)
_CRAWL_WITH_MD_HEADINGS["content"] = (
    "# Heading One\n"
    "First section of text here.\n\n"
    "## Second Heading\n"
    "Second section of text here.\n\n"
    "### Third Heading\n"
    "Third section of text here.\n\n"
    "#### Fourth Heading\n"
    "Fourth section of text here.\n"
)
_CRAWL_WITH_MD_HEADINGS["code_blocks"] = []


def _make_io_splitter(tmp_path: Path, md_index_enable: bool = False) -> ChunkSplitter:
    """Create a ChunkSplitter with temp directories rooted at tmp_path."""
    src_dir = tmp_path / "rag-src"
    src_dir.mkdir(exist_ok=True)
    cfg = dict(_CRAWL_CONFIG)
    cfg["rag_src_dir"] = str(src_dir)
    if md_index_enable:
        cfg["md_index_enable"] = True
    return ChunkSplitter(config=cfg)


# ── TestFetchedAtPropagation ──────────────────────────────────────────────────


class TestFetchedAtPropagation:
    """Every chunk file written by ChunkSplitter carries the same fetched_at value."""

    def _write_crawl_json(self, tmp_path: Path, payload: dict) -> Path:
        stem = Path(payload["url"]).name.replace("/", "_").replace(".", "_")
        path = tmp_path / "rag-src" / f"{stem}.json"
        path.write_bytes(orjson.dumps(payload))
        return path

    def test_long_text_splits_into_multiple_chunks_with_matching_fetched_at(
        self, tmp_path: Path
    ) -> None:
        splitter = _make_io_splitter(tmp_path)
        self._write_crawl_json(tmp_path, _CRAWL_WITH_MULTI_PARAGRAPHS)
        total = splitter.process_all(force=True)
        assert total >= 2
        chunk_dir = tmp_path / "rag-src" / "chunk"
        chunk_files = sorted(chunk_dir.glob("*.json"))
        assert len(chunk_files) >= 2
        expected = "2026-01-01T00:00:00Z"
        for cf in chunk_files:
            data = orjson.loads(cf.read_bytes())
            assert data["fetched_at"] == expected

    def test_text_plus_code_block_both_have_matching_fetched_at(
        self, tmp_path: Path
    ) -> None:
        splitter = _make_io_splitter(tmp_path)
        self._write_crawl_json(tmp_path, _CRAWL_WITH_TEXT_AND_CODE)
        total = splitter.process_all(force=True)
        assert total >= 2
        chunk_dir = tmp_path / "rag-src" / "chunk"
        chunk_files = sorted(chunk_dir.glob("*.json"))
        assert len(chunk_files) >= 2
        expected = "2026-01-01T00:00:00Z"
        for cf in chunk_files:
            data = orjson.loads(cf.read_bytes())
            assert data["fetched_at"] == expected

    def test_long_single_paragraph_has_fetched_at(self, tmp_path: Path) -> None:
        splitter = _make_io_splitter(tmp_path)
        self._write_crawl_json(tmp_path, _CRAWL_WITH_LONG_SINGLE)
        total = splitter.process_all(force=True)
        assert total == 1
        chunk_dir = tmp_path / "rag-src" / "chunk"
        chunk_files = sorted(chunk_dir.glob("*.json"))
        assert len(chunk_files) == 1
        expected = "2026-01-01T00:00:00Z"
        data = orjson.loads(chunk_files[0].read_bytes())
        assert data["fetched_at"] == expected

    def test_code_only_chunk_has_fetched_at(self, tmp_path: Path) -> None:
        splitter = _make_io_splitter(tmp_path)
        self._write_crawl_json(tmp_path, _CRAWL_WITH_CODE_ONLY)
        total = splitter.process_all(force=True)
        assert total == 1
        chunk_dir = tmp_path / "rag-src" / "chunk"
        chunk_files = sorted(chunk_dir.glob("*.json"))
        assert len(chunk_files) == 1
        expected = "2026-01-01T00:00:00Z"
        data = orjson.loads(chunk_files[0].read_bytes())
        assert data["fetched_at"] == expected

    def test_md_heading_splits_have_matching_fetched_at(self, tmp_path: Path) -> None:
        splitter = _make_io_splitter(tmp_path, md_index_enable=True)
        self._write_crawl_json(tmp_path, _CRAWL_WITH_MD_HEADINGS)
        total = splitter.process_all(force=True)
        assert total >= 3
        chunk_dir = tmp_path / "rag-src" / "chunk"
        chunk_files = sorted(chunk_dir.glob("*.json"))
        assert len(chunk_files) >= 3
        expected = "2026-01-01T00:00:00Z"
        for cf in chunk_files:
            data = orjson.loads(cf.read_bytes())
            assert data["fetched_at"] == expected

    def test_different_fetched_at_values_are_preserved_per_file(
        self, tmp_path: Path
    ) -> None:
        splitter = _make_io_splitter(tmp_path)
        payload_a = dict(_CRAWL_PAYLOAD_BASE)
        payload_a["url"] = "http://example.com/pageA"
        payload_a["content"] = _LONG_SINGLE
        payload_a["code_blocks"] = []
        payload_a["fetched_at"] = "2026-02-01T00:00:00Z"
        self._write_crawl_json(tmp_path, payload_a)
        payload_b = dict(_CRAWL_PAYLOAD_BASE)
        payload_b["url"] = "http://example.com/pageB"
        payload_b["content"] = _LONG_SINGLE
        payload_b["code_blocks"] = [_CODE_BLOCK]
        payload_b["fetched_at"] = "2026-03-01T00:00:00Z"
        self._write_crawl_json(tmp_path, payload_b)
        total = splitter.process_all(force=True)
        assert total >= 2
        chunk_dir = tmp_path / "rag-src" / "chunk"
        chunk_files = sorted(chunk_dir.glob("*.json"))
        page_a_files = [cf for cf in chunk_files if "pageA" in cf.name]
        page_b_files = [cf for cf in chunk_files if "pageB" in cf.name]
        for cf in page_a_files:
            data = orjson.loads(cf.read_bytes())
            assert data["fetched_at"] == "2026-02-01T00:00:00Z"
        for cf in page_b_files:
            data = orjson.loads(cf.read_bytes())
            assert data["fetched_at"] == "2026-03-01T00:00:00Z"
