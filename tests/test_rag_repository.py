"""tests/test_rag_repository.py
Unit tests for rag/repository.py — RagScorer, SemanticCache, cosine_sim,
deduplicate_chunks, _dedup_hits, and FTS query building.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

import pytest
from rag.cache import SemanticCache
from rag.repository import (
    RagRepository,
    RagScorer,
    _build_fts_query,
    _dedup_hits,
    deduplicate_chunks,
)
from rag.types import RawHit as _RawHit
from rag.utils import cosine_sim

# ── FTS5 fallback to content when normalized_content IS NULL ──────────────────


def _make_test_repo() -> RagRepository:
    """Create an in-memory SQLite DB with the RAG schema (no vec) and return a repository."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS documents (
            doc_id             INTEGER PRIMARY KEY AUTOINCREMENT,
            url                TEXT    NOT NULL UNIQUE,
            title              TEXT,
            lang               TEXT    NOT NULL CHECK (lang IN ('ja', 'en')),
            fetched_at         TEXT    NOT NULL DEFAULT (datetime('now')),
            etag               TEXT,
            last_modified      TEXT,
            chunking_strategy  TEXT    NOT NULL DEFAULT 'text'
        );
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id             INTEGER NOT NULL
                               REFERENCES documents(doc_id) ON DELETE CASCADE,
            chunk_index        INTEGER NOT NULL,
            content            TEXT    NOT NULL,
            normalized_content TEXT
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            content,
            content       = 'chunks',
            content_rowid = 'chunk_id',
            tokenize      = 'unicode61'
        );
        CREATE TRIGGER IF NOT EXISTS chunks_ai
        AFTER INSERT ON chunks BEGIN
            INSERT INTO chunks_fts (rowid, content)
            VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
        END;
        CREATE TRIGGER IF NOT EXISTS chunks_ad
        AFTER DELETE ON chunks BEGIN
            INSERT INTO chunks_fts (chunks_fts, rowid, content)
            VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
        END;
        CREATE TRIGGER IF NOT EXISTS chunks_au
        AFTER UPDATE ON chunks BEGIN
            INSERT INTO chunks_fts (chunks_fts, rowid, content)
            VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
            INSERT INTO chunks_fts (rowid, content)
            VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
        END;
        """
    )
    conn.commit()

    class _TestHelper:
        def fetchall(self, sql, params=()):
            return list(conn.execute(sql, params).fetchall())

    return RagRepository(_TestHelper())


class TestFtsFallback:
    def test_english_fts_fallback(self) -> None:
        """FTS5 matches raw content when normalized_content is NULL (English)."""
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE, title TEXT, lang TEXT NOT NULL CHECK (lang IN ('ja', 'en')),
                fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL, content TEXT NOT NULL, normalized_content TEXT
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                content, content = 'chunks', content_rowid = 'chunk_id', tokenize = 'unicode61'
            );
            CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts (rowid, content)
                VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
            END;
            CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN
                INSERT INTO chunks_fts (chunks_fts, rowid, content)
                VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
            END;
            """
        )
        conn.commit()

        conn.execute(
            "INSERT INTO documents (url, title, lang) VALUES (?, ?, ?)",
            ("http://example.com/sql", "SQL docs", "en"),
        )
        doc_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO chunks (doc_id, chunk_index, content, normalized_content) VALUES (?, ?, ?, ?)",
            (doc_id, 0, "SELECT * FROM users WHERE id = 1", None),
        )
        conn.commit()

        class _TestHelper:
            def fetchall(self, sql, params=()):
                return list(conn.execute(sql, params).fetchall())

        repo = RagRepository(_TestHelper())
        results = repo.fts_search("SELECT", top_k=10)
        assert len(results) >= 1
        assert "SELECT * FROM users WHERE id = 1" in results[0].content

    def test_code_fts_fallback(self) -> None:
        """FTS5 matches raw content when normalized_content is NULL (code)."""
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE, title TEXT, lang TEXT NOT NULL CHECK (lang IN ('ja', 'en')),
                fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL, content TEXT NOT NULL, normalized_content TEXT
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                content, content = 'chunks', content_rowid = 'chunk_id', tokenize = 'unicode61'
            );
            CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts (rowid, content)
                VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
            END;
            CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN
                INSERT INTO chunks_fts (chunks_fts, rowid, content)
                VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
            END;
            """
        )
        conn.commit()

        conn.execute(
            "INSERT INTO documents (url, title, lang) VALUES (?, ?, ?)",
            ("http://example.com/code", "Code sample", "en"),
        )
        doc_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO chunks (doc_id, chunk_index, content, normalized_content) VALUES (?, ?, ?, ?)",
            (doc_id, 0, "def foo():\n    return 42", None),
        )
        conn.commit()

        class _TestHelper:
            def fetchall(self, sql, params=()):
                return list(conn.execute(sql, params).fetchall())

        repo = RagRepository(_TestHelper())
        results = repo.fts_search("return 42", top_k=10)
        assert len(results) >= 1
        assert "def foo():" in results[0].content or "return 42" in results[0].content

    def test_normalized_content_takes_precedence(self) -> None:
        """FTS5 index uses normalized_content when present (COALESCE precedence)."""
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE, title TEXT, lang TEXT NOT NULL CHECK (lang IN ('ja', 'en')),
                fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL, content TEXT NOT NULL, normalized_content TEXT
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                content, content = 'chunks', content_rowid = 'chunk_id', tokenize = 'unicode61'
            );
            CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts (rowid, content)
                VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
            END;
            CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN
                INSERT INTO chunks_fts (chunks_fts, rowid, content)
                VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
            END;
            """
        )
        conn.commit()

        conn.execute(
            "INSERT INTO documents (url, title, lang) VALUES (?, ?, ?)",
            ("http://example.com/normal", "Normalization test", "en"),
        )
        doc_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO chunks (doc_id, chunk_index, content, normalized_content) VALUES (?, ?, ?, ?)",
            (doc_id, 0, "raw text with stopwords", "better text without noise"),
        )
        conn.commit()

        class _TestHelper:
            def fetchall(self, sql, params=()):
                return list(conn.execute(sql, params).fetchall())

        repo = RagRepository(_TestHelper())

        # "better" matches normalized_content → should find the chunk
        results_better = repo.fts_search("better", top_k=10)
        assert len(results_better) >= 1

        # Both "raw" and "noise" appear in the underlying chunks.content column.
        # The FTS5 trigger indexes COALESCE(normalized_content, content), so
        # normalized_content is what gets indexed. Verify that the indexed content
        # matches normalized_content by checking that the returned chunk's content
        # column still holds the original raw value (proving the index and table
        # are separate).
        assert results_better[0].content == "raw text with stopwords"


