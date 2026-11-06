"""tests/test_chunk_splitter.py
Behavior-lock tests for ChunkSplitter._is_markdown_source(), chunking_strategy in chunk JSON,
and fetched_at propagation across all written chunk files.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from unittest.mock import patch

import orjson
import pytest
from rag.ingestion.chunk_japanese import ChunkJapaneseMixin
from rag.ingestion.chunk_splitter import ChunkSplitter
from rag.ingestion.pipeline_utils import read_chunk_json
from rag.models_data import ChunkDocument
from rag.utils import normalize_unicode


def _make_splitter(md_index_enable: bool = False) -> ChunkSplitter:
    splitter = object.__new__(ChunkSplitter)
    splitter._md_index_enable = md_index_enable
    return splitter


def _make_chunk_doc(url: str, content: str = "", lang: str = "en") -> ChunkDocument:
    return ChunkDocument(
        url=url,
        title="",
        lang=lang,
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


# ── Helpers for Japanese chunk overlap characterization ───────────────────────


def _make_ja_mixin(**kwargs: Any) -> ChunkJapaneseMixin:
    """Create a ChunkJapaneseMixin with minimal attributes for direct testing."""
    mixin = object.__new__(ChunkJapaneseMixin)
    mixin._max_chunk = kwargs.get("_max_chunk", 500)
    mixin._min_chunk = kwargs.get("_min_chunk", 10)
    mixin._chunk_overlap = kwargs.get("_chunk_overlap", 10)
    mixin._ja_stop_pos = frozenset()
    mixin._sd_tkn = None
    mixin._split_c = None
    mixin._orig_buf = ""
    mixin._norm_buf = ""
    return mixin


# ── TestJapaneseChunkOverlap ──────────────────────────────────────────────────

# Note: These tests exercise _emit_and_start_new directly without Sudachi,
# using raw string buffers to make overlap behavior fully deterministic.


class TestJapaneseChunkOverlap:
    """Characterization tests for Japanese chunking with chunk_overlap > 0."""

    def test_emit_with_overlap_carries_tail_into_new_buffer(self) -> None:
        mixin = _make_ja_mixin(_chunk_overlap=10, _min_chunk=10)
        mixin._orig_buf = "abcdefghij1234567890"  # 20 chars
        mixin._norm_buf = "abcdefghij1234567890"
        result: list[tuple[str, str | None]] = []
        mixin._emit_and_start_new(result, "xyz", "xyz")
        assert len(result) == 1
        assert mixin._orig_buf == "1234567890 xyz"
        assert mixin._norm_buf == "1234567890 xyz"

    def test_emit_without_overlap_starts_fresh(self) -> None:
        mixin = _make_ja_mixin(_chunk_overlap=0, _min_chunk=10)
        mixin._orig_buf = "abcdefghij1234567890"
        mixin._norm_buf = "abcdefghij1234567890"
        result: list[tuple[str, str | None]] = []
        mixin._emit_and_start_new(result, "xyz", "xyz")
        assert len(result) == 1
        assert mixin._orig_buf == "xyz"
        assert mixin._norm_buf == "xyz"

    def test_emit_short_buffer_below_min_chunk_resets(self) -> None:
        mixin = _make_ja_mixin(_chunk_overlap=10, _min_chunk=10)
        mixin._orig_buf = "ab"  # below min_chunk
        mixin._norm_buf = "ab"
        # _merge_ja_sentence_pairs would call _reset_buffer here, not _emit_and_start_new
        # But we test _emit_and_start_new directly: it still emits the short buffer
        result: list[tuple[str, str | None]] = []
        mixin._emit_and_start_new(result, "xyz", "xyz")
        assert len(result) == 1
        # "ab"[-10:] = "ab" (full string since shorter than overlap size)
        assert mixin._orig_buf == "ab xyz"
        assert mixin._norm_buf == "ab xyz"

    def test_multiple_emits_preserve_consecutive_overlaps(self) -> None:
        mixin = _make_ja_mixin(_chunk_overlap=5, _min_chunk=10)
        result: list[tuple[str, str | None]] = []
        # First emit
        mixin._orig_buf = "aaaaabbbbbccccc"  # 15 chars
        mixin._norm_buf = "AAAAABBBBBCCCCC"
        mixin._emit_and_start_new(result, "11111", "11111")
        assert mixin._orig_buf == "ccccc 11111"
        assert mixin._norm_buf == "CCCCC 11111"
        # Second emit
        mixin._orig_buf = "11111dddddeeeee"  # 15 chars
        mixin._norm_buf = "11111DDDDDEEEEE"
        mixin._emit_and_start_new(result, "22222", "22222")
        assert mixin._orig_buf == "eeeee 22222"
        assert mixin._norm_buf == "EEEEE 22222"
        assert len(result) == 2

    def test_empty_buffer_at_emit_start_is_harmless(self) -> None:
        mixin = _make_ja_mixin(_chunk_overlap=10, _min_chunk=10)
        mixin._orig_buf = ""
        mixin._norm_buf = ""
        result: list[tuple[str, str | None]] = []
        mixin._emit_and_start_new(result, "xyz", "xyz")
        assert len(result) == 1
        assert mixin._orig_buf == "xyz"
        assert mixin._norm_buf == "xyz"

    def test_overlap_equals_buffer_length(self) -> None:
        mixin = _make_ja_mixin(_chunk_overlap=15, _min_chunk=10)
        mixin._orig_buf = "aaaaabbbbbccccc"  # exactly 15 chars
        mixin._norm_buf = "AAAAABBBBBCCCCC"
        result: list[tuple[str, str | None]] = []
        mixin._emit_and_start_new(result, "xyz", "xyz")
        assert mixin._orig_buf == "aaaaabbbbbccccc xyz"
        assert mixin._norm_buf == "AAAAABBBBBCCCCC xyz"

    def test_overlap_larger_than_buffer_returns_full_buffer_plus_new(self) -> None:
        mixin = _make_ja_mixin(_chunk_overlap=100, _min_chunk=10)
        mixin._orig_buf = "abc"  # shorter than overlap
        mixin._norm_buf = "ABC"
        result: list[tuple[str, str | None]] = []
        mixin._emit_and_start_new(result, "xyz", "xyz")
        # prev[-100:] = "abc" (full buffer since shorter than overlap)
        assert mixin._orig_buf == "abc xyz"
        assert mixin._norm_buf == "ABC xyz"

    def test_strip_removes_trailing_space_before_sep(self) -> None:
        mixin = _make_ja_mixin(_chunk_overlap=5, _min_chunk=10)
        mixin._orig_buf = "aaaaabbbbbccccc"  # ends with 'c'
        mixin._norm_buf = "AAAAABBBBBCCCCC"
        result: list[tuple[str, str | None]] = []
        mixin._emit_and_start_new(result, "xyz", "xyz")
        # overlap = "ccccc", sep = " ", next = "xyz" => "ccccc xyz"
        # strip removes leading space if overlap is empty — but overlap is not empty here
        assert mixin._orig_buf == "ccccc xyz"
        assert mixin._norm_buf == "CCCCC xyz"


# ── TestEmptyNormalization (RAG-002 regression) ───────────────────────────────


class TestEmptyNormalization:
    """Regression tests that Japanese sentences whose normalized result is empty
    are retained (not dropped) and surfaced with a NULL normalized value.

    Covers RAG-002 / ADR-009 INV-11: normalization must not lose original text.
    """

    def test_empty_normalization_kept_not_dropped(self) -> None:
        mixin = _make_ja_mixin()
        with patch.object(mixin, "_normalize_ja_sentence", return_value=""):
            pairs = mixin._split_into_ja_sentences("。")
        assert pairs == [("。", None)]

    def test_all_empty_normalization_chunk_surfaces_original_with_none(
        self,
    ) -> None:
        mixin = _make_ja_mixin(_min_chunk=10)
        with patch.object(mixin, "_normalize_ja_sentence", return_value=""):
            chunks = mixin._chunk_japanese("。" * 11)
        assert len(chunks) == 1
        original, normalized = chunks[0]
        assert original.count("。") == 11
        assert normalized is None


# ── TestJapaneseMergeRegression (raging001 REQ-003) ────────────────────────────


class TestJapaneseMergeRegression:
    """Regression: every chunk emitted by _merge_ja_sentence_pairs is returned.

    Pre-fix the helpers appended to a never-initialized self._result, raising
    AttributeError as soon as a boundary emit happened.
    """

    def test_multi_emit_overlap_returns_all_chunks_in_order(self) -> None:
        mixin = _make_ja_mixin(_max_chunk=20, _min_chunk=10, _chunk_overlap=5)
        pairs = [
            ("あ" * 12, "あ" * 12),
            ("い" * 12, "い" * 12),
            ("う" * 12, "う" * 12),
        ]
        chunks = mixin._merge_ja_sentence_pairs(pairs)
        assert len(chunks) == 3
        original = [o for o, _ in chunks]
        normalized = [n for _, n in chunks]
        assert all(n is not None for n in normalized)
        assert all(len(chunk) >= 10 for chunk in original)
        assert original[0] == "あ" * 12
        assert "う" * 12 in original[2]

    def test_multi_emit_zero_overlap_returns_all_chunks(self) -> None:
        mixin = _make_ja_mixin(_max_chunk=20, _min_chunk=10, _chunk_overlap=0)
        pairs = [
            ("あ" * 12, "あ" * 12),
            ("い" * 12, "い" * 12),
            ("う" * 12, "う" * 12),
        ]
        chunks = mixin._merge_ja_sentence_pairs(pairs)
        assert chunks == [
            ("あ" * 12, "あ" * 12),
            ("い" * 12, "い" * 12),
            ("う" * 12, "う" * 12),
        ]

    def test_short_tail_merge_returns_all_chunks(self) -> None:
        mixin = _make_ja_mixin(_max_chunk=14, _min_chunk=10, _chunk_overlap=0)
        pairs = [
            ("あ" * 12, "あ" * 12),
            ("い" * 12, "い" * 12),
            ("うう", "うう"),
        ]
        chunks = mixin._merge_ja_sentence_pairs(pairs)
        assert len(chunks) == 2
        assert chunks[1][0] == "い" * 12 + " うう"
        assert chunks[1][1] == "い" * 12 + " うう"


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


# ── TestChunkPayloadKeyContract ───────────────────────────────────────────────


class TestChunkPayloadKeyContract:
    """The real ChunkSplitter writer output must satisfy read_chunk_json's key contract."""

    _EXPECTED_KEYS = {
        "schema_version",
        "artifact_type",
        "created_by",
        "url",
        "content",
        "title",
        "lang",
        "code_blocks",
        "etag",
        "last_modified",
        "normalized_content",
        "chunk_index",
        "source_file",
        "chunk_type",
        "chunking_strategy",
        "fetched_at",
    }

    def _write_crawl_json(self, tmp_path: Path, payload: dict) -> Path:
        stem = Path(payload["url"]).name.replace("/", "_").replace(".", "_")
        path = tmp_path / "rag-src" / f"{stem}.json"
        path.write_bytes(orjson.dumps(payload))
        return path

    def test_written_chunk_payload_satisfies_key_contract(self, tmp_path: Path) -> None:
        """Every chunk file written by the real writer must pass read_chunk_json (AC-001/003)."""
        splitter = _make_io_splitter(tmp_path)
        self._write_crawl_json(tmp_path, _CRAWL_WITH_TEXT_AND_CODE)
        splitter.process_all(force=True)
        chunk_dir = tmp_path / "rag-src" / "chunk"
        chunk_files = sorted(chunk_dir.glob("*.json"))
        assert chunk_files
        for cf in chunk_files:
            data = orjson.loads(cf.read_bytes())
            assert set(data.keys()) == self._EXPECTED_KEYS
            parsed = read_chunk_json(cf)
            assert parsed.code_blocks == []


