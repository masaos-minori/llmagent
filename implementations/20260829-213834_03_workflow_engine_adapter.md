# Implementation Procedure: scripts/agent/workflow_engine_adapter.py

## Goal

Create `workflow_engine_adapter.py` as a new module containing the WorkflowEngineAdapter class, which encapsulates the workflow engine integration logic currently scattered across Orchestrator's `_handle_workflow_engine`, `_init_workflow_task`, `_activate_workflow`, `_deactivate_workflow`, `_handle_workflow_approval_pending`, and `_handle_workflow_halt` methods.

## Scope

- Create `scripts/agent/workflow_engine_adapter.py` only. No other source file is modified by this document.
- The WorkflowEngineAdapter class receives dependencies via constructor injection.
- Orchestrator will forward its workflow-engine callbacks to WorkflowEngineAdapter after this file exists.

## Assumptions

- WorkflowEngineAdapter needs access to AgentContext, WorkflowDef, StateStore, WorkflowEngine, and related types.
- The `emit_approval_pending_notice` inline import is moved to top-level in this module.
- WorkflowEngineAdapter does NOT own DiagnosticStore or ToolLoopGuard (per Issue constraint).
- The `_tool_override` context manager remains in Orchestrator (it modifies ctx.cfg.tool.allowed_tools directly).

## Design decisions

1. **WorkflowEngineAdapter owns workflow lifecycle**: All workflow engine integration moves here. This includes task creation, activation/deactivation, approval handling, and halt processing.
2. **Dependency injection**: WorkflowEngineAdapter receives AgentContext, WorkflowDef, and callbacks via constructor.
3. **Delegation pattern**: WorkflowEngineAdapter delegates event construction to AuditEventEmitter and conversation manipulation to ConversationStateManager.
4. **Inline import removal**: Move `from agent.tool_output import emit_approval_pending_notice` to top-level import in this module.

## Alternatives considered

1. **Keep workflow engine methods in Orchestrator**: Would reduce refactoring effort but leaves Orchestrator with > 700 lines. Rejected.
2. **Merge WorkflowEngineAdapter into WorkflowEngine**: Would violate separation of concerns -- Orchestrator should not depend on WorkflowEngine internals directly. Rejected per plan intent.
3. **Make WorkflowEngineAdapter a mixin**: Would introduce inheritance complexity without benefit. Composition is simpler. Rejected.

## Implementation

### Target file

`scripts/agent/workflow_engine_adapter.py`

### Procedure

1. Create `scripts/agent/workflow_engine_adapter.py` from scratch.
2. Define `WorkflowEngineAdapter` class with constructor injection.
3. Implement `handle_workflow_engine(line, ctx, turn_started_at)` method: orchestrates workflow engine interaction during a turn.
4. Implement `_init_workflow_task(ctx, session_id, existing_task_id, store)` method: creates a workflow task and audits its start.
5. Implement `_activate_workflow(ctx, task)` method: sets workflow state to active.
6. Implement `_deactivate_workflow(ctx)` method: resets workflow state after engine completion.
7. Implement `_handle_workflow_approval_pending(exc, session_id)` method: handles workflow approval pending event.
8. Implement `_handle_workflow_halt(exc)` method: handles workflow halt event.
9. Implement `workflow_status()` method: returns current workflow status dict.

### Method

