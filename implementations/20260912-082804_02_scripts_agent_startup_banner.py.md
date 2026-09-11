## Goal

Remove the `getattr(orchestrator, "workflow_status", None)` defensive fallback in `StartupBanner._get_workflow_status()` and call `orchestrator.workflow_status()` directly (REQ-003).

## Scope

- Update `scripts/agent/startup_banner.py`'s `_get_workflow_status()` method
- Remove the `getattr` fallback branch that returns `"not loaded"` when the method doesn't exist
- Simplify the logic to always call `orchestrator.workflow_status()`

## Assumptions

- After the previous target file's change, `Orchestrator.workflow_status()` always exists
- The `"not_loaded"` → `"not loaded"` mapping in the banner output is preserved for backward compatibility
- `orchestrator` is guaranteed to have the `workflow_status()` method after this change

## Design decisions

- Remove the `getattr` check entirely — the method now always exists on `Orchestrator`
- Keep the `"not_loaded"` → `"not loaded"` string mapping to preserve CLI output compatibility
- Keep the `if orchestrator is None: return "unknown"` guard — still needed for the case where no orchestrator is passed

## Alternatives considered

- Keeping the `getattr` fallback as a safety net — rejected; the method is now part of the `Orchestrator` contract and the fallback would mask bugs silently
- Returning a different default when `workflow_status()` returns `None` — rejected; `workflow_status()` always returns a dict per its spec

## Implementation

### Target file

`scripts/agent/startup_banner.py`

### Procedure

1. Locate `_get_workflow_status()` method in `scripts/agent/startup_banner.py`
2. Replace the current implementation:
   - Remove: `get_status = getattr(orchestrator, "workflow_status", None)`
   - Remove: `if get_status is None: return "not loaded"`
   - Change: `status = get_status()` → `status = orchestrator.workflow_status()`
3. Update the docstring to remove the reference to the missing method workaround

### Method

Current implementation:
```python
def _get_workflow_status(self, orchestrator: Orchestrator | None) -> str:
    if orchestrator is None:
        return "unknown"
    get_status = getattr(orchestrator, "workflow_status", None)
    if get_status is None:
        return "not loaded"
    status = get_status()
    if status["tracking"] == "enabled":
        return "enabled"
    return "not loaded"
```

After change:
```python
def _get_workflow_status(self, orchestrator: Orchestrator | None) -> str:
    """Return a human-readable workflow status string for the startup banner."""
    if orchestrator is None:
        return "unknown"
    status = orchestrator.workflow_status()["tracking"]
    return status if status != "not_loaded" else "not loaded"
```

### Details

- Read `scripts/agent/orchestrator.py` to confirm `workflow_status()` is now a public method (from the previous target file)
- Update the docstring to remove the comment about `issues/20260911-153000_replbanner01_orchestrator-workflow-status-unimplemented.md`
- The `"not_loaded"` → `"not loaded"` mapping preserves the existing CLI output format

## Compatibility considerations

- The `"not loaded"` output for inactive workflows is preserved (backward compatible)
- The `"unknown"` output for None orchestrator is preserved (unchanged behavior)
- No callers depend on the old `getattr` fallback behavior since the method now exists

## Security considerations

N/A: no user input, no network access, no credential handling.

## Rollback considerations

- Revert: restore the `getattr` fallback and the original docstring
- Safe rollback path: the old code path was simpler and did not raise errors

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|---|---|---|---|
| `_get_workflow_status()` with orchestrator | Unit — verify no AttributeError | `uv run pytest tests/agent/test_repl.py::TestGetWorkflowStatus` | All 3 tests pass without AttributeError |
| `_get_workflow_status()` with None orchestrator | Unit — verify "unknown" returned | `uv run pytest tests/agent/test_repl.py::TestGetWorkflowStatus` | Returns "unknown" |

## Completion criteria

- `StartupBanner._get_workflow_status()` calls `orchestrator.workflow_status()` directly without `getattr` fallback
- All `TestGetWorkflowStatus` tests pass without modification to test assertions (the mock attribute assignment still works since MagicMock is callable)

## Out of scope

- Adding new workflow status values
- Changing the `"unknown"` / `"enabled"` / `"not loaded"` output strings
- Modifying `Orchestrator.workflow_status()` (handled in the previous target file document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove getattr fallback in StartupBanner._get_workflow_status() | Pending | — | — | |
| 2 | Verify tests pass without AttributeError | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260911-153000_replbanner01_orchestrator-workflow-status-unimplemented.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-214126_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-082804
- **Related target files**: scripts/agent/startup_banner.py
