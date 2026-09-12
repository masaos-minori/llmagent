# Implementation: scripts/agent/llm_turn_executor.py

## Goal

Add `call_on_llm_wait_start()` helper (mirrors existing `call_on_llm_wait_end()`); wrap the `runner.run(...)` call in `handle_llm_turn()` with `call_on_llm_wait_start()` before and `call_on_llm_wait_end()` in a `finally` block after; remove `on_turn_start`/`on_turn_end` constructor parameters, storage, and the now-unused `call_on_turn_end()` helper; correct `on_llm_wait_start`'s type annotation to `Callable[[], None] | None`.

## Scope

- Modify `scripts/agent/llm_turn_executor.py` only.
- Add `call_on_llm_wait_start()` helper method.
- Wrap the `runner.run(...)` call in `handle_llm_turn()` with `call_on_llm_wait_start()` before and `call_on_llm_wait_end()` in a `finally` block after.
- Remove `on_turn_start`/`on_turn_end` constructor parameters, storage, and the now-unused `call_on_turn_end()` helper.
- Correct `on_llm_wait_start`'s type annotation from `Callable[[], Any] | None` to `Callable[[], None] | None`.

## Assumptions

- The `LLMTurnExecutor` class already stores `on_llm_wait_start`/`on_llm_wait_end` as `self._on_llm_wait_start`/`self._on_llm_wait_end` but never invokes them.
- The `LLMTurnExecutor` class currently stores `on_turn_start`/`on_turn_end` as `self._on_turn_start`/`self._on_turn_end` but never uses them.
- The callbacks should be invoked unconditionally (no gating on success/failure).

## Design decisions

- Add the callback invocations around the `runner.run(...)` call in `handle_llm_turn()`.
- Use `try/finally` to ensure `call_on_llm_wait_end()` fires symmetrically even if `run()` raises.
- Remove the unused `on_turn_start`/`on_turn_end` constructor parameters and storage.
- Correct the type annotation for `on_llm_wait_start` to match `on_llm_wait_end`.

## Alternatives considered

- **Keep both liveness methods**: Would preserve backward compatibility but perpetuates the inconsistency bug where callers cannot know which liveness model applies.
- **Deprecate rather than remove**: Would allow gradual migration but adds maintenance burden for deprecated methods.

## Implementation

### Target file

`scripts/agent/llm_turn_executor.py`

### Procedure

1. Read `handle_llm_turn()` to understand its current structure.
2. Add `call_on_llm_wait_start()` helper method.
3. Wrap the `runner.run(...)` call in `handle_llm_turn()` with `call_on_llm_wait_start()` before and `call_on_llm_wait_end()` in a `finally` block after.
4. Remove `on_turn_start`/`on_turn_end` constructor parameters, storage, and the now-unused `call_on_turn_end()` helper.
5. Correct `on_llm_wait_start`'s type annotation.

### Method

```python
# Step 1: Read handle_llm_turn() to understand its current structure
# In llm_turn_executor.py (around line 74-99):
#     async def handle_llm_turn(self, turn_id: str, ...) -> TurnResult:
#         """Handle an LLM turn."""
#         runner = LLMTurnRunner(self._ctx, guard, tracer=self._tracer)
#         result = await runner.run(turn_id, ...)
#         # Currently does NOT invoke self._on_llm_wait_start or self._on_llm_wait_end
#         ...

# Step 2: Add call_on_llm_wait_start() helper method
# After call_on_llm_wait_end() (around line 67):
# Before:
#     def call_on_llm_wait_end(self) -> None:
#         """Call the on_llm_wait_end callback if set."""
#         if self._on_llm_wait_end is not None:
#             try:
#                 self._on_llm_wait_end()
#             except Exception:
#                 logger.warning("on_llm_wait_end callback failed", exc_info=True)
# After:
#     def call_on_llm_wait_start(self) -> None:
#         """Call the on_llm_wait_start callback if set."""
#         if self._on_llm_wait_start is not None:
#             try:
#                 self._on_llm_wait_start()
#             except Exception:
#                 logger.warning("on_llm_wait_start callback failed", exc_info=True)

# Step 3: Wrap runner.run(...) call with try/finally
# In handle_llm_turn() (around line 85-90):
# Before:
#     runner = LLMTurnRunner(self._ctx, guard, tracer=self._tracer)
#     result = await runner.run(turn_id, ...)
#     ...
# After:
#     runner = LLMTurnRunner(self._ctx, guard, tracer=self._tracer)
#     self.call_on_llm_wait_start()
#     try:
#         result = await runner.run(turn_id, ...)
#     finally:
#         self.call_on_llm_wait_end()
#     ...

# Step 4: Remove on_turn_start/on_turn_end constructor parameters, storage, and call_on_turn_end()
# In __init__() (around line 59-67):
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
#     ...
#     def call_on_turn_end(self) -> None:
#         """Call the on_turn_end callback if set."""
#         if self._on_turn_end is not None:
#             try:
#                 self._on_turn_end()
#             except Exception:
#                 logger.warning("on_turn_end callback failed", exc_info=True)
# After:
#     def __init__(
#         self,
#         ...,
#         on_llm_wait_start: Callable[[], None] | None = None,
#         on_llm_wait_end: Callable[[], None] | None = None,
#         ...
#     ):
#         ...
#         self._on_llm_wait_start = on_llm_wait_start
#         self._on_llm_wait_end = on_llm_wait_end
#         ...
#     ...
#     # call_on_turn_end() removed entirely

# Step 5: Correct on_llm_wait_start's type annotation
# In __init__() signature (around line 59):
# Before:
#     on_llm_wait_start: Callable[[], Any] | None = None,
# After:
#     on_llm_wait_start: Callable[[], None] | None = None,
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

- [ ] `call_on_llm_wait_start()` helper added.
- [ ] `runner.run(...)` wrapped with `call_on_llm_wait_start()` before and `call_on_llm_wait_end()` in `finally`.
- [ ] `on_turn_start`/`on_turn_end` constructor parameters removed.
- [ ] `self._on_turn_start`/`self._on_turn_end` storage removed.
- [ ] `call_on_turn_end()` helper removed.
- [ ] `on_llm_wait_start`'s type annotation corrected to `Callable[[], None] | None`.
- [ ] Existing tests pass without modification.
- [ ] No type/lint regressions.

## Out of scope

- Modifying `scripts/agent/audit_event_emitter.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/conversation_state_manager.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/orchestrator.py` — handled by a separate implementation procedure document.
- Modifying `tests/agent/test_orchestrator.py` — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read handle_llm_turn() | Completed | — | — | NOTE: handle_llm_turn() already has call_on_llm_wait_start/call_on_llm_wait_end around runner.run() |
| 2 | Add call_on_llm_wait_start() | Completed | — | — | N/A: Already present in current source |
| 3 | Wrap runner.run(...) with try/finally | Completed | — | — | N/A: Already present in current source |
| 4 | Remove on_turn_* parameters and storage | Completed | — | — | N/A: No on_turn_* parameters exist in current source |
| 5 | Correct type annotation | Completed | — | — | N/A: Already Callable[[], None] | None in current source |
| 6 | Run validation sequence (rules/toolchain.md) | Completed | — | — | N/A: no changes made |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-001
- **Source issue**: issues/20260911-150000_orchcb01_turn-and-llm-wait-callbacks-never-invoked.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-211456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-010239
- **Related target files**: scripts/agent/llm_turn_executor.py
