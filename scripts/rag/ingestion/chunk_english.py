#!/usr/bin/env python3
"""scripts/rag/ingestion/chunk_english.py

ChunkEnglishMixin: paragraph/sentence-level chunking for English text.

Provides _chunk_english, _merge_paragraphs_en, _split_sentences_en,
_filter_stopwords_en. Mixed into ChunkSplitter via multiple inheritance.
"""

from __future__ import annotations

import re

from rag.ingestion.chunk_utils import start_next_buf


class ChunkEnglishMixin:
    """English text chunking methods, mixed into ChunkSplitter."""

    # Declared here so mypy sees them; values come from ChunkSplitter.__init__
    _max_chunk: int
    _min_chunk: int
    _en_stopwords: frozenset[str]
    _chunk_overlap: int

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
            if len(stripped) >= self._min_chunk:
                kept.append(raw)
            else:
                self._discarded_count += 1
                self._discarded_chars += len(stripped)
        return kept

    def _merge_paragraphs_en(self, paragraphs: list[str]) -> list[str]:
        """Accumulate paragraphs into <=max_chunk chunks; split oversized paragraphs."""
        if not paragraphs:
            return []
        raw_chunks: list[str] = []
        self._buf = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(para) > self._max_chunk:
                self._flush_and_split(para, raw_chunks)
            elif len(self._buf) + len(para) + 1 <= self._max_chunk:
                self._buf = (self._buf + "\n" + para).strip()
            elif self._buf:
                self._flush_and_merge(self._buf, para, raw_chunks)
            else:
                self._buf = para
        if self._buf:
            raw_chunks.append(self._buf)
        return raw_chunks

    def _flush_and_split(self, para: str, chunks: list[str]) -> None:
        """Flush buffer and split oversized paragraph."""
        if buf := self._buf:
            chunks.append(buf)
            self._buf = ""
        chunks.extend(self._split_sentences_en(para))

    def _flush_and_merge(self, buf: str, para: str, chunks: list[str]) -> None:
        """Flush buffer and start new buffer with overlap."""
        chunks.append(buf)
        self._buf = start_next_buf(buf, para, "\n", self._chunk_overlap)

    def _split_sentences_en(self, text: str) -> list[str]:
        """Split at sentence boundaries (. ! ?). Oversized sentences are kept as-is."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        buf = ""
        chunks: list[str] = []
        for s in sentences:
            if len(buf) + len(s) + 1 <= self._max_chunk:
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
        kept = [w for w in words if w and w.lower() not in self._en_stopwords]
        return " ".join(kept)
