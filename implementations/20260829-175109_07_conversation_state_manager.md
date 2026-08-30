# Implementation Procedure: scripts/agent/conversation_state_manager.py

## Goal

Create `conversation_state_manager.py` with the ConversationStateManager class owning `_handle_memory_injection`, `_handle_history_compression`, `_clear_previous_turn_ephemeral_messages`, `_sync_system_prompt`, `_append_user_message`, and related conversation history manipulation logic extracted from Orchestrator.

## Scope

- Create `scripts/agent/conversation_state_manager.py` only. No other source file is modified by this document.
- The ConversationStateManager class owns exactly one concern: conversation history manipulation.
- Methods moved from orchestrator.py lines 445, 466, 629, 642, 663.
- Class attribute `_EPHEMERAL_KEYS` moved here as a class attribute.

## Assumptions

- ConversationStateManager receives AgentContext via constructor injection (same as Orchestrator).
- Callbacks (`on_first_turn`, `on_turn_start`, `on_turn_end`, `on_error`) are passed through to ConversationStateManager rather than consumed directly by Orchestrator.
- Background task management (`_background_tasks`, `_discard_and_log`) remains in Orchestrator -- they bridge to BgTaskMonitor's `_discard_and_log` callback.
- `ToolLoopGuard` ownership remains shared between Orchestrator and LLMTurnRunner.
- `DiagnosticStore` ownership remains in Orchestrator.

## Design decisions

1. **ConversationStateManager owns conversation history manipulation**: The class encapsulates all methods related to conversation history state changes, including ephemeral message cleanup, system prompt synchronization, user message appending, memory injection, and history compression.
2. **Constructor injection for dependencies**: AgentContext, callbacks, and required services are injected via `__init__`. This enables independent instantiation and testing.
3. **No circular imports**: ConversationStateManager depends only on shared types (AgentContext, etc.) and never imports Orchestrator itself.
4. **Class attribute for _EPHEMERAL_KEYS**: Move the constant as a class attribute rather than instance attribute.

## Alternatives considered

1. **Merge ConversationStateManager + TurnCoordinator**: Would reduce the number of new files but violates the Single Responsibility Principle that motivated this refactor. Rejected per plan's design intent.
2. **Keep `_handle_memory_injection` and `_handle_history_compression` in Orchestrator**: Would reduce refactoring effort but leaves the file at > 700 lines. Rejected because it defeats the purpose of the refactor.
3. **Make ConversationStateManager a mixin or base class**: Would introduce inheritance complexity without benefit. Composition is simpler and more testable. Rejected.

## Implementation

### Target file

`scripts/agent/conversation_state_manager.py`

### Procedure

1. Create stub module with class definition and docstring.
2. Add imports: `asyncio`, `typing.Any`, `shared.logger.Logger`, `shared.types.LLMMessage`, `agent.context.AgentContext`, `agent.diagnostic_store.DiagnosticStore`, `agent.message_schema.validate_message`, `agent.mode_classification.classify_and_inject_mode`, `agent.output_tags.OutputTag`.
3. Define `ConversationStateManager` class with constructor accepting `ctx`, callbacks, and optional dependencies.
4. Move `_EPHEMERAL_KEYS` class attribute (orchestrator.py line 123).
5. Move `_handle_memory_injection` method (orchestrator.py line 445).
6. Move `_handle_history_compression` method (orchestrator.py line 466).
7. Move `_clear_previous_turn_ephemeral_messages` method (orchestrator.py line 629).
8. Move `_sync_system_prompt` method (orchestrator.py line 642).
9. Move `_append_user_message` method (orchestrator.py line 663).

### Method

The ConversationStateManager class structure:

```python
class ConversationStateManager:
    """Owns conversation history manipulation: ephemeral cleanup, system prompt sync, user message append, memory injection, history compression.

    Extracted from Orchestrator to isolate conversation lifecycle management.
    """

    _EPHEMERAL_KEYS: frozenset[str] = frozenset(
        {"_ephemeral", "_memory_injected", "_skill_ephemeral"}
    )

    def __init__(
        self,
        ctx: AgentContext,
        *,
        diagnostic_store: DiagnosticStore,
        tracer: Any = None,
        on_first_turn: Callable[[str], Any] | None = None,
        on_turn_start: Callable[[], None] | None = None,
        on_turn_end: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self._ctx = ctx
        self._diagnostic_store = diagnostic_store
        self._tracer = tracer
        self._on_first_turn = on_first_turn
        self._on_turn_start = on_turn_start
        self._on_turn_end = on_turn_end
        self._on_error = on_error

    def handle_memory_injection(self, line: str) -> None:
        """Retrieve relevant memory snippets and inject them into conversation history."""
        ...

    async def handle_history_compression(self) -> None:
        """Compress conversation history and replace messages if compression occurred."""
        ...

    def clear_previous_turn_ephemeral_messages(self) -> None:
        """Strip ephemeral/memory-injected system messages left over from the previous turn."""
        ...

    def sync_system_prompt(self) -> None:
        """Sync history[0] from ctx.conv.system_prompt_content before each turn."""
        ...

    async def append_user_message(self, line: str) -> None:
        """Append user message to history, sync system prompt, and increment turn counter."""
        ...
```

Key points:
- Public method names use snake_case without underscore prefix (cleaner API for Orchestrator delegation).
- `_EPHEMERAL_KEYS` is a class attribute (not instance attribute).
- `_append_user_message` references `self._background_tasks` and `self._discard_and_log` -- these remain in Orchestrator. The method body needs adjustment: the background task creation should be delegated back to Orchestrator after the user message is appended. Consider adding a separate `create_background_task` method or keeping the background task creation in Orchestrator.

### Details

