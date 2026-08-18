#!/usr/bin/env python3
"""scripts/rag/repository.py

RAG data-access layer: FTS5/vector search, RRF merge, and document fetching.

Extracted from rag/pipeline.py.  Contains:
  - Japanese FTS5 tokenization helpers (Sudachi)
  - RagRepository  — all SQL confined here
  - RagScorer      — Reciprocal Rank Fusion (RRF)
  - Standalone helper functions: vector_search, fts_search, fetch_full_document,
    deduplicate_chunks, _dedup_hits
"""

import logging
import re
import time
from typing import Any

from db.helper import SQLiteHelper
from shared.types import (
    MergedHit,
    RagHit,  # noqa: F401 — imported for use in this module
    RawHit,
)

from rag.utils import floats_to_blob

logger = logging.getLogger(__name__)

# Maximum number of tokens to include in an FTS5 query (prevents query explosion)
_MAX_FTS_TOKENS = 20
# Sudachi POS categories retained for Japanese FTS5 query tokens (content words only)
_FTS_KEEP_POS: frozenset[str] = frozenset({"名詞", "動詞", "形容詞"})


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁ_SudachiTokenizerǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut: MutantDict = {}  # type: ignore


class _SudachiTokenizer:
    """Lazy wrapper around sudachipy Tokenizer — loaded on first use."""

    @_mutmut_mutated(mutants_xǁ_SudachiTokenizerǁ__init____mutmut)
    def __init__(self) -> None:
        """Initialize with uninitialized tokenizer state."""
        self._tkn: object = None
        self._mode: object = None

    def xǁ_SudachiTokenizerǁ__init____mutmut_orig(self) -> None:
        """Initialize with uninitialized tokenizer state."""
        self._tkn: object = None
        self._mode: object = None

    def xǁ_SudachiTokenizerǁ__init____mutmut_1(self) -> None:
        """Initialize with uninitialized tokenizer state."""
        self._tkn: object = ""
        self._mode: object = None

    def xǁ_SudachiTokenizerǁ__init____mutmut_2(self) -> None:
        """Initialize with uninitialized tokenizer state."""
        self._tkn: object = None
        self._mode: object = ""

    @_mutmut_mutated(mutants_xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut)
    def _ensure_loaded(self) -> None:
        """Lazily initialize the Sudachi tokenizer on first use."""
        if self._tkn is None:
            from sudachipy import (
                dictionary as _sd_dict,
            )
            from sudachipy import (
                tokenizer as _sd_tok,
            )

            d = _sd_dict.Dictionary(dict="core")
            self._tkn = d.create()
            self._mode = _sd_tok.Tokenizer.SplitMode.C

    def xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_orig(self) -> None:
        """Lazily initialize the Sudachi tokenizer on first use."""
        if self._tkn is None:
            from sudachipy import (
                dictionary as _sd_dict,
            )
            from sudachipy import (
                tokenizer as _sd_tok,
            )

            d = _sd_dict.Dictionary(dict="core")
            self._tkn = d.create()
            self._mode = _sd_tok.Tokenizer.SplitMode.C

    def xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_1(self) -> None:
        """Lazily initialize the Sudachi tokenizer on first use."""
        if self._tkn is not None:
            from sudachipy import (
                dictionary as _sd_dict,
            )
            from sudachipy import (
                tokenizer as _sd_tok,
            )

            d = _sd_dict.Dictionary(dict="core")
            self._tkn = d.create()
            self._mode = _sd_tok.Tokenizer.SplitMode.C

    def xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_2(self) -> None:
        """Lazily initialize the Sudachi tokenizer on first use."""
        if self._tkn is None:
            from sudachipy import (
                dictionary as _sd_dict,
            )
            from sudachipy import (
                tokenizer as _sd_tok,
            )

            d = None
            self._tkn = d.create()
            self._mode = _sd_tok.Tokenizer.SplitMode.C

    def xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_3(self) -> None:
        """Lazily initialize the Sudachi tokenizer on first use."""
        if self._tkn is None:
            from sudachipy import (
                dictionary as _sd_dict,
            )
            from sudachipy import (
                tokenizer as _sd_tok,
            )

            d = _sd_dict.Dictionary(dict=None)
            self._tkn = d.create()
            self._mode = _sd_tok.Tokenizer.SplitMode.C

    def xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_4(self) -> None:
        """Lazily initialize the Sudachi tokenizer on first use."""
        if self._tkn is None:
            from sudachipy import (
                dictionary as _sd_dict,
            )
            from sudachipy import (
                tokenizer as _sd_tok,
            )

            d = _sd_dict.Dictionary(dict="XXcoreXX")
            self._tkn = d.create()
            self._mode = _sd_tok.Tokenizer.SplitMode.C

    def xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_5(self) -> None:
        """Lazily initialize the Sudachi tokenizer on first use."""
        if self._tkn is None:
            from sudachipy import (
                dictionary as _sd_dict,
            )
            from sudachipy import (
                tokenizer as _sd_tok,
            )

            d = _sd_dict.Dictionary(dict="CORE")
            self._tkn = d.create()
            self._mode = _sd_tok.Tokenizer.SplitMode.C

    def xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_6(self) -> None:
        """Lazily initialize the Sudachi tokenizer on first use."""
        if self._tkn is None:
            from sudachipy import (
                dictionary as _sd_dict,
            )
            from sudachipy import (
                tokenizer as _sd_tok,
            )

            d = _sd_dict.Dictionary(dict="core")
            self._tkn = None
            self._mode = _sd_tok.Tokenizer.SplitMode.C

    def xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_7(self) -> None:
        """Lazily initialize the Sudachi tokenizer on first use."""
        if self._tkn is None:
            from sudachipy import (
                dictionary as _sd_dict,
            )
            from sudachipy import (
                tokenizer as _sd_tok,
            )

            d = _sd_dict.Dictionary(dict="core")
            self._tkn = d.create()
            self._mode = None

    @_mutmut_mutated(mutants_xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut)
    def tokenize_pos_filter(self, text: str, keep_pos: frozenset[str]) -> list[str]:
        """Return normalized_form() for tokens whose part_of_speech()[0] is in keep_pos."""
        self._ensure_loaded()
        try:
            return [
                m.normalized_form()
                for m in self._tkn.tokenize(text, self._mode)  # type: ignore[attr-defined]  # self._tkn is object; sudachipy loaded lazily
                if m.part_of_speech()[0] in keep_pos and m.normalized_form().strip()
            ]
        except RuntimeError as e:
            raise RuntimeError(f"Sudachi tokenization failed: {e}") from e

    def xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_orig(self, text: str, keep_pos: frozenset[str]) -> list[str]:
        """Return normalized_form() for tokens whose part_of_speech()[0] is in keep_pos."""
        self._ensure_loaded()
        try:
            return [
                m.normalized_form()
                for m in self._tkn.tokenize(text, self._mode)  # type: ignore[attr-defined]  # self._tkn is object; sudachipy loaded lazily
                if m.part_of_speech()[0] in keep_pos and m.normalized_form().strip()
            ]
        except RuntimeError as e:
            raise RuntimeError(f"Sudachi tokenization failed: {e}") from e

    def xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_1(self, text: str, keep_pos: frozenset[str]) -> list[str]:
        """Return normalized_form() for tokens whose part_of_speech()[0] is in keep_pos."""
        self._ensure_loaded()
        try:
            return [
                m.normalized_form()
                for m in self._tkn.tokenize(None, self._mode)  # type: ignore[attr-defined]  # self._tkn is object; sudachipy loaded lazily
                if m.part_of_speech()[0] in keep_pos and m.normalized_form().strip()
            ]
        except RuntimeError as e:
            raise RuntimeError(f"Sudachi tokenization failed: {e}") from e

    def xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_2(self, text: str, keep_pos: frozenset[str]) -> list[str]:
        """Return normalized_form() for tokens whose part_of_speech()[0] is in keep_pos."""
        self._ensure_loaded()
        try:
            return [
                m.normalized_form()
                for m in self._tkn.tokenize(text, None)  # type: ignore[attr-defined]  # self._tkn is object; sudachipy loaded lazily
                if m.part_of_speech()[0] in keep_pos and m.normalized_form().strip()
            ]
        except RuntimeError as e:
            raise RuntimeError(f"Sudachi tokenization failed: {e}") from e

    def xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_3(self, text: str, keep_pos: frozenset[str]) -> list[str]:
        """Return normalized_form() for tokens whose part_of_speech()[0] is in keep_pos."""
        self._ensure_loaded()
        try:
            return [
                m.normalized_form()
                for m in self._tkn.tokenize(self._mode)  # type: ignore[attr-defined]  # self._tkn is object; sudachipy loaded lazily
                if m.part_of_speech()[0] in keep_pos and m.normalized_form().strip()
            ]
        except RuntimeError as e:
            raise RuntimeError(f"Sudachi tokenization failed: {e}") from e

    def xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_4(self, text: str, keep_pos: frozenset[str]) -> list[str]:
        """Return normalized_form() for tokens whose part_of_speech()[0] is in keep_pos."""
        self._ensure_loaded()
        try:
            return [
                m.normalized_form()
                for m in self._tkn.tokenize(text, )  # type: ignore[attr-defined]  # self._tkn is object; sudachipy loaded lazily
                if m.part_of_speech()[0] in keep_pos and m.normalized_form().strip()
            ]
        except RuntimeError as e:
            raise RuntimeError(f"Sudachi tokenization failed: {e}") from e

    def xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_5(self, text: str, keep_pos: frozenset[str]) -> list[str]:
        """Return normalized_form() for tokens whose part_of_speech()[0] is in keep_pos."""
        self._ensure_loaded()
        try:
            return [
                m.normalized_form()
                for m in self._tkn.tokenize(text, self._mode)  # type: ignore[attr-defined]  # self._tkn is object; sudachipy loaded lazily
                if m.part_of_speech()[0] in keep_pos or m.normalized_form().strip()
            ]
        except RuntimeError as e:
            raise RuntimeError(f"Sudachi tokenization failed: {e}") from e

    def xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_6(self, text: str, keep_pos: frozenset[str]) -> list[str]:
        """Return normalized_form() for tokens whose part_of_speech()[0] is in keep_pos."""
        self._ensure_loaded()
        try:
            return [
                m.normalized_form()
                for m in self._tkn.tokenize(text, self._mode)  # type: ignore[attr-defined]  # self._tkn is object; sudachipy loaded lazily
                if m.part_of_speech()[1] in keep_pos and m.normalized_form().strip()
            ]
        except RuntimeError as e:
            raise RuntimeError(f"Sudachi tokenization failed: {e}") from e

    def xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_7(self, text: str, keep_pos: frozenset[str]) -> list[str]:
        """Return normalized_form() for tokens whose part_of_speech()[0] is in keep_pos."""
        self._ensure_loaded()
        try:
            return [
                m.normalized_form()
                for m in self._tkn.tokenize(text, self._mode)  # type: ignore[attr-defined]  # self._tkn is object; sudachipy loaded lazily
                if m.part_of_speech()[0] not in keep_pos and m.normalized_form().strip()
            ]
        except RuntimeError as e:
            raise RuntimeError(f"Sudachi tokenization failed: {e}") from e

    def xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_8(self, text: str, keep_pos: frozenset[str]) -> list[str]:
        """Return normalized_form() for tokens whose part_of_speech()[0] is in keep_pos."""
        self._ensure_loaded()
        try:
            return [
                m.normalized_form()
                for m in self._tkn.tokenize(text, self._mode)  # type: ignore[attr-defined]  # self._tkn is object; sudachipy loaded lazily
                if m.part_of_speech()[0] in keep_pos and m.normalized_form().strip()
            ]
        except RuntimeError as e:
            raise RuntimeError(None) from e

