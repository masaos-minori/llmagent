# Implementation Procedure: scripts/agent/workflow_engine_adapter.py

## Goal

Create `workflow_engine_adapter.py` with the WorkflowEngineAdapter class owning `_handle_workflow_engine`, `_init_workflow_task`, `_activate_workflow`, `_deactivate_workflow`, and `_handle_workflow_*` methods extracted from Orchestrator.

## Scope

- Create `scripts/agent/workflow_engine_adapter.py` only. No other source file is modified by this document.
- The WorkflowEngineAdapter class owns exactly one concern: workflow engine integration.
- Methods moved from orchestrator.py lines 241, 318, 362, 400, 411, 415.

## Assumptions

- WorkflowEngineAdapter receives `AgentContext` as a per-call method argument rather than via constructor injection (corrected during Step 3 adversarial verification: the constructor instead receives `workflow_def`, `state_store`, `tracer`, and the `process_turn`/`handle_turn_end`/`on_error` callables, since `ctx` is already available at every call site inside `Orchestrator.handle_turn`).
- The inline import `from agent.tool_output import emit_approval_pending_notice` in `_handle_workflow_approval_pending` is replaced by a top-level import in WorkflowEngineAdapter.
- `_format_session_id` constant is moved to AuditEventEmitter (REQ-013).
- `BG_FAILURE_THRESHOLD` constant scope is limited to first-turn session-title-generation; do not generalize it.
- `ToolLoopGuard` remains shared between Orchestrator and LLMTurnRunner.
- `DiagnosticStore` ownership remains in Orchestrator.

## Design decisions

1. **WorkflowEngineAdapter owns workflow engine integration**: The class encapsulates all methods related to workflow engine execution, including task creation, activation/deactivation, and error handling.
2. **Constructor injection for dependencies**: AgentContext, StateStore, and required services are injected via `__init__`. This enables independent instantiation and testing.
3. **No circular imports**: WorkflowEngineAdapter depends only on shared types (AgentContext, TaskRecord, etc.) and never imports Orchestrator itself.
4. **Inline import removal**: Replace `from agent.tool_output import emit_approval_pending_notice` with a top-level import at module level.

## Alternatives considered

1. **Merge WorkflowEngineAdapter + TurnCoordinator**: Would reduce the number of new files but violates the Single Responsibility Principle that motivated this refactor. Rejected per plan's design intent.
2. **Keep `_handle_workflow_engine` in Orchestrator**: Would reduce refactoring effort but leaves the file at > 700 lines. Rejected because it defeats the purpose of the refactor.
3. **Make WorkflowEngineAdapter a mixin or base class**: Would introduce inheritance complexity without benefit. Composition is simpler and more testable. Rejected.

## Implementation

### Target file

`scripts/agent/workflow_engine_adapter.py`

### Procedure

1. Create stub module with class definition and docstring.
2. Add imports: `uuid`, `time`, `logging`, `typing.Any`, `shared.json_utils.dumps as _json_dumps`, `shared.types.LLMMessage`, `agent.context.AgentContext`, `agent.diagnostic_store.DiagnosticStore`, `agent.output_tags.OutputTag`, `agent.workflow.StateStore`, `agent.workflow.TaskRecord`, `agent.workflow.WorkflowDef`, `agent.workflow.WorkflowEngine`, `agent.workflow.WorkflowHaltError`, `agent.workflow.WorkflowTimeoutError`, `agent.workflow.WorkflowPendingApprovalError`, `agent.workflow.WorkflowLoader`, `agent.workflow.WorkflowLoadError`, `agent.workflow.task_ops.create_task`, `agent.workflow.task_ops.get_task_by_id`, `agent.workflow.workflow_loader.WORKFLOWS_DIR`, `agent.tool_audit.audit_stage_completed`, `agent.tool_audit.audit_workflow_start`.
3. Define `WorkflowEngineAdapter` class with constructor accepting `ctx`, `store`, and optional dependencies.
4. Move `_handle_workflow_engine` method (orchestrator.py line 241).
5. Move `_init_workflow_task` method (orchestrator.py line 318).
6. Move `_activate_workflow` method (orchestrator.py line 362).
7. Move `_deactivate_workflow` method (orchestrator.py line 400).
8. Move `_handle_workflow_approval_pending` method (orchestrator.py line 411).
9. Move `_handle_workflow_halt` method (orchestrator.py line 415).

### Method

The WorkflowEngineAdapter class structure:

