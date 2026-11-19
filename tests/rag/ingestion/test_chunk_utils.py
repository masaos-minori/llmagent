"""
tests/test_chunk_utils.py
Unit tests for rag/ingestion/chunk_utils.py.
"""

from __future__ import annotations

import pytest
from rag.ingestion.chunk_utils import (
    _split_overlong,
    accumulate_items,
    merge_text_items,
    start_next_buf,
)


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

    def test_oversized_single_item_capped(self) -> None:
        long_item = "word " * 40
        result = merge_text_items(
            [long_item], " ", min_chunk=1, max_chunk=50, chunk_overlap=0
        )
        assert len(result) >= 2
        assert all(len(chunk) <= 50 for chunk in result)
        assert "".join(result) == long_item

    def test_item_at_max_chunk_emitted_unchanged(self) -> None:
        item = "a" * 50
        result = merge_text_items(
            [item], " ", min_chunk=1, max_chunk=50, chunk_overlap=0
        )
        assert result == [item]


class TestSplitOverlong:
    @pytest.mark.parametrize("max_chunk", [0, -1])
    def test_non_positive_max_chunk_raises(self, max_chunk: int) -> None:
        with pytest.raises(ValueError):
            _split_overlong("a" * 100, " ", max_chunk)

    def test_positive_max_chunk_splits_and_reproduces_input(self) -> None:
        item = "word " * 40
        chunks = _split_overlong(item, " ", 50)
        assert chunks
        assert all(len(c) <= 50 for c in chunks)
        assert "".join(chunks) == item


# ── TestMergeTextItemsCharacterization ────────────────────────────────────────
# Exact golden outputs for the code path, pinned so any change to the shared
# accumulation loop (chunk_utils.accumulate_items) or the code callbacks is
# caught. Values are hand-traced against the pre-refactor control flow.


class TestMergeTextItemsCharacterization:
    def test_oversized_item_split_into_max_chunk_pieces(self) -> None:
        # A single overlong item with an empty lead buffer is split into
        # <=max_chunk pieces; the concatenation reproduces the input exactly.
        result = merge_text_items(
            ["A" * 25], " ", min_chunk=10, max_chunk=10, chunk_overlap=0
        )
        assert result == ["A" * 10, "A" * 10, "A" * 5]
        assert "".join(result) == "A" * 25

    def test_oversized_then_short_tail_tail_merges_into_last_piece(self) -> None:
        # An overlong item splits (lead buffer dropped), then a short trailing
        # item (< min_chunk) is tail-merged into the last piece, not dropped.
        result = merge_text_items(
            ["A" * 30, "xy"], " ", min_chunk=10, max_chunk=12, chunk_overlap=0
        )
        assert result == ["A" * 12, "A" * 12, "AAAAAA xy"]
        assert "".join(result) == "A" * 30 + " xy"

    def test_overlap_carries_buffer_tail_into_next_chunk(self) -> None:
        # A full buffer that cannot absorb the next item emits, carrying the
        # configured overlap tail into the freshly started buffer.
        result = merge_text_items(
            ["AB" * 5, "CD" * 5], " ", min_chunk=10, max_chunk=12, chunk_overlap=3
        )
        assert result == ["AB" * 5, "BAB " + "CD" * 5]

    def test_short_buffer_below_min_is_replaced_by_next_item(self) -> None:
        # A short (< min_chunk) buffer that cannot grow is replaced by the next
        # item (code path drops it rather than emitting it mid-stream).
        result = merge_text_items(
            ["ab", "CD" * 5], " ", min_chunk=10, max_chunk=12, chunk_overlap=0
        )
        assert result == ["CD" * 5]


# ── TestAccumulateItemsBranches ───────────────────────────────────────────────
# Drive the collaborator directly with minimal callbacks so each loop branch
# (fits/append, oversized, emit+overlap, short-tail, finalize) is exercised in
# isolation. Each assertion pins the branch's observable effect, so a mutation
# in that branch fails the corresponding test.


