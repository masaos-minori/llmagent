# Implementation: scripts/agent/orchestrator.py

## Goal

`Orchestrator.__init__` keeps accepting all four callbacks as constructor parameters (unchanged public API) but stops storing them as `self._on_turn_start`/`self._on_turn_end`/`self._on_llm_wait_start`/`self._on_llm_wait_end` (confirmed never read after assignment); update the `AuditEventEmitter(...)` construction to drop `on_llm_wait_start`/`on_llm_wait_end` kwargs, the `ConversationStateManager(...)` construction to drop `on_turn_start`/`on_turn_end` kwargs, and the `LlmTurnExecutor(...)` construction to drop `on_turn_start`/`on_turn_end` kwargs; correct `on_llm_wait_start`'s type annotation.

## Scope

- Modify `scripts/agent/orchestrator.py` only.
- Remove `Orchestrator`'s own dead `self._on_turn_start`/`self._on_turn_end`/`self._on_llm_wait_start`/`self._on_llm_wait_end` storage.
- Drop `on_llm_wait_start`/`on_llm_wait_end` from the `AuditEventEmitter(...)` construction.
- Drop `on_turn_start`/`on_turn_end` from the `ConversationStateManager(...)` construction.
- Drop `on_turn_start`/`on_turn_end` from the `LlmTurnExecutor(...)` construction.
- Correct `on_llm_wait_start`'s type annotation.

## Assumptions

- The `Orchestrator` class currently accepts all four callbacks as constructor parameters but never reads them after assignment.
- The `Orchestrator` class forwards `on_llm_wait_start`/`on_llm_wait_end` to `AuditEventEmitter` and `on_turn_start`/`on_turn_end` to `ConversationStateManager`/`LlmTurnExecutor`.
- The public API contract requires all function signatures to remain identical except `redeliver_event()` which gains a `now` parameter.

## Design decisions

- Remove the dead instance-attribute assignments.
- Update the sub-component construction call sites to drop the now-unused kwargs.
- Correct the type annotation for `on_llm_wait_start`.

## Alternatives considered

- **Keep both liveness methods**: Would preserve backward compatibility but perpetuates the inconsistency bug where callers cannot know which liveness model applies.
- **Deprecate rather than remove**: Would allow gradual migration but adds maintenance burden for deprecated methods.

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

1. Read `__init__()` to understand its current structure.
2. Remove `Orchestrator`'s own dead `self._on_turn_start`/`self._on_turn_end`/`self._on_llm_wait_start`/`self._on_llm_wait_end` storage.
3. Update the `AuditEventEmitter(...)` construction to drop `on_llm_wait_start`/`on_llm_wait_end` kwargs.
4. Update the `ConversationStateManager(...)` construction to drop `on_turn_start`/`on_turn_end` kwargs.
5. Update the `LlmTurnExecutor(...)` construction to drop `on_turn_start`/`on_turn_end` kwargs.
6. Correct `on_llm_wait_start`'s type annotation.

### Method

```python
# Step 1: Read __init__() to understand its current structure
# In orchestrator.py (around line 106-110):
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
#         self._audit_emitter = AuditEventEmitter(
#             ...,
#             on_turn_start=on_turn_start,
#             on_turn_end=on_turn_end,
#             on_llm_wait_start=on_llm_wait_start,
#             on_llm_wait_end=on_llm_wait_end,
#         )
#         self._state_mgr = ConversationStateManager(
#             ...,
#             on_turn_start=on_turn_start,
#             on_turn_end=on_turn_end,
#         )
#         self._llm_executor = LlmTurnExecutor(
#             ...,
#             on_turn_start=on_turn_start,
#             on_turn_end=on_turn_end,
#             on_llm_wait_start=on_llm_wait_start,
#             on_llm_wait_end=on_llm_wait_end,
#         )

# Step 2: Remove Orchestrator's own dead storage
# In __init__() body (around line 106-110):
# Before:
#         self._on_turn_start = on_turn_start
#         self._on_turn_end = on_turn_end
#         self._on_llm_wait_start = on_llm_wait_start
#         self._on_llm_wait_end = on_llm_wait_end
# After:
#         # Removed — these callbacks are forwarded directly to their owners below

# Step 3: Update AuditEventEmitter(...) construction
# In __init__() body (around line 133-164):
# Before:
#         self._audit_emitter = AuditEventEmitter(
#             ...,
#             on_turn_start=on_turn_start,
#             on_turn_end=on_turn_end,
#             on_llm_wait_start=on_llm_wait_start,
#             on_llm_wait_end=on_llm_wait_end,
#         )
# After:
#         self._audit_emitter = AuditEventEmitter(
#             ...,
#             on_turn_start=on_turn_start,
#             on_turn_end=on_turn_end,
#         )

# Step 4: Update ConversationStateManager(...) construction
# In __init__() body (around line 133-164):
# Before:
#         self._state_mgr = ConversationStateManager(
#             ...,
#             on_turn_start=on_turn_start,
#             on_turn_end=on_turn_end,
#         )
# After:
#         self._state_mgr = ConversationStateManager(...)

# Step 5: Update LlmTurnExecutor(...) construction
# In __init__() body (around line 133-164):
# Before:
#         self._llm_executor = LlmTurnExecutor(
#             ...,
#             on_turn_start=on_turn_start,
#             on_turn_end=on_turn_end,
#             on_llm_wait_start=on_llm_wait_start,
#             on_llm_wait_end=on_llm_wait_end,
#         )
# After:
#         self._llm_executor = LlmTurnExecutor(
#             ...,
#             on_llm_wait_start=on_llm_wait_start,
#             on_llm_wait_end=on_llm_wait_end,
#         )

# Step 6: Correct on_llm_wait_start's type annotation
# In __init__() signature (around line 106):
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

- [ ] `Orchestrator`'s own dead storage removed.
- [ ] `AuditEventEmitter(...)` construction updated to drop `on_llm_wait_start`/`on_llm_wait_end` kwargs.
- [ ] `ConversationStateManager(...)` construction updated to drop `on_turn_start`/`on_turn_end` kwargs.
- [ ] `LlmTurnExecutor(...)` construction updated to drop `on_turn_start`/`on_turn_end` kwargs.
- [ ] `on_llm_wait_start`'s type annotation corrected to `Callable[[], None] | None`.
- [ ] Existing tests pass without modification.
- [ ] No type/lint regressions.

## Out of scope

- Modifying `scripts/agent/audit_event_emitter.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/llm_turn_executor.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/conversation_state_manager.py` — handled by a separate implementation procedure document.
- Modifying `tests/agent/test_orchestrator.py` — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read __init__() | Pending | — | — | |
| 2 | Remove Orchestrator's own dead storage | Pending | — | — | |
| 3 | Update AuditEventEmitter(...) construction | Pending | — | — | |
| 4 | Update ConversationStateManager(...) construction | Pending | — | — | |
| 5 | Update LlmTurnExecutor(...) construction | Pending | — | — | |
| 6 | Correct type annotation | Pending | — | — | |
| 7 | Run validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260911-150000_orchcb01_turn-and-llm-wait-callbacks-never-invoked.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-211456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-010239
- **Related target files**: scripts/agent/orchestrator.py
