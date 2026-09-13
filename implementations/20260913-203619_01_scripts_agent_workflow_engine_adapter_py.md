## Goal

Fix double-close risk in `WorkflowEngineAdapter.execute_turn` when `_init_workflow_task` creates a new StateStore and the outer finally block also closes it, ensuring single-owner semantics for store lifecycle management, per REQ-001 and REQ-002.

## Scope

- In-Scope: Adding `self._owns_state_store` attribute to track store ownership, modifying `_init_workflow_task` to set ownership, updating `execute_turn`'s finally block to conditionally close based on ownership
- Out-of-Scope: Modifying the entire execute_turn flow, adding new error handling paths, changing public API method signatures

## Assumptions

- Python's sqlite3 module silently ignores subsequent close() calls — this assumption is confirmed by CPython source code
- The backward-compatible public API methods (`init_workflow_task`, `activate_workflow`) must not change their signatures — confirmed by inspection of orchestrator.py callers
- The ownership flag should be stored as an instance attribute rather than returned as part of the return value, for backward compatibility

## Design decisions

1. Use the **ownership attribute approach** (Approach 2 from Plan): add `self._owns_state_store = close_store` after setting `close_store`, and check this attribute in `execute_turn`'s finally block instead of returning an additional tuple. This avoids mutating instance state changes and makes ownership explicit while preserving backward compatibility.
2. Always reset `self._owns_state_store = False` in the finally block after conditional close to prevent stale ownership across turns.
3. Keep `close_store=True` for the `store=None` case — only add ownership tracking, don't change the existing behavior.

## Alternatives considered

- **Return tuple approach**: `_init_workflow_task` returns `(workflow_id, task, store_closed)` where `store_closed` indicates whether the inner method closed the store. Rejected because it would require breaking changes to the backward-compatible public API methods (`init_workflow_task`).
- **Remove outer close entirely**: Rejected because it could break callers relying on the outer close for cleanup.

## Implementation
### Target file
`scripts/agent/workflow_engine_adapter.py`

### Procedure
1. Add `self._owns_state_store` attribute to track store ownership
2. Set `self._owns_state_store = close_store` in `_init_workflow_task` when `store=None`
3. Update `execute_turn`'s finally block to conditionally close `self._state_store` based on `self._owns_state_store`
4. Reset `self._owns_state_store = False` after successful execution

### Method
Instance attribute + conditional logic modification in two methods.

### Details
1. **Phase 1: Preparation / Refactoring**
   a. Locate the class initialization or first use of `self._state_store` in `__init__` or early method
   b. Add `self._owns_state_store: bool = False` as an instance attribute (default False since the caller owns the store by default)
   
2. **Phase 2: Core Logic Implementation**
   a. In `_init_workflow_task`: After the line that sets `close_store = True` (when `store=None`), add:
      ```python
      self._owns_state_store = close_store
      ```
      This records that this method owns the newly created store.
   
   b. In `execute_turn`'s finally block (around line 214): Replace the unconditional close:
      ```python
      # Before:
      finally:
          ...
          self._state_store.close()
      
      # After:
      finally:
          ...
          if self._owns_state_store:
              self._state_store.close()
          self._owns_state_store = False  # Reset to prevent stale ownership
      ```
      This ensures the store is only closed once — either by the inner method (if it owns it) or by the outer method (if it doesn't).

3. **Phase 3: Documentation update**
   a. Update `_init_workflow_task`'s docstring to clarify the store ownership contract:
      - When `store=None`: the method creates a new StateStore and takes ownership; the caller should not close it
      - When `store` is provided: the caller retains ownership; the method will not close it

## Compatibility considerations

- The backward-compatible public API methods (`init_workflow_task`, `activate_workflow`) must preserve existing signatures — confirmed by inspection of orchestrator.py callers
- The `self._owns_state_store` attribute is private (underscore prefix) and does not affect the public API surface
- The conditional close logic preserves existing behavior: when the caller provides a store, the caller still closes it; when the method creates a store, the method still closes it — only the double-close edge case is fixed

## Security considerations

N/A: Fixing a resource lifecycle bug, no security impact.

## Rollback considerations

Simple revert of the three modifications (attribute addition, ownership assignment, conditional close). No data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/workflow_engine_adapter.py | Unit test: verify single close on new task creation | pytest scripts/agent/test_workflow_engine_adapter.py::test_execute_turn_new_task_single_close | Test passes — no double-close exception |
| scripts/agent/workflow_engine_adapter.py | Unit test: verify caller-owned store not closed on task resumption | pytest scripts/agent/test_workflow_engine_adapter.py::test_execute_turn_existing_task_no_double_close | Test passes — caller's store remains open |
| scripts/agent/workflow_engine_adapter.py | Regression test: backward-compatible public API methods work unchanged | pytest scripts/agent/test_workflow_engine_adapter.py::test_init_workflow_task_backwards_compat | Test passes — no signature change |

## Completion criteria

- [ ] New workflow task creation does not double-close StateStore
- [ ] Existing workflow task resumption works without changing store ownership semantics
- [ ] No regressions in callers using the backward-compatible public API
- [ ] All existing tests pass after changes
- [ ] `pytest scripts/agent/test_workflow_engine_adapter.py` runs without errors

## Out of scope

- Modifying the entire execute_turn flow
- Adding new error handling paths
- Changing public API method signatures
- Modifying `scripts/agent/orchestrator.py` (reference file only)
- Modifying `scripts/agent/workflow/__init__.py` (reference file only)
- Implementing sentinel objects like `_NO_RESULT`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `self._owns_state_store` attribute to WorkflowEngineAdapter | Completed | — | — | Default False |
| 2 | Set `self._owns_state_store = close_store` in _init_workflow_task | Completed | — | — | When store=None |
| 3 | Update execute_turn's finally block to conditionally close | Completed | — | — | Based on ownership |
| 4 | Reset `self._owns_state_store = False` after execution | Completed | — | — | Prevent stale ownership |
| 5 | Update _init_workflow_task docstring for ownership contract | Completed | — | — | Clarify ownership semantics |
| 6 | Run validation sequence (rules/toolchain.md) | Completed | — | — | pytest scripts/agent/ |

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
- **Requirement ID**: REQ-001, REQ-002 — fix double-close risk by tracking store ownership
- **Source issue**: issues/20260913-160555_statestore_double_close.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-183415_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-203619
- **Related target files**: scripts/agent/workflow_engine_adapter.py