Current state verification (adversarial check against `orchestrator.py`):

- **Methods confirmed for extraction**:
  - `_handle_memory_injection` (line 445): retrieve relevant memory snippets and inject them into conversation history
  - `_handle_history_compression` (line 466): compress conversation history and replace messages if compression occurred
  - `_clear_previous_turn_ephemeral_messages` (line 629): strip ephemeral/memory-injected system messages left over from the previous turn
  - `_sync_system_prompt` (line 642): sync history[0] from ctx.conv.system_prompt_content before each turn
  - `_append_user_message` (line 663): append user message to history, sync system prompt, and increment turn counter
- **Dependencies used by extracted methods**:
  - `uuid.uuid4()` -- standard library
  - `time.perf_counter()` -- standard library
  - `ctx.services_required.memory` -- AgentContext dependency
  - `ctx.services_required.hist_mgr.compress(...)` -- AgentContext dependency
  - `ctx.conv.history` -- AgentContext dependency
  - `ctx.conv.append_message(...)` -- AgentContext dependency
  - `ctx.session.replace_messages(...)` -- AgentContext dependency
  - `ctx.session.save("user", line)` -- AgentContext dependency
  - `validate_message(dict(msg))` -- message_schema dependency
  - `classify_and_inject_mode(line, ctx)` -- mode_classification dependency
  - `ctx.stats.stat_turns` -- AgentContext dependency
  - `asyncio.create_task(...)` -- standard library
  - `self._background_tasks.add(_task)` -- Orchestrator dependency (bridge)
  - `self._discard_and_log` -- Orchestrator dependency (bridge)
  - `OutputTag.WORKFLOW` -- output_tags dependency
  - `logger.info("LLM response: %s", result.answer)` -- logging dependency
  - `ctx.session.save("assistant", result.answer)` -- AgentContext dependency
  - `handle_llm_transport_error(e, ctx, self._diagnostic_store)` -- llm_transport_errors dependency
  - `TurnResult(action="fail", ...)` -- turn_result dependency

- **REQ-012 compliance**: `_EPHEMERAL_KEYS` constant moved to ConversationStateManager.

## Compatibility considerations

- **REQ-008**: All existing public method signatures preserved. ConversationStateManager's public methods have cleaner names (no underscore prefix) but identical behavior.
- **REQ-009**: Existing import paths (`from agent.orchestrator import Orchestrator`) continue to work. The Orchestrator class name and constructor signature are unchanged.
- **REQ-012**: `_EPHEMERAL_KEYS` constant moved to ConversationStateManager.

## Security considerations

- No security-relevant behavior changes. The refactor preserves existing authentication, authorization, and input-validation logic.
- Ephemeral key filtering (`_clear_previous_turn_ephemeral_messages`) continues to use `_EPHEMERAL_KEYS` from ConversationStateManager (REQ-012).
- System prompt validation via `validate_message` is preserved.

## Rollback considerations

- If the refactor introduces regressions, revert to the original `orchestrator.py` (764 lines) using git.
- The six new module files can be deleted; Orchestrator continues to function with the original implementation.
- Test suite (`test_orchestrator.py`, `test_orchestrator_bg_failure_threshold.py`, `test_orchestrator_integration.py`) should catch behavioral regressions before deployment.

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|--------|----------|---------|------------------|
| `conversation_state_manager.py` module load | Static analysis: import succeeds | `python -c "from agent.conversation_state_manager import ConversationStateManager"` | Import succeeds |
| `conversation_state_manager.py` no circular imports | Static analysis: no ImportError | `python -c "import agent.conversation_state_manager"` | No ImportError |
| `conversation_state_manager.py` conversation state | Unit test: instantiate and verify methods | `uv run pytest -k conversation_state_manager` | Tests pass |
| Full suite | Integration test | `uv run pytest tests/agent/test_orchestrator.py` | All orchestrator-related tests pass |
| New modules lint | ruff check | `ruff check scripts/agent/conversation_state_manager.py` | No lint errors |
| New modules type check | mypy | `mypy scripts/agent/conversation_state_manager.py` | No type errors |

## Completion criteria

- [ ] ConversationStateManager class has all five conversation history methods
- [ ] `handle_memory_injection(line: str) -> None` has identical signature and behavior
- [ ] `handle_history_compression() -> None` has identical signature and behavior
- [ ] `clear_previous_turn_ephemeral_messages() -> None` has identical signature and behavior
- [ ] `sync_system_prompt() -> None` has identical signature and behavior
- [ ] `append_user_message(line: str) -> None` has identical signature and behavior
- [ ] No circular imports between new modules
- [ ] Existing import paths (`from agent.orchestrator import Orchestrator`) continue to work
- [ ] `_EPHEMERAL_KEYS` constant owned by ConversationStateManager (REQ-012)
- [ ] `ruff` lint passes on this file
- [ ] `mypy` type check passes on this file
- [ ] Existing Orchestrator unit tests confirm no behavioral regression

## Out of scope

- Adding a second background task type
- Changing the `BG_FAILURE_THRESHOLD` value or making it configurable
- Modifying LLMTurnRunner or ToolLoopGuard internals
- Adding new features or capabilities beyond structural refactoring
- Moving `_tool_override` context manager here (belongs to Orchestrator)
- Moving `_call_on_*` callback helpers here (belong to LlmTurnExecutor per REQ-004)
- Moving `_build_turn_end_*` helpers here (belong to AuditEventEmitter per REQ-005, REQ-013)

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
- **Requirement ID**: REQ-006, REQ-012, REQ-014, REQ-015
- **Source issue**: issues/20260829-080923_refactor_001_orchestrator_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-175109_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-175109
- **Related target files**: scripts/agent/conversation_state_manager.py
