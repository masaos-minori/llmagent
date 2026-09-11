## Goal

`Orchestrator.__init__` keeps accepting all four callbacks as constructor parameters (unchanged public API) but stops storing them as `self._on_turn_start`/`self._on_turn_end`/`self._on_llm_wait_start`/`self._on_llm_wait_end` (confirmed never read after assignment); update the `AuditEventEmitter(...)` construction to drop `on_llm_wait_start`/`on_llm_wait_end` kwargs, the `ConversationStateManager(...)` construction to drop `on_turn_start`/`on_turn_end` kwargs, and the `LlmTurnExecutor(...)` construction to drop `on_turn_start`/`on_turn_end` kwargs; correct `on_llm_wait_start`'s type annotation.

## Scope

- Remove dead `self._on_turn_start`/`self._on_turn_end`/`self._on_llm_wait_start`/`self._on_llm_wait_end` storage assignments from `Orchestrator.__init__`.
- Keep accepting all four callbacks as constructor parameters (public API unchanged).
- Drop `on_llm_wait_start`/`on_llm_wait_end` from `AuditEventEmitter(...)` construction call.
- Drop `on_turn_start`/`on_turn_end` from `ConversationStateManager(...)` construction call.
- Drop `on_turn_start`/`on_turn_end` from `LlmTurnExecutor(...)` construction call.
- Correct `on_llm_wait_start`'s type annotation from `Callable[[], Any] | None` to `Callable[[], None] | None`.

## Assumptions

- `orchestrator.py:106-110` contains dead storage confirmed never read after assignment.
- `orchestrator.py:133-164` contains the three sub-component constructions whose kwargs must change.
- All four callbacks are still accepted as constructor parameters — only their forwarding/storage changes.

## Design decisions

- Keep the public API surface intact: `Orchestrator(..., on_turn_start=..., on_turn_end=..., on_llm_wait_start=..., on_llm_wait_end=...)` still works.
- Forward each callback pair only to its new single owner:
  - `on_turn_start`/`on_turn_end` → `AuditEventEmitter`
  - `on_llm_wait_start`/`on_llm_wait_end` → `LlmTurnExecutor`
- No intermediate forwarding through `ConversationStateManager` or `Orchestrator` itself.

## Alternatives considered

- Removing the constructor parameters entirely — rejected because it would break existing callers who configure these callbacks.
- Keeping `Orchestrator` as a pass-through hub — rejected because the Plan's design consolidates ownership to the two owning classes.

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

1. In `__init__`: remove `self._on_turn_start = on_turn_start` assignment (line 106).
2. In `__init__`: remove `self._on_turn_end = on_turn_end` assignment (line 107).
3. In `__init__`: remove `self._on_llm_wait_start = on_llm_wait_start` assignment (line 109).
4. In `__init__`: remove `self._on_llm_wait_end = on_llm_wait_end` assignment (line 110).
5. In `__init__`: correct `on_llm_wait_start: Callable[[], Any] | None = None` parameter to `on_llm_wait_start: Callable[[], None] | None = None`.
6. In `__init__`: update `AuditEventEmitter(...)` construction to drop `on_llm_wait_start`/`on_llm_wait_end` kwargs.
7. In `__init__`: update `ConversationStateManager(...)` construction to drop `on_turn_start`/`on_turn_end` kwargs.
8. In `__init__`: update `LlmTurnExecutor(...)` construction to drop `on_turn_start`/`on_turn_end` kwargs.

### Method

- Read current `__init__` signature (lines 90-112) to identify which parameters/assignments to modify/remove.
- Read current sub-component constructions (lines 133-164) to identify which kwargs to drop.

### Details

**`__init__` parameter change:**
```python
# Before:
def __init__(
    self,
    ctx: AgentContext,
    *,
    allowed_tools: set[str],
    on_first_turn: Callable[[str], Any] | None = None,
    on_turn_start: Callable[[], None] | None = None,
    on_turn_end: Callable[[], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
    on_llm_wait_start: Callable[[], Any] | None = None,
    on_llm_wait_end: Callable[[], None] | None = None,
    tracer: Any = None,
    pause_on_critical_failure: bool = False,
):

# After:
def __init__(
    self,
    ctx: AgentContext,
    *,
    allowed_tools: set[str],
    on_first_turn: Callable[[str], Any] | None = None,
    on_turn_start: Callable[[], None] | None = None,
    on_turn_end: Callable[[], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
    on_llm_wait_start: Callable[[], None] | None = None,
    on_llm_wait_end: Callable[[], None] | None = None,
    tracer: Any = None,
    pause_on_critical_failure: bool = False,
):
```

**Remove dead storage (lines 106-110):**
```python
# Remove these lines:
self._on_turn_start = on_turn_start
self._on_turn_end = on_turn_end
self._on_error = on_error
self._on_llm_wait_start = on_llm_wait_start
self._on_llm_wait_end = on_llm_wait_end
```