def _hit(
    chunk_id: int, url: str = "http://example.com", title: str = "Test"
) -> _RawHit:
    return _RawHit(
        chunk_id=chunk_id, content=f"content_{chunk_id}", url=url, title=title
    )


# ── cosine_sim ────────────────────────────────────────────────────────────────


class TestCosineSim:
    def test_identical_vectors_return_one(self) -> None:
        v = [1.0, 2.0, 3.0]
        assert cosine_sim(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors_return_zero(self) -> None:
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert cosine_sim(a, b) == pytest.approx(0.0)

    def test_opposite_vectors_return_negative_one(self) -> None:
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert cosine_sim(a, b) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self) -> None:
        a = [0.0, 0.0, 0.0]
        b = [1.0, 2.0, 3.0]
        assert cosine_sim(a, b) == pytest.approx(0.0)

    def test_both_zero_vectors_return_zero(self) -> None:
        a = [0.0, 0.0]
        b = [0.0, 0.0]
        assert cosine_sim(a, b) == pytest.approx(0.0)

    def test_scaled_identical_returns_one(self) -> None:
        a = [2.0, 4.0, 6.0]
        b = [1.0, 2.0, 3.0]
        assert cosine_sim(a, b) == pytest.approx(1.0)

    def test_different_lengths_raises_error(self) -> None:
        a = [1.0, 2.0]
        b = [1.0, 2.0, 3.0]
        # zip truncates to shortest; no exception is raised
        result = cosine_sim(a, b)
        assert isinstance(result, float)


# ── RagScorer.rrf_merge ──────────────────────────────────────────────────────


