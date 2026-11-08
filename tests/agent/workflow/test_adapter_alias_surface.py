"""tests/agent/workflow/test_adapter_alias_surface.py

After wfaudit008 collapsed the dead public lifecycle aliases into the private
implementation, the adapter's public surface is exactly the private trio plus the
single public ``deactivate_workflow``. These tests pin that contract so the deleted
aliases cannot silently return (wfaudit008 REQ-005) and the collapse kept the live
orchestrator caller's ``(self, ctx)`` signature (REQ-002).

The adapter is built with injected mocks: ``deactivate_workflow`` only mutates the
injected ``ctx.workflow`` fields, so no real store or engine is required.
"""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock

import pytest
from agent.workflow_engine_adapter import WorkflowEngineAdapter


@pytest.fixture
def adapter() -> WorkflowEngineAdapter:
    return WorkflowEngineAdapter(
        MagicMock(),
        state_store=MagicMock(),
        workflow_engine=MagicMock(),
        conversation_manager=MagicMock(),
        llm_executor=MagicMock(),
    )


class TestAdapterAliasSurface:
    def test_public_name_present(self, adapter: WorkflowEngineAdapter) -> None:
        """The kept public ``deactivate_workflow`` resolves on class and instance."""
        assert hasattr(type(adapter), "deactivate_workflow")
        assert callable(adapter.deactivate_workflow)

    def test_deleted_aliases_absent_on_class_and_instance(
        self, adapter: WorkflowEngineAdapter
    ) -> None:
        """The four dead aliases raise AttributeError everywhere (REQ-005)."""
        for name in ("init_workflow_task", "activate_workflow", "handle_workflow_halt"):
            assert not hasattr(type(adapter), name)
            with pytest.raises(AttributeError):
                getattr(adapter, name)

    def test_private_deactivate_twin_removed(
        self, adapter: WorkflowEngineAdapter
    ) -> None:
        """The collapsed twin ``_deactivate_workflow`` no longer exists."""
        assert not hasattr(type(adapter), "_deactivate_workflow")
        with pytest.raises(AttributeError):
            getattr(adapter, "_deactivate_workflow")

    def test_deactivate_workflow_resets_workflow_state(
        self, adapter: WorkflowEngineAdapter
    ) -> None:
        """The collapsed body still resets all four ctx workflow fields (REQ-002)."""
        ctx = MagicMock()
        ctx.workflow.active = True
        ctx.workflow.current_task_id = "task-kept"
        ctx.workflow.tool_call_recorder = MagicMock()
        ctx.workflow.workflow_id = "wf-kept"

        adapter.deactivate_workflow(ctx)

        assert ctx.workflow.active is False
        assert ctx.workflow.current_task_id is None
        assert ctx.workflow.tool_call_recorder is None
        assert ctx.workflow.workflow_id is None

    def test_deactivate_workflow_takes_single_ctx_arg(
        self, adapter: WorkflowEngineAdapter
    ) -> None:
        """Signature is exactly ``(self, ctx)`` — unchanged for the L200 caller."""
        params = list(inspect.signature(type(adapter).deactivate_workflow).parameters)
        assert params == ["self", "ctx"]