```python
class WorkflowEngineAdapter:
    """Owns workflow engine integration: engine execution, task lifecycle, error handling.

    Extracted from Orchestrator to isolate workflow engine state machine logic.
    """

    def __init__(
        self,
        ctx: AgentContext,
        *,
        workflow_def: WorkflowDef,
        tracer: Any = None,
    ) -> None:
        self._ctx = ctx
        self._workflow_def = workflow_def
        self._tracer = tracer

    async def handle_workflow_engine(
        self, line: str, ctx: AgentContext, turn_started_at: float
    ) -> None:
        """Execute a turn through the workflow engine."""
        ...

    def _init_workflow_task(
        self,
        ctx: AgentContext,
        session_id: str,
        existing_task_id: str | None = None,
        store: StateStore | None = None,
    ) -> tuple[str, TaskRecord]:
        """Create a workflow task and audit its start."""
        ...

    def _activate_workflow(self, ctx: AgentContext, task: TaskRecord) -> None:
        """Activate workflow tracking for a task."""
        ...

    def _deactivate_workflow(self, ctx: AgentContext) -> None:
        """Deactivate workflow tracking for the current task."""
        ...

    def _handle_workflow_approval_pending(
        self, exc: WorkflowPendingApprovalError, session_id: str
    ) -> None:
        """Handle workflow pending approval error."""
        ...

    def _handle_workflow_halt(self, exc: WorkflowHaltError | WorkflowTimeoutError) -> None:
        """Handle workflow halt/timeout error."""
        ...
```

Key points:
- Public method names use snake_case without underscore prefix (cleaner API for Orchestrator delegation).
- Inline import removed from `_handle_workflow_approval_pending`: replace `from agent.tool_output import emit_approval_pending_notice` with top-level import.
- `_format_session_id` is called in `_handle_workflow_engine` -- this must be changed to use the constant from AuditEventEmitter (REQ-013).

### Details

Current state verification (adversarial check against `orchestrator.py`):

- **Methods confirmed for extraction**:
  - `_handle_workflow_engine` (line 241): executes turn through workflow engine
  - `_init_workflow_task` (line 318): creates workflow task and audits its start
  - `_activate_workflow` (line 362): activates workflow tracking for a task
  - `_deactivate_workflow` (line 400): deactivates workflow tracking for the current task
  - `_handle_workflow_approval_pending` (line 411): handles workflow pending approval error
  - `_handle_workflow_halt` (line 415): handles workflow halt/timeout error

- **Dependencies used by extracted methods**:
  - `uuid.uuid4()` -- standard library, no import change
  - `time.perf_counter()` -- standard library
  - `_format_session_id(ctx.session.session_id)` -- REQ-013: moved to AuditEventEmitter, need to reference the constant there
  - `_json_dumps(...)` -- imported from `shared.json_utils`
  - `self._state_store.recover_stale_attempts(...)` -- StateStore dependency
  - `self._state_store.get_connection()` -- StateStore dependency
  - `create_task(store._db, ...)` -- workflow.task_ops dependency
  - `get_task_by_id(store._db, ...)` -- workflow.task_ops dependency
  - `audit_approval_requested(ctx, task.task_id, ...)` -- tool_audit dependency
  - `audit_stage_completed(ctx, task.task_id, "execute", ...)` -- tool_audit dependency
  - `audit_workflow_start(ctx, task.task_id, ...)` -- tool_audit dependency
  - `emit_approval_pending_notice(...)` -- REQ-011: inline import removed, move to top-level import
  - `OutputTag.WORKFLOW` -- output_tags dependency
  - `WORKFLOWS_DIR / 'default.json'` -- workflow_loader dependency

- **REQ-011 compliance**: Inline import `from agent.tool_output import emit_approval_pending_notice` in `_handle_workflow_approval_pending` is replaced by a top-level import at module level.

## Compatibility considerations

- **REQ-008**: All existing public method signatures preserved. WorkflowEngineAdapter's public methods have cleaner names (no underscore prefix) but identical behavior.
- **REQ-009**: Existing import paths (`from agent.orchestrator import Orchestrator`) continue to work. The Orchestrator class name and constructor signature are unchanged.
- **REQ-011**: Inline import removed from `_handle_workflow_approval_pending`; moved to top-level import in WorkflowEngineAdapter.
- **REQ-013**: `_format_session_id` constant moved to AuditEventEmitter; referenced here instead.

## Security considerations

- No security-relevant behavior changes. The refactor preserves existing authentication, authorization, and input-validation logic.
- Inline import removal (`emit_approval_pending_notice`) does not change security posture -- the import is moved to top-level where it is available at module load time.

## Rollback considerations

- If the refactor introduces regressions, revert to the original `orchestrator.py` (764 lines) using git.
- The six new module files can be deleted; Orchestrator continues to function with the original implementation.
- Test suite (`test_orchestrator.py`, `test_orchestrator_bg_failure_threshold.py`, `test_orchestrator_integration.py`) should catch behavioral regressions before deployment.

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|--------|----------|---------|------------------|
| `workflow_engine_adapter.py` module load | Static analysis: import succeeds | `python -c "from agent.workflow_engine_adapter import WorkflowEngineAdapter"` | Import succeeds |
| `workflow_engine_adapter.py` no circular imports | Static analysis: no ImportError | `python -c "import agent.workflow_engine_adapter"` | No ImportError |
| `workflow_engine_adapter.py` workflow engine | Unit test: instantiate and verify methods | `uv run pytest -k workflow_engine_adapter` | Tests pass |
| Full suite | Integration test | `uv run pytest tests/agent/test_orchestrator.py` | All orchestrator-related tests pass |
| New modules lint | ruff check | `ruff check scripts/agent/workflow_engine_adapter.py` | No lint errors |
| New modules type check | mypy | `mypy scripts/agent/workflow_engine_adapter.py` | No type errors |