def _make_crawl_json(
    lang: str,
    content: str,
    url: str = "http://example.com/page",
    title: str = "Test Page",
) -> dict:
    return {
        "url": url,
        "title": title,
        "lang": lang,
        "fetched_at": "2024-01-01T00:00:00",
        "content": content,
        "code_blocks": [],
        "schema_version": "1",
        "artifact_type": "chunk",
        "created_by": "chunk_splitter",
        "etag": "etag-test",
        "last_modified": "2024-01-01T00:00:00",
    }


class TestProcessFileEndToEnd:
    def test_process_file_end_to_end_english(self, tmp_path: Path) -> None:
        import json

        content = "Hello world from the test page. " * 50
        data = _make_crawl_json(lang="en", content=content)
        src = tmp_path / "en-page.json"
        src.write_text(json.dumps(data), encoding="utf-8")

        chunk_dir = tmp_path / "chunk"
        chunk_dir.mkdir(exist_ok=True)
        chunker = ChunkSplitter(
            config={
                "rag_src_dir": str(tmp_path),
                "min_chunk": 10,
                "max_chunk": 1000,
                "en_stopwords": [],
                "ja_stop_pos": [],
            }
        )

        result = chunker.process_file(src, force=True)
        assert result >= 1

        outputs = sorted(chunk_dir.glob(f"{src.stem}-*.json"))
        assert len(outputs) == result
        reassembled = ""
        for i, out_path in enumerate(outputs):
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            assert payload["lang"] == "en"
            assert payload["source_file"] == src.name
            assert payload["chunk_index"] == i
            assert payload["content"]
            reassembled += payload["content"]
        assert "Hello world" in reassembled

    def test_process_file_end_to_end_japanese(self, tmp_path: Path) -> None:
        import json

        content = "日本語のテストページです。これはテスト用の文章です。" * 50
        data = _make_crawl_json(lang="ja", content=content)
        src = tmp_path / "ja-page.json"
        src.write_text(json.dumps(data), encoding="utf-8")

        chunk_dir = tmp_path / "chunk"
        chunk_dir.mkdir(exist_ok=True)
        chunker = ChunkSplitter(
            config={
                "rag_src_dir": str(tmp_path),
                "min_chunk": 10,
                "max_chunk": 1000,
                "en_stopwords": [],
                "ja_stop_pos": [],
            }
        )
        result = chunker.process_file(src, force=True)
        assert result >= 1

        outputs = sorted(chunk_dir.glob(f"{src.stem}-*.json"))
        assert len(outputs) == result
        reassembled = ""
        for i, out_path in enumerate(outputs):
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            assert payload["lang"] == "ja"
            assert payload["source_file"] == src.name
            assert payload["chunk_index"] == i
            assert payload["content"]
            reassembled += payload["content"]
        # Coverage: content lost to a swallowed chunk would break any of these.
        assert result >= 2
        stripped = reassembled.replace(" ", "")
        assert stripped.startswith("日本語のテストページです。")
        assert stripped.endswith("これはテスト用の文章です。")
        assert stripped.count("。") >= content.count("。")


