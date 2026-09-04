"""Behavior-lock tests for ComponentInitializer workflow preflight aborts.

Tests that _check_workflow_definition/_check_workflow_schema raise RuntimeError
on workflow definition/schema failures.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from agent.startup_component_init import ComponentInitializer


class TestComponentInitializerWorkflowPreflight:
    """ComponentInitializer aborts on workflow preflight failures."""

    def _make_initializer(self) -> ComponentInitializer:
        ctx = MagicMock()
        view = MagicMock()
        return ComponentInitializer(ctx, view)

    def test_aborts_on_missing_workflow_definition(self) -> None:
        initializer = self._make_initializer()
        with patch(
            "agent.startup_component_init.check_workflow_definition",
            side_effect=RuntimeError("missing workflow.json"),
        ):
            with pytest.raises(RuntimeError, match="missing workflow.json"):
                initializer._check_workflow_definition()

    def test_aborts_on_invalid_workflow_json(self) -> None:
        initializer = self._make_initializer()
        with patch(
            "agent.startup_component_init.check_workflow_definition",
            side_effect=RuntimeError("invalid JSON"),
        ):
            with pytest.raises(RuntimeError, match="invalid JSON"):
                initializer._check_workflow_definition()

    def test_aborts_on_invalid_workflow_schema(self) -> None:
        initializer = self._make_initializer()
        mock_result = MagicMock()
        mock_result.valid = False
        mock_result.error = "missing table: tasks"
        with patch(
            "agent.startup_component_init.check_workflow_schema",
            return_value=mock_result,
        ):
            with pytest.raises(RuntimeError, match="missing table"):
                initializer._check_workflow_schema()

    def test_definition_check_passes_when_no_error(self) -> None:
        initializer = self._make_initializer()
        with patch("agent.startup_component_init.check_workflow_definition"):
            initializer._check_workflow_definition()  # must not raise

    def test_schema_check_passes_when_valid(self) -> None:
        initializer = self._make_initializer()
        mock_result = MagicMock()
        mock_result.valid = True
        mock_result.error = None
        with patch(
            "agent.startup_component_init.check_workflow_schema",
            return_value=mock_result,
        ):
            initializer._check_workflow_schema()  # must not raise

    def test_error_message_has_no_workflow_mode_suggestion(self) -> None:
        initializer = self._make_initializer()
        with patch(
            "agent.startup_component_init.check_workflow_definition",
            side_effect=RuntimeError("definition missing"),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                initializer._check_workflow_definition()
        assert "workflow_mode" not in str(exc_info.value)
        assert "disabled" not in str(exc_info.value)
