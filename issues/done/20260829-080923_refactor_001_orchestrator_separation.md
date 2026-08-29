# Refactor orchestrator.py — separation of concerns (1/3)

## Priority
Medium

## Summary
Split `scripts/agent/orchestrator.py` (764 lines) into focused modules to reduce cyclomatic complexity, improve testability, and clarify responsibility boundaries between turn lifecycle, workflow engine integration, background task monitoring, and audit event emission.

## Background
The Orchestrator class coordinates turn-level operations including LLM streaming, tool dispatch, workflow engine integration, memory injection, history compression, background task monitoring, and audit event emission. It was written as a single facade class delegating to LLMTurnRunner and ToolLoopGuard, but accumulated responsibilities over time through incremental additions (workflow engine support, background task failure thresholding, approval pending guards, etc.).

## Problem
The Orchestrator class violates the Single Responsibility Principle by combining at least six distinct concerns into one class:

1. **Turn lifecycle coordination** — `_handle_turn_start`, `_handle_turn_end`, `_process_turn`
2. **Workflow engine integration** — `_handle_workflow_engine`, `_init_workflow_task`, `_activate_workflow`, `_deactivate_workflow`, `_handle_workflow_approval_pending`, `_handle_workflow_halt`
3. **Background task monitoring** — `_append_user_message` (task creation), `_discard_and_log` (failure tracking), `_notify_bg_failure_threshold`
4. **LLM turn execution** — `_handle_llm_turn`
5. **Audit event emission** — `_build_turn_end_event`, `_build_turn_end_metadata`, `_build_turn_end_llm_stats`, plus direct audit_logger calls
6. **Conversation state manipulation** — `_clear_previous_turn_ephemeral_messages`, `_sync_system_prompt`, `_append_user_message`

This makes the class hard to understand, test in isolation, and modify without unintended side effects.

## Reason for Change
- Cyclomatic complexity of `Orchestrator.handle_turn` and `_handle_workflow_engine` exceeds maintainable levels
- `_discard_and_log` alone has 10+ conditional branches for log-level selection and threshold notification
- New features require modifying this class even though they touch unrelated concerns (e.g., adding a second background task type would conflate failure streams)
- Test isolation is poor — mocking the entire Orchestrator is required for most unit tests because all concerns are tightly coupled
- The class has grown beyond the 400-line threshold defined in `skills/DESIGN.md` File Split Rule trigger condition

## Implementation Intent
Extract each concern into its own class/module while preserving the Orchestrator as a thin facade that composes these components:

1. **TurnCoordinator** — turn lifecycle (start/end, ephemeral cleanup, system prompt sync, user message append). Owns `_handle_turn_start`, `_handle_turn_end`, `_clear_previous_turn_ephemeral_messages`, `_sync_system_prompt`, `_append_user_message`.
2. **WorkflowEngineAdapter** — workflow engine integration (task init, activation, deactivation, approval/halt handling). Owns `_handle_workflow_engine`, `_init_workflow_task`, `_activate_workflow`, `_deactivate_workflow`, `_handle_workflow_approval_pending`, `_handle_workflow_halt`.
3. **BgTaskMonitor** — background task failure tracking and threshold notification. Owns `_discard_and_log`, `_notify_bg_failure_threshold`, `_consecutive_bg_failures`, `_bg_pause_state`, `BG_FAILURE_THRESHOLD`.
4. **LlmTurnExecutor** — LLM streaming and result processing. Owns `_handle_llm_turn`, `_call_on_llm_wait_end`, `_call_on_turn_end`, `_call_on_error`.
5. **AuditEventEmitter** — audit event construction and emission. Owns `_build_turn_end_event`, `_build_turn_end_metadata`, `_build_turn_end_llm_stats`, `_mode_hint`, `_format_session_id`.
6. **ConversationStateManager** — conversation history manipulation. Owns `_handle_memory_injection`, `_handle_history_compression`.

The Orchestrator class becomes a composition of these components, calling methods on each in sequence during `handle_turn`.

