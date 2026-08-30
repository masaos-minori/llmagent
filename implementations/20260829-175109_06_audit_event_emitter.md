# Implementation Procedure: scripts/agent/audit_event_emitter.py

## Goal

Create `audit_event_emitter.py` with the AuditEventEmitter class owning `_build_turn_end_event`, `_build_turn_end_metadata`, `_build_turn_end_llm_stats`, and related audit event construction logic extracted from Orchestrator.

## Scope

- Create `scripts/agent/audit_event_emitter.py` only. No other source file is modified by this document.
- The AuditEventEmitter class owns exactly one concern: audit event construction and emission.
- Methods moved from orchestrator.py lines 607, 93, 104.
- Module-level functions `_mode_hint`, `_format_session_id` moved here as well.

## Assumptions

- AuditEventEmitter receives AgentContext via constructor injection (same as Orchestrator).
- Callbacks (`on_turn_start`, `on_turn_end`, `on_error`) are passed through to AuditEventEmitter rather than consumed directly by Orchestrator.
- `ToolLoopGuard` ownership remains shared between Orchestrator and LLMTurnRunner.
- `DiagnosticStore` ownership remains in Orchestrator.

## Design decisions

1. **AuditEventEmitter owns audit event construction and emission**: The class encapsulates all methods related to building and emitting audit events, including turn_end metadata and LLM stats.
2. **Constructor injection for dependencies**: AgentContext, callbacks, and required services are injected via `__init__`. This enables independent instantiation and testing.
3. **No circular imports**: AuditEventEmitter depends only on shared types (AgentContext, etc.) and never imports Orchestrator itself.
4. **Module-level function extraction**: `_mode_hint`, `_format_session_id`, `_build_turn_end_metadata`, `_build_turn_end_llm_stats` are moved as module-level functions (not class methods) because they don't require instance state.

## Alternatives considered

1. **Merge AuditEventEmitter + TurnCoordinator**: Would reduce the number of new files but violates the Single Responsibility Principle that motivated this refactor. Rejected per plan's design intent.
2. **Keep `_build_turn_end_event` in Orchestrator**: Would reduce refactoring effort but leaves the file at > 700 lines. Rejected because it defeats the purpose of the refactor.
3. **Make AuditEventEmitter a mixin or base class**: Would introduce inheritance complexity without benefit. Composition is simpler and more testable. Rejected.

## Implementation

### Target file

`scripts/agent/audit_event_emitter.py`

### Procedure

1. Create stub module with class definition and docstring.
2. Add imports: `time`, `typing.Any`, `shared.json_utils.dumps as _json_dumps`, `shared.logger.Logger`, `shared.types.LLMMessage`, `agent.context.AgentContext`, `agent.diagnostic_store.DiagnosticStore`, `agent.output_tags.OutputTag`, `agent.tool_audit.audit_approval_requested`, `agent.tool_audit.audit_stage_completed`, `agent.tool_audit.audit_workflow_start`.
3. Define `AuditEventEmitter` class with constructor accepting `ctx`, callbacks, and optional dependencies.
4. Move `_build_turn_end_event` method (orchestrator.py line 607).
5. Move `_build_turn_end_metadata` function (orchestrator.py line 93).
6. Move `_build_turn_end_llm_stats` function (orchestrator.py line 104).
7. Move `_mode_hint` function (orchestrator.py line 79).
8. Move `_format_session_id` function (orchestrator.py line 88).

### Method

The AuditEventEmitter class structure:

```python
def _mode_hint(ctx: AgentContext) -> str:
    """Return mode hint string for audit logging."""
    ...

def _format_session_id(session_id: str | None) -> str:
    """Format session ID for audit logging."""
    ...

def _build_turn_end_metadata(ctx: AgentContext) -> dict[str, Any]:
    """Build turn_end audit log metadata dict."""
    ...

def _build_turn_end_llm_stats(llm: Any) -> dict[str, Any]:
    """Build turn_end audit log LLM stats dict."""
    ...

class AuditEventEmitter:
    """Owns audit event construction and emission: turn_end events, metadata, LLM stats.

    Extracted from Orchestrator to isolate audit lifecycle management.
    """

    def __init__(
        self,
        ctx: AgentContext,
        *,
        diagnostic_store: DiagnosticStore,
        tracer: Any = None,
    ) -> None:
        self._ctx = ctx
        self._diagnostic_store = diagnostic_store
        self._tracer = tracer

    def build_turn_end_event(
        self,
        elapsed_ms: float,
        error_kind: str | None,
        task_id: str | None,
        is_partial: bool = False,
    ) -> dict[str, int | float | str | None]:
        """Build turn_end audit log event dict."""
        ...
```

