"""
tests/test_chunk_utils.py
Unit tests for rag/ingestion/chunk_utils.py.
"""

from __future__ import annotations

import pytest
from rag.ingestion.chunk_utils import merge_text_items, start_next_buf


class TestStartNextBuf:
    def test_no_overlap_returns_next_item(self) -> None:
        result = start_next_buf("previous content", "next item", " ", chunk_overlap=0)
        assert result == "next item"

    def test_overlap_appends_tail_of_prev(self) -> None:
        result = start_next_buf("abcdef", "new", " ", chunk_overlap=3)
        assert result == "def new"

    def test_overlap_larger_than_prev(self) -> None:
        result = start_next_buf("ab", "new", " ", chunk_overlap=10)
        assert result == "ab new"

    def test_empty_prev_with_overlap(self) -> None:
        result = start_next_buf("", "new", " ", chunk_overlap=3)
        assert result == "new"

    def test_custom_separator(self) -> None:
        result = start_next_buf("abcdef", "new", "\n", chunk_overlap=2)
        assert result == "ef\nnew"

    def test_overlap_strip(self) -> None:
        result = start_next_buf("  end  ", "next", " ", chunk_overlap=5)
        assert result == result.strip()


class TestMergeTextItems:
    def test_empty_items_returns_empty(self) -> None:
        result = merge_text_items([], " ", min_chunk=10, max_chunk=100, chunk_overlap=0)
        assert result == []

    def test_single_item_within_range(self) -> None:
        result = merge_text_items(
            ["hello world"], " ", min_chunk=5, max_chunk=50, chunk_overlap=0
        )
        assert result == ["hello world"]

    def test_items_merged_within_max(self) -> None:
        items = ["aa", "bb", "cc"]
        result = merge_text_items(
            items, " ", min_chunk=1, max_chunk=20, chunk_overlap=0
        )
        assert result == ["aa bb cc"]

    def test_items_split_at_max(self) -> None:
        items = ["aaaaa", "bbbbb", "ccccc"]
        result = merge_text_items(items, " ", min_chunk=4, max_chunk=8, chunk_overlap=0)
        assert all(len(r) <= 10 for r in result)
        assert len(result) >= 2

    def test_short_tail_merged_into_last(self) -> None:
        items = ["a" * 50, "a" * 50, "x"]
        result = merge_text_items(
            items, " ", min_chunk=40, max_chunk=60, chunk_overlap=0
        )
        assert result[-1].endswith("x")

    def test_all_items_below_min_chunk(self) -> None:
        items = ["a", "b", "c"]
        result = merge_text_items(
            items, " ", min_chunk=5, max_chunk=20, chunk_overlap=0
        )
        assert len(result) >= 1

    def test_overlap_carries_tail(self) -> None:
        items = ["abcde", "fghij", "klmno"]
        result = merge_text_items(items, " ", min_chunk=4, max_chunk=8, chunk_overlap=2)
        assert len(result) >= 2
        for chunk in result:
            assert len(chunk) <= 12

    @pytest.mark.parametrize("min_c,max_c", [(1, 100), (5, 50), (10, 20)])
    def test_result_chunks_within_bounds(self, min_c: int, max_c: int) -> None:
        items = ["word " * 3 for _ in range(10)]
        result = merge_text_items(
            items, " ", min_chunk=min_c, max_chunk=max_c, chunk_overlap=0
        )
        for chunk in result[:-1]:
            assert len(chunk) <= max_c + 10