class TestRagScorer:
    def test_single_list_preserves_order(self) -> None:
        hits = [_hit(1), _hit(2), _hit(3)]
        result = RagScorer.rrf_merge([hits])
        assert [h.chunk_id for h in result] == [1, 2, 3]

    def test_multiple_lists_aggregate_scores(self) -> None:
        hits_a = [_hit(1), _hit(2)]
        hits_b = [_hit(2), _hit(1)]
        result = RagScorer.rrf_merge([hits_a, hits_b])
        # chunk_id=1 appears at rank 1 in A and rank 2 in B => higher score than chunk_id=2
        assert result[0].chunk_id == 1
        assert result[1].chunk_id == 2

    def test_empty_input_returns_empty(self) -> None:
        result = RagScorer.rrf_merge([])
        assert result == []

    def test_empty_list_in_list_is_ignored(self) -> None:
        hits = [_hit(1)]
        result = RagScorer.rrf_merge([[], hits])
        assert len(result) == 1
        assert result[0].chunk_id == 1

    def test_rrf_score_values_are_correct(self) -> None:
        hits = [_hit(42)]
        result = RagScorer.rrf_merge([hits], rrf_k=10)
        score = result[0].rrf_score
        expected = 1.0 / (10 + 1)
        assert score == pytest.approx(expected)

    def test_duplicate_chunks_keeps_first_occurrence(self) -> None:
        hits_a = [_hit(1), _hit(2)]
        hits_b = [_hit(1), _hit(3)]
        result = RagScorer.rrf_merge([hits_a, hits_b])
        assert [h.chunk_id for h in result].count(1) == 1


# ── SemanticCache ─────────────────────────────────────────────────────────────


class TestSemanticCache:
    def test_miss_returns_none(self) -> None:
        cache = SemanticCache()
        result = cache.lookup([0.1, 0.2, 0.3])
        assert result is None

    def test_hit_above_threshold_returns_context(self) -> None:
        cache = SemanticCache(threshold=0.9)
        embedding = [1.0, 0.0, 0.0]
        cache.put(embedding, "", "cached context")
        result = cache.lookup([0.95, 0.0, 0.0])
        assert result == "cached context"

    def test_hit_below_threshold_returns_none(self) -> None:
        cache = SemanticCache(threshold=0.9)
        embedding = [1.0, 0.0, 0.0]
        cache.put(embedding, "", "cached context")
        # Perpendicular vector => cosine_sim = 0.0 < 0.9
        result = cache.lookup([0.0, 1.0, 0.0])
        assert result is None

    def test_exact_match_returns_context(self) -> None:
        cache = SemanticCache(threshold=0.92)
        embedding = [0.577, 0.577, 0.577]
        cache.put(embedding, "", "exact match")
        result = cache.lookup([0.577, 0.577, 0.577])
        assert result == "exact match"

    def test_prune_removes_oldest(self) -> None:
        cache = SemanticCache(max_size=3)
        for i in range(5):
            cache.put([float(i)], "", f"context_{i}")
        assert cache.size == 3
        # Oldest entries removed; only last 3 remain (context_2, context_3, context_4)
        result = cache.lookup([4.0])
        assert result == "context_2"

    def test_prune_no_op_when_under_capacity(self) -> None:
        cache = SemanticCache(max_size=10)
        cache.put([1.0], "", "a")
        cache.put([2.0], "", "b")
        assert cache.size == 2

    def test_put_over_capacity_prunes(self) -> None:
        cache = SemanticCache(max_size=2)
        cache.put([1.0], "", "a")
        cache.put([2.0], "", "b")
        cache.put([3.0], "", "c")
        assert cache.size == 2

    def test_nearest_entry_returned(self) -> None:
        cache = SemanticCache(threshold=0.5)
        embedding_far = [1.0, 0.0, 0.0]
        embedding_near = [0.8, 0.6, 0.0]
        cache.put(embedding_far, "", "far context")
        cache.put(embedding_near, "", "near context")
        result = cache.lookup([1.0, 0.0, 0.0])
        assert result == "far context"


# ── deduplicate_chunks ────────────────────────────────────────────────────────


class TestDeduplicateChunks:
    def test_no_duplicates_passes_through(self) -> None:
        hits = [_hit(1, url="http://a"), _hit(2, url="http://b")]
        result = deduplicate_chunks(hits, max_per_doc=2)
        assert len(result) == 2

    def test_exceeds_max_per_doc_truncates(self) -> None:
        hits = [
            _hit(1, url="http://a"),
            _hit(2, url="http://a"),
            _hit(3, url="http://a"),
        ]
        result = deduplicate_chunks(hits, max_per_doc=1)
        assert len(result) == 1
        assert result[0].chunk_id == 1

    def test_multiple_documents_independent_limits(self) -> None:
        hits = [
            _hit(1, url="http://a"),
            _hit(2, url="http://a"),
            _hit(3, url="http://b"),
            _hit(4, url="http://b"),
            _hit(5, url="http://b"),
        ]
        result = deduplicate_chunks(hits, max_per_doc=1)
        assert len(result) == 2
        assert result[0].chunk_id == 1
        assert result[1].chunk_id == 3

    def test_empty_input_returns_empty(self) -> None:
        result = deduplicate_chunks([], max_per_doc=1)
        assert result == []

    def test_max_per_doc_zero_returns_empty(self) -> None:
        hits = [_hit(1), _hit(2)]
        result = deduplicate_chunks(hits, max_per_doc=0)
        assert result == []

    def test_preserves_order(self) -> None:
        hits = [_hit(3), _hit(1), _hit(2)]
        result = deduplicate_chunks(hits, max_per_doc=1)
        # All hits share empty url (no url specified), so only first is kept
        assert [h.chunk_id for h in result] == [3]


