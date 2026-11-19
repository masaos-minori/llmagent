#!/usr/bin/env python3
"""scripts/rag/ingestion/chunk_japanese.py

ChunkJapaneseMixin: morphological-analysis-based chunking for Japanese text.

Provides _chunk_japanese, _split_into_ja_sentences, _normalize_ja_sentence,
_merge_ja_sentence_pairs. Mixed into ChunkSplitter via multiple inheritance.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Protocol

from shared.logger import Logger
from sudachipy import tokenizer as sudachi_tok

from rag.exceptions import TokenizationError
from rag.ingestion.chunk_utils import _split_overlong, accumulate_items, start_next_buf
from rag.models_data import ChunkSettings
from rag.utils import normalize_unicode

logger = Logger(__name__, "/opt/llm/logs/chunk.log")


class _Token(Protocol):
    """A Sudachi morpheme as seen by the Japanese chunker.

    Captures exactly the two operations ``_normalize_ja_sentence`` uses so no
    third-party Sudachi type leaks into the typed path (ragcrv006, REQ-006).
    """

    def part_of_speech(self) -> list[str]: ...
    def normalized_form(self) -> str: ...


class Tokenizer(Protocol):
    """Sudachi-compatible tokenizer adapter behind a local Protocol.

    The real Sudachi tokenizer is stored on ``ChunkSplitter`` as ``self._tokenizer``
    and typed against this Protocol so the tokenization path carries no ``Any``
    (ragcrv006, REQ-006). ``mode`` is the ``SplitMode`` forwarded to ``tokenize``.
    """

    def tokenize(self, text: str, mode: object) -> Iterable[_Token]: ...


# SplitMode.C: longest compound unit; optimal for NLP downstream tasks. Kept at
# the consumer so the adapter stays a single ``self._tokenizer`` field.
_SPLIT_MODE_C = sudachi_tok.Tokenizer.SplitMode.C


class ChunkJapaneseMixin:
    """Japanese text chunking methods, mixed into ChunkSplitter."""

    # Declared here so mypy sees them. Settings arrive via the shared
    # ChunkSettings value object (ragcrv006); the tokenizer adapter is stored on
    # ChunkSplitter behind the local Protocol above.
    _settings: ChunkSettings
    _tokenizer: Tokenizer

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
            morphemes = self._tokenizer.tokenize(text, _SPLIT_MODE_C)
        except RuntimeError as e:
            raise TokenizationError(
                f"Sudachi tokenize error for {text[:50]!r}: {e}"
            ) from e
        tokens: list[str] = []
        for m in morphemes:
            pos = m.part_of_speech()[0]
            if pos in self._settings.ja_stop_pos:
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
            return len(buf[0]) + len(item[0]) + 1 <= self._settings.max_chunk

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
            if len(item[0]) > self._settings.max_chunk:
                return _split_overlong(item[0], " ", self._settings.max_chunk)
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
            return len(buf[0]) >= self._settings.min_chunk

        def emit_and_overlap(
            result: list[tuple[str, str | None]],
            buf: tuple[str, str | None],
            item: tuple[str, str | None],
        ) -> tuple[str, str | None]:
            result.append((buf[0], buf[1]))
            buf_norm = buf[1] if buf[1] is not None else ""
            item_norm = item[1] if item[1] is not None else ""
            new_orig = start_next_buf(
                buf[0], item[0], " ", self._settings.chunk_overlap
            )
            new_norm = start_next_buf(
                buf_norm, item_norm, " ", self._settings.chunk_overlap
            )
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
            if len(buf[0]) >= self._settings.min_chunk:
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
            initial_buffer=("", ""),
        )