class TestAccumulateItemsBranches:
    def test_fits_branch_appends_without_emit(self) -> None:
        log: list[object] = []

        def fits(buf: str, item: str) -> bool:
            log.append(("fits", buf, item))
            return True

        def append_item(buf: str, item: str) -> str:
            return buf + item

        def segment_oversized(buf: str, item: str) -> list[str] | None:
            return None

        def place_oversized(
            buf: str, item: str, pieces: list[str]
        ) -> tuple[list[str], str]:
            log.append(("place", buf))
            return (pieces, "")

        def should_emit(buf: str) -> bool:
            return False

        def emit_and_overlap(result: list[str], buf: str, item: str) -> str:
            result.append(buf)
            return item

        def short_tail(result: list[str], buf: str, item: str) -> str:
            return item

        def finalize_buffer(result: list[str], buf: str) -> None:
            if buf:
                result.append(buf)

        out = accumulate_items(
            ["aa", "bb", "cc"],
            " ",
            10,
            100,
            0,
            fits=fits,
            append_item=append_item,
            segment_oversized=segment_oversized,
            place_oversized=place_oversized,
            should_emit=should_emit,
            emit_and_overlap=emit_and_overlap,
            short_tail=short_tail,
            finalize_buffer=finalize_buffer,
            initial_buffer="",
        )
        # Every item fit, so they accumulated into one buffer and emitted once.
        assert out == ["aabbcc"]
        assert log == [("fits", "", "aa"), ("fits", "aa", "bb"), ("fits", "aabb", "cc")]

    def test_oversized_branch_splits_and_drops_lead(self) -> None:
        log: list[object] = []

        def fits(buf: str, item: str) -> bool:
            return False

        def append_item(buf: str, item: str) -> str:
            return buf + item

        def segment_oversized(buf: str, item: str) -> list[str] | None:
            log.append(("segment", item))
            return ["p1", "p2"]

        def place_oversized(
            buf: str, item: str, pieces: list[str]
        ) -> tuple[list[str], str]:
            log.append(("place", buf))
            return (pieces, "")

        def should_emit(buf: str) -> bool:
            return False

        def emit_and_overlap(result: list[str], buf: str, item: str) -> str:
            result.append(buf)
            return item

        def short_tail(result: list[str], buf: str, item: str) -> str:
            return item

        def finalize_buffer(result: list[str], buf: str) -> None:
            pass

        out = accumulate_items(
            ["OVERLONG"],
            " ",
            10,
            5,
            0,
            fits=fits,
            append_item=append_item,
            segment_oversized=segment_oversized,
            place_oversized=place_oversized,
            should_emit=should_emit,
            emit_and_overlap=emit_and_overlap,
            short_tail=short_tail,
            finalize_buffer=finalize_buffer,
            initial_buffer="",
        )
        assert out == ["p1", "p2"]
        assert log == [("segment", "OVERLONG"), ("place", "")]

    def test_emit_overlap_branch_flushes_and_starts_with_overlap(self) -> None:
        def fits(buf: str, item: str) -> bool:
            return len(buf) + len(item) + 1 <= 8

        def append_item(buf: str, item: str) -> str:
            return buf + item

        def segment_oversized(buf: str, item: str) -> list[str] | None:
            return None

        def place_oversized(
            buf: str, item: str, pieces: list[str]
        ) -> tuple[list[str], str]:
            return (pieces, "")

        def should_emit(buf: str) -> bool:
            return len(buf) >= 5

        def emit_and_overlap(result: list[str], buf: str, item: str) -> str:
            result.append(buf)
            return start_next_buf(buf, item, " ", 2)

        def short_tail(result: list[str], buf: str, item: str) -> str:
            return item

        def finalize_buffer(result: list[str], buf: str) -> None:
            if buf:
                result.append(buf)

        out = accumulate_items(
            ["aaaaaa", "bbbbbb", "cccccc"],
            " ",
            5,
            8,
            2,
            fits=fits,
            append_item=append_item,
            segment_oversized=segment_oversized,
            place_oversized=place_oversized,
            should_emit=should_emit,
            emit_and_overlap=emit_and_overlap,
            short_tail=short_tail,
            finalize_buffer=finalize_buffer,
            initial_buffer="",
        )
        assert out == ["aaaaaa", "aa " + "bbbbbb", "bb " + "cccccc"]

    def test_finalize_tail_merges_short_trailing_buffer(self) -> None:
        def fits(buf: str, item: str) -> bool:
            return len(buf) + len(item) + 1 <= 12

        def append_item(buf: str, item: str) -> str:
            return (buf + " " + item).strip()

        def segment_oversized(buf: str, item: str) -> list[str] | None:
            if len(item) > 12 and len(buf) < 10:
                return ["A" * 12, "A" * 12, "A" * 6]
            return None

        def place_oversized(
            buf: str, item: str, pieces: list[str]
        ) -> tuple[list[str], str]:
            return (pieces, "")

        def should_emit(buf: str) -> bool:
            return len(buf) >= 10

        def emit_and_overlap(result: list[str], buf: str, item: str) -> str:
            result.append(buf)
            return start_next_buf(buf, item, " ", 0)

        def short_tail(result: list[str], buf: str, item: str) -> str:
            return item

        def finalize_buffer(result: list[str], buf: str) -> None:
            if not buf:
                return
            if len(buf) >= 10:
                result.append(buf)
            elif result:
                result[-1] = (result[-1] + " " + buf).strip()

        out = accumulate_items(
            ["A" * 30, "xy"],
            " ",
            10,
            12,
            0,
            fits=fits,
            append_item=append_item,
            segment_oversized=segment_oversized,
            place_oversized=place_oversized,
            should_emit=should_emit,
            emit_and_overlap=emit_and_overlap,
            short_tail=short_tail,
            finalize_buffer=finalize_buffer,
            initial_buffer="",
        )
        assert out == ["A" * 12, "A" * 12, "AAAAAA xy"]


