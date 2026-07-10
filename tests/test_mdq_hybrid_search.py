#!/usr/bin/env python3
"""Tests for MDQ hybrid search (embedding mode)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from mcp_servers.mdq.search import _RRF_K, _merge_hybrid
from mcp_servers.mdq.service import MdqService


class TestHybridSearchConfig:
    """Verify hybrid search config fields are loaded correctly."""

    def test_use_embedding_disabled_by_default(self, tmp_path: Path) -> None:
        svc = MdqService(db_path=str(tmp_path / "mdq.sqlite"))
        assert svc.use_embedding is False

    def test_vector_table_default_value(self, tmp_path: Path) -> None:
        svc = MdqService(db_path=str(tmp_path / "mdq.sqlite"))
        assert svc.vector_table == "chunks_vec"

    def test_embedding_model_default_value(self, tmp_path: Path) -> None:
        svc = MdqService(db_path=str(tmp_path / "mdq.sqlite"))
        assert svc.embedding_model == "default"


class TestHybridSearchVectorTable:
    """Verify vector table is created only when use_embedding=True."""

    def test_vector_table_not_created_when_disabled(self, tmp_path: Path) -> None:
        svc = MdqService(db_path=str(tmp_path / "mdq.sqlite"))
        conn = svc._get_db_connection()
        try:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {row[0] for row in tables}
            assert "chunks_vec" not in table_names, (
                "chunks_vec should not be created when use_embedding=False"
            )
        finally:
            conn.close()

    def test_vector_table_created_when_enabled(self, tmp_path: Path) -> None:
        svc = MdqService(db_path=str(tmp_path / "mdq.sqlite"))
        svc.use_embedding = True
        # Re-initialize DB to trigger vector table creation
        try:
            svc._init_db()
        except sqlite3.OperationalError as e:
            msg = str(e)
            if "no such module: vec0" in msg or "No such file or directory" in msg:
                pytest.skip("vec0 module not available in this environment")
            raise
        conn = svc._get_db_connection()
        try:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {row[0] for row in tables}
            assert "chunks_vec" in table_names, (
                "chunks_vec should be created when use_embedding=True"
            )
        finally:
            conn.close()


class TestHybridSearchMerge:
    """Verify RRF merge of FTS5 and vector results."""

    def test_empty_results(self) -> None:

        fts = []
        vec = []
        result = _merge_hybrid(fts, vec)
        assert result == []

    def test_only_fts_results(self) -> None:
        from mcp_servers.mdq.models import SearchResultItem

        fts = [
            SearchResultItem(
                chunk_id="a",
                source_path="/a.md",
                heading="A",
                heading_path="",
                score=0.5,
                start_line=1,
                end_line=10,
                token_count=None,
                snippet="content A",
            ),
            SearchResultItem(
                chunk_id="b",
                source_path="/b.md",
                heading="B",
                heading_path="",
                score=0.3,
                start_line=1,
                end_line=10,
                token_count=None,
                snippet="content B",
            ),
        ]
        vec = []
        result = _merge_hybrid(fts, vec)
        assert len(result) == 2
        # FTS results should keep their original order (rank-based)
        assert result[0].chunk_id == "a"

    def test_rrf_merge_scores(self) -> None:
        from mcp_servers.mdq.models import SearchResultItem

        fts = [
            SearchResultItem(
                chunk_id="x",
                source_path="/x.md",
                heading="X",
                heading_path="",
                score=0.9,
                start_line=1,
                end_line=10,
                token_count=None,
                snippet="content X",
            ),
        ]
        vec = [
            SearchResultItem(
                chunk_id="x",
                source_path="/x.md",
                heading="X",
                heading_path="",
                score=0.8,
                start_line=1,
                end_line=10,
                token_count=None,
                snippet="content X",
            ),
            SearchResultItem(
                chunk_id="y",
                source_path="/y.md",
                heading="Y",
                heading_path="",
                score=0.7,
                start_line=1,
                end_line=10,
                token_count=None,
                snippet="content Y",
            ),
        ]
        result = _merge_hybrid(fts, vec)
        assert len(result) == 2

        # x should have highest RRF score (appears in both lists)
        # x rank: 1 in fts + 1 in vec
        x_score = 1.0 / (_RRF_K + 1) + 1.0 / (_RRF_K + 1)
        # y rank: 2 in vec only
        y_score = 1.0 / (_RRF_K + 2)

        assert result[0].score > result[1].score  # x should be ranked first
        assert abs(result[0].score - x_score) < 0.0001
        assert abs(result[1].score - y_score) < 0.0001

    def test_rrf_cross_list_ranking(self) -> None:
        from mcp_servers.mdq.models import SearchResultItem

        # FTS has a at rank 1, vec has b at rank 1, a at rank 2
        # a should be ranked higher because it appears in both lists
        fts = [
            SearchResultItem(
                chunk_id="a",
                source_path="/a.md",
                heading="A",
                heading_path="",
                score=0.9,
                start_line=1,
                end_line=10,
                token_count=None,
                snippet="content A",
            ),
        ]
        vec = [
            SearchResultItem(
                chunk_id="b",
                source_path="/b.md",
                heading="B",
                heading_path="",
                score=0.8,
                start_line=1,
                end_line=10,
                token_count=None,
                snippet="content B",
            ),
            SearchResultItem(
                chunk_id="a",
                source_path="/a.md",
                heading="A",
                heading_path="",
                score=0.7,
                start_line=1,
                end_line=10,
                token_count=None,
                snippet="content A",
            ),
        ]
        result = _merge_hybrid(fts, vec)
        assert len(result) == 2

        # a rank: 1 in fts + 2 in vec
        a_score = 1.0 / (_RRF_K + 1) + 1.0 / (_RRF_K + 3)
        # b rank: 1 in vec only
        b_score = 1.0 / (_RRF_K + 2)

        assert result[0].score > result[1].score  # a should be ranked first
        assert abs(result[0].score - a_score) < 0.0005
        assert abs(result[1].score - b_score) < 0.0005
