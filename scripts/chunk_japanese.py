#!/usr/bin/env python3
"""
chunk_japanese.py
ChunkJapaneseMixin: morphological-analysis-based chunking for Japanese text.

Provides _chunk_japanese, _split_into_ja_sentences, _normalize_ja_sentence,
_merge_ja_sentence_pairs. Mixed into ChunkSplitter via multiple inheritance.
"""

from __future__ import annotations

import re
from typing import Any

from logger import Logger
from rag_utils import normalize_unicode

logger = Logger(__name__, "/opt/llm/logs/chunk.log")


class ChunkJapaneseMixin:
    """Japanese text chunking methods, mixed into ChunkSplitter."""

    # Declared here so mypy sees them; values come from ChunkSplitter.__init__
    _max_chunk: int
    _min_chunk: int
    _chunk_overlap: int
    _ja_stop_pos: frozenset[str]
    _sd_tkn: Any  # sudachipy Tokenizer instance
    _split_c: Any  # sudachipy Tokenizer.SplitMode.C

    def _chunk_japanese(self, text: str) -> list[tuple[str, str]]:
        """Split Japanese text into (original_content, normalized_content) chunk pairs.

        Processing order:
        1. Normalize full-width alphanumerics via NFKC.
        2. Split into (original, normalized) sentence pairs at Japanese punctuation.
        3. Morphological analysis with Sudachi SplitMode.C for normalization.
        4. Remove stop-POS tokens; keep normalized content words in normalized.
        5. Merge pairs into chunks satisfying min_chunk <= len(original) <= max_chunk.
        """
        text = normalize_unicode(text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        pairs = self._split_into_ja_sentences(text)
        return self._merge_ja_sentence_pairs(pairs)

    def _split_into_ja_sentences(self, text: str) -> list[tuple[str, str]]:
        """Split Japanese text at clause boundaries (。！？ and newlines).

        Returns (original_text, normalized_text) pairs; empty pairs are discarded.
        """
        pairs: list[tuple[str, str]] = []
        for raw in re.split(r"(?<=[。！？\n])", text):
            original = raw.strip()
            if not original:
                continue
            normalized = self._normalize_ja_sentence(original)
            if normalized:
                pairs.append((original, normalized))
        return pairs

    def _normalize_ja_sentence(self, text: str) -> str:
        """Run Sudachi SplitMode.C morphological analysis; return normalized content words.

        normalized_form() unifies inflected forms to the dictionary base form
        (e.g. conjugated form -> infinitive).
        """
        if not text:
            return ""
        try:
            morphemes = self._sd_tkn.tokenize(text, self._split_c)
        except RuntimeError as e:
            logger.debug(f"Sudachi tokenize error for {text[:50]!r}: {e}")
            return ""
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
        self, pairs: list[tuple[str, str]]
    ) -> list[tuple[str, str]]:
        """Accumulate (original, normalized) pairs into chunk pairs.

        Chunk size is determined by original text length.
        Overlap (when configured) is taken from the tail of each buffer.
        """
        if not pairs:
            return []
        sep = " "
        overhead = len(sep)
        result: list[tuple[str, str]] = []
        orig_buf = ""
        norm_buf = ""
        for orig, norm in pairs:
            if len(orig_buf) + len(orig) + overhead <= self._max_chunk:
                # Current sentence still fits; append to the running buffer
                orig_buf = (orig_buf + sep + orig).strip()
                norm_buf = (norm_buf + sep + norm).strip()
            elif len(orig_buf) >= self._min_chunk:
                # Buffer is large enough to emit as a chunk
                result.append((orig_buf, norm_buf))
                if self._chunk_overlap:
                    orig_buf = (orig_buf[-self._chunk_overlap :] + sep + orig).strip()
                    norm_buf = (norm_buf[-self._chunk_overlap :] + sep + norm).strip()
                else:
                    orig_buf = orig
                    norm_buf = norm
            else:
                # Buffer too short to emit; discard and start fresh from this sentence
                orig_buf = orig
                norm_buf = norm
        if not orig_buf:
            return result
        if len(orig_buf) >= self._min_chunk:
            result.append((orig_buf, norm_buf))
        elif result:
            # Merge short tail into the last chunk to avoid losing content
            last_o, last_n = result[-1]
            result[-1] = (
                (last_o + sep + orig_buf).strip(),
                (last_n + sep + norm_buf).strip(),
            )
        return result
