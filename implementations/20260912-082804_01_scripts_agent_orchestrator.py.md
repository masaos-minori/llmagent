## Goal

Add `workflow_status()` method to `Orchestrator` class returning `{"tracking": "enabled"}` when `AgentContext.workflow.active == True`, otherwise `{"tracking": "not_loaded"}` (REQ-001, REQ-002).

## Scope

- Add `workflow_status()` public method to `Orchestrator` in `scripts/agent/orchestrator.py`
- Method reads `self._ctx.workflow.active` and returns the appropriate dict

## Assumptions

- `AgentContext.workflow.active` is a boolean on `WorkflowState` (context.py:241), set/cleared by `WorkflowEngineAdapter._activate_workflow()` / `_deactivate_workflow()`
- No other callers depend on `Orchestrator.workflow_status()` returning `None` or raising `AttributeError`
- `self._ctx` is available on `Orchestrator` instances and provides access to `workflow`

## Design decisions

- Return value format matches existing test expectations: `{"tracking": "enabled"}` / `{"tracking": "not_loaded"}`
- `"not_loaded"` maps to `"not loaded"` in `StartupBanner._get_workflow_status()` (preserves CLI output compatibility)
- Method is public (no underscore prefix) since `StartupBanner` calls it directly after this change

## Alternatives considered

- Returning a string directly (`"enabled"` / `"not_loaded"`) — rejected; dict format matches the existing test mock structure and allows future extension without API change
- Using a different signal than `workflow.active` — rejected; `WorkflowState.active` is the only concrete workflow state flag available

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

1. Locate the `Orchestrator` class definition in `scripts/agent/orchestrator.py`
2. Add a new public method `workflow_status(self) -> dict[str, str]` after existing methods
3. Implement the method body: read `self._ctx.workflow.active`, return the appropriate dict

### Method

```python
def workflow_status(self) -> dict[str, str]:
    """Return the current workflow tracking status."""
    if self._ctx.workflow.active:
        return {"tracking": "enabled"}
    return {"tracking": "not_loaded"}
```

### Details

- Read `scripts/agent/context.py` to confirm `WorkflowState.active` attribute exists and is a `bool`
- Confirm `Orchestrator.__init__` stores `self._ctx` pointing to `AgentContext`
- Add the method at a logical position within the class (near other status/query methods if they exist)
- Include a docstring explaining the return value semantics

## Compatibility considerations

- `StartupBanner._get_workflow_status()` currently uses `getattr(orchestrator, "workflow_status", None)` fallback — after this change, the fallback is no longer needed (addressed in the next target file document)
- Existing tests mock `repl._orchestrator.workflow_status` as a MagicMock — the new real method will satisfy those mocks naturally once the orchestrator instance has the method

## Security considerations

N/A: no user input, no network access, no credential handling.

## Rollback considerations

- Revert: remove the added `workflow_status()` method from `Orchestrator`
- The `getattr` fallback in `StartupBanner._get_workflow_status()` remains harmless even after removal — it simply returns `"not loaded"` again

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|---|---|---|---|
| `Orchestrator.workflow_status()` active=True | Unit — verify return value | `uv run pytest tests/agent/test_repl.py::TestGetWorkflowStatus` | Returns `{"tracking": "enabled"}` |
| `Orchestrator.workflow_status()` active=False | Unit — verify return value | `uv run pytest tests/agent/test_repl.py::TestGetWorkflowStatus` | Returns `{"tracking": "not_loaded"}` |

## Completion criteria

- `Orchestrator.workflow_status()` method exists and returns the correct dict based on `self._ctx.workflow.active`
- All `TestGetWorkflowStatus` tests pass with the new method present

## Out of scope

- Modifying `StartupBanner._get_workflow_status()` (handled in the next target file document)
- Updating tests (handled in the next target file document)
- Adding new config options or changing WorkflowEngineAdapter

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `workflow_status()` method to Orchestrator | Pending | — | — | |
| 2 | Verify method works via TestGetWorkflowStatus tests | Pending | — | — | |

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
- **Source issue**: issues/20260911-153000_replbanner01_orchestrator-workflow-status-unimplemented.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-214126_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-082804
- **Related target files**: scripts/agent/orchestrator.py