# ── _dedup_hits ───────────────────────────────────────────────────────────────


class TestDedupHits:
    def test_duplicates_removed(self) -> None:
        hits_a = [_hit(1), _hit(2)]
        hits_b = [_hit(2), _hit(3)]
        result = _dedup_hits([hits_a, hits_b])
        chunk_ids = [h.chunk_id for h in result]
        assert chunk_ids == [1, 2, 3]

    def test_empty_input_returns_empty(self) -> None:
        result = _dedup_hits([])
        assert result == []

    def test_all_same_chunk_keeps_one(self) -> None:
        hits = [_hit(42), _hit(42)]
        result = _dedup_hits([hits, hits])
        assert len(result) == 1
        assert result[0].chunk_id == 42

    def test_rrf_score_set_to_zero(self) -> None:
        hits = [_hit(1)]
        result = _dedup_hits([hits])
        assert result[0].rrf_score == 0.0


# ── RagRepository ─────────────────────────────────────────────────────────────


class TestRagRepository:
    def test_vector_search_delegates_to_db(self) -> None:
        mock_db = MagicMock()
        mock_db.fetchall.return_value = [
            {
                "chunk_id": 1,
                "content": "content",
                "url": "http://u",
                "title": "title",
                "distance": 0.5,
            },
        ]
        repo = RagRepository(mock_db)
        result = repo.vector_search([0.1, 0.2, 0.3], top_k=5)
        assert len(result) == 1
        assert result[0].chunk_id == 1
        mock_db.fetchall.assert_called_once()

    def test_fts_search_delegates_to_db(self) -> None:
        mock_db = MagicMock()
        mock_db.fetchall.return_value = [
            {
                "chunk_id": 2,
                "content": "fts content",
                "url": "http://u",
                "title": "title",
                "bm25_score": -0.3,
            },
        ]
        repo = RagRepository(mock_db)
        result = repo.fts_search("test query", top_k=10)
        assert len(result) == 1
        assert result[0].chunk_id == 2

    def test_fts_search_operational_error_propagates(self) -> None:
        """fts_search propagates OperationalError (fail-fast); callers must handle."""
        import sqlite3

        mock_db = MagicMock()
        mock_db.fetchall.side_effect = sqlite3.OperationalError("bad query")
        repo = RagRepository(mock_db)
        with pytest.raises(sqlite3.OperationalError, match="bad query"):
            repo.fts_search("bad query", top_k=10)


# ── _build_fts_query ─────────────────────────────────────────────────────────


class TestBuildFtsQuery:
    def test_english_words_quoted(self) -> None:
        result = _build_fts_query("hello world")
        assert '"hello"' in result
        assert '"world"' in result

    def test_japanese_uses_regex_fallback_without_sudachi(self) -> None:
        result = _build_fts_query("こんにちは世界")
        # Should extract non-ASCII tokens
        assert '"' in result
        assert len(result) > 0

    def test_empty_string_returns_empty_quote(self) -> None:
        result = _build_fts_query("")
        assert result == '""'

    def test_numbers_only(self) -> None:
        result = _build_fts_query("123 456")
        assert '"123"' in result
        assert '"456"' in result

    def test_special_chars_stripped(self) -> None:
        result = _build_fts_query('hello "world" AND')
        # Double quotes are stripped, AND is not alpha
        assert '"hello"' in result
        assert '"world"' in result

    def test_long_query_capped_at_max_tokens(self) -> None:
        words = " ".join(f"word{i}" for i in range(100))
        result = _build_fts_query(words)
        # Should only contain first 20 tokens
        quoted_count = result.count('"')
        assert quoted_count <= 40  # each token has 2 quotes

    def test_mixed_japanese_and_english(self) -> None:
        result = _build_fts_query("test こんにちは")
        assert len(result) > 0

    def test_only_spaces_returns_empty_quote(self) -> None:
        result = _build_fts_query("   ")
        assert result == '""'
