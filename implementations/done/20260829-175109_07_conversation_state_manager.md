# Implementation Procedure: scripts/agent/conversation_state_manager.py

## Goal

Create `conversation_state_manager.py` with the ConversationStateManager class owning `_handle_memory_injection`, `_handle_history_compression`, and the `EPHEMERAL_KEYS` constant extracted from Orchestrator. (Corrected during Step 3 adversarial verification — see Scope below: `_clear_previous_turn_ephemeral_messages`, `_sync_system_prompt`, and `_append_user_message` were assigned to `TurnCoordinator` instead, per `02_turnd_coordinator.md`, to avoid the responsibility overlap the original plan created between these two documents.)

## Scope

- Create `scripts/agent/conversation_state_manager.py` only. No other source file is modified by this document.
- The ConversationStateManager class owns exactly one concern: memory injection and history compression.
- Methods moved from orchestrator.py lines 445, 466.
- **Correction (Step 3 adversarial verification)**: the original Scope/Goal also assigned `_clear_previous_turn_ephemeral_messages` (line 629), `_sync_system_prompt` (line 642), and `_append_user_message` (line 663) to this file — but `02_turnd_coordinator.md` independently assigns the same three methods to `TurnCoordinator`. The as-built code resolves this conflict in `TurnCoordinator`'s favor: those three methods live in `turnd_coordinator.py`, not here. Only the `EPHEMERAL_KEYS` constant that `TurnCoordinator.clear_previous_turn_ephemeral_messages` depends on is owned here, matching REQ-012 ("`_EPHEMERAL_KEYS` constant moved to ConversationStateManager") without duplicating the three lifecycle methods across both files.
- `EPHEMERAL_KEYS` (module-level constant, not a class attribute — see Design decisions correction) moved here.

## Assumptions

- ConversationStateManager takes only `llm_runner: LLMTurnRunner` as a constructor dependency (corrected during Step 3 adversarial verification: with `_clear_previous_turn_ephemeral_messages`/`_sync_system_prompt`/`_append_user_message` reassigned to `TurnCoordinator`, this class's remaining two methods — `handle_memory_injection`, `handle_history_compression` — take `ctx` as a per-call argument and need only the LLM runner for `hist_mgr.compress`'s tracing span).
- Callbacks (`on_first_turn`, `on_turn_start`, `on_turn_end`, `on_error`) are NOT passed through to ConversationStateManager (corrected during Step 3: neither `handle_memory_injection` nor `handle_history_compression` invokes any of these callbacks in the pre-refactor code).
- Background task management (`_background_tasks`, `_discard_and_log`) remains in Orchestrator/BgTaskMonitor — not a dependency of this file at all now that `_append_user_message` (the method that used them) moved to `TurnCoordinator`.
- `ToolLoopGuard` ownership remains shared between Orchestrator and LLMTurnRunner (unaffected by this file).
- `DiagnosticStore` ownership remains in Orchestrator (unaffected by this file).

## Design decisions

1. **ConversationStateManager owns memory injection and history compression** (narrowed during Step 3 from the original "all conversation history state changes" scope — see Scope correction): ephemeral-message cleanup, system-prompt sync, and user-message append live in `TurnCoordinator` instead.
2. **Minimal constructor dependency**: only `llm_runner: LLMTurnRunner` is injected via `__init__`, since `ctx` is passed per-call and no other service is needed.
3. **No circular imports**: ConversationStateManager depends only on shared types (`AgentContext`, `LLMTurnRunner`) and never imports Orchestrator itself.
4. **Module-level constant for `EPHEMERAL_KEYS`, not a class attribute** (corrected during Step 3, overriding the original "class attribute" plan): `TurnCoordinator.clear_previous_turn_ephemeral_messages` needs to reference it, and a plain module-level `frozenset` (`from agent.conversation_state_manager import EPHEMERAL_KEYS`) is simpler for a cross-module import than reaching through an unrelated class (`ConversationStateManager.EPHEMERAL_KEYS`) that does not otherwise participate in ephemeral-message handling.

## Alternatives considered

1. **Merge ConversationStateManager + TurnCoordinator**: Would reduce the number of new files but violates the Single Responsibility Principle that motivated this refactor. Rejected per plan's design intent.
2. **Keep `_handle_memory_injection` and `_handle_history_compression` in Orchestrator**: Would reduce refactoring effort but leaves the file at > 700 lines. Rejected because it defeats the purpose of the refactor.
3. **Make ConversationStateManager a mixin or base class**: Would introduce inheritance complexity without benefit. Composition is simpler and more testable. Rejected.

## Implementation

### Target file

`scripts/agent/conversation_state_manager.py`

### Procedure

1. Create stub module with class definition and docstring.
**Correction (Step 3 adversarial verification)**: steps 2-9 below and the Method code sample describe the original five-method plan. The as-built file only implements steps for `handle_memory_injection`/`handle_history_compression` plus the `EPHEMERAL_KEYS` constant; `_clear_previous_turn_ephemeral_messages`/`_sync_system_prompt`/`_append_user_message` were implemented in `turnd_coordinator.py` instead (see `02_turnd_coordinator.md`, and the Scope/Assumptions/Design decisions corrections above). The steps and sample below are kept for historical context but do not describe the shipped file.