Key points:
- Public method names use snake_case without underscore prefix (cleaner API for Orchestrator delegation).
- Module-level functions (`_mode_hint`, `_format_session_id`, `_build_turn_end_metadata`, `_build_turn_end_llm_stats`) are NOT class methods -- they don't require instance state.
- `_build_turn_end_event` is a class method because it uses `self._ctx` for metadata.

### Details

Current state verification (adversarial check against `orchestrator.py`):

- **Methods confirmed for extraction**:
  - `_build_turn_end_event` (line 607): builds turn_end audit log event dict
  - `_build_turn_end_metadata` (line 93): builds turn_end audit log metadata dict
  - `_build_turn_end_llm_stats` (line 104): builds turn_end audit log LLM stats dict
  - `_mode_hint` (line 79): returns mode hint string for audit logging
  - `_format_session_id` (line 88): formats session ID for audit logging
- **Dependencies used by extracted methods**:
  - `uuid.uuid4()` -- standard library
  - `time.time()` -- standard library
  - `ctx.turn.current_turn_id` -- AgentContext dependency
  - `ctx.session.session_id` -- AgentContext dependency
  - `ctx.stats.stat_input_tokens` -- AgentContext dependency
  - `ctx.stats.stat_output_tokens` -- AgentContext dependency
  - `ctx.services_required.llm` -- AgentContext dependency
  - `OutputTag.WORKFLOW` -- output_tags dependency
  - `logger.info("LLM response: %s", result.answer)` -- logging dependency
  - `ctx.session.save("assistant", result.answer)` -- AgentContext dependency
  - `handle_llm_transport_error(e, ctx, self._diagnostic_store)` -- llm_transport_errors dependency
  - `TurnResult(action="fail", ...)` -- turn_result dependency

- **REQ-013 compliance**: `_build_turn_end_*` helper functions moved to AuditEventEmitter.

## Compatibility considerations

- **REQ-008**: All existing public method signatures preserved. AuditEventEmitter's public methods have cleaner names (no underscore prefix) but identical behavior.
- **REQ-009**: Existing import paths (`from agent.orchestrator import Orchestrator`) continue to work. The Orchestrator class name and constructor signature are unchanged.
- **REQ-013**: `_build_turn_end_*` helper functions moved to AuditEventEmitter.

## Security considerations

- No security-relevant behavior changes. The refactor preserves existing authentication, authorization, and input-validation logic.
- Audit event construction via `audit_approval_requested`, `audit_stage_completed`, `audit_workflow_start` is preserved.

## Rollback considerations

- If the refactor introduces regressions, revert to the original `orchestrator.py` (764 lines) using git.
- The six new module files can be deleted; Orchestrator continues to function with the original implementation.
- Test suite (`test_orchestrator.py`, `test_orchestrator_bg_failure_threshold.py`, `test_orchestrator_integration.py`) should catch behavioral regressions before deployment.

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|--------|----------|---------|------------------|
| `audit_event_emitter.py` module load | Static analysis: import succeeds | `python -c "from agent.audit_event_emitter import AuditEventEmitter"` | Import succeeds |
| `audit_event_emitter.py` no circular imports | Static analysis: no ImportError | `python -c "import agent.audit_event_emitter"` | No ImportError |
| `audit_event_emitter.py` audit events | Unit test: instantiate and verify methods | `uv run pytest -k audit_event_emitter` | Tests pass |
| Full suite | Integration test | `uv run pytest tests/agent/test_orchestrator.py` | All orchestrator-related tests pass |
| New modules lint | ruff check | `ruff check scripts/agent/audit_event_emitter.py` | No lint errors |
| New modules type check | mypy | `mypy scripts/agent/audit_event_emitter.py` | No type errors |

## Completion criteria

- [ ] AuditEventEmitter class has `_build_turn_end_event` method
- [ ] Module-level functions `_mode_hint`, `_format_session_id`, `_build_turn_end_metadata`, `_build_turn_end_llm_stats` exist
- [ ] `build_turn_end_event(elapsed_ms, error_kind, task_id, is_partial) -> dict[...]` has identical signature and behavior
- [ ] No circular imports between new modules
- [ ] Existing import paths (`from agent.orchestrator import Orchestrator`) continue to work
- [ ] `_build_turn_end_*` helper functions owned by AuditEventEmitter (REQ-013)
- [ ] `ruff` lint passes on this file
- [ ] `mypy` type check passes on this file
- [ ] Existing Orchestrator unit tests confirm no behavioral regression

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
- **Requirement ID**: REQ-005, REQ-013, REQ-014, REQ-015
- **Source issue**: issues/20260829-080923_refactor_001_orchestrator_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-175109_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-175109
- **Related target files**: scripts/agent/audit_event_emitter.py