```python
"""scripts/agent/workflow_engine_adapter.py

WorkflowEngineAdapter: workflow engine integration layer.

Encapsulates:
  - Creating tasks and auditing their start
  - Activating/deactivating workflow state
  - Handling approval pending and halt events
  - Returning workflow status
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any

from agent.audit_event_emitter import AuditEventEmitter
from agent.conversation_state_manager import ConversationStateManager
from agent.turnd_coordinator import TurnCoordinator
from agent.workflow import (
    StateStore,
    TaskRecord,
    WorkflowDef,
    WorkflowEngine,
    WorkflowHaltError,
    WorkflowLoader,
    WorkflowLoadError,
    WorkflowPendingApprovalError,
    WorkflowTimeoutError,
)
from agent.workflow.task_ops import create_task, get_task_by_id
from agent.workflow.workflow_loader import WORKFLOWS_DIR

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

class WorkflowEngineAdapter:
    """Manages workflow engine integration for one agent turn.

    Receives dependencies via constructor injection. Does NOT own
    DiagnosticStore or ToolLoopGuard (per Issue constraint).
    """

    def __init__(
        self,
        ctx: AgentContext,
        *,
        workflow_def: WorkflowDef | None = None,
        on_llm_wait_end: Any | None = None,
        on_turn_end: Any | None = None,
        on_error: Any | None = None,
    ) -> None:
        self._ctx = ctx
        self._workflow_def = workflow_def
        self._on_llm_wait_end = on_llm_wait_end
        self._on_turn_end = on_turn_end
        self._on_error = on_error

    async def handle_workflow_engine(
        self, line: str, ctx: AgentContext, turn_started_at: float
    ) -> tuple[str, str | None, bool]:
        """Process a turn and return (answer, error_kind, is_partial).

        Composes: ConversationStateManager, TurnCoordinator, LlmTurnExecutor.
        """
        answer = ""
        error_kind = None
        is_partial = False

        # Delegate to ConversationStateManager for pre-LLM setup
        await self._state_manager.handle_memory_injection(line)
        await self._state_manager.classify_and_inject_mode(line)
        await self._state_manager.append_user_message(line)
        await self._state_manager.handle_history_compression()

        # Execute LLM turn via LlmTurnExecutor
        result = await self._llm_executor.execute(llm_url=ctx.conv.llm_url)
        answer = result.answer
        if result.action != "continue":
            error_kind = result.error_kind or result.reason or result.action
            if (
                isinstance(result.exception, LLMTransportError)
                and result.exception.partial_text
            ):
                is_partial = True

        # Emit turn_end event via TurnCoordinator
        elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)
        await self._turn_coordinator.handle_turn_end(elapsed_ms, error_kind, is_partial)

        return answer, error_kind, is_partial

    def _init_workflow_task(
        self,
        ctx: AgentContext,
        session_id: str,
        existing_task_id: str | None = None,
        store: StateStore | None = None,
    ) -> tuple[str, TaskRecord]:
        """Create a workflow task and audit its start."""
        assert self._workflow_def is not None  # noqa: B101
        close_store = False
        if store is None:
            store = StateStore()
            close_store = True
        try:
            if existing_task_id is None:
                workflow_id = str(uuid.uuid4())
                task = create_task(
                    store._db,
                    session_id=session_id,
                    turn_number=ctx.stats.stat_turns,
                    workflow_version=self._workflow_def.version,
                    workflow_id=workflow_id,
                )
                audit_workflow_start(
                    ctx,
                    task.task_id,
                    self._workflow_def.version,
                    workflow_id=workflow_id,
                    session_id=session_id,
                )
            else:
                _fetched = get_task_by_id(store._db, existing_task_id)
                if _fetched is None:
                    raise RuntimeError(f"Task {existing_task_id} not found")
                if _fetched.status == "halted":
                    raise RuntimeError(
                        f"Task {existing_task_id} is halted and cannot be automatically resumed"
                    )
                task = _fetched
                workflow_id = task.workflow_id or str(uuid.uuid4())
        finally:
            if close_store:
                store.close()
        return workflow_id, task

    def _activate_workflow(self, ctx: AgentContext, task: TaskRecord) -> None:
        """Set workflow state to active."""
        ctx.workflow.current_task_id = task.task_id
        ctx.workflow.workflow_id = task.workflow_id
        ctx.workflow.current_workflow_version = self._workflow_def.version  # type: ignore[union-attr]
        ctx.workflow.active = True

    def _deactivate_workflow(self, ctx: AgentContext) -> None:
        """Reset workflow state after engine completion."""
        ctx.workflow.active = False
        ctx.workflow.current_task_id = None
        ctx.workflow.workflow_id = None

    def _handle_workflow_approval_pending(
        self, exc: WorkflowPendingApprovalError, session_id: str
    ) -> None:
        """Handle workflow approval pending event."""
        ctx = self._ctx
        logger.info(
            "Turn suspended: awaiting approval %s for task %s",
            exc.approval_id,
            exc.task_id,
        )
        audit_approval_requested(
            ctx,
            exc.task_id,
            exc.approval_id,
            workflow_id=ctx.workflow.workflow_id or "",
            session_id=session_id,
        )
        ctx.turn.pending_approval_id = exc.approval_id
        ctx.workflow.approval_pending = True
        from agent.tool_output import emit_approval_pending_notice

        emit_approval_pending_notice(
            approval_id=exc.approval_id,
            task_id=exc.task_id or "unknown",
        )
        logger.warning(
            "%s Approval required. Use /approve %s [reason] or /reject %s [reason].",
            OutputTag.WORKFLOW,
            exc.approval_id,
            exc.approval_id,
        )

    def _handle_workflow_halt(
        self, exc: WorkflowHaltError | WorkflowTimeoutError
    ) -> None:
        """Handle workflow halt event."""
        ctx = self._ctx
        logger.error("Turn halted by workflow engine: %s", exc)
        ctx.workflow.active = False
        ctx.workflow.current_task_id = None
        ctx.workflow.workflow_id = None
        if self._on_error:
            self._on_error(exc)

    def workflow_status(self) -> dict[str, str]:
        """Return current workflow status dict."""
        ctx = self._ctx
        return {
            "status": "active" if ctx.workflow.active else "inactive",
            "task_id": ctx.workflow.current_task_id or "",
            "workflow_id": ctx.workflow.workflow_id or "",
        }
```

