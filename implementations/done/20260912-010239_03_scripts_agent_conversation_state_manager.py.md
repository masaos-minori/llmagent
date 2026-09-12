# Implementation: scripts/agent/conversation_state_manager.py

## Goal

Remove `on_turn_start`/`on_turn_end` constructor parameters and storage entirely — confirmed pure dead redundant copy, never invoked anywhere in this class.

## Scope

- Modify `scripts/agent/conversation_state_manager.py` only.
- Remove `on_turn_start`/`on_turn_end` constructor parameters.
- Remove `self._on_turn_start`/`self._on_turn_end` storage.

## Assumptions

- The `ConversationStateManager` class currently stores `on_turn_start`/`on_turn_end` as `self._on_turn_start`/`self._on_turn_end` but never uses them.
- No other file in `scripts/`/`tests/` constructs `ConversationStateManager` directly with these kwargs.

## Design decisions

- Remove the unused `on_turn_start`/`on_turn_end` constructor parameters and storage.
- Keep the existing `on_llm_wait_start`/`on_llm_wait_end` constructor parameters since they're used elsewhere.

## Alternatives considered

- **Keep both liveness methods**: Would preserve backward compatibility but perpetuates the inconsistency bug where callers cannot know which liveness model applies.
- **Deprecate rather than remove**: Would allow gradual migration but adds maintenance burden for deprecated methods.

## Implementation

### Target file

`scripts/agent/conversation_state_manager.py`

### Procedure

1. Read `__init__()` to understand its current structure.
2. Remove `on_turn_start`/`on_turn_end` constructor parameters.
3. Remove `self._on_turn_start`/`self._on_turn_end` storage.

### Method

```python
# Step 1: Read __init__() to understand its current structure
# In conversation_state_manager.py (around line 62-63):
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

# Step 2: Remove on_turn_start/on_turn_end constructor parameters
# In __init__() signature (around line 62):
# Before:
#     def __init__(
#         self,
#         ...,
#         on_turn_start: Callable[[], Any] | None = None,
#         on_turn_end: Callable[[], Any] | None = None,
#         ...
#     ):
# After:
#     def __init__(
#         self,
#         ...,
#         ...
#     ):

# Step 3: Remove self._on_turn_start/self._on_turn_end storage
# In __init__() body (around line 73-74):
# Before:
#         self._on_turn_start = on_turn_start
#         self._on_turn_end = on_turn_end
# After:
#         # Removed — these callbacks move exclusively to AuditEventEmitter
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

- [ ] `on_turn_start`/`on_turn_end` constructor parameters removed.
- [ ] `self._on_turn_start`/`self._on_turn_end` storage removed.
- [ ] Existing tests pass without modification.
- [ ] No type/lint regressions.

## Out of scope

- Modifying `scripts/agent/audit_event_emitter.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/llm_turn_executor.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/orchestrator.py` — handled by a separate implementation procedure document.
- Modifying `tests/agent/test_orchestrator.py` — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read __init__() | Completed | — | — | NOTE: __init__() does not have on_turn_start/on_turn_end parameters |
| 2 | Remove on_turn_start/on_turn_end parameters | Completed | — | — | N/A: Already absent in current source |
| 3 | Remove self._on_turn_start/self._on_turn_end storage | Completed | — | — | N/A: Already absent in current source |
| 4 | Run validation sequence (rules/toolchain.md) | Completed | — | — | N/A: no changes made |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260911-150000_orchcb01_turn-and-llm-wait-callbacks-never-invoked.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-211456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-010239
- **Related target files**: scripts/agent/conversation_state_manager.py
