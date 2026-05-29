#!/usr/bin/env python3
"""
rag/repository.py
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
import math
import re
import sqlite3
import time
from typing import cast

from db.helper import SQLiteHelper
from rag.types import RagHit
from rag.utils import floats_to_blob

logger = logging.getLogger(__name__)

# Maximum number of tokens to include in an FTS5 query (prevents query explosion)
_MAX_FTS_TOKENS = 20
# Sudachi POS categories retained for Japanese FTS5 query tokens (content words only)
_FTS_KEEP_POS: frozenset[str] = frozenset({"名詞", "動詞", "形容詞"})

# Lazily-initialized Sudachi tokenizer for FTS5 query tokenization
_sd_tkn = None
_sd_split_c = None


def _get_sudachi_tokenizer() -> tuple:
    """Lazy-initialize Sudachi tokenizer for FTS5 Japanese query POS filtering."""
    global _sd_tkn, _sd_split_c
    if _sd_tkn is None:
        from sudachipy import dictionary as sudachi_dict  # noqa: PLC0415
        from sudachipy import tokenizer as sudachi_tok  # noqa: PLC0415

        _sd_dict = sudachi_dict.Dictionary(dict="core")
        _sd_tkn = _sd_dict.create()
        _sd_split_c = sudachi_tok.Tokenizer.SplitMode.C
    return _sd_tkn, _sd_split_c


def _build_fts_tokens_ja(text: str) -> list[str]:
    """Extract normalized_form() of nouns/verbs/adjectives from Japanese text.

    Tokens match against FTS5 index content built from ChunkSplitter's
    normalized_content (same Sudachi normalized_form space-separated tokens).
    Falls back to raw non-ASCII extraction on tokenizer error.
    """
    try:
        tkn, split_c = _get_sudachi_tokenizer()
        return [
            m.normalized_form()
            for m in tkn.tokenize(text, split_c)
            if m.part_of_speech()[0] in _FTS_KEEP_POS and m.normalized_form().strip()
        ]
    except Exception as e:
        logger.debug(f"Sudachi FTS tokenization failed: {e}")
        return re.findall(r"[^\x00-\x7F]+", text)


def _build_fts_query(text: str) -> str:
    """
    Convert text to an FTS5 query string.
    For Japanese queries, applies Sudachi POS filter (nouns/verbs/adjectives) and
    returns normalized_form() tokens that match against the FTS5 index which stores
    Sudachi-normalized content from ChunkSplitter.
    Each token is double-quoted to escape FTS5 reserved words (AND/OR/NOT/*).
    """
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
        """
        Retrieve chunks closest to the query embedding using KNN (K Nearest Neighbors).
        Distance is L2; smaller values indicate closer semantic similarity.
        """
        t0 = time.perf_counter()
        rows = self._db.fetchall(self._SQL_VEC, (floats_to_blob(embedding), top_k))
        elapsed_ms = (time.perf_counter() - t0) * 1000
        results: list[RagHit] = cast(list[RagHit], [dict(r) for r in rows])
        logger.info(
            f"vector_search: top_k={top_k} hits={len(results)}"
            f" elapsed_ms={elapsed_ms:.1f}"
        )
        return results

    def fts_search(self, query: str, top_k: int) -> list[RagHit]:
        """
        Retrieve keyword-matching chunks using FTS5 BM25 scoring.
        bm25() returns negative values; smaller (more negative) means higher relevance.
        Returns empty list on FTS5 query syntax error to continue the pipeline.
        """
        fts_query = _build_fts_query(query)
        t0 = time.perf_counter()
        try:
            rows = self._db.fetchall(self._SQL_FTS, (fts_query, top_k))
        except sqlite3.OperationalError as e:
            logger.warning(
                f"fts_search error query={query!r} fts_query={fts_query!r}: {e}"
            )
            return []
        elapsed_ms = (time.perf_counter() - t0) * 1000
        results: list[RagHit] = cast(list[RagHit], [dict(r) for r in rows])
        logger.info(
            f"fts_search: query={query!r} fts_query={fts_query!r}"
            f" top_k={top_k} hits={len(results)} elapsed_ms={elapsed_ms:.1f}"
        )
        return results


class RagScorer:
    """Reciprocal Rank Fusion for merging multiple search result lists."""

    @staticmethod
    def rrf_merge(results_list: list[list[RagHit]], rrf_k: int = 60) -> list[RagHit]:
        """
        Merge multiple search result lists using RRF.
        RRF score formula: score(d) = Σ_i  1 / (rrf_k + rank_i(d))
          rank_i(d) : rank of document d in list i (1-based)
          rrf_k=60  : constant that dampens impact of lower-ranked documents
        Aggregates scores across all lists by chunk_id, sorted descending.
        """
        scores: dict[int, float] = {}
        meta: dict[int, RagHit] = {}
        for results in results_list:
            for rank, item in enumerate(results, start=1):
                cid = item["chunk_id"]
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
                meta[cid] = item
        merged = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return cast(
            list[RagHit], [{**meta[cid], "rrf_score": score} for cid, score in merged]
        )


def cosine_sim(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two equal-length float vectors.

    Returns 0.0 when either vector has zero magnitude.
    """
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


class SemanticCache:
    """In-memory nearest-neighbour cache for RAG context strings.

    Stores (embedding, context_str) pairs. lookup() returns a cached context
    when the best cosine similarity exceeds threshold. Excess entries are pruned
    on put() to keep memory bounded by max_size.
    """

    def __init__(self, max_size: int = 100, threshold: float = 0.92) -> None:
        self._entries: list[dict] = []  # [{embedding, context_str}]
        self._max_size = max_size
        self._threshold = threshold

    def lookup(self, embedding: list[float]) -> str | None:
        """Return cached context for the nearest embedding, or None on miss."""
        best_sim = -1.0
        best_ctx: str | None = None
        for entry in self._entries:
            sim = cosine_sim(embedding, entry["embedding"])
            if sim > best_sim:
                best_sim = sim
                best_ctx = entry["context_str"]
        if best_sim >= self._threshold:
            logger.debug(f"SemanticCache hit: sim={best_sim:.4f}")
            return best_ctx
        return None

    def put(self, embedding: list[float], context_str: str) -> None:
        """Add a new entry, then prune if over capacity."""
        self._entries.append({"embedding": embedding, "context_str": context_str})
        self.prune()

    def prune(self) -> None:
        """Remove oldest entries when size exceeds max_size."""
        if len(self._entries) > self._max_size:
            self._entries = self._entries[-self._max_size :]

    @property
    def size(self) -> int:
        return len(self._entries)


def vector_search(embedding: list[float], top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """KNN vector search. Delegates to RagRepository."""
    return RagRepository(db).vector_search(embedding, top_k)


def fts_search(query: str, top_k: int, db: SQLiteHelper) -> list[RagHit]:
    """FTS5 BM25 search. Delegates to RagRepository."""
    return RagRepository(db).fts_search(query, top_k)


def fetch_full_document(
    chunk_id: int, db: SQLiteHelper, window: int | None = None
) -> list[RagHit]:
    """Retrieve surrounding chunks for a given chunk_id from the same document.

    window=None: return all chunks from the same document (full expansion).
    window=N: return chunks within N positions of chunk_id (±N window).
    Results are ordered by chunk_index ascending (document reading order).
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
    return cast(list[RagHit], [dict(r) for r in rows])


def deduplicate_chunks(hits: list[RagHit], max_per_doc: int) -> list[RagHit]:
    """Keep at most max_per_doc chunks per document (identified by URL).

    Prevents chunk_overlap near-duplicates from the same document dominating
    the RAG context. Input hits must already be sorted by descending relevance.
    """
    counts: dict[str, int] = {}
    result: list[RagHit] = []
    for hit in hits:
        url = hit.get("url", "")
        n = counts.get(url, 0)
        if n < max_per_doc:
            result.append(hit)
            counts[url] = n + 1
    logger.info(
        f"deduplicate_chunks: {len(hits)} → {len(result)} (max_per_doc={max_per_doc})"
    )
    return result


def _dedup_hits(all_results: list[list[RagHit]]) -> list[RagHit]:
    """Deduplicate hits by chunk_id, keeping the first occurrence per chunk."""
    seen: set[int] = set()
    merged: list[RagHit] = []
    for results in all_results:
        for item in results:
            if item["chunk_id"] not in seen:
                seen.add(item["chunk_id"])
                merged.append({**item, "rrf_score": 0.0})
    return merged
