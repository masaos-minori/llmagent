# Implementation Procedure: scripts/agent/conversation_state_manager.py

## Goal

Create `conversation_state_manager.py` as a new module containing the ConversationStateManager class, which encapsulates the conversation history manipulation logic currently scattered across Orchestrator's `_clear_previous_turn_ephemeral_messages`, `_sync_system_prompt`, `_append_user_message`, `_handle_memory_injection`, and `_handle_history_compression` methods, plus the `_EPHEMERAL_KEYS` class attribute.

## Scope

- Create `scripts/agent/conversation_state_manager.py` only. No other source file is modified by this document.
- The ConversationStateManager class receives dependencies via constructor injection.
- Orchestrator will forward its conversation-state callbacks to ConversationStateManager after this file exists.

## Assumptions

- ConversationStateManager needs access to AgentContext, on_first_turn callback, and background task management.
- The `_EPHEMERAL_KEYS` frozenset is moved to ConversationStateManager as a class attribute.
- The `_tool_override` context manager remains in Orchestrator (it modifies ctx.cfg.tool.allowed_tools directly).
- The `_discard_and_log` callback is moved to BgTaskMonitor (not ConversationStateManager).

## Design decisions

1. **ConversationStateManager owns conversation history manipulation**: All conversation history operations move here. This includes ephemeral message stripping, system prompt syncing, user message appending, memory injection, and history compression.
2. **Dependency injection**: ConversationStateManager receives AgentContext, on_first_turn callback, and background task set via constructor.
3. **Class attribute pattern**: `_EPHEMERAL_KEYS` becomes a class attribute on ConversationStateManager.
4. **Delegation pattern**: ConversationStateManager delegates event construction to AuditEventEmitter and background task monitoring to BgTaskMonitor.

## Alternatives considered

1. **Keep conversation state methods in Orchestrator**: Would reduce refactoring effort but leaves Orchestrator with > 700 lines. Rejected.
2. **Merge ConversationStateManager into WorkflowEngineAdapter**: Would violate separation of concerns -- conversation history is orthogonal to workflow engine integration. Rejected per plan intent.
3. **Make ConversationStateManager a mixin**: Would introduce inheritance complexity without benefit. Composition is simpler. Rejected.

## Implementation

### Target file

`scripts/agent/conversation_state_manager.py`

### Procedure

1. Create `scripts/agent/conversation_state_manager.py` from scratch.
2. Define `ConversationStateManager` class with constructor injection.
3. Implement `_EPHEMERAL_KEYS` class attribute: frozenset of ephemeral message keys.
4. Implement `__init__` method: receive AgentContext, on_first_turn callback, background task set.
5. Implement `_clear_previous_turn_ephemeral_messages()` method: strip ephemeral messages from history.
6. Implement `_sync_system_prompt()` method: sync system prompt from ctx.conv.system_prompt_content.
7. Implement `_append_user_message(line)` method: append user message, sync system prompt, increment turn counter.
8. Implement `_handle_memory_injection(line)` method: retrieve memory snippets and inject into history.
9. Implement `_handle_history_compression()` method: compress conversation history.

### Method

