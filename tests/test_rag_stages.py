"""Characterization tests for RAG pipeline stages.

This module contains characterization tests that document the current behavior
of each RAG stage. Tests cover:
- Normal execution paths
- Edge cases (empty inputs, missing fields)
- Error handling and fallbacks
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rag.stage import PipelineContext
from rag.stages.augment import AugmentStage
from rag.stages.fusion import FusionStage
from rag.stages.mqe import MqeStage, _run_mqe
from rag.stages.rerank import RerankStage, _rerank
from rag.stages.search import SearchStage, _search_all_queries


@pytest.fixture
def mock_context():
    """Create a mock PipelineContext."""
    context = MagicMock(spec=PipelineContext)
    context.queries = ["test query"]
    context.search_results = []
    context.history_context = ""
    context.query = "test query"
    context.merged = []
    context.reranked = []
    return context


@pytest.fixture
def mock_llm():
    """Create a mock LLM client."""
    return AsyncMock()


@pytest.fixture
def mock_db():
    """Create a mock database helper."""
    db = MagicMock()
    db.execute = MagicMock()
    db.fetchall = MagicMock(return_value=[])
    db._http = AsyncMock()
    return db


@pytest.fixture
def sample_cfg():
    """Create a sample configuration dict."""
    return {
        "use_mqe": True,
        "use_rerank": True,
        "use_search": True,
        "top_k_search": 10,
        "top_k_rerank": 20,
        "rag_top_k": 5,
        "rrf_k": 60,
        "max_chunks_per_doc": 3,
        "rag_min_score": 0.0,
    }


class TestSearchStage:
    """Tests for SearchStage."""

    def test_init(self):
        """Test SearchStage initialization with http client."""
        cfg = {"top_k_search": 10}
        http = AsyncMock()
        stage = SearchStage(cfg, http)
        assert stage._cfg == cfg
        assert stage._http == http

    def test_init_without_http(self):
        """Test SearchStage initialization without http client."""
        cfg = {"top_k_search": 10}
        stage = SearchStage(cfg)
        assert stage._cfg == cfg
        assert stage._http is None

    @pytest.mark.asyncio
    async def test_run_success(self, mock_context, mock_llm, mock_db):
        """Test successful execution of SearchStage."""
        mock_context.queries = ["test query"]

        with (
            patch(
                "rag.llm.get_embedding", new_callable=AsyncMock
            ) as mock_get_embedding,
            patch("rag.stages.search.RagRepository") as mock_repo,
        ):
            mock_get_embedding.return_value = [0.1, 0.2, 0.3]
            mock_repo_instance = MagicMock()
            mock_repo.return_value = mock_repo_instance
            mock_repo_instance.vector_search.return_value = [
                {"chunk_id": 1, "content": "vector_result"}
            ]
            mock_repo_instance.fts_search.return_value = [
                {"chunk_id": 2, "content": "fts_result"}
            ]

            cfg = {"top_k_search": 10}
            stage = SearchStage(cfg, mock_llm)

            await stage.run(mock_context, db=mock_db)

            expected_results = [
                [{"chunk_id": 1, "content": "vector_result"}],
                [{"chunk_id": 2, "content": "fts_result"}],
            ]
            assert mock_context.search_results == expected_results

    @pytest.mark.asyncio
    async def test_run_db_none(self, mock_context):
        """Test SearchStage with None db returns empty results."""
        mock_context.queries = ["test query"]

        cfg = {"top_k_search": 10}
        stage = SearchStage(cfg)

        await stage.run(mock_context, db=None)

        assert mock_context.search_results == []

    @pytest.mark.asyncio
    async def test_run_empty_queries(self, mock_db):
        """Test SearchStage with empty queries list."""
        mock_context = MagicMock(spec=PipelineContext)
        mock_context.queries = []

        cfg = {"top_k_search": 10}
        stage = SearchStage(cfg)

        await stage.run(mock_context, db=mock_db)

        assert mock_context.search_results == []

    @pytest.mark.asyncio
    async def test_run_embedding_exception(self, mock_context, mock_db):
        """Test SearchStage handles embedding exceptions gracefully."""
        mock_context.queries = ["test query"]

        with (
            patch(
                "rag.llm.get_embedding", new_callable=AsyncMock
            ) as mock_get_embedding,
        ):
            mock_get_embedding.side_effect = Exception("Embedding failed")
            cfg = {"top_k_search": 10}
            stage = SearchStage(cfg)

            await stage.run(mock_context, db=mock_db)

            assert mock_context.search_results == []

    @pytest.mark.asyncio
    async def test_run_multiple_queries(self, mock_context, mock_db):
        """Test SearchStage with multiple queries."""
        mock_context.queries = ["query1", "query2"]

        with (
            patch(
                "rag.llm.get_embedding", new_callable=AsyncMock
            ) as mock_get_embedding,
            patch("rag.stages.search.RagRepository") as mock_repo,
        ):
            mock_get_embedding.side_effect = [
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6],
            ]
            mock_repo_instance = MagicMock()
            mock_repo.return_value = mock_repo_instance
            mock_repo_instance.vector_search.side_effect = [
                [{"chunk_id": 1, "content": "result1"}],
                [{"chunk_id": 2, "content": "result2"}],
            ]
            mock_repo_instance.fts_search.return_value = []

            cfg = {"top_k_search": 10}
            stage = SearchStage(cfg)

            await stage.run(mock_context, db=mock_db)

            assert len(mock_context.search_results) == 2

    @pytest.mark.asyncio
    async def test_run_only_vector_results(self, mock_context, mock_db):
        """Test SearchStage when only vector search returns results."""
        mock_context.queries = ["test query"]

        with (
            patch(
                "rag.llm.get_embedding", new_callable=AsyncMock
            ) as mock_get_embedding,
            patch("rag.stages.search.RagRepository") as mock_repo,
        ):
            mock_get_embedding.return_value = [0.1, 0.2, 0.3]
            mock_repo_instance = MagicMock()
            mock_repo.return_value = mock_repo_instance
            mock_repo_instance.vector_search.return_value = [
                {"chunk_id": 1, "content": "vector_result"}
            ]
            mock_repo_instance.fts_search.return_value = []

            cfg = {"top_k_search": 10}
            stage = SearchStage(cfg)

            await stage.run(mock_context, db=mock_db)

            assert len(mock_context.search_results) == 1

    @pytest.mark.asyncio
    async def test_run_only_fts_results(self, mock_context, mock_db):
        """Test SearchStage when only FTS search returns results."""
        mock_context.queries = ["test query"]

        with (
            patch(
                "rag.llm.get_embedding", new_callable=AsyncMock
            ) as mock_get_embedding,
            patch("rag.stages.search.RagRepository") as mock_repo,
        ):
            mock_get_embedding.return_value = [0.1, 0.2, 0.3]
            mock_repo_instance = MagicMock()
            mock_repo.return_value = mock_repo_instance
            mock_repo_instance.vector_search.return_value = []
            mock_repo_instance.fts_search.return_value = [
                {"chunk_id": 1, "content": "fts_result"}
            ]

            cfg = {"top_k_search": 10}
            stage = SearchStage(cfg)

            await stage.run(mock_context, db=mock_db)

            assert len(mock_context.search_results) == 1

    @pytest.mark.asyncio
    async def test_run_embedding_not_list(self, mock_context, mock_db):
        """Test SearchStage handles non-list embedding result."""
        mock_context.queries = ["test query"]

        with (
            patch(
                "rag.llm.get_embedding", new_callable=AsyncMock
            ) as mock_get_embedding,
        ):
            mock_get_embedding.return_value = "not a list"
            cfg = {"top_k_search": 10}
            stage = SearchStage(cfg)

            await stage.run(mock_context, db=mock_db)

            assert mock_context.search_results == []

    @pytest.mark.asyncio
    async def test_run_search_exception(self, mock_context, mock_db):
        """Test SearchStage handles search exceptions gracefully."""
        mock_context.queries = ["test query"]

        with (
            patch(
                "rag.llm.get_embedding", new_callable=AsyncMock
            ) as mock_get_embedding,
            patch("rag.stages.search.RagRepository") as mock_repo,
        ):
            mock_get_embedding.return_value = [0.1, 0.2, 0.3]
            mock_repo_instance = MagicMock()
            mock_repo.return_value = mock_repo_instance
            mock_repo_instance.vector_search.side_effect = Exception("Search error")

            cfg = {"top_k_search": 10}
            stage = SearchStage(cfg)

            await stage.run(mock_context, db=mock_db)

            assert mock_context.search_results == []


class TestMqeStage:
    """Tests for MqeStage."""

    def test_init(self):
        """Test MqeStage initialization."""
        cfg = {"use_mqe": True}
        llm = AsyncMock()
        stage = MqeStage(cfg, llm)
        assert stage._cfg == cfg
        assert stage._llm == llm

    @pytest.mark.asyncio
    async def test_run_success(self, mock_context, mock_llm):
        """Test successful execution of MqeStage."""
        mock_llm.expand_queries.return_value = ["mqe_query_1", "mqe_query_2"]

        cfg = {"use_mqe": True}
        stage = MqeStage(cfg, mock_llm)

        await stage.run(mock_context)

        assert mock_context.queries == ["mqe_query_1", "mqe_query_2"]

    @pytest.mark.asyncio
    async def test_run_mqe_disabled(self, mock_context, mock_llm):
        """Test MqeStage with MQE disabled returns original query."""
        cfg = {"use_mqe": False}
        stage = MqeStage(cfg, mock_llm)

        await stage.run(mock_context)

        assert mock_context.queries == ["test query"]
        mock_llm.expand_queries.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_llm_exception(self, mock_context, mock_llm):
        """Test MqeStage handles LLM exceptions with fallback."""
        mock_llm.expand_queries.side_effect = Exception("LLM error")

        cfg = {"use_mqe": True}
        stage = MqeStage(cfg, mock_llm)

        await stage.run(mock_context)

        assert mock_context.queries == ["test query"]

    @pytest.mark.asyncio
    async def test_run_empty_expansion(self, mock_context, mock_llm):
        """Test MqeStage with empty expansion result."""
        mock_llm.expand_queries.return_value = []

        cfg = {"use_mqe": True}
        stage = MqeStage(cfg, mock_llm)

        await stage.run(mock_context)

        assert mock_context.queries == []


class TestRunMqe:
    """Tests for _run_mqe helper function."""

    @pytest.mark.asyncio
    async def test_mqe_enabled_success(self, mock_llm):
        """Test _run_mqe with MQE enabled and successful expansion."""
        mock_llm.expand_queries.return_value = ["expanded1", "expanded2"]
        cfg = {"use_mqe": True}

        result = await _run_mqe("original query", cfg, mock_llm)

        assert result == ["expanded1", "expanded2"]

    @pytest.mark.asyncio
    async def test_mqe_disabled(self, mock_llm):
        """Test _run_mqe with MQE disabled."""
        cfg = {"use_mqe": False}

        result = await _run_mqe("original query", cfg, mock_llm)

        assert result == ["original query"]
        mock_llm.expand_queries.assert_not_called()

    @pytest.mark.asyncio
    async def test_mqe_exception_fallback(self, mock_llm):
        """Test _run_mqe falls back to original query on exception."""
        mock_llm.expand_queries.side_effect = Exception("Error")
        cfg = {"use_mqe": True}

        result = await _run_mqe("original query", cfg, mock_llm)

        assert result == ["original query"]


class TestFusionStage:
    """Tests for FusionStage."""

    def test_init(self):
        """Test FusionStage initialization with custom rrf_k."""
        cfg = {"rrf_k": 20}
        stage = FusionStage(cfg)
        assert stage._cfg == cfg
        assert stage._rrf_k == 20

    def test_init_default_rrf_k(self):
        """Test FusionStage initialization with default rrf_k."""
        cfg = {}
        stage = FusionStage(cfg)
        assert stage._cfg == cfg
        assert stage._rrf_k == 60

    @pytest.mark.asyncio
    async def test_run_success(self, mock_context):
        """Test successful execution of FusionStage."""
        mock_context.search_results = [
            [
                {"chunk_id": 1, "content": "result1"},
                {"chunk_id": 2, "content": "result2"},
            ],
            [
                {"chunk_id": 3, "content": "result3"},
                {"chunk_id": 4, "content": "result4"},
            ],
        ]

        cfg = {"rrf_k": 20}
        stage = FusionStage(cfg)

        await stage.run(mock_context)

        assert hasattr(mock_context, "merged")
        assert len(mock_context.merged) == 4

    @pytest.mark.asyncio
    async def test_run_empty_results(self, mock_context):
        """Test FusionStage with empty search results."""
        mock_context.search_results = []

        cfg = {"rrf_k": 20}
        stage = FusionStage(cfg)

        await stage.run(mock_context)

        assert mock_context.merged == []

    @pytest.mark.asyncio
    async def test_run_single_result_list(self, mock_context):
        """Test FusionStage with single result list."""
        mock_context.search_results = [
            [{"chunk_id": 1, "content": "result1"}]
        ]

        cfg = {"rrf_k": 20}
        stage = FusionStage(cfg)

        await stage.run(mock_context)

        assert len(mock_context.merged) == 1

    @pytest.mark.asyncio
    async def test_run_with_duplicates(self, mock_context):
        """Test FusionStage with duplicate chunk_ids across lists."""
        mock_context.search_results = [
            [{"chunk_id": 1, "content": "result1"}],
            [{"chunk_id": 1, "content": "result1_duplicate"}],
        ]

        cfg = {"rrf_k": 20}
        stage = FusionStage(cfg)

        await stage.run(mock_context)

        assert len(mock_context.merged) == 1
        assert mock_context.merged[0]["chunk_id"] == 1

    @pytest.mark.asyncio
    async def test_run_rrf_scores_assigned(self, mock_context):
        """Test FusionStage assigns RRF scores to results."""
        mock_context.search_results = [
            [{"chunk_id": 1, "content": "result1"}],
            [{"chunk_id": 2, "content": "result2"}],
        ]

        cfg = {"rrf_k": 60}
        stage = FusionStage(cfg)

        await stage.run(mock_context)

        for result in mock_context.merged:
            assert "rrf_score" in result


class TestRerankStage:
    """Tests for RerankStage."""

    def test_init(self):
        """Test RerankStage initialization."""
        cfg = {"use_rerank": True}
        llm = AsyncMock()
        stage = RerankStage(cfg, llm)
        assert stage._cfg == cfg
        assert stage._llm == llm

    @pytest.mark.asyncio
    async def test_run_success(self, mock_context, mock_llm):
        """Test successful execution of RerankStage."""
        mock_context.merged = [
            {"chunk_id": 1, "content": "result1", "title": "Title 1"},
            {"chunk_id": 2, "content": "result2", "title": "Title 2"},
        ]

        mock_llm.cross_encoder_rerank.return_value = [
            {"chunk_id": 2, "content": "result2", "title": "Title 2", "score": 0.9},
            {"chunk_id": 1, "content": "result1", "title": "Title 1", "score": 0.8},
        ]

        cfg = {
            "use_rerank": True,
            "rag_top_k": 5,
            "max_chunks_per_doc": 3,
            "top_k_rerank": 20,
            "rag_min_score": 0.0,
        }
        stage = RerankStage(cfg, mock_llm)

        await stage.run(mock_context)

        assert hasattr(mock_context, "reranked")
        assert len(mock_context.reranked) == 2

    @pytest.mark.asyncio
    async def test_run_rerank_disabled(self, mock_context, mock_llm):
        """Test RerankStage with rerank disabled uses RRF order."""
        mock_context.merged = [
            {"chunk_id": 1, "content": "result1", "url": "http://example.com/1"},
            {"chunk_id": 2, "content": "result2", "url": "http://example.com/2"},
        ]

        cfg = {
            "use_rerank": False,
            "rag_top_k": 5,
            "max_chunks_per_doc": 3,
        }
        stage = RerankStage(cfg, mock_llm)

        await stage.run(mock_context)

        assert mock_context.reranked == mock_context.merged[:5]
        mock_llm.cross_encoder_rerank.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_llm_exception(self, mock_context, mock_llm):
        """Test RerankStage handles LLM exceptions with fallback."""
        mock_context.merged = [
            {"chunk_id": 1, "content": "result1", "url": "http://example.com/1"},
        ]

        mock_llm.cross_encoder_rerank.side_effect = Exception("LLM error")

        cfg = {
            "use_rerank": True,
            "rag_top_k": 5,
            "max_chunks_per_doc": 3,
            "top_k_rerank": 20,
            "rag_min_score": 0.0,
        }
        stage = RerankStage(cfg, mock_llm)

        await stage.run(mock_context)

        assert len(mock_context.reranked) == 1

    @pytest.mark.asyncio
    async def test_run_empty_merged(self, mock_context, mock_llm):
        """Test RerankStage with empty merged results."""
        mock_context.merged = []

        cfg = {
            "use_rerank": True,
            "rag_top_k": 5,
            "max_chunks_per_doc": 3,
            "top_k_rerank": 20,
            "rag_min_score": 0.0,
        }
        stage = RerankStage(cfg, mock_llm)

        await stage.run(mock_context)

        assert mock_context.reranked == []

    @pytest.mark.asyncio
    async def test_run_deduplication(self, mock_context, mock_llm):
        """Test RerankStage applies deduplication."""
        mock_context.merged = [
            {"chunk_id": 1, "content": "result1", "url": "http://example.com/1"},
            {"chunk_id": 2, "content": "result2", "url": "http://example.com/1"},
            {"chunk_id": 3, "content": "result3", "url": "http://example.com/1"},
            {"chunk_id": 4, "content": "result4", "url": "http://example.com/1"},
        ]

        mock_llm.cross_encoder_rerank.return_value = mock_context.merged

        cfg = {
            "use_rerank": True,
            "rag_top_k": 10,
            "max_chunks_per_doc": 2,
            "top_k_rerank": 20,
            "rag_min_score": 0.0,
        }
        stage = RerankStage(cfg, mock_llm)

        await stage.run(mock_context)

        assert len(mock_context.reranked) == 2


class TestRerank:
    """Tests for _rerank helper function."""

    @pytest.mark.asyncio
    async def test_rerank_enabled_success(self, mock_llm):
        """Test _rerank with rerank enabled and successful execution."""
        merged = [
            {"chunk_id": 1, "content": "result1", "url": "http://example.com/1"},
        ]
        mock_llm.cross_encoder_rerank.return_value = merged

        cfg = {
            "use_rerank": True,
            "rag_top_k": 5,
            "max_chunks_per_doc": 3,
            "top_k_rerank": 20,
            "rag_min_score": 0.0,
        }

        result = await _rerank("test query", merged, cfg, mock_llm)

        assert result == merged

    @pytest.mark.asyncio
    async def test_rerank_disabled(self, mock_llm):
        """Test _rerank with rerank disabled."""
        merged = [
            {"chunk_id": 1, "content": "result1", "url": "http://example.com/1"},
            {"chunk_id": 2, "content": "result2", "url": "http://example.com/2"},
        ]

        cfg = {
            "use_rerank": False,
            "rag_top_k": 1,
            "max_chunks_per_doc": 3,
        }

        result = await _rerank("test query", merged, cfg, mock_llm)

        assert len(result) == 1
        mock_llm.cross_encoder_rerank.assert_not_called()

    @pytest.mark.asyncio
    async def test_rerank_exception_fallback(self, mock_llm):
        """Test _rerank falls back to RRF order on exception."""
        merged = [
            {"chunk_id": 1, "content": "result1", "url": "http://example.com/1"},
        ]
        mock_llm.cross_encoder_rerank.side_effect = Exception("Error")

        cfg = {
            "use_rerank": True,
            "rag_top_k": 5,
            "max_chunks_per_doc": 3,
            "top_k_rerank": 20,
            "rag_min_score": 0.0,
        }

        result = await _rerank("test query", merged, cfg, mock_llm)

        assert len(result) == 1


class TestAugmentStage:
    """Tests for AugmentStage."""

    def test_init(self):
        """Test AugmentStage initialization."""
        stage = AugmentStage()
        assert stage is not None

    @pytest.mark.asyncio
    async def test_run_success(self, mock_context):
        """Test successful execution of AugmentStage."""
        mock_context.reranked = [
            {"chunk_id": 1, "content": "result1", "url": "http://example.com/1"},
            {"chunk_id": 2, "content": "result2", "url": "http://example.com/2"},
        ]

        stage = AugmentStage()

        await stage.run(mock_context)

        assert hasattr(mock_context, "augment_result")
        assert "[RAG_CONTEXT_START]" in mock_context.augment_result
        assert "[RAG_CONTEXT_END]" in mock_context.augment_result

    @pytest.mark.asyncio
    async def test_run_empty_reranked(self, mock_context):
        """Test AugmentStage with empty reranked results."""
        mock_context.reranked = []

        stage = AugmentStage()

        await stage.run(mock_context)

        assert mock_context.augment_result == "[RAG_CONTEXT_START]\n\n[RAG_CONTEXT_END]"

    @pytest.mark.asyncio
    async def test_run_with_title(self, mock_context):
        """Test AugmentStage with title field."""
        mock_context.reranked = [
            {
                "chunk_id": 1,
                "content": "result1",
                "url": "http://example.com/1",
                "title": "Test Title",
            }
        ]

        stage = AugmentStage()

        await stage.run(mock_context)

        assert "Test Title" in mock_context.augment_result

    @pytest.mark.asyncio
    async def test_run_source_format(self, mock_context):
        """Test AugmentStage source format."""
        mock_context.reranked = [
            {"chunk_id": 1, "content": "result1", "url": "http://example.com/1"}
        ]

        stage = AugmentStage()

        await stage.run(mock_context)

        assert "[Source: http://example.com/1 | http://example.com/1]" in mock_context.augment_result

    @pytest.mark.asyncio
    async def test_run_separator(self, mock_context):
        """Test AugmentStage separator between chunks."""
        mock_context.reranked = [
            {"chunk_id": 1, "content": "result1", "url": "http://example.com/1"},
            {"chunk_id": 2, "content": "result2", "url": "http://example.com/2"},
        ]

        stage = AugmentStage()

        await stage.run(mock_context)

        assert "\n\n---\n\n" in mock_context.augment_result
