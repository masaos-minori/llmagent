# Implementation: scripts/agent/audit_event_emitter.py

## Goal

Invoke `self._on_turn_start()`/`self._on_turn_end()` (each gated on being set) at the start of `emit_turn_start()` and the end of `emit_turn_end()`. Remove the now-unused `on_llm_wait_start`/`on_llm_wait_end` constructor parameters and storage (this class never needs them — they move exclusively to `LlmTurnExecutor`).

## Scope

- Modify `scripts/agent/audit_event_emitter.py` only.
- Add invocation of `self._on_turn_start()` at the start of `emit_turn_start()`.
- Add invocation of `self._on_turn_end()` at the end of `emit_turn_end()`.
- Remove `on_llm_wait_start`/`on_llm_wait_end` constructor parameters and storage.

## Assumptions

- The `AuditEventEmitter` class already stores `on_turn_start`/`on_turn_end` as `self._on_turn_start`/`self._on_turn_end` but never invokes them.
- The `AuditEventEmitter` class currently stores `on_llm_wait_start`/`on_llm_wait_end` as `self._on_llm_wait_start`/`self._on_llm_wait_end` but never uses them.
- The callbacks should be invoked unconditionally (no gating on success/failure).

## Design decisions

- Add the callback invocations at the beginning/end of the respective methods.
- Remove the unused `on_llm_wait_start`/`on_llm_wait_end` constructor parameters and storage.
- Keep the existing `on_turn_start`/`on_turn_end` constructor parameters since they're used elsewhere.

## Alternatives considered

- **Keep both liveness methods**: Would preserve backward compatibility but perpetuates the inconsistency bug where callers cannot know which liveness model applies.
- **Deprecate rather than remove**: Would allow gradual migration but adds maintenance burden for deprecated methods.

## Implementation

### Target file

`scripts/agent/audit_event_emitter.py`

### Procedure

1. Read `emit_turn_start()` and `emit_turn_end()` to understand their current structure.
2. Add invocation of `self._on_turn_start()` at the start of `emit_turn_start()`.
3. Add invocation of `self._on_turn_end()` at the end of `emit_turn_end()`.
4. Remove `on_llm_wait_start`/`on_llm_wait_end` constructor parameters and storage.

### Method

```python
# Step 1: Read emit_turn_start() and emit_turn_end() to understand their current structure
# In audit_event_emitter.py (around line 75-91):
#     def emit_turn_start(self, turn_id: str, ...):
#         """Emit a turn-start event."""
#         # Currently does NOT invoke self._on_turn_start
#         ...
#
#     def emit_turn_end(self, turn_id: str, ...):
#         """Emit a turn-end event."""
#         # Currently does NOT invoke self._on_turn_end
#         ...

# Step 2: Add invocation of self._on_turn_start() at the start of emit_turn_start()
# In emit_turn_start() (around line 75):
# Before:
#     def emit_turn_start(self, turn_id: str, ...):
#         """Emit a turn-start event."""
#         ...
# After:
#     def emit_turn_start(self, turn_id: str, ...):
#         """Emit a turn-start event."""
#         if self._on_turn_start is not None:
#             try:
#                 self._on_turn_start()
#             except Exception:
#                 logger.warning("on_turn_start callback failed", exc_info=True)
#         ...

# Step 3: Add invocation of self._on_turn_end() at the end of emit_turn_end()
# In emit_turn_end() (around line 129+):
# Before:
#     def emit_turn_end(self, turn_id: str, ...):
#         """Emit a turn-end event."""
#         ...
# After:
#     def emit_turn_end(self, turn_id: str, ...):
#         """Emit a turn-end event."""
#         ...
#         if self._on_turn_end is not None:
#             try:
#                 self._on_turn_end()
#             except Exception:
#                 logger.warning("on_turn_end callback failed", exc_info=True)

# Step 4: Remove on_llm_wait_start/on_llm_wait_end constructor parameters and storage
# In __init__() (around line 63-64):
# Before:
#     def __init__(
#         self,
#         ...,
#         on_turn_start: Callable[[], Any] | None = None,
#         on_turn_end: Callable[[], Any] | None = None,
#         on_llm_wait_start: Callable[[], Any] | None = None,
#         on_llm_wait_end: Callable[[], Any] | None = None,
#         ...
#     ):
#         ...
#         self._on_turn_start = on_turn_start
#         self._on_turn_end = on_turn_end
#         self._on_llm_wait_start = on_llm_wait_start
#         self._on_llm_wait_end = on_llm_wait_end
#         ...
# After:
#     def __init__(
#         self,
#         ...,
#         on_turn_start: Callable[[], Any] | None = None,
#         on_turn_end: Callable[[], Any] | None = None,
#         ...
#     ):
#         ...
#         self._on_turn_start = on_turn_start
#         self._on_turn_end = on_turn_end
#         ...
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- Need to carefully reconcile the behavioral differences between the old and new implementations — the plan explicitly notes these differences must be reconciled during migration.
- The SIGINT handler logic moved to `ShutdownCoordinator` must be verified to work correctly with the new architecture.

## Compatibility considerations

- **Breaking change** for consumers of `get_process_info()` that expect only `pid`, `pgid`, and `running` fields. New fields (`last_exit_code`, `runtime_seconds`) will be present in the output.
- **No breaking change** for existing callers of `verify_running()` — the method signature remains compatible (new parameter has default value).

## Security considerations

- No new security surface introduced. Adding component delegation does not introduce new attack vectors.
- The SIGINT handling logic moved to `ShutdownCoordinator` maintains the same security properties.

## Rollback considerations

- Revert the component initialization and delegation updates.
- If the new fields cause unexpected behavior, remove them and investigate further.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| Callback invocation | Unit test | `uv run pytest tests/agent/test_orchestrator.py::TestHandleLlmTurnOptionalCallbacks -q` | All 3 tests pass, none skipped |
| Type checking | Static | Type checker against modified file | No type errors |
| Lint checking | Static | Lint tool against modified file | No lint errors |

## Completion criteria

- [ ] `self._on_turn_start()` invoked at the start of `emit_turn_start()`.
- [ ] `self._on_turn_end()` invoked at the end of `emit_turn_end()`.
- [ ] `on_llm_wait_start`/`on_llm_wait_end` constructor parameters removed.
- [ ] `self._on_llm_wait_start`/`self._on_llm_wait_end` storage removed.
- [ ] Existing tests pass without modification.
- [ ] No type/lint regressions.

## Out of scope

- Modifying `scripts/agent/llm_turn_executor.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/conversation_state_manager.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/orchestrator.py` — handled by a separate implementation procedure document.
- Modifying `tests/agent/test_orchestrator.py` — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read emit_turn_start() and emit_turn_end() | Pending | — | — | |
| 2 | Add on_turn_start() invocation | Pending | — | — | |
| 3 | Add on_turn_end() invocation | Pending | — | — | |
| 4 | Remove on_llm_wait_* parameters | Pending | — | — | |
| 5 | Run validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260911-150000_orchcb01_turn-and-llm-wait-callbacks-never-invoked.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-211456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-010239
- **Related target files**: scripts/agent/audit_event_emitter.py
