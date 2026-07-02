#!/usr/bin/env python3
"""chunk_japanese.py
ChunkJapaneseMixin: morphological-analysis-based chunking for Japanese text.

Provides _chunk_japanese, _split_into_ja_sentences, _normalize_ja_sentence,
_merge_ja_sentence_pairs. Mixed into ChunkSplitter via multiple inheritance.
"""

from __future__ import annotations

import re
from typing import Any

from rag.exceptions import TokenizationError
from rag.utils import normalize_unicode
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/chunk.log")


class ChunkJapaneseMixin:
    """Japanese text chunking methods, mixed into ChunkSplitter."""

    # Declared here so mypy sees them; values come from ChunkSplitter.__init__
    _max_chunk: int
    _min_chunk: int
    _chunk_overlap: int
    _ja_stop_pos: frozenset[str]
    _sd_tkn: Any  # sudachipy Tokenizer instance — third-party type not available at runtime
    _split_c: Any  # sudachipy Tokenizer.SplitMode.C — enum value, not a class
    _orig_buf: str
    _norm_buf: str
    _result: list[tuple[str, str]]

    def _chunk_japanese(self, text: str) -> list[tuple[str, str]]:
        """Split Japanese text into (original, normalized) chunk pairs via NFKC normalization, sentence splitting, and Sudachi morphological analysis."""
        text = normalize_unicode(text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        pairs = self._split_into_ja_sentences(text)
        return self._merge_ja_sentence_pairs(pairs)

    def _split_into_ja_sentences(self, text: str) -> list[tuple[str, str]]:
        """Split Japanese text at clause boundaries (。！？ and newlines); returns (original, normalized) pairs with empty pairs discarded."""
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
        pairs: list[tuple[str, str]],
    ) -> list[tuple[str, str]]:
        """Accumulate (original, normalized) sentence pairs into chunk pairs by original text length; applies overlap from buffer tail when configured."""
        if not pairs:
            return []
        result: list[tuple[str, str]] = []
        self._orig_buf = ""
        self._norm_buf = ""
        for orig, norm in pairs:
            if len(self._orig_buf) + len(orig) + 1 <= self._max_chunk:
                self._append_to_buffer(orig, norm)
            elif len(self._orig_buf) >= self._min_chunk:
                self._emit_and_start_new(orig, norm)
            else:
                self._reset_buffer(orig, norm)
        if not self._orig_buf:
            return result
        if len(self._orig_buf) >= self._min_chunk:
            result.append((self._orig_buf, self._norm_buf))
        elif result:
            self._merge_tail_into_last()
        return result

    def _append_to_buffer(self, orig: str, norm: str) -> None:
        """Append sentence to the running buffer."""
        self._orig_buf = (self._orig_buf + " " + orig).strip()
        self._norm_buf = (self._norm_buf + " " + norm).strip()

    def _emit_and_start_new(self, orig: str, norm: str) -> None:
        """Emit buffer as chunk and start new buffer with overlap."""
        self._result.append((self._orig_buf, self._norm_buf))
        if self._chunk_overlap:
            self._orig_buf = (
                self._orig_buf[-self._chunk_overlap :] + " " + orig
            ).strip()
            self._norm_buf = (
                self._norm_buf[-self._chunk_overlap :] + " " + norm
            ).strip()
        else:
            self._orig_buf = orig
            self._norm_buf = norm

    def _reset_buffer(self, orig: str, norm: str) -> None:
        """Discard buffer and start fresh from this sentence."""
        self._orig_buf = orig
        self._norm_buf = norm

    def _merge_tail_into_last(self) -> None:
        """Merge short tail into the last chunk to avoid losing content."""
        last_o, last_n = self._result[-1]
        self._result[-1] = (
            (last_o + " " + self._orig_buf).strip(),
            (last_n + " " + self._norm_buf).strip(),
        )
