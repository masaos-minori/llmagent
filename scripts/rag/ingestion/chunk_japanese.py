#!/usr/bin/env python3
"""scripts/rag/ingestion/chunk_japanese.py

ChunkJapaneseMixin: morphological-analysis-based chunking for Japanese text.

Provides _chunk_japanese, _split_into_ja_sentences, _normalize_ja_sentence,
_merge_ja_sentence_pairs. Mixed into ChunkSplitter via multiple inheritance.
"""

from __future__ import annotations

import re
from typing import Any

from shared.logger import Logger

from rag.exceptions import TokenizationError
from rag.ingestion.chunk_utils import _split_overlong, accumulate_items, start_next_buf
from rag.utils import normalize_unicode

logger = Logger(__name__, "/opt/llm/logs/chunk.log")


class ChunkJapaneseMixin:
    """Japanese text chunking methods, mixed into ChunkSplitter."""

    # Declared here so mypy sees them; values come from ChunkSplitter.__init__
    _max_chunk: int
    _min_chunk: int
    _chunk_overlap: int
    _ja_stop_pos: frozenset[str]
    _sd_tkn: (
        Any  # sudachipy Tokenizer instance — third-party type not available at runtime
    )
    _split_c: Any  # sudachipy Tokenizer.SplitMode.C — enum value, not a class
    _orig_buf: str
    _norm_buf: str

    def _chunk_japanese(self, text: str) -> list[tuple[str, str | None]]:
        """Split Japanese text into (original, normalized) chunk pairs via NFKC normalization, sentence splitting, and Sudachi morphological analysis."""
        text = normalize_unicode(text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        pairs = self._split_into_ja_sentences(text)
        return self._merge_ja_sentence_pairs(pairs)

    def _split_into_ja_sentences(self, text: str) -> list[tuple[str, str | None]]:
        """Split Japanese text at clause boundaries (。！？ and newlines); keeps every non-empty sentence and maps an empty normalized result to None so downstream COALESCE falls back to the original text."""
        pairs: list[tuple[str, str | None]] = []
        for raw in re.split(r"(?<=[。！？\n])", text):
            original = raw.strip()
            if not original:
                continue
            normalized = self._normalize_ja_sentence(original)
            normalized_value = normalized if normalized else None
            pairs.append((original, normalized_value))
        return pairs

    def _normalize_ja_sentence(self, text: str) -> str:
        """Run Sudachi SplitMode.C morphological analysis; return space-joined normalized content words (normalized_form() unifies inflected forms)."""
        if not text:
            return ""
        try:
            morphemes = self._sd_tkn.tokenize(text, self._split_c)
        except RuntimeError as e:
            raise TokenizationError(
                f"Sudachi tokenize error for {text[:50]!r}: {e}"
            ) from e
        tokens: list[str] = []
        for m in morphemes:
            pos = m.part_of_speech()[0]
            if pos in self._ja_stop_pos:
                continue
            nf = m.normalized_form()
            if nf and nf.strip():
                tokens.append(nf)
        return " ".join(tokens)

    def _merge_ja_sentence_pairs(
        self,
        pairs: list[tuple[str, str | None]],
    ) -> list[tuple[str, str | None]]:
        """Accumulate (original, normalized) sentence pairs into chunk pairs by original text length; applies overlap from buffer tail when configured. A sentence longer than max_chunk is segmented by the shared _split_overlong rule and an empty buffer never emits. Empty normalized results (None) are preserved and surfaced as NULL so downstream COALESCE falls back to the original text.

        Delegates the accumulation loop to :func:`accumulate_items`; morphological normalization stays here.
        """

        def fits(buf: tuple[str, str | None], item: tuple[str, str | None]) -> bool:
            return len(buf[0]) + len(item[0]) + 1 <= self._max_chunk

        def append_item(
            buf: tuple[str, str | None], item: tuple[str, str | None]
        ) -> tuple[str, str | None]:
            prev_norm = buf[1] if buf[1] is not None else ""
            item_norm = item[1] if item[1] is not None else ""
            new_orig = (buf[0] + " " + item[0]).strip()
            new_norm = (prev_norm + " " + item_norm).strip()
            return (new_orig, new_norm)

        def segment_oversized(
            buf: tuple[str, str | None], item: tuple[str, str | None]
        ) -> list[str] | None:
            # An oversized sentence is segmented within max_chunk; any buffered
            # lead is flushed by place_oversized before the pieces are dumped.
            del buf  # unused; oversized detection depends only on the item.
            if len(item[0]) > self._max_chunk:
                return _split_overlong(item[0], " ", self._max_chunk)
            return None

        def place_oversized(
            buf: tuple[str, str | None],
            item: tuple[str, str | None],
            pieces: list[str],
        ) -> tuple[list[tuple[str, str | None]], tuple[str, str | None]]:
            # Flush any buffered lead, then dump split pieces with None norm.
            del item  # unused; only the buffered lead is flushed.
            appends: list[tuple[str, str | None]] = (
                [(buf[0], buf[1] or None)] if buf[0] else []
            )
            wrapped: list[tuple[str, str | None]] = [(p, None) for p in pieces]
            return (appends + wrapped, ("", ""))

        def should_emit(buf: tuple[str, str | None]) -> bool:
            return len(buf[0]) >= self._min_chunk

        def emit_and_overlap(
            result: list[tuple[str, str | None]],
            buf: tuple[str, str | None],
            item: tuple[str, str | None],
        ) -> tuple[str, str | None]:
            result.append((buf[0], buf[1]))
            buf_norm = buf[1] if buf[1] is not None else ""
            item_norm = item[1] if item[1] is not None else ""
            new_orig = start_next_buf(buf[0], item[0], " ", self._chunk_overlap)
            new_norm = start_next_buf(buf_norm, item_norm, " ", self._chunk_overlap)
            return (new_orig, new_norm)

        def short_tail(
            result: list[tuple[str, str | None]],
            buf: tuple[str, str | None],
            item: tuple[str, str | None],
        ) -> tuple[str, str | None]:
            norm_str = item[1] if item[1] is not None else ""
            # Retain the short (< min_chunk) buffer as its own chunk rather than
            # dropping it; an empty buffer simply starts fresh from this sentence.
            if buf[0]:
                result.append((buf[0], buf[1] or None))
            return (item[0], norm_str)

        def finalize_buffer(
            result: list[tuple[str, str | None]],
            buf: tuple[str, str | None],
        ) -> None:
            if not buf[0]:
                return
            if len(buf[0]) >= self._min_chunk:
                result.append((buf[0], buf[1] or None))
            elif result:
                buf_norm = buf[1] if buf[1] is not None else ""
                last_o, last_n = result[-1]
                result[-1] = (
                    (last_o + " " + buf[0]).strip(),
                    (last_n + " " + buf_norm).strip() if last_n is not None else None,
                )

        return accumulate_items(
            pairs,
            " ",
            self._min_chunk,
            self._max_chunk,
            self._chunk_overlap,
            fits=fits,
            append_item=append_item,
            segment_oversized=segment_oversized,
            place_oversized=place_oversized,
            should_emit=should_emit,
            emit_and_overlap=emit_and_overlap,
            short_tail=short_tail,
            finalize_buffer=finalize_buffer,
            initial_buffer=("", ""),
        )