# ── ChunkSplitter dictionary resolver wiring (REQ-003) ───────────────────────


class TestSudachiResolverWiring:
    def test_init_passes_resolver_arg_to_dictionary(
        self, monkeypatch, tmp_path
    ) -> None:
        """ChunkSplitter builds Dictionary with the resolver's dict argument."""
        from pathlib import Path
        from unittest.mock import MagicMock

        import rag.ingestion.chunk_splitter as cs_mod

        sentinel = Path("/tmp/sentinel-sudachi.dic")
        monkeypatch.setattr(cs_mod, "resolve_sudachi_dict_path", lambda: sentinel)
        mock_dictionary = MagicMock(name="Dictionary")
        monkeypatch.setattr("sudachipy.dictionary.Dictionary", mock_dictionary)

        ChunkSplitter(
            config={
                "rag_src_dir": str(tmp_path),
                "min_chunk": 10,
                "max_chunk": 1000,
                "en_stopwords": [],
                "ja_stop_pos": [],
            }
        )

        # The resolver's return value is forwarded verbatim to Dictionary(dict=...).
        mock_dictionary.assert_called_once_with(dict=sentinel)

    def test_init_default_core_when_unset_uncompiled(
        self, monkeypatch, tmp_path
    ) -> None:
        """With LLMAGENT_SUDACHI_DICT unset and uncompiled, Dictionary gets "core"."""
        from unittest.mock import MagicMock

        import rag.ingestion.chunk_splitter as cs_mod

        monkeypatch.delenv("LLMAGENT_SUDACHI_DICT", raising=False)
        monkeypatch.delattr(cs_mod, "__compiled__", raising=False)

        mock_dictionary = MagicMock(name="Dictionary")
        monkeypatch.setattr("sudachipy.dictionary.Dictionary", mock_dictionary)

        ChunkSplitter(
            config={
                "rag_src_dir": str(tmp_path),
                "min_chunk": 10,
                "max_chunk": 1000,
                "en_stopwords": [],
                "ja_stop_pos": [],
            }
        )

        mock_dictionary.assert_called_once_with(dict="core")