```python
"""scripts/agent/conversation_state_manager.py

ConversationStateManager: conversation history manipulation.

Encapsulates:
  - Stripping ephemeral messages from history
  - Syncing system prompts
  - Appending user messages
  - Injecting memory snippets
  - Compressing conversation history
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from agent.message_schema import validate_message
from shared.types import LLMMessage

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

class ConversationStateManager:
    """Manages conversation history manipulation for one agent turn.

    Receives dependencies via constructor injection. Does NOT own
    DiagnosticStore or ToolLoopGuard (per Issue constraint).
    """

    # Ephemeral message keys used to filter out temporary system messages
    # from conversation history. These keys indicate messages that were
    # injected during a previous turn and should be stripped before the
    # current turn's own injections begin.
    _EPHEMERAL_KEYS: frozenset[str] = frozenset(
        {"_ephemeral", "_memory_injected", "_skill_ephemeral"}
    )

    def __init__(
        self,
        ctx: AgentContext,
        *,
        on_first_turn: Any | None = None,
        background_tasks: set[asyncio.Task[object]] | None = None,
        discard_callback: Any | None = None,
    ) -> None:
        self._ctx = ctx
        self._on_first_turn = on_first_turn
        self._background_tasks = background_tasks or set()
        self._discard_callback = discard_callback

    def clear_previous_turn_ephemeral_messages(self) -> None:
        """Strip ephemeral/memory-injected system messages left over from the
        previous turn. Must run before this turn's own injections
        (_handle_memory_injection, classify_and_inject_mode) so it never
        strips content just added for the current turn.
        """
        ctx = self._ctx
        ctx.conv.history = [
            m
            for m in ctx.conv.history
            if not any(k in self._EPHEMERAL_KEYS for k in m.keys())
        ]

    def sync_system_prompt(self) -> None:
        """Sync history[0] from ctx.conv.system_prompt_content before each turn."""
        ctx = self._ctx
        if not ctx.conv.system_prompt_content:
            return
        if ctx.conv.history and ctx.conv.history[0]["role"] == "system":
            ctx.conv.history[0]["content"] = ctx.conv.system_prompt_content
        else:
            msg: LLMMessage = {
                "role": "system",
                "content": ctx.conv.system_prompt_content,
            }
            result = validate_message(dict(msg))
            if not result.success:
                logger.error(
                    "Dropping system prompt sync message that failed validation: %s",
                    result.reason,
                )
                return
            ctx.conv.history.insert(0, msg)

    async def append_user_message(self, line: str) -> None:
        """Append user message to history, sync system prompt, and increment turn counter."""
        ctx = self._ctx
        self.sync_system_prompt()
        await ctx.conv.append_message({"role": "user", "content": line})
        ctx.stats.stat_turns += 1
        if ctx.stats.stat_turns == 1 and self._on_first_turn is not None:
            _task = asyncio.create_task(
                self._on_first_turn(line),
                name=getattr(self._on_first_turn, "__name__", "unknown_bg_task"),
            )
            self._background_tasks.add(_task)
            _task.add_done_callback(self._discard_callback)
        ctx.session.save("user", line)

    async def handle_memory_injection(self, line: str) -> None:
        """Retrieve relevant memory snippets and inject them into conversation history."""
        ctx = self._ctx
        if ctx.services_required.memory is not None:
            memory_snippets = await ctx.services_required.memory.on_user_prompt(
                query=line,
                session_id=ctx.session.session_id,
            )
            if memory_snippets:
                memory_block = "--- USER MEMORY ---\n" + "\n".join(
                    f"- {snippet.text}" for snippet in memory_snippets
                )
                await ctx.conv.append_message(
                    {
                        "role": "system",
                        "content": memory_block,
                        "_memory_injected": True,
                    },
                    source="memory_injection",
                )

    async def handle_history_compression(self) -> None:
        """Compress conversation history and replace messages if compression occurred.

        Note: ephemeral/memory-injected messages are NOT filtered here because
        clear_previous_turn_ephemeral_messages() already strips them before every
        turn. Passing the full history avoids double-filtering.

        Note: the compressed history is also NOT routed through
        ConversationState.replace_history() — hist_mgr.compress() only produces
        role/content-only summary messages (see history.py's
        _build_summary_message()), which are already schema-conformant by
        construction, so re-validating here would be redundant.
        """
        ctx = self._ctx
        with self._llm_runner._span_ctx("compress"):
            ctx.conv.history, result = await ctx.services_required.hist_mgr.compress(
                ctx.conv.history
            )
            if (
                result.compressed_count > 0
                or result.summary_added
                or result.is_fallback
            ):
                ctx.session.replace_messages(ctx.conv.history)
```

### Details

Current state verification (adversarial check against `orchestrator.py`):

- **Methods confirmed**: `_clear_previous_turn_ephemeral_messages` (line 629), `_sync_system_prompt` (line 642), `_append_user_message` (line 663), `_handle_memory_injection` (line 445), `_handle_history_compression` (line 466). All moved to ConversationStateManager.
- **Dependencies confirmed**: AgentContext, on_first_turn callback, background task set, discard_callback. These are passed via constructor injection.
- **Class attribute confirmed**: `_EPHEMERAL_KEYS: frozenset[str] = frozenset({"_ephemeral", "_memory_injected", "_skill_ephemeral"})` (line 123). Moved to ConversationStateManager as class attribute.
- **Ephemeral message filtering confirmed**: `any(k in self._EPHEMERAL_KEYS for k in m.keys())`. Preserved in ConversationStateManager.
- **System prompt sync confirmed**: `ctx.conv.history[0]["content"] = ctx.conv.system_prompt_content`. Preserved in ConversationStateManager.
- **User message append confirmed**: `ctx.conv.append_message({"role": "user", "content": line})`, `ctx.stats.stat_turns += 1`. Preserved in ConversationStateManager.
- **First-turn background task confirmed**: `asyncio.create_task(self._on_first_turn(line), ...)`. Preserved in ConversationStateManager.
- **Memory injection confirmed**: `ctx.services_required.memory.on_user_prompt(query=line, session_id=ctx.session.session_id)`. Preserved in ConversationStateManager.
- **History compression confirmed**: `ctx.services_required.hist_mgr.compress(ctx.conv.history)`. Preserved in ConversationStateManager.
- **LLM runner span context confirmed**: `self._llm_runner._span_ctx("compress")`. This requires passing LLMTurnRunner to ConversationStateManager.