## Completion criteria

- [x] WorkflowEngineAdapter class has all six workflow engine methods (per Key Points, exposed without the underscore prefix used in Orchestrator's pre-refactor private methods: `init_workflow_task`, `activate_workflow`, `deactivate_workflow`, `handle_workflow_approval_pending`, `handle_workflow_halt`, plus `handle_workflow_engine`)
- [x] `handle_workflow_engine(line, ctx, turn_started_at) -> None` has identical signature and behavior
- [x] `init_workflow_task(ctx, session_id, existing_task_id, store) -> tuple[str, TaskRecord]` has identical behavior (renamed from `_init_workflow_task` per Key Points; Orchestrator keeps a `_init_workflow_task` delegating wrapper for backward compatibility with tests)
- [x] `activate_workflow(ctx, task) -> None` has identical behavior (renamed from `_activate_workflow`; Orchestrator keeps a `_activate_workflow` delegating wrapper — added during Step 3 adversarial verification after `rg` found `test_orchestrator.py` patches it directly)
- [x] `deactivate_workflow(ctx) -> None` has identical behavior (renamed from `_deactivate_workflow`; same wrapper situation as above)
- [x] `handle_workflow_approval_pending(ctx, exc, session_id) -> None` has identical behavior (renamed; `ctx` added as an explicit parameter per the Assumptions correction)
- [x] `handle_workflow_halt(ctx, exc) -> None` has identical behavior (renamed; `ctx` added as an explicit parameter)
- [x] No circular imports between new modules
- [x] Existing import paths (`from agent.orchestrator import Orchestrator`) continue to work
- [x] Inline import removed from `handle_workflow_approval_pending` (REQ-011) — `from agent.tool_output import emit_approval_pending_notice` is now a top-level import in `workflow_engine_adapter.py`
- [x] `_format_session_id` function owned by `audit_event_emitter.py` (not duplicated here — imported by `workflow_engine_adapter.py`)
- [x] `ruff` lint passes on this file (one unjustified `# noqa: B101` suppression found and fixed per `tools/check_suppression_justification.py` during this cycle)
- [x] `mypy` type check passes on this file
- [x] Existing Orchestrator unit tests confirm no behavioral regression (`uv run pytest tests/agent/test_orchestrator.py tests/agent/test_orchestrator_bg_failure_threshold.py tests/integration/test_orchestrator_integration.py` — 136 passed)

## Out of scope

- Adding a second background task type
- Changing the `BG_FAILURE_THRESHOLD` value or making it configurable
- Modifying LLMTurnRunner or ToolLoopGuard internals
- Adding new features or capabilities beyond structural refactoring
- Moving `_tool_override` context manager here (belongs to Orchestrator)
- Moving `_clear_previous_turn_ephemeral_messages` here (belongs to TurnCoordinator per REQ-002)
- Moving `_handle_memory_injection` here (belongs to ConversationStateManager per REQ-006)
- Moving `_handle_history_compression` here (belongs to ConversationStateManager per REQ-006)
- Moving `_call_on_*` callback helpers here (belong to LlmTurnExecutor per REQ-004)
- Moving `_build_turn_end_*` helpers here (belong to AuditEventEmitter per REQ-005, REQ-013)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260831-135000 | 20260831-135813 | `scripts/agent/workflow_engine_adapter.py` already existed on disk at cycle start; this cycle fixed an unjustified `# noqa: B101` suppression (missing em-dash justification per `tools/check_suppression_justification.py`) and corrected the constructor-injection Assumption to match the actual per-call `ctx` parameter design. |
| 2 | Add or update tests per Validation plan | Completed | 20260831-135000 | 20260831-135813 | No dedicated `test_workflow_engine_adapter.py` exists; behavior is covered indirectly through `tests/agent/test_orchestrator.py` and `tests/integration/test_orchestrator_integration.py`, whose mock patch targets (`agent.workflow_engine_adapter.create_task`/`audit_workflow_start`/`WorkflowEngine`/`get_task_by_id`, `orch._workflow_adapter.init_workflow_task`/`activate_workflow`/`deactivate_workflow`/`_process_turn`, `orch._workflow_adapter._workflow_def`/`_state_store`) were retargeted from stale `agent.orchestrator.*` references and instance-attribute mocks during this cycle. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260831-135000 | 20260831-135813 | `ruff format/check`, `mypy`, and `bandit` clean on this file after the suppression fix; full suite result identical to master baseline (see 01_orchestrator.md Execution Status). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260831-135000 | 20260831-135813 | N/A: no `docs/00_index.md` task-scope row references this file's symbols by name. |

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
- **Requirement ID**: REQ-003, REQ-011, REQ-013, REQ-014, REQ-015
- **Source issue**: issues/20260829-080923_refactor_001_orchestrator_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-175109_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-175109
- **Related target files**: scripts/agent/workflow_engine_adapter.py
