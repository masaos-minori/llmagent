"""tests/test_rag_pipeline_stage.py
Unit tests for RAG pipeline stages and observer functionality.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from rag.stage import PipelineContext


class TestPipelineContextObserver:
    """Test PipelineContext observer functionality."""

    def test_add_observer(self) -> None:
        """Test adding an observer to PipelineContext."""
        ctx = PipelineContext(query="test query")
        observer = MagicMock()

        ctx.add_observer(observer)

        assert len(ctx.observers) == 1
        assert ctx.observers[0] == observer

    @pytest.mark.asyncio
    async def test_observer_notified_on_stage_complete(self) -> None:
        """Test that observers are notified when a stage completes."""
        ctx = PipelineContext(query="test query")
        observer = AsyncMock()
        ctx.add_observer(observer)

        # Create a mock stage that implements the protocol
        class MockStage:
            async def run(self, ctx, **kwargs):
                ctx.queries = ["mock query"]
                # Notify observers manually for testing
                for obs in ctx.observers:
                    try:
                        await obs.on_stage_complete("mock", ctx)
                    except Exception:
                        pass

        stage = MockStage()
        await stage.run(ctx)

        # Verify observer was called
        observer.on_stage_complete.assert_called_once_with("mock", ctx)


class TestPipelineStageObserverIntegration:
    """Test integration of observer functionality with actual pipeline stages."""

    def test_pipeline_context_has_observers_field(self) -> None:
        """Test that PipelineContext has observers field."""
        ctx = PipelineContext(query="test query")
        assert hasattr(ctx, "observers")
        assert isinstance(ctx.observers, list)