# ── Helpers for forced re-chunk prune tests (raging004) ────────────────────────


def _make_prune_splitter(
    tmp_path: Path, min_chunk: int = 40, max_chunk: int = 500
) -> ChunkSplitter:
    """ChunkSplitter rooted at tmp_path for forced re-chunk prune tests."""
    return ChunkSplitter(
        config={
            "rag_src_dir": str(tmp_path),
            "min_chunk": min_chunk,
            "max_chunk": max_chunk,
            "en_stopwords": [],
            "ja_stop_pos": [],
        }
    )


def _write_prune_src(tmp_path: Path, stem: str, content: str) -> Path:
    """Write a crawler JSON source named {stem}.json under the splitter's rag_src_dir."""
    src = tmp_path / f"{stem}.json"
    src.write_bytes(
        orjson.dumps(
            _make_crawl_json(
                lang="en", content=content, url=f"http://example.com/{stem}"
            )
        )
    )
    return src


def _chunk_series(chunk_dir: Path, stem: str) -> list[Path]:
    """Files of chunk_dir whose full name belongs to the stem's chunk series."""
    if not chunk_dir.exists():
        return []
    pattern = re.compile(rf"^{re.escape(stem)}-\d{{4,}}\.json$")
    return sorted(p for p in chunk_dir.glob("*.json") if pattern.fullmatch(p.name))


