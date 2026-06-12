#!/usr/bin/env python3
"""rag/repository.py
RAG data-access layer: FTS5/vector search, RRF merge, and document fetching.

Extracted from rag/pipeline.py.  Contains:
  - Japanese FTS5 tokenization helpers (Sudachi)
  - RagRepository  — all SQL confined here
  - RagScorer      — Reciprocal Rank Fusion (RRF)
  - SemanticCache  — in-memory nearest-neighbour cache
  - Standalone helper functions: vector_search, fts_search, fetch_full_document,
    deduplicate_chunks, cosine_sim, _dedup_hits
"""

import logging
import re
import time
from typing import cast

from db.helper import SQLiteHelper

from rag.types import MergedHit, RankedHit, RawHit
from rag.utils import floats_to_blob

RagHit = RawHit | MergedHit | RankedHit

logger = logging.getLogger(__name__)

# Maximum number of tokens to include in an FTS5 query (prevents query explosion)
_MAX_FTS_TOKENS = 20
# Sudachi POS categories retained for Japanese FTS5 query tokens (content words only)
_FTS_KEEP_POS: frozenset[str] = frozenset({"名詞", "動詞", "形容詞"})


class _SudachiTokenizer:
    """Lazy wrapper around sudachipy Tokenizer — loaded on first use."""

    def __init__(self) -> None:
        self._tkn: object = None
        self._mode: object = None

    def _ensure_loaded(self) -> None:
        if self._tkn is None:
            from sudachipy import (  # noqa: PLC0415
                dictionary as _sd_dict,
            )
            from sudachipy import (  # noqa: PLC0415
                tokenizer as _sd_tok,
            )

            d = _sd_dict.Dictionary(dict="core")
            self._tkn = d.create()
            self._mode = _sd_tok.Tokenizer.SplitMode.C

    def tokenize_pos_filter(self, text: str, keep_pos: frozenset[str]) -> list[str]:
        """Return normalized_form() for tokens whose part_of_speech()[0] is in keep_pos."""
        self._ensure_loaded()
        try:
            return [
                m.normalized_form()
                for m in self._tkn.tokenize(text, self._mode)  # type: ignore[attr-defined]
                if m.part_of_speech()[0] in keep_pos and m.normalized_form().strip()
            ]
        except RuntimeError as e:
            raise RuntimeError(f"Sudachi tokenization failed: {e}") from e


_sudachi = _SudachiTokenizer()


def _get_sudachi_tokenizer() -> _SudachiTokenizer:
    """Return the module-level lazy Sudachi tokenizer."""
    return _sudachi


def _build_fts_tokens_ja(text: str) -> list[str]:
    """Extract normalized_form() of nouns/verbs/adjectives from Japanese text.

    Tokens match against FTS5 index content built from ChunkSplitter's
    normalized_content (same Sudachi normalized_form space-separated tokens).
    Raises ImportError if Sudachi is not installed.
    Raises RuntimeError on tokenization failure.
    """
    return _get_sudachi_tokenizer().tokenize_pos_filter(text, _FTS_KEEP_POS)


def _build_fts_query(text: str) -> str:
    """Convert text to FTS5 query; Japanese uses Sudachi POS filter, tokens are quoted to escape AND/OR/NOT."""
    has_japanese = bool(re.search(r"[぀-ヿ一-鿿]", text))
    if has_japanese:
        tokens = _build_fts_tokens_ja(text)
    else:
        tokens = re.findall(r"[a-zA-Z0-9]+", text)
    if not tokens:
        return '""'
    # Strip double-quotes (FTS5 metachar) and whitespace; drop empty tokens
    sanitized = [
        s for s in (t.replace('"', "").strip() for t in tokens[:_MAX_FTS_TOKENS]) if s
    ]
    if not sanitized:
        return '""'
    return " ".join(f'"{t}"' for t in sanitized)


class RagRepository:
    """SQL-based chunk retrieval. All SQL is confined to this class.

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

    def __init__(self, db: SQLiteHelper) -> None:
        self._db = db

    def vector_search(self, embedding: list[float], top_k: int) -> list[RagHit]:
        """Retrieve top_k chunks by L2-distance KNN (smaller distance = higher similarity)."""
        t0 = time.perf_counter()
        rows = self._db.fetchall(self._SQL_VEC, (floats_to_blob(embedding), top_k))
        elapsed_ms = (time.perf_counter() - t0) * 1000
        results: list[RagHit] = cast(
            "list[RagHit]",
            [
                RawHit(
                    chunk_id=r["chunk_id"],
                    content=r["content"],
                    url=r["url"] or "",
                    title=r["title"] or "",
                    distance=float(r["distance"] or 0.0),
                )
                for r in rows
            ],
        )
        logger.info(
            f"vector_search: top_k={top_k} hits={len(results)}"
            f" elapsed_ms={elapsed_ms:.1f}",
        )
        return results

    def fts_search(self, query: str, top_k: int) -> list[RagHit]:
        """Retrieve chunks by FTS5 BM25 (negative scores; more-negative = higher relevance).

        Raises sqlite3.OperationalError on FTS syntax errors — callers must handle.
        """
        fts_query = _build_fts_query(query)
        t0 = time.perf_counter()
        rows = self._db.fetchall(self._SQL_FTS, (fts_query, top_k))
        elapsed_ms = (time.perf_counter() - t0) * 1000
        results: list[RagHit] = cast(
            "list[RagHit]",
            [
                RawHit(
                    chunk_id=r["chunk_id"],
                    content=r["content"],
                    url=r["url"] or "",
                    title=r["title"] or "",
                    bm25_score=float(r["bm25_score"] or 0.0),
                )
                for r in rows
            ],
        )
        logger.info(
            f"fts_search: query={query!r} fts_query={fts_query!r}"
            f" top_k={top_k} hits={len(results)} elapsed_ms={elapsed_ms:.1f}",
        )
        return results


class RagScorer:
    """Reciprocal Rank Fusion for merging multiple search result lists."""

    @staticmethod
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
        return cast(
            "list[RagHit]",
            [
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
            ],
        )


def vector_search(embedding: list[float], top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """KNN vector search. Delegates to RagRepository."""
    return RagRepository(db).vector_search(embedding, top_k)


def fts_search(query: str, top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """FTS5 BM25 search. Delegates to RagRepository."""
    return RagRepository(db).fts_search(query, top_k)


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
    return cast(
        "list[RawHit]",
        [
            RawHit(
                chunk_id=r["chunk_id"],
                content=r["content"],
                url=r["url"] or "",
                title=r["title"] or "",
            )
            for r in rows
        ],
    )


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
        f"deduplicate_chunks: {len(hits)} → {len(result)} (max_per_doc={max_per_doc})",
    )
    return result


def _dedup_hits(all_results: list[list[RagHit]]) -> list[RagHit]:
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