# ── TestPairedCompanion ───────────────────────────────────────────────────────
# The Japanese path feeds (original, normalized) pairs through the same loop,
# where the buffer element type is a pair whose normalized value may be None.
# These pin that contract directly on the collaborator.


class TestPairedCompanion:
    @staticmethod
    def _pair_callbacks(min_chunk: int, max_chunk: int, overlap: int):
        def fits(buf: tuple[str, str | None], item: tuple[str, str | None]) -> bool:
            return len(buf[0]) + len(item[0]) + 1 <= max_chunk

        def append_item(
            buf: tuple[str, str | None], item: tuple[str, str | None]
        ) -> tuple[str, str | None]:
            norm_str = item[1] if item[1] is not None else ""
            new_orig = (buf[0] + " " + item[0]).strip()
            new_norm = (buf[1] + " " + norm_str).strip()
            return (new_orig, new_norm)

        def segment_oversized(
            buf: tuple[str, str | None], item: tuple[str, str | None]
        ) -> list[str] | None:
            return None

        def place_oversized(
            buf: tuple[str, str | None],
            item: tuple[str, str | None],
            pieces: list[str],
        ) -> tuple[list[tuple[str, str | None]], tuple[str, str | None]]:
            appends = [(buf[0], buf[1] or None)] if buf[0] else []
            return (appends + [(p, None) for p in pieces], ("", ""))

        def should_emit(buf: tuple[str, str | None]) -> bool:
            return len(buf[0]) >= min_chunk

        def emit_and_overlap(
            result: list[tuple[str, str | None]],
            buf: tuple[str, str | None],
            item: tuple[str, str | None],
        ) -> tuple[str, str | None]:
            result.append(buf)
            norm_str = item[1] if item[1] is not None else ""
            new_orig = start_next_buf(buf[0], item[0], " ", overlap)
            new_norm = start_next_buf(buf[1] or "", norm_str, " ", overlap)
            return (new_orig, new_norm)

        def short_tail(
            result: list[tuple[str, str | None]],
            buf: tuple[str, str | None],
            item: tuple[str, str | None],
        ) -> tuple[str, str | None]:
            norm_str = item[1] if item[1] is not None else ""
            if buf[0]:
                result.append((buf[0], buf[1] or None))
            return (item[0], norm_str)

        def finalize_buffer(
            result: list[tuple[str, str | None]],
            buf: tuple[str, str | None],
        ) -> None:
            if not buf[0]:
                return
            if len(buf[0]) >= min_chunk:
                result.append((buf[0], buf[1] or None))
            elif result:
                last_o, last_n = result[-1]
                buf_norm = buf[1] if buf[1] is not None else ""
                result[-1] = (
                    (last_o + " " + buf[0]).strip(),
                    (last_n + " " + buf_norm).strip() if last_n is not None else None,
                )

        return dict(
            fits=fits,
            append_item=append_item,
            segment_oversized=segment_oversized,
            place_oversized=place_oversized,
            should_emit=should_emit,
            emit_and_overlap=emit_and_overlap,
            short_tail=short_tail,
            finalize_buffer=finalize_buffer,
        )

    def test_none_norm_is_preserved_as_none_in_emitted_pair(self) -> None:
        # A paired item whose normalized value is None must surface as None in
        # the emitted pair (Japanese COALESCE contract), never as "".
        out = accumulate_items(
            [("ab", None), ("DD" * 5, "DD" * 5)],
            " ",
            10,
            12,
            0,
            **self._pair_callbacks(10, 12, 0),
            initial_buffer=("", ""),
        )
        assert out == [("ab", None), ("DDDDDDDDDD", "DDDDDDDDDD")]

    def test_accumulated_pairs_coalesce_none_then_emit(self) -> None:
        # When a None-norm item accumulates with a valid-norm item, the empty
        # normalized values collapse and the merged pair carries the valid norm.
        out = accumulate_items(
            [("one", None), ("two", "two")],
            " ",
            2,
            100,
            0,
            **self._pair_callbacks(2, 100, 0),
            initial_buffer=("", ""),
        )
        assert out == [("one two", "two")]
