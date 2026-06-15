# Implementation Plan: Orchestrator Integration (Step 7)

## Goal

Integrate `WorkflowEngine` into `agent/orchestrator.py` with minimal changes to existing turn processing logic.

## Scope

**In:**
- `scripts/agent/orchestrator.py`: Add WorkflowEngine reference, wrap `handle_turn()` with workflow execution

**Out:**
- Stage handler implementations (plan/execute/verify/retry are existing methods, refactored minimally)
- New config files (Step 2)
- DB schema (Step 1)

## Assumptions

1. `WorkflowEngine` wraps the existing turn flow without modifying internal stage logic.
2. Integration point is at the top of `handle_turn()` — wrap with workflow, delegate to existing methods.
3. Task ID = `f"turn-{ctx.session.session_id}-{ctx.turn.current_turn_id}"`.
4. Existing tests must pass; new tests added for workflow integration paths.

## Implementation

### Target File

| File | Change Type |
|---|---|
| `scripts/agent/orchestrator.py` | Modify (minimal) |

### Procedure

#### Update `scripts/agent/orchestrator.py`

Add imports at top:
```python
from agent.workflow.models import TaskRecord, TaskStatus, WorkflowStage
from agent.workflow.state_store import StateStore
from agent.workflow.workflow_engine import WorkflowEngine
from agent.workflow.workflow_loader import load_workflow, WorkflowLoadError
```

Add to `__init__` or `build()` method:
```python
class Orchestrator:
    def __init__(self, ctx, ...):
        # ... existing init ...
        self._workflow_store = StateStore()
        self._workflow_engine: WorkflowEngine | None = None

        try:
            wf_def = load_workflow("default")
            self._workflow_engine = WorkflowEngine(wf_def, self._workflow_store)
        except WorkflowLoadError as e:
            logger.warning("Workflow loading failed, running without workflow engine: %s", e)
```

Wrap `handle_turn()` (or `_run_turn()`) with workflow execution:
```python
async def _run_turn(self, user_message: str) -> None:
    """Run a single turn with optional workflow wrapping."""
    if self._workflow_engine is None:
        # Fallback to existing logic without workflow
        await self._run_turn_no_workflow(user_message)
        return

    task_id = f"turn-{self.ctx.session.session_id or 0}-{self.ctx.turn.current_turn_id or 0}"
    task_version = "1.0"

    task = TaskRecord(
        task_id=task_id,
        session_id=self.ctx.session.session_id or 0,
        turn_number=self.ctx.turn.current_turn_id or 0,
        workflow_version=task_version,
    )

    handlers = {
        "plan": self._handle_plan_stage,
        "execute": self._handle_execute_stage,
        "verify": self._handle_verify_stage,
        "retry": self._handle_retry_stage,
    }

    result = await self._workflow_engine.run(
        task=task,
        handlers=handlers,
        context={"user_message": user_message},
    )

    if result.status == TaskStatus.FAILED:
        logger.error("Turn %s failed at stage %s: %s", task_id, result.failed_stage, result.error_message)
    elif result.status == TaskStatus.HALTED:
        logger.warning("Turn %s halted: %s", task_id, result.error_message)
```

Extract existing logic into stage handlers:
```python
async def _handle_plan_stage(self, task_id: str, context: dict) -> Any:
    """Plan stage: memory injection + user message append."""
    # Existing _handle_memory_injection() and _handle_note_injection() logic
    # ... (move existing code here)
    return None

async def _handle_execute_stage(self, task_id: str, context: dict) -> Any:
    """Execute stage: LLM call + tool loop."""
    # Existing _handle_llm_turn() logic
    # ... (move existing code here)
    return None

async def _handle_verify_stage(self, task_id: str, context: dict) -> Any:
    """Verify stage: history compression + turn end."""
    # Existing _handle_history_compression() and _handle_turn_end() logic
    # ... (move existing code here)
    return None

async def _handle_retry_stage(self, task_id: str, context: dict) -> Any:
    """Retry stage: transport error handling."""
    # Existing _handle_llm_transport_error() logic
    # ... (move existing code here)
    return None
```

### Details

- Workflow engine is optional: if loading fails, fall back to existing `_run_turn_no_workflow()` path
- Stage handlers are thin wrappers around existing methods to minimize refactoring
- Task ID format: `turn-{session_id}-{turn_number}` for uniqueness and traceability
- No changes to existing method signatures; extracted logic preserved in new handlers
- `ctx.session.session_id` and `ctx.turn.current_turn_id` accessed safely with `or 0` defaults

## Validation Plan

| Check | Tool | Target |
|---|---|---|
| Type check | `uv run mypy scripts/agent/orchestrator.py` | no new errors |
| Import layer | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Existing tests | `uv run pytest tests/test_orchestrator*.py -v` | all pass (no regression) |
| Workflow enabled | Normal turn with workflow loaded | task created in workflow.sqlite, stages recorded |
| Workflow disabled | Workflow file missing | fallback to `_run_turn_no_workflow()`, no crash |
| Stage failure | Mock handler raises | task status=FAILED, error logged |