## Target Files or Areas
- `scripts/agent/orchestrator.py` — primary target
- `scripts/agent/llm_turn_runner.py` — referenced by LlmTurnExecutor
- `scripts/agent/tool_loop_guard.py` — referenced by Orchestrator.__init__
- `scripts/agent/diagnostic_store.py` — referenced by Orchestrator.__init__
- `scripts/agent/workflow/*.py` — referenced by WorkflowEngineAdapter
- `scripts/agent/message_schema.py` — referenced by ConversationStateManager
- `scripts/agent/output_tags.py` — referenced throughout
- `scripts/agent/tool_audit.py` — referenced by WorkflowEngineAdapter

## Required Changes
- Create new module files under `scripts/agent/` for each extracted concern (5-6 new files)
- Move methods from Orchestrator into the appropriate new class
- Update Orchestrator to compose the new classes via dependency injection
- Remove inline imports (e.g., `from agent.tool_output import emit_approval_pending_notice` inside `_handle_workflow_approval_pending`)
- Extract `_EPHEMERAL_KEYS` constant usage into ConversationStateManager
- Extract `_build_turn_end_*` helpers into AuditEventEmitter
- Ensure all public APIs of Orchestrator remain unchanged (backward compatibility)
- Update `__init__.py` exports if needed

## Constraints
- Must preserve all existing public method signatures and return types (backward compatibility)
- Must not change any observable behavior (no behavioral regression)
- Must not break existing import paths (e.g., `from agent.orchestrator import Orchestrator`)
- Must not introduce circular dependencies between new modules
- `BG_FAILURE_THRESHOLD` constant scope is limited to first-turn session-title-generation; do not generalize it
- The `pause_on_critical_failure` opt-in flag and `_bg_pause_state` dict must remain in BgTaskMonitor

## Acceptance Criteria
- [ ] Orchestrator class reduced to fewer than 200 lines (from 764)
- [ ] Each extracted concern has its own dedicated class with clear responsibility boundary
- [ ] All existing public methods of Orchestrator work identically after refactor
- [ ] No circular imports between new modules
- [ ] Existing import paths (`from agent.orchestrator import Orchestrator`) continue to work
- [ ] Inline import removed from `_handle_workflow_approval_pending`
- [ ] `_EPHEMERAL_KEYS` constant moved to ConversationStateManager
- [ ] `_build_turn_end_*` helper functions moved to AuditEventEmitter
- [ ] `ruff` lint passes on all modified/new files
- [ ] `mypy` type check passes on all modified/new files

## Testing Expectations
- Run existing Orchestrator unit tests to confirm no behavioral regression
- Verify each extracted class can be instantiated and tested independently
- Confirm `handle_turn` still respects both guard conditions (approval_pending, bg_pause_state)
- Verify background task failure threshold logic produces identical log output
- Verify audit event structure remains identical (same keys/values)
- Run `uv run pytest` for full suite validation

## Documentation Impact
Update module docstrings for each new extracted class to describe its single responsibility. Update `orchestrator.py` module docstring to reflect its new role as a thin composition facade. No user-facing documentation changes required.

## Out of Scope
- Adding a second background task type (separate issue)
- Changing the `BG_FAILURE_THRESHOLD` value or making it configurable (currently only affects log level)
- Modifying LLMTurnRunner or ToolLoopGuard internals
- Adding new features or capabilities beyond structural refactoring
- Changing the workflow engine integration protocol

## Dependencies
N/A: none

## Unresolved Questions
- Should `ToolLoopGuard` be passed to LlmTurnExecutor instead of being constructed inside Orchestrator? Currently it's shared between Orchestrator and LLMTurnRunner.
- Should `DiagnosticStore` be owned by Orchestrator or moved to a separate concern? It's currently set on `ctx.diagnostics` during __init__.
- Is the current 200-line target for Orchestrator reasonable, or should we aim lower given it will become a pure composition layer?

## AI Implementation Instruction
When implementing this issue:
- Do NOT rewrite unrelated files (llm_turn_runner.py, tool_loop_guard.py, workflow engine internals)
- Keep changes minimal per module — move methods, update references, remove inline imports
- Preserve all public method signatures exactly as-is
- Verify backward compatibility by running existing tests before closing
- Stop and report open questions if requirements are unclear — do not guess about shared dependencies
- Do not implement out-of-scope items (second background task type, config changes, new features)
