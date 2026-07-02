#!/usr/bin/env python3
"""agent/memory/retriever.py
FTS5-based memory search with importance / pin / recency scoring.
Phase 2: optional KNN search via memories_vec + RRF merge.

Classes:
  FtsRetriever     — FTS5 BM25 search + rescoring
  VectorRetriever  — KNN search on memories_vec; knn_search() is the public API
  HybridRetriever  — composes both; primary external interface

See scoring.py for scoring formula details.
"""

from __future__ import annotations

import logging

from db.helper import SQLiteHelper

from agent.memory.embedding_client import EmbeddingClient
from agent.memory.enums import MemoryType
from agent.memory.exceptions import MemorySchemaError
from agent.memory.mapper import _floats_to_blob, row_to_entry
from agent.memory.scoring import context_boost, recency_boost, score
from agent.memory.types import MemoryEntry, MemoryHit, MemoryQuery

logger = logging.getLogger(__name__)

# Maximum number of raw FTS5 candidates before rescoring
_FTS_CANDIDATE_LIMIT = 50

# RRF constant
_RRF_K = 60


def _build_fts_query(text: str) -> str:
    """Build FTS5 MATCH query with token quoting to escape reserved terms.

    All tokens are double-quoted to escape AND/OR/NOT/NEAR as literals.
    No column filter: memories_fts searches content, summary, and tags.
    """
    import re  # noqa: PLC0415 — lazy import, only needed for regex

    tokens = re.findall(r"\w+", text)
    if not tokens:
        return '""'
    return " OR ".join(f'"{t}"' for t in tokens)


def _rrf_merge(
    hit_lists: list[list[MemoryHit]],
    k: int = _RRF_K,
) -> list[MemoryHit]:
    """Reciprocal Rank Fusion: merge multiple ranked hit lists by rank position.

    Each list contributes 1/(k + rank) to the memory_id's final RRF score.
    Sets hit.score to the RRF score before returning.
    Returns a deduplicated list sorted by descending RRF score.
    """
    rrf_scores: dict[str, float] = {}
    by_id: dict[str, MemoryHit] = {}
    for lst in hit_lists:
        for rank, hit in enumerate(lst):
            mid = hit.entry.memory_id
            rrf_scores[mid] = rrf_scores.get(mid, 0.0) + 1.0 / (k + rank + 1)
            by_id[mid] = hit
    for mid, hit in by_id.items():
        hit.score = rrf_scores[mid]
    return sorted(by_id.values(), key=lambda h: h.score, reverse=True)


class FtsRetriever:
    """FTS5 BM25 search with importance / pin / recency rescoring."""

    def __init__(
        self,
        *,
        fts_limit: int = _FTS_CANDIDATE_LIMIT,
        recency_days: float = 7.0,
    ) -> None:
        self._fts_limit = fts_limit
        self._recency_days = recency_days

    def search(
        self,
        query: MemoryQuery,
        project: str = "",
        repo: str = "",
        branch: str = "",
    ) -> list[MemoryHit]:
        """FTS5 BM25 search; returns [] on error or empty query."""
        fts_query = _build_fts_query(query.query)
        if not fts_query or fts_query == '""':
            return []

        sql, params = self._build_search_query(fts_query, query.memory_type, branch)
        hits = self._fetch_hits(sql, tuple(params), project, repo, branch)
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[: query.limit]

    def _build_search_query(
        self, fts_query: str, memory_type: str | None, branch: str = ""
    ) -> tuple[str, list[object]]:
        """Build FTS5 search SQL and parameter tuple."""
        type_filter = ""
        params: list[object] = [fts_query, self._fts_limit]
        if memory_type:
            type_filter = "AND m.memory_type = ?"
            params.insert(1, memory_type)

        branch_filter = ""
        if branch:
            branch_filter = "AND (? = '' OR m.branch = '' OR m.branch = ?)"
            # Insert branch params before the trailing LIMIT param.
            # params layout after type_filter: [fts_query, (type?), ..., fts_limit]
            # We insert two branch params at position len(params)-1 to keep LIMIT last.
            params.insert(len(params) - 1, branch)
            params.insert(len(params) - 1, branch)

        sql = f"""
            SELECT m.memory_id, m.memory_type, m.source_type, m.session_id, m.turn_id,
                   m.project, m.repo, m.branch, m.content, m.summary, m.tags,
                   m.importance, m.pinned, m.created_at, m.updated_at,
                   f.rank AS bm25_rank
            FROM memories_fts f
            JOIN memories m ON m.memory_id = f.memory_id
            WHERE memories_fts MATCH ?
            {type_filter}
            {branch_filter}
            ORDER BY f.rank
            LIMIT ?
        """  # nosec B608 — type_filter and branch_filter are literal strings; all values use ? placeholders
        return sql, params

    def _fetch_hits(
        self,
        sql: str,
        params: tuple[object, ...],
        project: str,
        repo: str,
        branch: str = "",
    ) -> list[MemoryHit]:
        """Execute query and build scored MemoryHit list."""
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(sql, params)

        hits: list[MemoryHit] = []
        for row in rows:
            d = dict(row)
            bm25_rank = float(d.pop("bm25_rank", 0.0))
            entry = row_to_entry(d)
            s = score(bm25_rank, entry, project, repo, self._recency_days, branch)
            hits.append(MemoryHit(entry=entry, score=s))
        return hits


