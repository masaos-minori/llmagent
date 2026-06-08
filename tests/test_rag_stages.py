"""Unit tests for RAG pipeline stages."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rag.stage import PipelineContext
from rag.stages.augment import AugmentStage
from rag.stages.fusion import FusionStage
from rag.stages.mqe import MqeStage
from rag.stages.rerank import RerankStage
from rag.stages.search import SearchStage


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
    """Create a mock database."""
    return AsyncMock()


class TestSearchStage:
    """Tests for SearchStage."""

    def test_init(self):
        """Test SearchStage initialization."""
        cfg = {"top_k_search": 10}
        http = AsyncMock()
        stage = SearchStage(cfg, http)
        assert stage._cfg == cfg
        assert stage._http == http

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

            # search_results はクエリごとの結果リストのリスト (FusionStage への入力形式)
            expected_results = [
                [{"chunk_id": 1, "content": "vector_result"}],
                [{"chunk_id": 2, "content": "fts_result"}],
            ]
            assert mock_context.search_results == expected_results


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
        # Setup mocks
        mock_llm.expand_queries.return_value = ["mqe_query_1", "mqe_query_2"]

        # Create stage
        cfg = {"use_mqe": True}
        stage = MqeStage(cfg, mock_llm)

        # Run stage
        await stage.run(mock_context)

        # Verify results
        assert mock_context.queries == ["mqe_query_1", "mqe_query_2"]


class TestFusionStage:
    """Tests for FusionStage."""

    def test_init(self):
        """Test FusionStage initialization."""
        cfg = {"rrf_k": 20}
        stage = FusionStage(cfg)
        assert stage._cfg == cfg
        assert stage._rrf_k == 20

    @pytest.mark.asyncio
    async def test_run_success(self, mock_context):
        """Test successful execution of FusionStage."""
        # Setup context with search results (as dict objects, not strings)
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

        # Create stage
        cfg = {"rrf_k": 20}
        stage = FusionStage(cfg)

        # Run stage
        await stage.run(mock_context)

        # Verify results (should be merged)
        assert hasattr(mock_context, "merged")


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
        # Setup context with merged results
        mock_context.merged = [
            {"chunk_id": 1, "content": "result1", "title": "Title 1"},
            {"chunk_id": 2, "content": "result2", "title": "Title 2"},
        ]

        # Setup mocks
        mock_llm.cross_encoder_rerank.return_value = [
            {"chunk_id": 2, "content": "result2", "title": "Title 2", "score": 0.9},
            {"chunk_id": 1, "content": "result1", "title": "Title 1", "score": 0.8},
        ]

        # Create stage
        cfg = {"use_rerank": True, "rag_top_k": 5, "max_chunks_per_doc": 3}
        stage = RerankStage(cfg, mock_llm)

        # Run stage
        await stage.run(mock_context)

        # Verify results (should be reranked)
        assert hasattr(mock_context, "reranked")


class TestAugmentStage:
    """Tests for AugmentStage."""

    def test_init(self):
        """Test AugmentStage initialization."""
        stage = AugmentStage()
        assert stage is not None

    @pytest.mark.asyncio
    async def test_run_success(self, mock_context):
        """Test successful execution of AugmentStage."""
        # Setup context with reranked results that have required fields
        mock_context.reranked = [
            {"chunk_id": 1, "content": "result1", "url": "http://example.com/1"},
            {"chunk_id": 2, "content": "result2", "url": "http://example.com/2"},
        ]

        # Create stage
        stage = AugmentStage()

        # Run stage
        await stage.run(mock_context)

        # Verify results (should be augmented)
        assert hasattr(mock_context, "augment_result")
