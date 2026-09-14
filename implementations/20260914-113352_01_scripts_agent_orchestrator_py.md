## Goal

Add property-based accessors emitting DeprecationWarning to `Orchestrator._llm_runner` and
`Orchestrator._guard` fields; keep instantiation for backward compatibility. Per REQ-001,
REQ-002.

## Scope

- Modify exactly one file: `scripts/agent/orchestrator.py`
- Add property getters/setters for `_llm_runner` and `_guard` that emit DeprecationWarning
- Keep field instantiation in `__init__` for backward compatibility during deprecation phase
- Preserve public API surface (REQ-005): method signatures unchanged

## Assumptions

- `LLMTurnRunner` and `ToolLoopGuard` classes exist and are importable (confirmed: lines 115-111)
- No production callers access these fields directly (confirmed: UNK-02 resolved)
- Test callers will be migrated separately (Phase 2)
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- Use `__dict__` to store/retrieve actual values, avoiding infinite recursion from property access
- Emit DeprecationWarning on both getter and setter access
- Include clear migration message pointing to replacement API in each warning
- Use `stacklevel=2` so warnings point to caller code, not the property accessor itself

## Alternatives considered

- Using `warnings.warn` vs `DeprecationWarning` class: confirmed `DeprecationWarning` is correct
- Adding a single deprecation flag vs per-property warnings: per-property preferred for clarity
- Making the properties raise instead of warn: warn preferred for gradual migration

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

1. **Add `_llm_runner` property accessor** after the `__init__` method body:
   - Getter: emits DeprecationWarning, returns `self.__dict__.get("_llm_runner")`
   - Setter: emits DeprecationWarning, sets `self.__dict__["_llm_runner"] = value`

2. **Add `_guard` property accessor** after `_llm_runner` property:
   - Getter: emits DeprecationWarning, returns `self.__dict__.get("_guard")`
   - Setter: emits DeprecationWarning, sets `self.__dict__["_guard"] = value`

3. **Keep field instantiation in `__init__`**:
   - `self._guard = ToolLoopGuard(ctx)` at line 111 — kept for backward compatibility
   - `self._llm_runner = LLMTurnRunner(...)` at lines 115-119 — kept for backward compatibility

### Method

1. Read `orchestrator.py` to identify insertion point after `__init__` method body
2. Add `_llm_runner` property getter/setter pair:
   ```python
   @property
   def _llm_runner(self):
       import warnings
       warnings.warn(
           "Orchestrator._llm_runner is deprecated. Use Orchestrator._llm_executor.handle_llm_turn() instead.",
           DeprecationWarning,
           stacklevel=2,
       )
       return self.__dict__.get("_llm_runner")

   @_llm_runner.setter
   def _llm_runner(self, value):
       import warnings
       warnings.warn(
           "Orchestrator._llm_runner is deprecated. Use Orchestrator._llm_executor.handle_llm_turn() instead.",
           DeprecationWarning,
           stacklevel=2,
       )
       self.__dict__["_llm_runner"] = value
   ```
3. Add `_guard` property getter/setter pair similarly:
   ```python
   @property
   def _guard(self):
       import warnings
       warnings.warn(
           "Orchestrator._guard is deprecated. Create ToolLoopGuard directly if needed.",
           DeprecationWarning,
           stacklevel=2,
       )
       return self.__dict__.get("_guard")

   @_guard.setter
   def _guard(self, value):
       import warnings
       warnings.warn(
           "Orchestrator._guard is deprecated. Create ToolLoopGuard directly if needed.",
           DeprecationWarning,
           stacklevel=2,
       )
       self.__dict__["_guard"] = value
   ```
4. Verify no infinite recursion: accessing `self._llm_runner` inside the property must use
   `self.__dict__.get("_llm_runner")`, not `self._llm_runner`

### Details

**Step 1 — Insertion point:**

After the `__init__` method body (line 119), before the next method definition. The exact
insertion point is after line 119 (`)`) and before the next `def` statement.

**Step 2 — `_llm_runner` property:**

```python
@property
def _llm_runner(self):
    """Deprecated: use _llm_executor.handle_llm_turn() instead."""
    import warnings
    warnings.warn(
        "Orchestrator._llm_runner is deprecated. Use Orchestrator._llm_executor.handle_llm_turn() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return self.__dict__.get("_llm_runner")

@_llm_runner.setter
def _llm_runner(self, value):
    """Deprecated: use _llm_executor.handle_llm_turn() instead."""
    import warnings
    warnings.warn(
        "Orchestrator._llm_runner is deprecated. Use Orchestrator._llm_executor.handle_llm_turn() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    self.__dict__["_llm_runner"] = value
```

**Step 3 — `_guard` property:**

```python
@property
def _guard(self):
    """Deprecated: create ToolLoopGuard directly if needed."""
    import warnings
    warnings.warn(
        "Orchestrator._guard is deprecated. Create ToolLoopGuard directly if needed.",
        DeprecationWarning,
        stacklevel=2,
    )
    return self.__dict__.get("_guard")

@_guard.setter
def _guard(self, value):
    """Deprecated: create ToolLoopGuard directly if needed."""
    import warnings
    warnings.warn(
        "Orchestrator._guard is deprecated. Create ToolLoopGuard directly if needed.",
        DeprecationWarning,
        stacklevel=2,
    )
    self.__dict__["_guard"] = value
```

## Compatibility considerations

- Backward compatible: existing test code continues to work (fields still accessible, just with warning)
- Warning suppression: callers can suppress via `warnings.filterwarnings("ignore", category=DeprecationWarning)`
- Phase 2 removal will break callers who haven't migrated — document as expected breaking change

## Security considerations

N/A: deprecation warnings don't introduce security-sensitive operations.

## Rollback considerations

- Revert the two property additions to restore original behavior
- No data loss risk — only adding warnings around existing field access

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/orchestrator.py | Type check — verify mypy passes after adding properties | `uv run mypy scripts/agent/orchestrator.py` | Clean (no errors) |
| scripts/agent/orchestrator.py | Deprecation warning verification — confirm warnings emitted | `uv run python -W error::DeprecationWarning -c "from agent.orchestrator import Orchestrator; o = Orchestrator(...); _ = o._llm_runner"` | DeprecationWarning raised |
| scripts/agent/orchestrator.py | Property access safety — verify no infinite recursion | Manual: access `_llm_runner` and `_guard` through property | Returns value without RecursionError |

## Completion criteria

- [ ] `_llm_runner` property getter emits DeprecationWarning when accessed
- [ ] `_llm_runner` property setter emits DeprecationWarning when assigned
- [ ] `_guard` property getter emits DeprecationWarning when accessed
- [ ] `_guard` property setter emits DeprecationWarning when assigned
- [ ] mypy passes on `scripts/agent/orchestrator.py`
- [ ] No infinite recursion from property access
- [ ] Field values retrievable via `__dict__` after property assignment

## Out of scope

- Migrating test callers (Phase 2)
- Removing the fields entirely (Phase 2)
- Refactoring `LlmTurnExecutor` to share guard state across turns
- Adding new guard functionality

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: existing tests cover regression |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Update docstrings for delegation clarification |

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
- **Source issue**: issues/20260913-172211_unused_orchestrator_llm_runner.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-220251_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-113352
- **Related target files**: scripts/agent/orchestrator.py