class VectorRetriever:
    """KNN search on memories_vec using sqlite-vec extension."""

    def knn_search(
        self,
        embedding: list[float],
        memory_type: str | None,
        limit: int,
        branch: str = "",
    ) -> list[MemoryHit]:
        """KNN search on memories_vec; raises OperationalError when table missing."""
        type_filter = ""
        params: list[object] = [_floats_to_blob(embedding), limit]
        if memory_type:
            type_filter = "AND m.memory_type = ?"
            params.insert(1, memory_type)

        branch_filter = ""
        if branch:
            branch_filter = "AND (? = '' OR m.branch = '' OR m.branch = ?)"
            params.insert(len(params) - 1, branch)
            params.insert(len(params) - 1, branch)

        sql = f"""
            SELECT m.memory_id, m.memory_type, m.source_type, m.session_id, m.turn_id,
                   m.project, m.repo, m.branch, m.content, m.summary, m.tags,
                   m.importance, m.pinned, m.created_at, m.updated_at,
                   mv.distance
            FROM memories_vec mv
            JOIN memories m ON m.memory_id = mv.memory_id
            WHERE mv.embedding MATCH ?
            {type_filter}
            {branch_filter}
            ORDER BY mv.distance
            LIMIT ?
        """  # nosec B608 — type_filter and branch_filter are literal strings; all values use ? placeholders

        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(sql, tuple(params))

        hits: list[MemoryHit] = []
        for row in rows:
            d = dict(row)
            distance = float(d.pop("distance", 999.0))
            entry = row_to_entry(d)
            # Negate distance: MemoryHit.score convention is higher-is-better
            hits.append(MemoryHit(entry=entry, score=-distance))
        return hits


class HybridRetriever:
    """FTS5 + optional KNN hybrid search with RRF merge.

    Primary external interface. Composes FtsRetriever and VectorRetriever.
    """

    def __init__(
        self,
        *,
        fts_limit: int = _FTS_CANDIDATE_LIMIT,
        rrf_k: int = _RRF_K,
        recency_days: float = 7.0,
        embed_client: EmbeddingClient | None = None,
    ) -> None:
        self._fts = FtsRetriever(fts_limit=fts_limit, recency_days=recency_days)
        self._vec = VectorRetriever()
        self._rrf_k = rrf_k
        self._recency_days = recency_days
        self.embed_client: EmbeddingClient | None = embed_client
        self.last_retrieval_mode: str = "unknown"
        self.fts_fallback_count: int = 0

    def search(
        self,
        query: MemoryQuery,
        embedding: list[float] | None = None,
        project: str = "",
        repo: str = "",
        branch: str = "",
    ) -> list[MemoryHit]:
        """Run FTS5 search (and optionally KNN) and return ranked MemoryHit list.

        Falls back to FTS-only when embedding is None or vec table is unavailable.
        When embedding is supplied, merges FTS5 and KNN results via RRF.
        """
        fts_hits = self._fts.search(query, project, repo, branch)
        if embedding is None:
            logger.info("retrieval: fts_only (reason=embedding_disabled_or_none)")
            self.last_retrieval_mode = "fts_only"
            self.fts_fallback_count += 1
            return fts_hits

        vec_hits = self._vec.knn_search(
            embedding, query.memory_type, self._fts._fts_limit, branch
        )
        if not vec_hits:
            logger.info("retrieval: fts_only (reason=vec_returned_empty)")
            self.last_retrieval_mode = "fts_only"
            self.fts_fallback_count += 1
            return fts_hits

        self.last_retrieval_mode = "hybrid"
        merged = _rrf_merge([fts_hits, vec_hits], k=self._rrf_k)
        # hit.score is set to the RRF score by _rrf_merge; already sorted by _rrf_merge.
        return merged[: query.limit]

    def knn_search(
        self,
        embedding: list[float],
        memory_type: str | None,
        limit: int,
        branch: str = "",
    ) -> list[MemoryHit]:
        """Delegate KNN search to VectorRetriever (used by ingestion dedup)."""
        return self._vec.knn_search(embedding, memory_type, limit, branch)

    def top_semantic(
        self,
        limit: int = 5,
        min_importance: float = 0.0,
        project: str = "",
        repo: str = "",
        branch: str = "",
    ) -> list[MemoryEntry]:
        """Return top semantic entries by importance + pin, no FTS needed."""
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                """SELECT memory_id, memory_type, source_type, session_id, turn_id,
                          project, repo, branch, content, summary, tags,
                          importance, pinned, created_at, updated_at
                   FROM memories
                   WHERE memory_type = 'semantic' AND importance >= ?
                   AND (? = '' OR branch = '' OR branch = ?)
                   ORDER BY pinned DESC, importance DESC, created_at DESC
                   LIMIT ?""",
                (min_importance, branch, branch, limit),
            )
            return [row_to_entry(dict(r)) for r in rows]