def _series_indices(files: list[Path]) -> list[str]:
    """Chunk suffix (zero-padded index part) of each series file."""
    return [p.name[len(p.name) - 9 : -5] for p in files]


# ── TestForceRechunkPrune (raging004 REQ-001 / REQ-003) ────────────────────────


class TestForceRechunkPrune:
    """A force=True run is authoritative for its source's chunk series.

    Red before the fix: shrink (a) and zero-chunk (c). Characterization:
    grow (b), stem isolation (d), broken source (e), chunking error (f),
    non-forced rerun (g).
    """

    def test_shrink_forced_run_replaces_full_series(self, tmp_path: Path) -> None:
        src = _write_prune_src(tmp_path, "page", _LONG_SINGLE)
        old_count = _make_prune_splitter(tmp_path, max_chunk=200).process_file(
            src, force=True
        )
        new_count = _make_prune_splitter(tmp_path, max_chunk=600).process_file(
            src, force=True
        )
        assert new_count < old_count  # shrink precondition
        files = _chunk_series(tmp_path / "chunk", "page")
        assert len(files) == new_count
        assert _series_indices(files) == [f"{i:04d}" for i in range(new_count)]
        for i, path in enumerate(files):
            assert orjson.loads(path.read_bytes())["chunk_index"] == i

    def test_grow_forced_run_leaves_no_gaps(self, tmp_path: Path) -> None:
        src = _write_prune_src(tmp_path, "page", _LONG_SINGLE)
        old_count = _make_prune_splitter(tmp_path, max_chunk=600).process_file(
            src, force=True
        )
        new_count = _make_prune_splitter(tmp_path, max_chunk=200).process_file(
            src, force=True
        )
        assert new_count > old_count  # grow precondition
        files = _chunk_series(tmp_path / "chunk", "page")
        assert len(files) == new_count
        assert _series_indices(files) == [f"{i:04d}" for i in range(new_count)]

    def test_zero_chunk_forced_run_removes_old_series(self, tmp_path: Path) -> None:
        src = _write_prune_src(tmp_path, "page", _LONG_SINGLE)
        old_count = _make_prune_splitter(tmp_path, max_chunk=200).process_file(
            src, force=True
        )
        assert old_count >= 1
        new_count = _make_prune_splitter(
            tmp_path, min_chunk=100000, max_chunk=600
        ).process_file(src, force=True)
        assert new_count == 0
        assert _chunk_series(tmp_path / "chunk", "page") == []

    def test_forced_run_does_not_touch_numeric_suffix_stem(
        self, tmp_path: Path
    ) -> None:
        src_page = _write_prune_src(tmp_path, "page", _LONG_SINGLE)
        src_other = _write_prune_src(tmp_path, "page-1234", _LONG_SINGLE)
        splitter = _make_prune_splitter(tmp_path, max_chunk=200)
        assert splitter.process_file(src_page, force=True) >= 1
        assert splitter.process_file(src_other, force=True) >= 1
        before = {
            p.name: p.read_bytes()
            for p in _chunk_series(tmp_path / "chunk", "page-1234")
        }
        assert before
        _make_prune_splitter(tmp_path, max_chunk=600).process_file(src_page, force=True)
        after = {
            p.name: p.read_bytes()
            for p in _chunk_series(tmp_path / "chunk", "page-1234")
        }
        assert after == before

    def test_broken_source_preserves_existing_series(self, tmp_path: Path) -> None:
        src = _write_prune_src(tmp_path, "page", _LONG_SINGLE)
        old_count = _make_prune_splitter(tmp_path, max_chunk=200).process_file(
            src, force=True
        )
        assert old_count >= 1
        before = [p.name for p in _chunk_series(tmp_path / "chunk", "page")]
        src.write_text("{ not json", encoding="utf-8")
        assert (
            _make_prune_splitter(tmp_path, max_chunk=600).process_file(src, force=True)
            == 0
        )
        assert [p.name for p in _chunk_series(tmp_path / "chunk", "page")] == before

    def test_chunking_error_preserves_existing_series(self, tmp_path: Path) -> None:
        src = _write_prune_src(tmp_path, "page", _LONG_SINGLE)
        old_count = _make_prune_splitter(tmp_path, max_chunk=200).process_file(
            src, force=True
        )
        assert old_count >= 1
        before = [p.name for p in _chunk_series(tmp_path / "chunk", "page")]
        splitter = _make_prune_splitter(tmp_path, max_chunk=600)
        with patch.object(
            splitter, "_build_chunk_list", side_effect=RuntimeError("chunking boom")
        ):
            with pytest.raises(RuntimeError, match="chunking boom"):
                splitter.process_file(src, force=True)
        assert [p.name for p in _chunk_series(tmp_path / "chunk", "page")] == before

    def test_non_forced_rerun_skips_and_keeps_files(self, tmp_path: Path) -> None:
        src = _write_prune_src(tmp_path, "page", _LONG_SINGLE)
        splitter = _make_prune_splitter(tmp_path, max_chunk=200)
        old_count = splitter.process_file(src, force=True)
        assert old_count >= 1
        before = [p.name for p in _chunk_series(tmp_path / "chunk", "page")]
        assert splitter.process_file(src, force=False) == 0
        assert [p.name for p in _chunk_series(tmp_path / "chunk", "page")] == before


