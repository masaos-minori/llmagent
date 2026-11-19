#!/usr/bin/env python3
"""scripts/rag/ingestion/chunk_english.py

ChunkEnglishMixin: paragraph/sentence-level chunking for English text.

Provides _chunk_english, _merge_paragraphs_en, _split_sentences_en,
_filter_stopwords_en. Mixed into ChunkSplitter via multiple inheritance.
"""

from __future__ import annotations

import re

from rag.ingestion.chunk_utils import accumulate_items, start_next_buf
from rag.models_data import ChunkSettings


class ChunkEnglishMixin:
    """English text chunking methods, mixed into ChunkSplitter."""

    # Settings arrive via the shared ChunkSettings value object (ragcrv006).
    _settings: ChunkSettings

    # Per-file size-rule discard accumulator. Reset at the start of
    # ChunkSplitter._build_chunk_list; written by the chunkers below and read by
    # ChunkSplitter.process_file. Initialized to 0 here (not in __init__) so a
    # direct chunker call on an object.__new__ splitter never raises AttributeError
    # before the first reset.
    _discarded_count: int = 0
    _discarded_chars: int = 0

    def _chunk_english(self, text: str) -> list[str]:
        """Split English text into chunks at paragraph/sentence boundaries; merges short paragraphs and discards chunks below min_chunk (measured on the post-filter length). Returns the UNFILTERED original regions as content; normalized_content is NULL."""
        paragraphs = re.split(r"\n{2,}", text.strip())
        raw_chunks = self._merge_paragraphs_en(paragraphs)
        # Discard basis preserved: measure len over the post-filter (stopword-stripped)
        # string. Store the UNFILTERED original as content (Shape B, REQ-001/REQ-002).
        filtered = [self._filter_stopwords_en(r) for r in raw_chunks]
        kept: list[str] = []
        for raw, stripped in zip(raw_chunks, filtered):
            if len(stripped) >= self._settings.min_chunk:
                kept.append(raw)
            else:
                self._discarded_count += 1
                self._discarded_chars += len(stripped)
        return kept

    def _merge_paragraphs_en(self, paragraphs: list[str]) -> list[str]:
        """Accumulate paragraphs into <=max_chunk chunks; split oversized paragraphs.

        Delegates the accumulation loop to :func:`accumulate_items`; sentence
        splitting stays in this mixin.
        """
        non_empty = [p.strip() for p in paragraphs if p.strip()]

        def fits(buf: str, item: str) -> bool:
            return len(buf) + len(item) + 1 <= self._settings.max_chunk

        def append_item(buf: str, item: str) -> str:
            return (buf + "\n" + item).strip()

        def segment_oversized(buf: str, item: str) -> list[str] | None:
            if len(item) > self._settings.max_chunk:
                return self._split_sentences_en(item)
            return None

        def place_oversized(
            buf: str, item: str, pieces: list[str]
        ) -> tuple[list[str], str]:
            # Flush any buffered lead before dumping the split pieces.
            appends: list[str] = [buf] if buf else []
            return (appends + pieces, "")

        def should_emit(buf: str) -> bool:
            return bool(buf)

        def emit_and_overlap(result: list[str], buf: str, item: str) -> str:
            result.append(buf)
            return start_next_buf(buf, item, "\n", self._settings.chunk_overlap)

        def short_tail(result: list[str], buf: str, item: str) -> str:
            return item

        def finalize_buffer(result: list[str], buf: str) -> None:
            if buf:
                result.append(buf)

        return accumulate_items(
            non_empty,
            "\n",
            self._settings.min_chunk,
            self._settings.max_chunk,
            self._settings.chunk_overlap,
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

    def _split_sentences_en(self, text: str) -> list[str]:
        """Split at sentence boundaries (. ! ?). Oversized sentences are kept as-is."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        buf = ""
        chunks: list[str] = []
        for s in sentences:
            if len(buf) + len(s) + 1 <= self._settings.max_chunk:
                buf = (buf + " " + s).strip()
            else:
                if buf:
                    chunks.append(buf)
                buf = s
        if buf:
            chunks.append(buf)
        return chunks

    def _filter_stopwords_en(self, text: str) -> str:
        """Remove EN stopwords (case-insensitive) and return space-joined tokens."""
        words = re.split(r"\s+", text.strip())
        kept = [w for w in words if w and w.lower() not in self._settings.en_stopwords]
        return " ".join(kept)