mutants_xǁ_SudachiTokenizerǁ__init____mutmut['_mutmut_orig'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁ__init____mutmut['xǁ_SudachiTokenizerǁ__init____mutmut_1'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁ__init____mutmut['xǁ_SudachiTokenizerǁ__init____mutmut_2'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁ__init____mutmut_2 # type: ignore # mutmut generated

mutants_xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut['_mutmut_orig'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut['xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_1'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut['xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_2'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_2 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut['xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_3'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_3 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut['xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_4'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_4 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut['xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_5'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_5 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut['xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_6'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_6 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut['xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_7'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁ_ensure_loaded__mutmut_7 # type: ignore # mutmut generated

mutants_xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut['_mutmut_orig'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut['xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_1'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut['xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_2'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_2 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut['xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_3'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_3 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut['xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_4'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_4 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut['xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_5'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_5 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut['xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_6'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_6 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut['xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_7'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_7 # type: ignore # mutmut generated
mutants_xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut['xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_8'] = _SudachiTokenizer.xǁ_SudachiTokenizerǁtokenize_pos_filter__mutmut_8 # type: ignore # mutmut generated


_sudachi = _SudachiTokenizer()
mutants_x__build_fts_tokens_ja__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__build_fts_tokens_ja__mutmut)
def _build_fts_tokens_ja(text: str) -> list[str]:
    """Extract normalized_form() of nouns/verbs/adjectives from Japanese text.

    Tokens match against FTS5 index content built from ChunkSplitter's
    normalized_content (same Sudachi normalized_form space-separated tokens).
    Raises ImportError if Sudachi is not installed.
    Raises RuntimeError on tokenization failure.
    """
    return _sudachi.tokenize_pos_filter(text, _FTS_KEEP_POS)


def x__build_fts_tokens_ja__mutmut_orig(text: str) -> list[str]:
    """Extract normalized_form() of nouns/verbs/adjectives from Japanese text.

    Tokens match against FTS5 index content built from ChunkSplitter's
    normalized_content (same Sudachi normalized_form space-separated tokens).
    Raises ImportError if Sudachi is not installed.
    Raises RuntimeError on tokenization failure.
    """
    return _sudachi.tokenize_pos_filter(text, _FTS_KEEP_POS)


def x__build_fts_tokens_ja__mutmut_1(text: str) -> list[str]:
    """Extract normalized_form() of nouns/verbs/adjectives from Japanese text.

    Tokens match against FTS5 index content built from ChunkSplitter's
    normalized_content (same Sudachi normalized_form space-separated tokens).
    Raises ImportError if Sudachi is not installed.
    Raises RuntimeError on tokenization failure.
    """
    return _sudachi.tokenize_pos_filter(None, _FTS_KEEP_POS)


def x__build_fts_tokens_ja__mutmut_2(text: str) -> list[str]:
    """Extract normalized_form() of nouns/verbs/adjectives from Japanese text.

    Tokens match against FTS5 index content built from ChunkSplitter's
    normalized_content (same Sudachi normalized_form space-separated tokens).
    Raises ImportError if Sudachi is not installed.
    Raises RuntimeError on tokenization failure.
    """
    return _sudachi.tokenize_pos_filter(text, None)


def x__build_fts_tokens_ja__mutmut_3(text: str) -> list[str]:
    """Extract normalized_form() of nouns/verbs/adjectives from Japanese text.

    Tokens match against FTS5 index content built from ChunkSplitter's
    normalized_content (same Sudachi normalized_form space-separated tokens).
    Raises ImportError if Sudachi is not installed.
    Raises RuntimeError on tokenization failure.
    """
    return _sudachi.tokenize_pos_filter(_FTS_KEEP_POS)


def x__build_fts_tokens_ja__mutmut_4(text: str) -> list[str]:
    """Extract normalized_form() of nouns/verbs/adjectives from Japanese text.

    Tokens match against FTS5 index content built from ChunkSplitter's
    normalized_content (same Sudachi normalized_form space-separated tokens).
    Raises ImportError if Sudachi is not installed.
    Raises RuntimeError on tokenization failure.
    """
    return _sudachi.tokenize_pos_filter(text, )

mutants_x__build_fts_tokens_ja__mutmut['_mutmut_orig'] = x__build_fts_tokens_ja__mutmut_orig # type: ignore # mutmut generated
mutants_x__build_fts_tokens_ja__mutmut['x__build_fts_tokens_ja__mutmut_1'] = x__build_fts_tokens_ja__mutmut_1 # type: ignore # mutmut generated
mutants_x__build_fts_tokens_ja__mutmut['x__build_fts_tokens_ja__mutmut_2'] = x__build_fts_tokens_ja__mutmut_2 # type: ignore # mutmut generated
mutants_x__build_fts_tokens_ja__mutmut['x__build_fts_tokens_ja__mutmut_3'] = x__build_fts_tokens_ja__mutmut_3 # type: ignore # mutmut generated
mutants_x__build_fts_tokens_ja__mutmut['x__build_fts_tokens_ja__mutmut_4'] = x__build_fts_tokens_ja__mutmut_4 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__build_fts_query__mutmut)
def _build_fts_query(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_orig(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_1(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = None
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_2(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(None)
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_3(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(None, text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_4(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", None))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_5(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_6(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", ))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_7(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"XX[぀-ヿ一-鿿]XX", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_8(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = None
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_9(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(None)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_10(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = None
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_11(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(None, text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_12(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", None)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_13(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_14(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", )
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_15(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"XX[a-zA-Z0-9]+XX", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_16(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-za-z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_17(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[A-ZA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_18(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_19(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return "XXXX"

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_20(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = None
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_21(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = None
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_22(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace(None, "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_23(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', None).strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_24(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace("").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_25(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', ).strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_26(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('XX"XX', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_27(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "XXXX").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_28(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = None
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_29(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = None

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_30(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count >= _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_31(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            None,
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_32(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            None,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_33(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            None,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_34(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_35(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_36(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_37(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "XXFTS query construction: original=%d, used=%d, truncated=TrueXX",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_38(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "fts query construction: original=%d, used=%d, truncated=true",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_39(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS QUERY CONSTRUCTION: ORIGINAL=%D, USED=%D, TRUNCATED=TRUE",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_40(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            None,
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_41(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            None,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_42(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            None,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_43(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_44(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_45(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_46(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "XXFTS query construction: original=%d, used=%d, truncated=FalseXX",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_47(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "fts query construction: original=%d, used=%d, truncated=false",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_48(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS QUERY CONSTRUCTION: ORIGINAL=%D, USED=%D, TRUNCATED=FALSE",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_49(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if sanitized:
        return ""
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_50(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return "XXXX"
    return " ".join(f'"{t}"' for t in sanitized)


def x__build_fts_query__mutmut_51(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return " ".join(None)


def x__build_fts_query__mutmut_52(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return ""

    original_token_count = len(tokens)
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    used_token_count = len(sanitized)
    truncated = original_token_count > _MAX_FTS_TOKENS

    if truncated:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=True",
            original_token_count,
            used_token_count,
        )
    else:
        logger.info(
            "FTS query construction: original=%d, used=%d, truncated=False",
            original_token_count,
            used_token_count,
        )

    if not sanitized:
        return ""
    return "XX XX".join(f'"{t}"' for t in sanitized)

mutants_x__build_fts_query__mutmut['_mutmut_orig'] = x__build_fts_query__mutmut_orig # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_1'] = x__build_fts_query__mutmut_1 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_2'] = x__build_fts_query__mutmut_2 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_3'] = x__build_fts_query__mutmut_3 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_4'] = x__build_fts_query__mutmut_4 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_5'] = x__build_fts_query__mutmut_5 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_6'] = x__build_fts_query__mutmut_6 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_7'] = x__build_fts_query__mutmut_7 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_8'] = x__build_fts_query__mutmut_8 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_9'] = x__build_fts_query__mutmut_9 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_10'] = x__build_fts_query__mutmut_10 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_11'] = x__build_fts_query__mutmut_11 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_12'] = x__build_fts_query__mutmut_12 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_13'] = x__build_fts_query__mutmut_13 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_14'] = x__build_fts_query__mutmut_14 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_15'] = x__build_fts_query__mutmut_15 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_16'] = x__build_fts_query__mutmut_16 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_17'] = x__build_fts_query__mutmut_17 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_18'] = x__build_fts_query__mutmut_18 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_19'] = x__build_fts_query__mutmut_19 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_20'] = x__build_fts_query__mutmut_20 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_21'] = x__build_fts_query__mutmut_21 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_22'] = x__build_fts_query__mutmut_22 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_23'] = x__build_fts_query__mutmut_23 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_24'] = x__build_fts_query__mutmut_24 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_25'] = x__build_fts_query__mutmut_25 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_26'] = x__build_fts_query__mutmut_26 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_27'] = x__build_fts_query__mutmut_27 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_28'] = x__build_fts_query__mutmut_28 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_29'] = x__build_fts_query__mutmut_29 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_30'] = x__build_fts_query__mutmut_30 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_31'] = x__build_fts_query__mutmut_31 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_32'] = x__build_fts_query__mutmut_32 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_33'] = x__build_fts_query__mutmut_33 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_34'] = x__build_fts_query__mutmut_34 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_35'] = x__build_fts_query__mutmut_35 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_36'] = x__build_fts_query__mutmut_36 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_37'] = x__build_fts_query__mutmut_37 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_38'] = x__build_fts_query__mutmut_38 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_39'] = x__build_fts_query__mutmut_39 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_40'] = x__build_fts_query__mutmut_40 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_41'] = x__build_fts_query__mutmut_41 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_42'] = x__build_fts_query__mutmut_42 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_43'] = x__build_fts_query__mutmut_43 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_44'] = x__build_fts_query__mutmut_44 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_45'] = x__build_fts_query__mutmut_45 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_46'] = x__build_fts_query__mutmut_46 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_47'] = x__build_fts_query__mutmut_47 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_48'] = x__build_fts_query__mutmut_48 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_49'] = x__build_fts_query__mutmut_49 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_50'] = x__build_fts_query__mutmut_50 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_51'] = x__build_fts_query__mutmut_51 # type: ignore # mutmut generated
mutants_x__build_fts_query__mutmut['x__build_fts_query__mutmut_52'] = x__build_fts_query__mutmut_52 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagRepositoryǁ_validate_top_k__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagRepositoryǁ_execute_with_timing__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagRepositoryǁvector_search__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagRepositoryǁfts_search__mutmut: MutantDict = {}  # type: ignore


class RagRepository:
    """BM25 + vector (KNN) retrieval over SQLite FTS5 and sqlite-vec; scorer normalizes BM25 scores to [0,1].

    Logs query / fts_query / top_k / elapsed_ms on every call for observability.
    """

    _SQL_VEC = """
        SELECT c.chunk_id, c.content, d.url, d.title, cv.distance
        FROM   chunks_vec cv
        JOIN   chunks     c  ON c.chunk_id = cv.chunk_id
        JOIN   documents  d  ON d.doc_id   = c.doc_id
        WHERE  cv.embedding MATCH ?
        ORDER  BY cv.distance
        LIMIT  ?
    """

    _SQL_FTS = """
        SELECT c.chunk_id, c.content, d.url, d.title, bm25(chunks_fts) AS bm25_score
        FROM   chunks_fts
        JOIN   chunks     c  ON c.chunk_id = chunks_fts.rowid
        JOIN   documents  d  ON d.doc_id   = c.doc_id
        WHERE  chunks_fts MATCH ?
        ORDER  BY bm25(chunks_fts)
        LIMIT  ?
    """

    @_mutmut_mutated(mutants_xǁRagRepositoryǁ__init____mutmut)
    def __init__(self, db: SQLiteHelper) -> None:
        """Initialize with a database helper instance."""
        self._db = db

    def xǁRagRepositoryǁ__init____mutmut_orig(self, db: SQLiteHelper) -> None:
        """Initialize with a database helper instance."""
        self._db = db

    def xǁRagRepositoryǁ__init____mutmut_1(self, db: SQLiteHelper) -> None:
        """Initialize with a database helper instance."""
        self._db = None

    @_mutmut_mutated(mutants_xǁRagRepositoryǁ_validate_top_k__mutmut)
    def _validate_top_k(self, top_k: Any) -> None:
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise ValueError(
                f"Invalid top_k: {top_k}. Must be an integer greater than zero."
            )

    def xǁRagRepositoryǁ_validate_top_k__mutmut_orig(self, top_k: Any) -> None:
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise ValueError(
                f"Invalid top_k: {top_k}. Must be an integer greater than zero."
            )

    def xǁRagRepositoryǁ_validate_top_k__mutmut_1(self, top_k: Any) -> None:
        if not isinstance(top_k, int) or isinstance(top_k, bool) and top_k <= 0:
            raise ValueError(
                f"Invalid top_k: {top_k}. Must be an integer greater than zero."
            )

    def xǁRagRepositoryǁ_validate_top_k__mutmut_2(self, top_k: Any) -> None:
        if not isinstance(top_k, int) and isinstance(top_k, bool) or top_k <= 0:
            raise ValueError(
                f"Invalid top_k: {top_k}. Must be an integer greater than zero."
            )

    def xǁRagRepositoryǁ_validate_top_k__mutmut_3(self, top_k: Any) -> None:
        if isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise ValueError(
                f"Invalid top_k: {top_k}. Must be an integer greater than zero."
            )

    def xǁRagRepositoryǁ_validate_top_k__mutmut_4(self, top_k: Any) -> None:
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 0:
            raise ValueError(
                f"Invalid top_k: {top_k}. Must be an integer greater than zero."
            )

    def xǁRagRepositoryǁ_validate_top_k__mutmut_5(self, top_k: Any) -> None:
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 1:
            raise ValueError(
                f"Invalid top_k: {top_k}. Must be an integer greater than zero."
            )

    def xǁRagRepositoryǁ_validate_top_k__mutmut_6(self, top_k: Any) -> None:
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise ValueError(
                None
            )

    @staticmethod
    @_mutmut_mutated(mutants_xǁRagRepositoryǁ_execute_with_timing__mutmut)
    def _execute_with_timing(
        sql: str, params: tuple[object, ...], db: SQLiteHelper
    ) -> tuple[list[dict[str, Any]], float]:
        """Execute a SQL query and return (rows, elapsed_ms)."""
        t0 = time.perf_counter()
        rows = db.fetchall(sql, params)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return rows, elapsed_ms

    @staticmethod
    def xǁRagRepositoryǁ_execute_with_timing__mutmut_orig(
        sql: str, params: tuple[object, ...], db: SQLiteHelper
    ) -> tuple[list[dict[str, Any]], float]:
        """Execute a SQL query and return (rows, elapsed_ms)."""
        t0 = time.perf_counter()
        rows = db.fetchall(sql, params)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return rows, elapsed_ms

    @staticmethod
    def xǁRagRepositoryǁ_execute_with_timing__mutmut_1(
        sql: str, params: tuple[object, ...], db: SQLiteHelper
    ) -> tuple[list[dict[str, Any]], float]:
        """Execute a SQL query and return (rows, elapsed_ms)."""
        t0 = None
        rows = db.fetchall(sql, params)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return rows, elapsed_ms

    @staticmethod
    def xǁRagRepositoryǁ_execute_with_timing__mutmut_2(
        sql: str, params: tuple[object, ...], db: SQLiteHelper
    ) -> tuple[list[dict[str, Any]], float]:
        """Execute a SQL query and return (rows, elapsed_ms)."""
        t0 = time.perf_counter()
        rows = None
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return rows, elapsed_ms

    @staticmethod
    def xǁRagRepositoryǁ_execute_with_timing__mutmut_3(
        sql: str, params: tuple[object, ...], db: SQLiteHelper
    ) -> tuple[list[dict[str, Any]], float]:
        """Execute a SQL query and return (rows, elapsed_ms)."""
        t0 = time.perf_counter()
        rows = db.fetchall(None, params)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return rows, elapsed_ms

    @staticmethod
    def xǁRagRepositoryǁ_execute_with_timing__mutmut_4(
        sql: str, params: tuple[object, ...], db: SQLiteHelper
    ) -> tuple[list[dict[str, Any]], float]:
        """Execute a SQL query and return (rows, elapsed_ms)."""
        t0 = time.perf_counter()
        rows = db.fetchall(sql, None)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return rows, elapsed_ms

    @staticmethod
    def xǁRagRepositoryǁ_execute_with_timing__mutmut_5(
        sql: str, params: tuple[object, ...], db: SQLiteHelper
    ) -> tuple[list[dict[str, Any]], float]:
        """Execute a SQL query and return (rows, elapsed_ms)."""
        t0 = time.perf_counter()
        rows = db.fetchall(params)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return rows, elapsed_ms

    @staticmethod
    def xǁRagRepositoryǁ_execute_with_timing__mutmut_6(
        sql: str, params: tuple[object, ...], db: SQLiteHelper
    ) -> tuple[list[dict[str, Any]], float]:
        """Execute a SQL query and return (rows, elapsed_ms)."""
        t0 = time.perf_counter()
        rows = db.fetchall(sql, )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return rows, elapsed_ms

    @staticmethod
    def xǁRagRepositoryǁ_execute_with_timing__mutmut_7(
        sql: str, params: tuple[object, ...], db: SQLiteHelper
    ) -> tuple[list[dict[str, Any]], float]:
        """Execute a SQL query and return (rows, elapsed_ms)."""
        t0 = time.perf_counter()
        rows = db.fetchall(sql, params)
        elapsed_ms = None
        return rows, elapsed_ms

    @staticmethod
    def xǁRagRepositoryǁ_execute_with_timing__mutmut_8(
        sql: str, params: tuple[object, ...], db: SQLiteHelper
    ) -> tuple[list[dict[str, Any]], float]:
        """Execute a SQL query and return (rows, elapsed_ms)."""
        t0 = time.perf_counter()
        rows = db.fetchall(sql, params)
        elapsed_ms = (time.perf_counter() - t0) / 1000
        return rows, elapsed_ms

    @staticmethod
    def xǁRagRepositoryǁ_execute_with_timing__mutmut_9(
        sql: str, params: tuple[object, ...], db: SQLiteHelper
    ) -> tuple[list[dict[str, Any]], float]:
        """Execute a SQL query and return (rows, elapsed_ms)."""
        t0 = time.perf_counter()
        rows = db.fetchall(sql, params)
        elapsed_ms = (time.perf_counter() + t0) * 1000
        return rows, elapsed_ms

    @staticmethod
    def xǁRagRepositoryǁ_execute_with_timing__mutmut_10(
        sql: str, params: tuple[object, ...], db: SQLiteHelper
    ) -> tuple[list[dict[str, Any]], float]:
        """Execute a SQL query and return (rows, elapsed_ms)."""
        t0 = time.perf_counter()
        rows = db.fetchall(sql, params)
        elapsed_ms = (time.perf_counter() - t0) * 1001
        return rows, elapsed_ms

    @_mutmut_mutated(mutants_xǁRagRepositoryǁvector_search__mutmut)
    def vector_search(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_orig(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_1(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(None)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_2(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = None
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_3(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            None, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_4(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, None, self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_5(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), None
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_6(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_7(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_8(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_9(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(None), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_10(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = None
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_11(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=None,
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_12(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=None,
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_13(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=None,
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_14(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=None,
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_15(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=None,
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_16(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_17(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_18(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_19(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_20(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_21(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(None),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_22(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["XXchunk_idXX"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_23(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["CHUNK_ID"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_24(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(None),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_25(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["XXcontentXX"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_26(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["CONTENT"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_27(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(None) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_28(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["XXurlXX"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_29(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["URL"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_30(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["XXurlXX"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_31(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["URL"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_32(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "XXXX",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_33(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(None) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_34(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["XXtitleXX"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_35(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["TITLE"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_36(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["XXtitleXX"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_37(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["TITLE"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_38(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "XXXX",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_39(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(None),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_40(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] and 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_41(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["XXdistanceXX"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_42(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["DISTANCE"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_43(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 1.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_44(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            None,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_45(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            None,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_46(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            None,
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_47(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            None,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_48(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_49(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_50(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_51(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "vector_search: top_k=%s hits=%s elapsed_ms=%.1f",
            top_k,
            len(results),
            )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_52(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "XXvector_search: top_k=%s hits=%s elapsed_ms=%.1fXX",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁvector_search__mutmut_53(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_VEC, (floats_to_blob(embedding), top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=int(r["chunk_id"]),
                content=str(r["content"]),
                url=str(r["url"]) if r["url"] else "",
                title=str(r["title"]) if r["title"] else "",
                distance=float(r["distance"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "VECTOR_SEARCH: TOP_K=%S HITS=%S ELAPSED_MS=%.1F",
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    @_mutmut_mutated(mutants_xǁRagRepositoryǁfts_search__mutmut)
    def fts_search(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_orig(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_1(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = None
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_2(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(None)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_3(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_4(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info(None)
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_5(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("XXfts_search: empty query, returning earlyXX")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_6(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("FTS_SEARCH: EMPTY QUERY, RETURNING EARLY")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_7(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(None)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_8(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = None
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_9(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            None, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_10(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, None, self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_11(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), None
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_12(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_13(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_14(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_15(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = None
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_16(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=None,
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_17(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=None,
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_18(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=None,
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_19(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=None,
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_20(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=None,
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_21(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_22(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_23(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_24(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_25(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_26(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["XXchunk_idXX"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_27(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["CHUNK_ID"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_28(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["XXcontentXX"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_29(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["CONTENT"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_30(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] and "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_31(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["XXurlXX"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_32(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["URL"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_33(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "XXXX",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_34(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] and "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_35(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["XXtitleXX"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_36(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["TITLE"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_37(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "XXXX",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_38(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(None),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_39(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] and 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_40(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["XXbm25_scoreXX"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_41(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["BM25_SCORE"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_42(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 1.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_43(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            None,
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_44(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            None,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_45(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            None,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_46(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            None,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_47(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            None,
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_48(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            None,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_49(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_50(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_51(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_52(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_53(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_54(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "fts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1f",
            query,
            fts_query,
            top_k,
            len(results),
            )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_55(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "XXfts_search: query=%r fts_query=%r top_k=%s hits=%s elapsed_ms=%.1fXX",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

    def xǁRagRepositoryǁfts_search__mutmut_56(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        if not fts_query:
            logger.info("fts_search: empty query, returning early")
            return []
        self._validate_top_k(top_k)
        rows, elapsed_ms = self._execute_with_timing(
            self._SQL_FTS, (fts_query, top_k), self._db
        )
        results: list[RagHit] = [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
                bm25_score=float(r["bm25_score"] or 0.0),
            )
            for r in rows
        ]
        logger.info(
            "FTS_SEARCH: QUERY=%R FTS_QUERY=%R TOP_K=%S HITS=%S ELAPSED_MS=%.1F",
            query,
            fts_query,
            top_k,
            len(results),
            elapsed_ms,
        )
        return results

mutants_xǁRagRepositoryǁ__init____mutmut['_mutmut_orig'] = RagRepository.xǁRagRepositoryǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ__init____mutmut['xǁRagRepositoryǁ__init____mutmut_1'] = RagRepository.xǁRagRepositoryǁ__init____mutmut_1 # type: ignore # mutmut generated

mutants_xǁRagRepositoryǁ_validate_top_k__mutmut['_mutmut_orig'] = RagRepository.xǁRagRepositoryǁ_validate_top_k__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_validate_top_k__mutmut['xǁRagRepositoryǁ_validate_top_k__mutmut_1'] = RagRepository.xǁRagRepositoryǁ_validate_top_k__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_validate_top_k__mutmut['xǁRagRepositoryǁ_validate_top_k__mutmut_2'] = RagRepository.xǁRagRepositoryǁ_validate_top_k__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_validate_top_k__mutmut['xǁRagRepositoryǁ_validate_top_k__mutmut_3'] = RagRepository.xǁRagRepositoryǁ_validate_top_k__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_validate_top_k__mutmut['xǁRagRepositoryǁ_validate_top_k__mutmut_4'] = RagRepository.xǁRagRepositoryǁ_validate_top_k__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_validate_top_k__mutmut['xǁRagRepositoryǁ_validate_top_k__mutmut_5'] = RagRepository.xǁRagRepositoryǁ_validate_top_k__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_validate_top_k__mutmut['xǁRagRepositoryǁ_validate_top_k__mutmut_6'] = RagRepository.xǁRagRepositoryǁ_validate_top_k__mutmut_6 # type: ignore # mutmut generated

mutants_xǁRagRepositoryǁ_execute_with_timing__mutmut['_mutmut_orig'] = RagRepository.xǁRagRepositoryǁ_execute_with_timing__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_execute_with_timing__mutmut['xǁRagRepositoryǁ_execute_with_timing__mutmut_1'] = RagRepository.xǁRagRepositoryǁ_execute_with_timing__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_execute_with_timing__mutmut['xǁRagRepositoryǁ_execute_with_timing__mutmut_2'] = RagRepository.xǁRagRepositoryǁ_execute_with_timing__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_execute_with_timing__mutmut['xǁRagRepositoryǁ_execute_with_timing__mutmut_3'] = RagRepository.xǁRagRepositoryǁ_execute_with_timing__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_execute_with_timing__mutmut['xǁRagRepositoryǁ_execute_with_timing__mutmut_4'] = RagRepository.xǁRagRepositoryǁ_execute_with_timing__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_execute_with_timing__mutmut['xǁRagRepositoryǁ_execute_with_timing__mutmut_5'] = RagRepository.xǁRagRepositoryǁ_execute_with_timing__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_execute_with_timing__mutmut['xǁRagRepositoryǁ_execute_with_timing__mutmut_6'] = RagRepository.xǁRagRepositoryǁ_execute_with_timing__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_execute_with_timing__mutmut['xǁRagRepositoryǁ_execute_with_timing__mutmut_7'] = RagRepository.xǁRagRepositoryǁ_execute_with_timing__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_execute_with_timing__mutmut['xǁRagRepositoryǁ_execute_with_timing__mutmut_8'] = RagRepository.xǁRagRepositoryǁ_execute_with_timing__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_execute_with_timing__mutmut['xǁRagRepositoryǁ_execute_with_timing__mutmut_9'] = RagRepository.xǁRagRepositoryǁ_execute_with_timing__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁ_execute_with_timing__mutmut['xǁRagRepositoryǁ_execute_with_timing__mutmut_10'] = RagRepository.xǁRagRepositoryǁ_execute_with_timing__mutmut_10 # type: ignore # mutmut generated

mutants_xǁRagRepositoryǁvector_search__mutmut['_mutmut_orig'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_1'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_2'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_3'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_4'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_5'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_6'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_7'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_8'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_9'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_10'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_11'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_12'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_13'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_14'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_15'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_16'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_17'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_18'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_19'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_20'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_20 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_21'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_21 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_22'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_22 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_23'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_23 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_24'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_24 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_25'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_25 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_26'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_26 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_27'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_27 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_28'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_28 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_29'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_29 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_30'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_30 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_31'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_31 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_32'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_32 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_33'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_33 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_34'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_34 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_35'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_35 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_36'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_36 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_37'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_37 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_38'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_38 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_39'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_39 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_40'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_40 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_41'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_41 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_42'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_42 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_43'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_43 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_44'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_44 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_45'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_45 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_46'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_46 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_47'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_47 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_48'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_48 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_49'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_49 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_50'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_50 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_51'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_51 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_52'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_52 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁvector_search__mutmut['xǁRagRepositoryǁvector_search__mutmut_53'] = RagRepository.xǁRagRepositoryǁvector_search__mutmut_53 # type: ignore # mutmut generated

mutants_xǁRagRepositoryǁfts_search__mutmut['_mutmut_orig'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_1'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_2'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_3'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_4'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_5'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_6'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_7'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_8'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_9'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_10'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_11'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_12'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_13'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_14'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_15'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_16'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_17'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_18'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_19'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_20'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_20 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_21'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_21 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_22'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_22 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_23'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_23 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_24'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_24 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_25'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_25 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_26'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_26 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_27'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_27 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_28'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_28 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_29'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_29 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_30'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_30 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_31'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_31 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_32'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_32 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_33'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_33 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_34'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_34 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_35'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_35 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_36'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_36 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_37'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_37 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_38'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_38 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_39'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_39 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_40'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_40 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_41'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_41 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_42'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_42 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_43'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_43 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_44'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_44 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_45'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_45 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_46'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_46 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_47'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_47 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_48'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_48 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_49'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_49 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_50'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_50 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_51'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_51 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_52'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_52 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_53'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_53 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_54'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_54 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_55'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_55 # type: ignore # mutmut generated
mutants_xǁRagRepositoryǁfts_search__mutmut['xǁRagRepositoryǁfts_search__mutmut_56'] = RagRepository.xǁRagRepositoryǁfts_search__mutmut_56 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut: MutantDict = {}  # type: ignore


class RagScorer:
    """Reciprocal Rank Fusion for merging multiple search result lists."""

    @staticmethod
    @_mutmut_mutated(mutants_xǁRagScorerǁrrf_merge__mutmut)
    def rrf_merge(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_orig(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_1(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 61
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_2(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = None
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_3(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = None
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_4(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(None, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_5(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=None):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_6(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_7(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, ):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_8(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=2):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_9(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = None
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_10(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = None
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_11(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) - 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_12(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(None, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_13(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, None) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_14(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_15(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, ) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_16(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 1.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_17(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 * (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_18(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 2.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_19(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k - rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_20(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = None
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_21(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = None
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_22(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(None, key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_23(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=None, reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_24(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=None)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_25(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_26(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_27(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], )
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_28(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: None, reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_29(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[2], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_30(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=False)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_31(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=None,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_32(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=None,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_33(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=None,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_34(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=None,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_35(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=None,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_36(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=None,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_37(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=None,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_38(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_39(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_40(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_41(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_42(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                bm25_score=meta[cid].bm25_score,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_43(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                rrf_score=score,
            )
            for cid, score in merged_list
        ]

    @staticmethod
    def xǁRagScorerǁrrf_merge__mutmut_44(
        results_list: list[list[RawHit]] | list[list[RagHit]], rrf_k: int = 60
    ) -> list[RagHit]:
        """Merge ranked lists via RRF: score(d)=Σ 1/(rrf_k+rank_i(d)); returns descending by score."""
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item.chunk_id
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            MergedHit(
                chunk_id=meta[cid].chunk_id,
                content=meta[cid].content,
                url=meta[cid].url,
                title=meta[cid].title,
                distance=meta[cid].distance,
                bm25_score=meta[cid].bm25_score,
                )
            for cid, score in merged_list
        ]

mutants_xǁRagScorerǁrrf_merge__mutmut['_mutmut_orig'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_1'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_2'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_3'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_4'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_5'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_6'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_7'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_8'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_9'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_10'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_11'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_12'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_13'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_14'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_15'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_16'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_17'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_18'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_19'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_20'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_20 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_21'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_21 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_22'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_22 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_23'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_23 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_24'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_24 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_25'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_25 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_26'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_26 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_27'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_27 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_28'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_28 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_29'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_29 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_30'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_30 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_31'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_31 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_32'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_32 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_33'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_33 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_34'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_34 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_35'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_35 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_36'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_36 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_37'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_37 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_38'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_38 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_39'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_39 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_40'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_40 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_41'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_41 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_42'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_42 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_43'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_43 # type: ignore # mutmut generated
mutants_xǁRagScorerǁrrf_merge__mutmut['xǁRagScorerǁrrf_merge__mutmut_44'] = RagScorer.xǁRagScorerǁrrf_merge__mutmut_44 # type: ignore # mutmut generated
mutants_x_vector_search__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_vector_search__mutmut)
def vector_search(embedding: list[float], top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """KNN vector search. Delegates to RagRepository."""
    return RagRepository(db).vector_search(embedding, top_k)


def x_vector_search__mutmut_orig(embedding: list[float], top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """KNN vector search. Delegates to RagRepository."""
    return RagRepository(db).vector_search(embedding, top_k)


def x_vector_search__mutmut_1(embedding: list[float], top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """KNN vector search. Delegates to RagRepository."""
    return RagRepository(db).vector_search(None, top_k)


def x_vector_search__mutmut_2(embedding: list[float], top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """KNN vector search. Delegates to RagRepository."""
    return RagRepository(db).vector_search(embedding, None)


def x_vector_search__mutmut_3(embedding: list[float], top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """KNN vector search. Delegates to RagRepository."""
    return RagRepository(db).vector_search(top_k)


def x_vector_search__mutmut_4(embedding: list[float], top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """KNN vector search. Delegates to RagRepository."""
    return RagRepository(db).vector_search(embedding, )


def x_vector_search__mutmut_5(embedding: list[float], top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """KNN vector search. Delegates to RagRepository."""
    return RagRepository(None).vector_search(embedding, top_k)

mutants_x_vector_search__mutmut['_mutmut_orig'] = x_vector_search__mutmut_orig # type: ignore # mutmut generated
mutants_x_vector_search__mutmut['x_vector_search__mutmut_1'] = x_vector_search__mutmut_1 # type: ignore # mutmut generated
mutants_x_vector_search__mutmut['x_vector_search__mutmut_2'] = x_vector_search__mutmut_2 # type: ignore # mutmut generated
mutants_x_vector_search__mutmut['x_vector_search__mutmut_3'] = x_vector_search__mutmut_3 # type: ignore # mutmut generated
mutants_x_vector_search__mutmut['x_vector_search__mutmut_4'] = x_vector_search__mutmut_4 # type: ignore # mutmut generated
mutants_x_vector_search__mutmut['x_vector_search__mutmut_5'] = x_vector_search__mutmut_5 # type: ignore # mutmut generated
mutants_x_fts_search__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_fts_search__mutmut)
def fts_search(query: str, top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """FTS5 BM25 search. Delegates to RagRepository."""
    return RagRepository(db).fts_search(query, top_k)


def x_fts_search__mutmut_orig(query: str, top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """FTS5 BM25 search. Delegates to RagRepository."""
    return RagRepository(db).fts_search(query, top_k)


def x_fts_search__mutmut_1(query: str, top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """FTS5 BM25 search. Delegates to RagRepository."""
    return RagRepository(db).fts_search(None, top_k)


def x_fts_search__mutmut_2(query: str, top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """FTS5 BM25 search. Delegates to RagRepository."""
    return RagRepository(db).fts_search(query, None)


def x_fts_search__mutmut_3(query: str, top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """FTS5 BM25 search. Delegates to RagRepository."""
    return RagRepository(db).fts_search(top_k)


def x_fts_search__mutmut_4(query: str, top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """FTS5 BM25 search. Delegates to RagRepository."""
    return RagRepository(db).fts_search(query, )


def x_fts_search__mutmut_5(query: str, top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """FTS5 BM25 search. Delegates to RagRepository."""
    return RagRepository(None).fts_search(query, top_k)

mutants_x_fts_search__mutmut['_mutmut_orig'] = x_fts_search__mutmut_orig # type: ignore # mutmut generated
mutants_x_fts_search__mutmut['x_fts_search__mutmut_1'] = x_fts_search__mutmut_1 # type: ignore # mutmut generated
mutants_x_fts_search__mutmut['x_fts_search__mutmut_2'] = x_fts_search__mutmut_2 # type: ignore # mutmut generated
mutants_x_fts_search__mutmut['x_fts_search__mutmut_3'] = x_fts_search__mutmut_3 # type: ignore # mutmut generated
mutants_x_fts_search__mutmut['x_fts_search__mutmut_4'] = x_fts_search__mutmut_4 # type: ignore # mutmut generated
mutants_x_fts_search__mutmut['x_fts_search__mutmut_5'] = x_fts_search__mutmut_5 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_fetch_full_document__mutmut)
def fetch_full_document(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_orig(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_1(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = None
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_2(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        None,
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_3(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        None,
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_4(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_5(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_6(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "XXSELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?XX",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_7(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "select c.doc_id, c.chunk_index from chunks c where c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_8(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT C.DOC_ID, C.CHUNK_INDEX FROM CHUNKS C WHERE C.CHUNK_ID = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_9(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_10(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = None
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_11(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[1], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_12(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[2]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_13(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is not None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_14(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = None
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_15(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            None,
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_16(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            None,
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_17(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_18(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_19(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "XXSELECT c.chunk_id, c.content, d.url, d.titleXX"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_20(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "select c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_21(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT C.CHUNK_ID, C.CONTENT, D.URL, D.TITLE"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_22(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            "XX FROM chunks c JOIN documents d ON d.doc_id = c.doc_idXX"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_23(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " from chunks c join documents d on d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_24(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM CHUNKS C JOIN DOCUMENTS D ON D.DOC_ID = C.DOC_ID"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_25(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            "XX WHERE c.doc_id = ? ORDER BY c.chunk_indexXX",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_26(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " where c.doc_id = ? order by c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_27(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE C.DOC_ID = ? ORDER BY C.CHUNK_INDEX",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_28(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = None
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_29(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            None,
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_30(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            None,
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_31(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_32(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_33(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "XXSELECT c.chunk_id, c.content, d.url, d.titleXX"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_34(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "select c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_35(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT C.CHUNK_ID, C.CONTENT, D.URL, D.TITLE"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_36(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            "XX FROM chunks c JOIN documents d ON d.doc_id = c.doc_idXX"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_37(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " from chunks c join documents d on d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_38(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM CHUNKS C JOIN DOCUMENTS D ON D.DOC_ID = C.DOC_ID"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_39(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            "XX WHERE c.doc_id = ?XX"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_40(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " where c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_41(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE C.DOC_ID = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_42(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            "XX AND c.chunk_index BETWEEN ? AND ?XX"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_43(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " and c.chunk_index between ? and ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_44(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND C.CHUNK_INDEX BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_45(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            "XX ORDER BY c.chunk_indexXX",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_46(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " order by c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_47(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY C.CHUNK_INDEX",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_48(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(None, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_49(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, None), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_50(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_51(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, ), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_52(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(1, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_53(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index + window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_54(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index - window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_55(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=None,
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_56(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=None,
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_57(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=None,
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_58(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=None,
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_59(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_60(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_61(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_62(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            )
        for r in rows
    ]


def x_fetch_full_document__mutmut_63(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["XXchunk_idXX"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_64(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["CHUNK_ID"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_65(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["XXcontentXX"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_66(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["CONTENT"],
            url=r["url"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_67(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] and "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_68(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["XXurlXX"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_69(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["URL"] or "",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_70(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "XXXX",
            title=r["title"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_71(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] and "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_72(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["XXtitleXX"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_73(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["TITLE"] or "",
        )
        for r in rows
    ]


def x_fetch_full_document__mutmut_74(
    chunk_id: int,
    db: SQLiteHelper,
    window: int | None = None,
) -> list[RawHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
    Returns empty list when chunk_id is not found (valid not-found result).
    """
    row = db.execute(
        "SELECT c.doc_id, c.chunk_index FROM chunks c WHERE c.chunk_id = ?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return []
    doc_id, chunk_index = row[0], row[1]
    if window is None:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ? ORDER BY c.chunk_index",
            (doc_id,),
        )
    else:
        rows = db.fetchall(
            "SELECT c.chunk_id, c.content, d.url, d.title"
            " FROM chunks c JOIN documents d ON d.doc_id = c.doc_id"
            " WHERE c.doc_id = ?"
            " AND c.chunk_index BETWEEN ? AND ?"
            " ORDER BY c.chunk_index",
            (doc_id, max(0, chunk_index - window), chunk_index + window),
        )
    return [
        RawHit(
            chunk_id=r["chunk_id"],
            content=r["content"],
            url=r["url"] or "",
            title=r["title"] or "XXXX",
        )
        for r in rows
    ]

mutants_x_fetch_full_document__mutmut['_mutmut_orig'] = x_fetch_full_document__mutmut_orig # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_1'] = x_fetch_full_document__mutmut_1 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_2'] = x_fetch_full_document__mutmut_2 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_3'] = x_fetch_full_document__mutmut_3 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_4'] = x_fetch_full_document__mutmut_4 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_5'] = x_fetch_full_document__mutmut_5 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_6'] = x_fetch_full_document__mutmut_6 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_7'] = x_fetch_full_document__mutmut_7 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_8'] = x_fetch_full_document__mutmut_8 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_9'] = x_fetch_full_document__mutmut_9 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_10'] = x_fetch_full_document__mutmut_10 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_11'] = x_fetch_full_document__mutmut_11 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_12'] = x_fetch_full_document__mutmut_12 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_13'] = x_fetch_full_document__mutmut_13 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_14'] = x_fetch_full_document__mutmut_14 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_15'] = x_fetch_full_document__mutmut_15 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_16'] = x_fetch_full_document__mutmut_16 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_17'] = x_fetch_full_document__mutmut_17 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_18'] = x_fetch_full_document__mutmut_18 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_19'] = x_fetch_full_document__mutmut_19 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_20'] = x_fetch_full_document__mutmut_20 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_21'] = x_fetch_full_document__mutmut_21 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_22'] = x_fetch_full_document__mutmut_22 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_23'] = x_fetch_full_document__mutmut_23 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_24'] = x_fetch_full_document__mutmut_24 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_25'] = x_fetch_full_document__mutmut_25 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_26'] = x_fetch_full_document__mutmut_26 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_27'] = x_fetch_full_document__mutmut_27 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_28'] = x_fetch_full_document__mutmut_28 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_29'] = x_fetch_full_document__mutmut_29 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_30'] = x_fetch_full_document__mutmut_30 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_31'] = x_fetch_full_document__mutmut_31 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_32'] = x_fetch_full_document__mutmut_32 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_33'] = x_fetch_full_document__mutmut_33 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_34'] = x_fetch_full_document__mutmut_34 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_35'] = x_fetch_full_document__mutmut_35 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_36'] = x_fetch_full_document__mutmut_36 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_37'] = x_fetch_full_document__mutmut_37 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_38'] = x_fetch_full_document__mutmut_38 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_39'] = x_fetch_full_document__mutmut_39 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_40'] = x_fetch_full_document__mutmut_40 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_41'] = x_fetch_full_document__mutmut_41 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_42'] = x_fetch_full_document__mutmut_42 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_43'] = x_fetch_full_document__mutmut_43 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_44'] = x_fetch_full_document__mutmut_44 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_45'] = x_fetch_full_document__mutmut_45 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_46'] = x_fetch_full_document__mutmut_46 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_47'] = x_fetch_full_document__mutmut_47 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_48'] = x_fetch_full_document__mutmut_48 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_49'] = x_fetch_full_document__mutmut_49 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_50'] = x_fetch_full_document__mutmut_50 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_51'] = x_fetch_full_document__mutmut_51 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_52'] = x_fetch_full_document__mutmut_52 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_53'] = x_fetch_full_document__mutmut_53 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_54'] = x_fetch_full_document__mutmut_54 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_55'] = x_fetch_full_document__mutmut_55 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_56'] = x_fetch_full_document__mutmut_56 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_57'] = x_fetch_full_document__mutmut_57 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_58'] = x_fetch_full_document__mutmut_58 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_59'] = x_fetch_full_document__mutmut_59 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_60'] = x_fetch_full_document__mutmut_60 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_61'] = x_fetch_full_document__mutmut_61 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_62'] = x_fetch_full_document__mutmut_62 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_63'] = x_fetch_full_document__mutmut_63 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_64'] = x_fetch_full_document__mutmut_64 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_65'] = x_fetch_full_document__mutmut_65 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_66'] = x_fetch_full_document__mutmut_66 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_67'] = x_fetch_full_document__mutmut_67 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_68'] = x_fetch_full_document__mutmut_68 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_69'] = x_fetch_full_document__mutmut_69 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_70'] = x_fetch_full_document__mutmut_70 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_71'] = x_fetch_full_document__mutmut_71 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_72'] = x_fetch_full_document__mutmut_72 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_73'] = x_fetch_full_document__mutmut_73 # type: ignore # mutmut generated
mutants_x_fetch_full_document__mutmut['x_fetch_full_document__mutmut_74'] = x_fetch_full_document__mutmut_74 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_deduplicate_chunks__mutmut)
def deduplicate_chunks(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_orig(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_1(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = None
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_2(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = None
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_3(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = None
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_4(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = None
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_5(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(None, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_6(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, None)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_7(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_8(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, )
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_9(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 1)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_10(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n <= max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_11(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(None)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_12(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = None
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_13(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n - 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_14(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 2
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_15(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        None,
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_16(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        None,
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_17(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        None,
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_18(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        None,
    )
    return result


def x_deduplicate_chunks__mutmut_19(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_20(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_21(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_22(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "deduplicate_chunks: %s → %s (max_per_doc=%s)",
        len(hits),
        len(result),
        )
    return result


def x_deduplicate_chunks__mutmut_23(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "XXdeduplicate_chunks: %s → %s (max_per_doc=%s)XX",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result


def x_deduplicate_chunks__mutmut_24(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.url
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        "DEDUPLICATE_CHUNKS: %S → %S (MAX_PER_DOC=%S)",
        len(hits),
        len(result),
        max_per_doc,
    )
    return result

mutants_x_deduplicate_chunks__mutmut['_mutmut_orig'] = x_deduplicate_chunks__mutmut_orig # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_1'] = x_deduplicate_chunks__mutmut_1 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_2'] = x_deduplicate_chunks__mutmut_2 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_3'] = x_deduplicate_chunks__mutmut_3 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_4'] = x_deduplicate_chunks__mutmut_4 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_5'] = x_deduplicate_chunks__mutmut_5 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_6'] = x_deduplicate_chunks__mutmut_6 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_7'] = x_deduplicate_chunks__mutmut_7 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_8'] = x_deduplicate_chunks__mutmut_8 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_9'] = x_deduplicate_chunks__mutmut_9 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_10'] = x_deduplicate_chunks__mutmut_10 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_11'] = x_deduplicate_chunks__mutmut_11 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_12'] = x_deduplicate_chunks__mutmut_12 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_13'] = x_deduplicate_chunks__mutmut_13 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_14'] = x_deduplicate_chunks__mutmut_14 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_15'] = x_deduplicate_chunks__mutmut_15 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_16'] = x_deduplicate_chunks__mutmut_16 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_17'] = x_deduplicate_chunks__mutmut_17 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_18'] = x_deduplicate_chunks__mutmut_18 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_19'] = x_deduplicate_chunks__mutmut_19 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_20'] = x_deduplicate_chunks__mutmut_20 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_21'] = x_deduplicate_chunks__mutmut_21 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_22'] = x_deduplicate_chunks__mutmut_22 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_23'] = x_deduplicate_chunks__mutmut_23 # type: ignore # mutmut generated
mutants_x_deduplicate_chunks__mutmut['x_deduplicate_chunks__mutmut_24'] = x_deduplicate_chunks__mutmut_24 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__dedup_hits__mutmut)
def _dedup_hits(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_orig(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_1(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = None
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_2(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = None
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_3(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_4(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(None)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_5(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    None
                )
    return merged


def x__dedup_hits__mutmut_6(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=None,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_7(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=None,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_8(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=None,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_9(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=None,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_10(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=None,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_11(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=None,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_12(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=None,
                    )
                )
    return merged


def x__dedup_hits__mutmut_13(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_14(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_15(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_16(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_17(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        bm25_score=item.bm25_score,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_18(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        rrf_score=0.0,
                    )
                )
    return merged


def x__dedup_hits__mutmut_19(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        )
                )
    return merged


def x__dedup_hits__mutmut_20(all_results: list[list[RawHit]] | list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                merged.append(
                    MergedHit(
                        chunk_id=item.chunk_id,
                        content=item.content,
                        url=item.url,
                        title=item.title,
                        distance=item.distance,
                        bm25_score=item.bm25_score,
                        rrf_score=1.0,
                    )
                )
    return merged

mutants_x__dedup_hits__mutmut['_mutmut_orig'] = x__dedup_hits__mutmut_orig # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_1'] = x__dedup_hits__mutmut_1 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_2'] = x__dedup_hits__mutmut_2 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_3'] = x__dedup_hits__mutmut_3 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_4'] = x__dedup_hits__mutmut_4 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_5'] = x__dedup_hits__mutmut_5 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_6'] = x__dedup_hits__mutmut_6 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_7'] = x__dedup_hits__mutmut_7 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_8'] = x__dedup_hits__mutmut_8 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_9'] = x__dedup_hits__mutmut_9 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_10'] = x__dedup_hits__mutmut_10 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_11'] = x__dedup_hits__mutmut_11 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_12'] = x__dedup_hits__mutmut_12 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_13'] = x__dedup_hits__mutmut_13 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_14'] = x__dedup_hits__mutmut_14 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_15'] = x__dedup_hits__mutmut_15 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_16'] = x__dedup_hits__mutmut_16 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_17'] = x__dedup_hits__mutmut_17 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_18'] = x__dedup_hits__mutmut_18 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_19'] = x__dedup_hits__mutmut_19 # type: ignore # mutmut generated
mutants_x__dedup_hits__mutmut['x__dedup_hits__mutmut_20'] = x__dedup_hits__mutmut_20 # type: ignore # mutmut generated