# ── TestEnglishMarkdownCharacterization ────────────────────────────────────────

_EN_MD_CHAR_CONTENT = (
    "# Alpha Section\n"
    "This fitting section is comfortably longer than the minimum chunk size.\n\n"
    "## Beta Oversized Section\n"
    + "The oversized section contains many sentences so that it exceeds the snippet maximum. "
    * 8
    + "\n\n### Tiny\n"
    "Too small to keep.\n\n"
    "## Gamma Fit\n"
    "Another fitting section that stays comfortably within the snippet maximum limit.\n"
)

_EN_MD_CHAR_BASELINE: list[tuple[str, str, str | None]] = [
    (
        "text",
        "# Alpha Section\n"
        "This fitting section is comfortably longer than the minimum chunk size.",
        "",
    ),
    (
        "text",
        "## Beta Oversized Section oversized section contains sentences exceeds snippet maximum. "
        "oversized section contains sentences exceeds snippet maximum. "
        "oversized section contains sentences exceeds snippet maximum. "
        "oversized section contains sentences exceeds snippet maximum. "
        "oversized section contains sentences exceeds snippet maximum.",
        "",
    ),
    (
        "text",
        "oversized section contains sentences exceeds snippet maximum. "
        "oversized section contains sentences exceeds snippet maximum. "
        "oversized section contains sentences exceeds snippet maximum.",
        "",
    ),
    (
        "text",
        "## Gamma Fit\n"
        "Another fitting section that stays comfortably within the snippet maximum limit.",
        "",
    ),
]


