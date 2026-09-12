## Goal

Remove `on_turn_start`/`on_turn_end` constructor parameters and storage entirely — confirmed pure dead redundant copy, never invoked anywhere in this class.

## Scope

- Remove `on_turn_start: Callable[[], None] | None = None` parameter from `ConversationStateManager.__init__`.
- Remove `on_turn_end: Callable[[], None] | None = None` parameter from `ConversationStateManager.__init__`.
- Remove `self._on_turn_start = on_turn_start` assignment.
- Remove `self._on_turn_end = on_turn_end` assignment.

## Assumptions

- `rg -n "_on_turn_start\|_on_turn_end" scripts/agent/conversation_state_manager.py` shows only the constructor assignment lines (73-74), no invocation — confirmed via grep above.
- `Orchestrator.__init__` is the only constructor of `ConversationStateManager` anywhere in `scripts/`/`tests/` — this Plan updates that single call site in the same step.

## Design decisions

- Simple removal: no replacement needed since this class never invokes these callbacks. The callbacks are owned exclusively by `AuditEventEmitter` (for turn callbacks) and `LlmTurnExecutor` (for LLM wait callbacks).

## Alternatives considered

- Keeping the parameters as no-op — rejected because they serve no purpose and add confusion about whether the class uses them.

## Implementation

### Target file

`scripts/agent/conversation_state_manager.py`

### Procedure

1. In `__init__`: remove `on_turn_start: Callable[[], None] | None = None` parameter.
2. In `__init__`: remove `on_turn_end: Callable[[], None] | None = None` parameter.
3. In `__init__`: remove `self._on_turn_start = on_turn_start` assignment.
4. In `__init__`: remove `self._on_turn_end = on_turn_end` assignment.

### Method

- Read current `__init__` signature (lines 55-75) to identify which parameters/assignments to remove.
- Confirm no invocation of `self._on_turn_start`/`self._on_turn_end` elsewhere in the class body.

### Details

**`__init__` changes:**
```python
# Before:
def __init__(
    self,
    ctx: AgentContext,
    *,
    diagnostic_store: DiagnosticStore | None = None,
    tasks: set[asyncio.Task[Any]],
    on_discard: Callable[[asyncio.Task[Any]], None],
    tracer: Any = None,
    on_first_turn: Callable[[str], Any] | None = None,
    on_turn_start: Callable[[], None] | None = None,
    on_turn_end: Callable[[], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
) -> None:
    ...
    self._on_first_turn = on_first_turn
    self._on_turn_start = on_turn_start
    self._on_turn_end = on_turn_end
    self._on_error = on_error

# After:
def __init__(
    self,
    ctx: AgentContext,
    *,
    diagnostic_store: DiagnosticStore | None = None,
    tasks: set[asyncio.Task[Any]],
    on_discard: Callable[[asyncio.Task[Any]], None],
    tracer: Any = None,
    on_first_turn: Callable[[str], Any] | None = None,
    on_error: Callable[[Exception], None] | None = None,
) -> None:
    ...
    self._on_first_turn = on_first_turn
    self._on_error = on_error
```

## Compatibility considerations

- `Orchestrator.__init__` currently passes `on_turn_start`/`on_turn_end` kwargs to `ConversationStateManager(...)` construction (orchestrator.py:151-152). After removing these parameters from `ConversationStateManager.__init__`, those kwargs must be dropped there too — handled in the `orchestrator.py` procedure document.
- No other file constructs `ConversationStateManager` directly with these kwargs (confirmed via architecture/dependency analysis).

## Security considerations

N/A: no new security-sensitive behavior introduced.

## Rollback considerations

- If removal causes issues, revert to pre-modification state: restore the two constructor parameters and assignments.
- The rollback is bounded to this one file only.

## Validation plan

- Regression: `uv run pytest tests/agent/test_orchestrator.py -q` — expected 87 passed, 0 skipped.
- Static: `uv run ruff check scripts/agent/conversation_state_manager.py`; `uv run mypy scripts/agent/conversation_state_manager.py`.

## Completion criteria

- `ConversationStateManager.__init__` no longer accepts `on_turn_start`/`on_turn_end` parameters.
- No `self._on_turn_start`/`self._on_turn_end` instance attributes remain.
- No lint/type errors introduced.

## Out of scope

- Removing `on_turn_start`/`on_turn_end` from `Orchestrator` — handled in `orchestrator.py` procedure document.
- Removing `on_turn_start`/`on_turn_end` from `AuditEventEmitter` — handled in `audit_event_emitter.py` procedure document.
- Removing `on_turn_start`/`on_turn_end` from `LlmTurnExecutor` — handled in `llm_turn_executor.py` procedure document.
- Test corrections — handled in `test_orchestrator.py` procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: no test changes needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | N/A: no changes made |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: no documentation updates needed |

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
- **Generated at**: 20260911-234502
- **Related target files**: scripts/agent/conversation_state_manager.py
