"""tests/test_workflow_execution_policy.py
Unit tests for WorkflowExecutionPolicy covering all three modes and all public methods.
"""

from __future__ import annotations

import pytest
from agent.workflow_execution_policy import WorkflowExecutionPolicy


class TestWorkflowExecutionPolicy:
    def test_disabled_is_workflow_enabled_false(self) -> None:
        policy = WorkflowExecutionPolicy("disabled")
        assert policy.is_workflow_enabled() is False

    def test_auto_is_workflow_enabled_true(self) -> None:
        policy = WorkflowExecutionPolicy("auto")
        assert policy.is_workflow_enabled() is True

    def test_required_is_workflow_enabled_true(self) -> None:
        policy = WorkflowExecutionPolicy("required")
        assert policy.is_workflow_enabled() is True

    def test_required_requires_startup_definition_true(self) -> None:
        policy = WorkflowExecutionPolicy("required")
        assert policy.requires_startup_definition() is True

    def test_auto_requires_startup_definition_false(self) -> None:
        policy = WorkflowExecutionPolicy("auto")
        assert policy.requires_startup_definition() is False

    def test_disabled_requires_startup_definition_false(self) -> None:
        policy = WorkflowExecutionPolicy("disabled")
        assert policy.requires_startup_definition() is False

    def test_auto_allow_startup_fallback_true(self) -> None:
        policy = WorkflowExecutionPolicy("auto")
        assert policy.allow_startup_fallback() is True

    def test_disabled_allow_startup_fallback_false(self) -> None:
        policy = WorkflowExecutionPolicy("disabled")
        assert policy.allow_startup_fallback() is False

    def test_allow_turn_fallback_always_false(self) -> None:
        for mode in ("disabled", "auto", "required"):
            policy = WorkflowExecutionPolicy(mode)
            assert policy.allow_turn_fallback(RuntimeError("err")) is False

    def test_fail_closed_on_creation_error_always_true(self) -> None:
        for mode in ("disabled", "auto", "required"):
            policy = WorkflowExecutionPolicy(mode)
            assert policy.fail_closed_on_creation_error() is True

    def test_invalid_mode_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid workflow_mode"):
            WorkflowExecutionPolicy("unknown_mode")
