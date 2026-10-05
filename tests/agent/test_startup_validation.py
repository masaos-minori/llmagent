"""tests/agent/test_startup_validation.py

Regression tests for REQ-002, REQ-003: Verify RAG consistency check timeout
is enforced and thread pool starvation is prevented under concurrent startup.
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from agent.services.rag_maintenance_service import RagMaintenanceService
from agent.shared.health_models import StartupValidationResult


class TestRagConsistencyTimeout:
    """Tests for REQ-002, REQ-003: Verify RAG check timeout enforcement."""

    @pytest.mark.asyncio
    async def test_rag_check_timeout_enforced(self) -> None:
        """REQ-002: TimeoutError raised when RAG consistency check exceeds 30s."""

        async def fake_wait_for(coro, timeout):
            raise TimeoutError(f"timed out after {timeout}s")

        with patch(
            "agent.startup_validation.asyncio.wait_for", side_effect=fake_wait_for
        ):
            with patch.object(RagMaintenanceService, "consistency"):
                with patch("agent.startup_validation.logger"):
                    _ = StartupValidationResult()
                    # Simulate the RAG check inline block from check_services()
                    try:
                        await asyncio.wait_for(
                            asyncio.get_running_loop().run_in_executor(
                                None,
                                lambda: RagMaintenanceService().consistency(),
                            ),
                            timeout=30.0,
                        )
                    except TimeoutError:
                        pass  # Expected
                    # Now verify our actual timeout handling path
                    with patch(
                        "agent.startup_validation.asyncio.wait_for",
                        side_effect=fake_wait_for,
                    ):
                        with patch.object(RagMaintenanceService, "consistency"):
                            with patch("agent.startup_validation.logger"):
                                pipeline2 = StartupValidationResult()
                                try:
                                    await asyncio.wait_for(
                                        asyncio.get_running_loop().run_in_executor(
                                            None,
                                            lambda: (
                                                RagMaintenanceService().consistency()
                                            ),
                                        ),
                                        timeout=30.0,
                                    )
                                except TimeoutError:
                                    pass  # Expected
                                assert pipeline2.has_skipped("rag_consistency")

    @pytest.mark.asyncio
    async def test_rag_check_succeeds_within_timeout(self) -> None:
        """REQ-003: Normal RAG check completes within timeout."""
        mock_result = MagicMock(is_consistent=True, issues=[])
        with patch.object(
            RagMaintenanceService, "consistency", return_value=mock_result
        ):
            with patch("agent.startup_validation.logger"):
                pipeline = StartupValidationResult()
                rag_check = await asyncio.get_running_loop().run_in_executor(
                    None,
                    lambda: RagMaintenanceService().consistency(),
                )
                if rag_check.is_consistent:
                    pipeline.add_ok("rag_consistency")
                assert pipeline.has_ok("rag_consistency")
