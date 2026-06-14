"""tests/test_chunk_splitter.py
Behavior-lock tests for ChunkSplitter._is_markdown_source() and chunking_strategy in chunk JSON.
"""

from __future__ import annotations

from rag.ingestion.chunk_splitter import ChunkSplitter


def _make_splitter(md_index_enable: bool = False) -> ChunkSplitter:
    splitter = object.__new__(ChunkSplitter)
    splitter._md_index_enable = md_index_enable
    return splitter


class TestIsMarkdownSource:
    def test_md_extension_returns_true_regardless_of_flag(self) -> None:
        splitter = _make_splitter(md_index_enable=False)
        assert (
            splitter._is_markdown_source({"url": "https://example.com/README.md"})
            is True
        )

    def test_markdown_extension_returns_true(self) -> None:
        splitter = _make_splitter(md_index_enable=False)
        assert splitter._is_markdown_source({"url": "docs/guide.markdown"}) is True

    def test_mdx_extension_returns_true(self) -> None:
        splitter = _make_splitter(md_index_enable=False)
        assert splitter._is_markdown_source({"url": "component.mdx"}) is True

    def test_non_md_url_returns_false_when_flag_disabled(self) -> None:
        splitter = _make_splitter(md_index_enable=False)
        assert (
            splitter._is_markdown_source({"url": "https://example.com/page.html"})
            is False
        )

    def test_non_md_url_heuristic_when_flag_enabled(self) -> None:
        splitter = _make_splitter(md_index_enable=True)
        content = "# Heading 1\nsome text\n## Heading 2\nmore text"
        assert (
            splitter._is_markdown_source({"url": "page.html", "content": content})
            is True
        )

    def test_non_md_no_headings_returns_false_even_when_flag_enabled(self) -> None:
        splitter = _make_splitter(md_index_enable=True)
        assert (
            splitter._is_markdown_source({"url": "page.html", "content": "plain text"})
            is False
        )