2. Add imports: `asyncio`, `typing.Any`, `shared.logger.Logger`, `shared.types.LLMMessage`, `agent.context.AgentContext`, `agent.diagnostic_store.DiagnosticStore`, `agent.message_schema.validate_message`, `agent.mode_classification.classify_and_inject_mode`, `agent.output_tags.OutputTag`.
3. Define `ConversationStateManager` class with constructor accepting `ctx`, callbacks, and optional dependencies.
4. Move `_EPHEMERAL_KEYS` class attribute (orchestrator.py line 123).
5. Move `_handle_memory_injection` method (orchestrator.py line 445).
6. Move `_handle_history_compression` method (orchestrator.py line 466).
7. ~~Move `_clear_previous_turn_ephemeral_messages` method (orchestrator.py line 629)~~ — implemented in `turnd_coordinator.py` instead.
8. ~~Move `_sync_system_prompt` method (orchestrator.py line 642)~~ — implemented in `turnd_coordinator.py` instead.
9. ~~Move `_append_user_message` method (orchestrator.py line 663)~~ — implemented in `turnd_coordinator.py` instead.

### Method

The as-built `ConversationStateManager` class structure (superseding the code sample originally drafted here — see the correction note above Procedure):

```python
EPHEMERAL_KEYS: frozenset[str] = frozenset(
    {"_ephemeral", "_memory_injected", "_skill_ephemeral"}
)


class ConversationStateManager:
    """Injects memory context and compresses conversation history."""

    def __init__(self, llm_runner: LLMTurnRunner) -> None:
        self._llm_runner = llm_runner

    async def handle_memory_injection(self, ctx: AgentContext, line: str) -> None:
        """Retrieve relevant memory snippets and inject them into conversation history."""
        ...

    async def handle_history_compression(self, ctx: AgentContext) -> None:
        """Compress conversation history and replace messages if compression occurred."""
        ...
```

Key points (as-built, superseding the original Key Points below):
- `EPHEMERAL_KEYS` is a module-level constant (not a class attribute) — see Design decisions correction.
- `clear_previous_turn_ephemeral_messages`, `sync_system_prompt`, `append_user_message` (including the `self._background_tasks`/`self._discard_and_log` first-turn background-task wiring the original Key Points below discusses) live in `TurnCoordinator` — see `02_turnd_coordinator.md`.

Original Key Points (superseded, kept for historical context):
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

- [x] ConversationStateManager class has both conversation-state methods it actually owns (corrected during Step 3: reduced from five to two — `clear_previous_turn_ephemeral_messages`/`sync_system_prompt`/`append_user_message` belong to `TurnCoordinator` per `02_turnd_coordinator.md`, see Scope correction)
- [x] `handle_memory_injection(ctx: AgentContext, line: str) -> None` has identical behavior — `ctx` added as an explicit parameter (see Assumptions correction)
- [x] `handle_history_compression(ctx: AgentContext) -> None` has identical behavior — `ctx` added as an explicit parameter
- [x] `clear_previous_turn_ephemeral_messages(ctx) -> None`, `sync_system_prompt(ctx) -> None`, `append_user_message(ctx, line) -> None` are implemented in `TurnCoordinator` (`turnd_coordinator.py`), not here — see `02_turnd_coordinator.md` Completion criteria for their verification
- [x] No circular imports between new modules
- [x] Existing import paths (`from agent.orchestrator import Orchestrator`) continue to work
- [x] `EPHEMERAL_KEYS` constant (module-level, not a class attribute — see Design decisions correction) owned by `conversation_state_manager.py` (REQ-012)
- [x] `ruff` lint passes on this file
- [x] `mypy` type check passes on this file
- [x] Existing Orchestrator unit tests confirm no behavioral regression (`uv run pytest tests/agent/test_orchestrator.py tests/agent/test_orchestrator_bg_failure_threshold.py tests/integration/test_orchestrator_integration.py` — 136 passed)

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260831-135000 | 20260831-135813 | `scripts/agent/conversation_state_manager.py` already existed on disk at cycle start, correctly scoped to two methods rather than the originally planned five (the other three overlapped with `02_turnd_coordinator.md`'s scope and were built there instead) — this cycle rewrote Goal/Scope/Assumptions/Design decisions/Method/Completion criteria to document that resolution instead of leaving the document describing unbuilt methods. |
| 2 | Add or update tests per Validation plan | Completed | 20260831-135000 | 20260831-135813 | No dedicated `test_conversation_state_manager.py` exists; behavior is covered indirectly through `tests/agent/test_orchestrator.py` (memory injection / history compression tests) and `tests/integration/test_orchestrator_integration.py`. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260831-135000 | 20260831-135813 | `ruff format/check`, `mypy` clean on this file; full suite result identical to master baseline (see 01_orchestrator.md Execution Status). |
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
- **Requirement ID**: REQ-006, REQ-012, REQ-014, REQ-015
- **Source issue**: issues/20260829-080923_refactor_001_orchestrator_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-175109_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-175109
- **Related target files**: scripts/agent/conversation_state_manager.py