**Update `AuditEventEmitter(...)` construction (lines 133-143):**
```python
# Before:
self._audit_emitter = AuditEventEmitter(
    ctx,
    diagnostic_store=self._diagnostic_store,
    tracer=tracer,
    on_turn_start=on_turn_start,
    on_turn_end=on_turn_end,
    on_error=on_error,
    on_first_turn=on_first_turn,
    on_llm_wait_start=on_llm_wait_start,
    on_llm_wait_end=on_llm_wait_end,
)

# After:
self._audit_emitter = AuditEventEmitter(
    ctx,
    diagnostic_store=self._diagnostic_store,
    tracer=tracer,
    on_turn_start=on_turn_start,
    on_turn_end=on_turn_end,
    on_error=on_error,
    on_first_turn=on_first_turn,
)
```

**Update `ConversationStateManager(...)` construction (lines 144-154):**
```python
# Before:
self._conversation_manager = ConversationStateManager(
    ctx,
    diagnostic_store=self._diagnostic_store,
    tasks=self._background_tasks,
    on_discard=self._on_discard,
    tracer=tracer,
    on_first_turn=on_first_turn,
    on_turn_start=on_turn_start,
    on_turn_end=on_turn_end,
    on_error=on_error,
)

# After:
self._conversation_manager = ConversationStateManager(
    ctx,
    diagnostic_store=self._diagnostic_store,
    tasks=self._background_tasks,
    on_discard=self._on_discard,
    tracer=tracer,
    on_first_turn=on_first_turn,
    on_error=on_error,
)
```

**Update `LlmTurnExecutor(...)` construction (lines 155-164):**
```python
# Before:
self._llm_executor = LlmTurnExecutor(
    ctx,
    diagnostic_store=self._diagnostic_store,
    tracer=tracer,
    on_turn_start=on_turn_start,
    on_turn_end=on_turn_end,
    on_error=on_error,
    on_llm_wait_start=on_llm_wait_start,
    on_llm_wait_end=on_llm_wait_end,
)

# After:
self._llm_executor = LlmTurnExecutor(
    ctx,
    diagnostic_store=self._diagnostic_store,
    tracer=tracer,
    on_error=on_error,
    on_llm_wait_start=on_llm_wait_start,
    on_llm_wait_end=on_llm_wait_end,
)
```

## Compatibility considerations

- Public API of `Orchestrator.__init__` is unchanged — all four callbacks still accepted.
- `AuditEventEmitter` no longer receives `on_llm_wait_start`/`on_llm_wait_end` — handled in `audit_event_emitter.py` procedure document.
- `ConversationStateManager` no longer receives `on_turn_start`/`on_turn_end` — handled in `conversation_state_manager.py` procedure document.
- `LlmTurnExecutor` no longer receives `on_turn_start`/`on_turn_end` — handled in `llm_turn_executor.py` procedure document.

## Security considerations

N/A: no new security-sensitive behavior introduced.

## Rollback considerations

- If callback forwarding causes issues, revert to pre-modification state: restore dead storage assignments and original kwargs.
- The rollback is bounded to this one file only.

## Validation plan

- Unit test: `uv run pytest tests/agent/test_orchestrator.py::TestHandleLlmTurnOptionalCallbacks -q` — all 3 tests pass, none skipped.
- Regression: `uv run pytest tests/agent/test_orchestrator.py -q` — expected 87 passed, 0 skipped.
- Regression: `uv run pytest tests/integration/test_orchestrator_integration.py -q` — no regression (baseline: 39 passed, 0 skipped).
- Static: `uv run ruff check scripts/agent/orchestrator.py`; `uv run mypy scripts/agent/orchestrator.py`.

## Completion criteria

- `Orchestrator.__init__` stops storing `self._on_turn_start`/`self._on_turn_end`/`self._on_llm_wait_start`/`self._on_llm_wait_end`.
- `AuditEventEmitter(...)` construction drops `on_llm_wait_start`/`on_llm_wait_end` kwargs.
- `ConversationStateManager(...)` construction drops `on_turn_start`/`on_turn_end` kwargs.
- `LlmTurnExecutor(...)` construction drops `on_turn_start`/`on_turn_end` kwargs.
- `on_llm_wait_start` type annotation corrected to `Callable[[], None] | None`.
- No lint/type errors introduced.

## Out of scope

- Removing `on_turn_start`/`on_turn_end` from `AuditEventEmitter` — handled in `audit_event_emitter.py` procedure document.
- Removing `on_turn_start`/`on_turn_end` from `LlmTurnExecutor` — handled in `llm_turn_executor.py` procedure document.
- Test corrections — handled in `test_orchestrator.py` procedure document.

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260911-150000_orchcb01_turn-and-llm-wait-callbacks-never-invoked.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-211456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-234502
- **Related target files**: scripts/agent/orchestrator.py