class TestEnglishMarkdownCharacterization:
    """REQ-003: pin today's English .md heading chunk output byte-identical (behavior lock)."""

    def _write_md_crawl(self, tmp_path: Path, lang: str, content: str) -> None:
        payload = dict(_CRAWL_PAYLOAD_BASE)
        payload["url"] = "http://example.com/docs/README.md"
        payload["lang"] = lang
        payload["content"] = content
        payload["code_blocks"] = []
        (tmp_path / "rag-src" / "readme.json").write_bytes(orjson.dumps(payload))

    def _split(self, tmp_path: Path) -> list[tuple[str, str, str | None]]:
        splitter = _make_io_splitter(tmp_path)
        return splitter._build_chunk_list(
            _make_chunk_doc("http://example.com/README.md", _EN_MD_CHAR_CONTENT)
        )

    def test_english_markdown_snapshot_is_byte_identical(self, tmp_path: Path) -> None:
        assert self._split(tmp_path) == _EN_MD_CHAR_BASELINE

    def test_english_markdown_normalized_content_is_empty(self, tmp_path: Path) -> None:
        assert all(norm == "" for _, _, norm in self._split(tmp_path))

    def test_english_markdown_sub_min_chunk_section_is_dropped(
        self, tmp_path: Path
    ) -> None:
        assert all("Tiny" not in content for _, content, _ in self._split(tmp_path))

    def test_english_markdown_strategy_pin_is_heading(self, tmp_path: Path) -> None:
        splitter = _make_io_splitter(tmp_path)
        self._write_md_crawl(tmp_path, "en", _EN_MD_CHAR_CONTENT)
        assert splitter.process_all(force=True) >= 1
        chunk_files = sorted((tmp_path / "rag-src" / "chunk").glob("*.json"))
        assert chunk_files
        for cf in chunk_files:
            data = orjson.loads(cf.read_bytes())
            assert data["chunking_strategy"] == "heading"


# ── TestJapaneseMarkdownChunking ───────────────────────────────────────────────

_JA_MD_FIT_SECTION = (
    "# First Section\n"
    "これは日本語の見出し内セクションです。固定長で、四十字を超える十分な本文を含みます。"
)
_JA_MD_OVERSIZED_BODY = (
    "これは日本語の過大セクションです。文を繰り返して六百字を超えます。" * 25
)
_JA_MD_OVERSIZED_SECTION = "## Second Section\n" + _JA_MD_OVERSIZED_BODY
_JA_MD_CONTENT = _JA_MD_FIT_SECTION + "\n\n" + _JA_MD_OVERSIZED_SECTION


class TestJapaneseMarkdownChunking:
    """REQ-004: ja .md sources must follow Japanese chunking semantics with normalized pairs."""

    def _split(
        self, tmp_path: Path
    ) -> tuple[ChunkSplitter, list[tuple[str, str, str | None]]]:
        splitter = _make_io_splitter(tmp_path)
        triples = splitter._build_chunk_list(
            _make_chunk_doc("http://example.com/README.md", _JA_MD_CONTENT, lang="ja")
        )
        return splitter, triples

    def test_ja_oversized_section_is_segmented_by_japanese_rules(
        self, tmp_path: Path
    ) -> None:
        splitter, triples = self._split(tmp_path)
        expected = splitter._chunk_japanese(_JA_MD_OVERSIZED_SECTION)
        assert len(expected) > 1
        assert triples[1:] == [("text", orig, norm) for orig, norm in expected]

    def test_ja_oversized_chunks_carry_non_empty_normalized(
        self, tmp_path: Path
    ) -> None:
        _, triples = self._split(tmp_path)
        assert triples[1:]
        assert all(norm for _, _, norm in triples[1:])

    def test_ja_in_section_stays_whole_but_carries_normalized(
        self, tmp_path: Path
    ) -> None:
        splitter, triples = self._split(tmp_path)
        expected_norm = splitter._normalize_ja_sentence(
            re.sub(r"\n{3,}", "\n\n", normalize_unicode(_JA_MD_FIT_SECTION)).strip()
        )
        assert expected_norm
        assert triples[0] == ("text", _JA_MD_FIT_SECTION, expected_norm)

    def test_ja_markdown_strategy_pin_is_heading(self, tmp_path: Path) -> None:
        splitter = _make_io_splitter(tmp_path)
        payload = dict(_CRAWL_PAYLOAD_BASE)
        payload["url"] = "http://example.com/docs/README.md"
        payload["lang"] = "ja"
        payload["content"] = _JA_MD_CONTENT
        payload["code_blocks"] = []
        (tmp_path / "rag-src" / "readme.json").write_bytes(orjson.dumps(payload))
        assert splitter.process_all(force=True) >= 1
        chunk_files = sorted((tmp_path / "rag-src" / "chunk").glob("*.json"))
        assert chunk_files
        for cf in chunk_files:
            data = orjson.loads(cf.read_bytes())
            assert data["chunking_strategy"] == "heading"