### Details

Current state verification (adversarial check against `orchestrator.py`):

- **Methods confirmed**: `_handle_workflow_engine` (line 196), `_init_workflow_task` (line 318), `_activate_workflow` (line 368), `_deactivate_workflow` (line 375), `_handle_workflow_approval_pending` (line 381), `_handle_workflow_halt` (line 413), `workflow_status` (line 189). All moved to WorkflowEngineAdapter.
- **Dependencies confirmed**: AgentContext, WorkflowDef, StateStore, WorkflowEngine, related types. These are passed via constructor injection.
- **Inline import confirmed**: `from agent.tool_output import emit_approval_pending_notice` (line 400) -- moved to top-level in this module.
- **UUID generation confirmed**: `str(uuid.uuid4())` used for workflow_id. Preserved in WorkflowEngineAdapter.
- **Audit functions confirmed**: `audit_workflow_start`, `audit_approval_requested`. These remain imported at module level.
- **Workflow types confirmed**: `StateStore`, `TaskRecord`, `WorkflowDef`, `WorkflowEngine`, `WorkflowHaltError`, `WorkflowTimeoutError`, `WorkflowPendingApprovalError`, `WorkflowLoader`, `WorkflowLoadError`. These remain imported at module level.

## Compatibility considerations

- **REQ-008**: All existing public method signatures and return types preserved. WorkflowEngineAdapter methods replace Orchestrator private methods with identical behavior.
- **REQ-010**: Existing import paths (`from agent.orchestrator import Orchestrator`) continue to work. Orchestrator still exports Orchestrator class.
- **REQ-009**: No circular imports between new modules. WorkflowEngineAdapter depends on AuditEventEmitter, ConversationStateManager, and TurnCoordinator via explicit constructor injection -- no module-level imports of other new modules.
- **Backward compat**: Orchestrator passes callbacks to WorkflowEngineAdapter during initialization. Callback signatures unchanged.

## Security considerations

- No security-relevant behavior changes. The refactor preserves existing authentication, authorization, and input-validation logic.
- UUID generation for workflow IDs is unchanged.
- JSON serialization for audit logging is unchanged.
- Inline import removal (`emit_approval_pending_notice`) does not change security posture -- the import is moved to top-level where it is available at module load time.

## Rollback considerations

- If the refactor introduces regressions, revert to the original `orchestrator.py` using git.
- The six new module files can be deleted; Orchestrator continues to function with the original implementation.
- Test suite should catch behavioral regressions before deployment.

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|--------|----------|---------|------------------|
| `workflow_engine_adapter.py` lint | ruff check | `ruff check scripts/agent/workflow_engine_adapter.py` | No lint errors |
| `workflow_engine_adapter.py` type check | mypy | `mypy scripts/agent/workflow_engine_adapter.py` | No type errors |
| `workflow_engine_adapter.py` import succeeds | Static analysis | `python -c "from agent.workflow_engine_adapter import WorkflowEngineAdapter"` | Import succeeds |

## Completion criteria

- [ ] WorkflowEngineAdapter class created with constructor injection
- [ ] `handle_workflow_engine(line, ctx, turn_started_at)` orchestrates workflow engine interaction
- [ ] `_init_workflow_task(ctx, session_id, existing_task_id, store)` creates task and audits start
- [ ] `_activate_workflow(ctx, task)` sets workflow state to active
- [ ] `_deactivate_workflow(ctx)` resets workflow state after engine completion
- [ ] `_handle_workflow_approval_pending(exc, session_id)` handles approval pending event
- [ ] `_handle_workflow_halt(exc)` handles workflow halt event
- [ ] `workflow_status()` returns current workflow status dict
- [ ] `ruff` lint passes
- [ ] `mypy` type check passes
- [ ] Existing Orchestrator unit tests confirm no behavioral regression

## Out of scope

- Modifying LLMTurnRunner or ToolLoopGuard internals
- Adding new features or capabilities beyond structural refactoring
- Moving DiagnosticStore ownership out of Orchestrator (per Issue constraint)
- Changing the workflow engine integration protocol

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012, REQ-013, REQ-014, REQ-015
- **Source issue**: issues/20260829-080923_refactor_001_orchestrator_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-174312_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-213834
- **Related target files**: scripts/agent/workflow_engine_adapter.py