## Compatibility considerations

- **REQ-008**: All existing public method signatures and return types preserved. ConversationStateManager methods replace Orchestrator private methods with identical behavior.
- **REQ-010**: Existing import paths (`from agent.orchestrator import Orchestrator`) continue to work. Orchestrator still exports Orchestrator class.
- **REQ-009**: No circular imports between new modules. ConversationStateManager depends on AgentContext, LLMTurnRunner via explicit constructor injection -- no module-level imports of other new modules.
- **Backward compat**: Orchestrator passes callbacks to ConversationStateManager during initialization. Callback signatures unchanged.

## Security considerations

- No security-relevant behavior changes. The refactor preserves existing authentication, authorization, and input-validation logic.
- Message validation via `validate_message(dict(msg))` is unchanged.
- Session saving is unchanged.

## Rollback considerations

- If the refactor introduces regressions, revert to the original `orchestrator.py` using git.
- The six new module files can be deleted; Orchestrator continues to function with the original implementation.
- Test suite should catch behavioral regressions before deployment.

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|--------|----------|---------|------------------|
| `conversation_state_manager.py` lint | ruff check | `ruff check scripts/agent/conversation_state_manager.py` | No lint errors |
| `conversation_state_manager.py` type check | mypy | `mypy scripts/agent/conversation_state_manager.py` | No type errors |
| `conversation_state_manager.py` import succeeds | Static analysis | `python -c "from agent.conversation_state_manager import ConversationStateManager"` | Import succeeds |

## Completion criteria

- [ ] ConversationStateManager class created with constructor injection
- [ ] `_EPHEMERAL_KEYS` defined as class attribute (frozenset of ephemeral keys)
- [ ] `clear_previous_turn_ephemeral_messages()` strips ephemeral messages from history
- [ ] `sync_system_prompt()` syncs system prompt from ctx.conv.system_prompt_content
- [ ] `append_user_message(line)` appends user message, syncs system prompt, increments turn counter
- [ ] `handle_memory_injection(line)` retrieves memory snippets and injects into history
- [ ] `handle_history_compression()` compresses conversation history
- [ ] `ruff` lint passes
- [ ] `mypy` type check passes
- [ ] Existing Orchestrator unit tests confirm no behavioral regression

## Out of scope

- Modifying LLMTurnRunner internals
- Adding new features or capabilities beyond structural refactoring
- Moving DiagnosticStore ownership out of Orchestrator (per Issue constraint)
- Changing the conversation history schema

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260831-144218 | 20260831-144218 | **Duplicate/superseded procedure, no code change made.** Generated from `plans/20260829-174312_plan.md` for the same source issue as `implementations/done/20260829-175109_07_conversation_state_manager.md` (from `plans/20260829-175109_plan.md`), which was already implemented and merged (commit `25eb40b56`) with a narrower, corrected scope. Adversarial verification found this document assigns all five methods (`clear_previous_turn_ephemeral_messages`, `sync_system_prompt`, `append_user_message`, `handle_memory_injection`, `handle_history_compression`) to `ConversationStateManager`, but the merged implementation splits them: the first three live in `TurnCoordinator` (`turnd_coordinator.py`) and only the latter two live here — the 175109-derived `07_conversation_state_manager.md` documents why (avoiding the same overlap this document reintroduces). This document's `_EPHEMERAL_KEYS` class attribute (merged: module-level `EPHEMERAL_KEYS` constant, imported by `TurnCoordinator`) and its constructor (`ctx`, `on_first_turn`, `background_tasks`, `discard_callback` — merged: only `llm_runner`) also diverge; its `append_user_message` sample references `self._background_tasks`/`self._discard_callback`, which the merged `ConversationStateManager` does not have (that wiring lives in `TurnCoordinator`, which owns `append_user_message`). The user chose to treat this set as a duplicate rather than reconcile or re-implement it. |
| 2 | Add or update tests per Validation plan | Completed | 20260831-144218 | 20260831-144218 | N/A: no code change was made — existing tests already pass against the merged implementation. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260831-144218 | 20260831-144218 | N/A: no code change was made. `ruff check`/`mypy` on `scripts/agent/conversation_state_manager.py` (the merged file) both pass. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260831-144218 | 20260831-144218 | N/A: no `docs/00_index.md` task-scope row references this file's symbols by name. |

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
- **Related target files**: scripts/agent/conversation_state_manager.py
