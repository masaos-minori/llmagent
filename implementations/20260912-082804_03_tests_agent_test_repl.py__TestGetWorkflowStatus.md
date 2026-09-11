## Goal

Update `TestGetWorkflowStatus` tests in `tests/agent/test_repl.py` to reflect the new `Orchestrator.workflow_status()` method behavior (REQ-004).

## Scope

- Update `test_returns_enabled_when_tracking_enabled`: use `workflow_status()` mock instead of direct attribute assignment
- Add test for `workflow.active == False` case (`test_returns_not_loaded_when_active_false`)
- Keep `test_returns_unknown_when_orchestrator_is_none` unchanged

## Assumptions

- `Orchestrator.workflow_status()` is now a real method (from the previous target file)
- Tests currently mock via `repl._orchestrator.workflow_status = MagicMock(...)` which makes it callable
- The new method will satisfy those mocks naturally once the orchestrator instance has the real method

## Design decisions

- Keep the existing test structure (3 tests) but update the active=True test to work with the real method
- Add a new test for the `workflow.active == False` case using a real orchestrator instance with `workflow.active = False`
- Preserve the `"not loaded"` assertion for the inactive case

## Alternatives considered

- Removing the `getattr` fallback from tests entirely — rejected; the tests should continue to work with both the old mock approach and the new real method
- Using `MagicMock` for all three tests — rejected; mixing mock approaches makes it unclear whether the real method is being exercised

## Implementation

### Target file

`tests/agent/test_repl.py::TestGetWorkflowStatus`

### Procedure

1. Locate `TestGetWorkflowStatus` class in `tests/agent/test_repl.py`
2. Update `test_returns_enabled_when_tracking_enabled`:
   - Before: assigns `repl._orchestrator.workflow_status = MagicMock(return_value={"tracking": "enabled"})`
   - After: either keep as-is (works because MagicMock is callable) OR replace with a real orchestrator that has `workflow.active = True`
3. Add `test_returns_not_loaded_when_active_false`:
   - Create an orchestrator with `workflow.active = False`
   - Assert `_get_workflow_status()` returns `"not loaded"`
4. Keep `test_returns_unknown_when_orchestrator_is_none` unchanged

### Method

Existing tests:
```python
class TestGetWorkflowStatus:
    def test_returns_unknown_when_orchestrator_is_none(self) -> None:
        repl = _make_bare_repl()
        repl._orchestrator = None
        assert repl._banner._get_workflow_status(repl._orchestrator) == "unknown"

    def test_returns_enabled_when_tracking_enabled(self) -> None:
        repl = _make_bare_repl()
        repl._orchestrator.workflow_status = MagicMock(
            return_value={"tracking": "enabled"}
        )
        assert repl._banner._get_workflow_status(repl._orchestrator) == "enabled"

    def test_returns_not_loaded_when_tracking_not_loaded(self) -> None:
        repl = _make_bare_repl()
        repl._orchestrator.workflow_status = MagicMock(
            return_value={"tracking": "not_loaded"}
        )
        assert repl._banner._get_workflow_status(repl._orchestrator) == "not loaded"
```

After change:
```python
class TestGetWorkflowStatus:
    def test_returns_unknown_when_orchestrator_is_none(self) -> None:
        repl = _make_bare_repl()
        repl._orchestrator = None
        assert repl._banner._get_workflow_status(repl._orchestrator) == "unknown"

    def test_returns_enabled_when_tracking_enabled(self) -> None:
        repl = _make_bare_repl()
        # Use real orchestrator with workflow.active = True
        repl._orchestrator.workflow.active = True
        assert repl._banner._get_workflow_status(repl._orchestrator) == "enabled"

    def test_returns_not_loaded_when_active_false(self) -> None:
        repl = _make_bare_repl()
        # Use real orchestrator with workflow.active = False
        repl._orchestrator.workflow.active = False
        assert repl._banner._get_workflow_status(repl._orchestrator) == "not loaded"
```

### Details

- Read `scripts/agent/context.py` to confirm `AgentContext.workflow` provides access to `WorkflowState.active`
- Confirm `_make_bare_repl()` creates an orchestrator instance with a valid `workflow` attribute
- The new tests exercise the real `workflow_status()` method path rather than mocking it

## Compatibility considerations

- Existing tests use `MagicMock` on `repl._orchestrator.workflow_status` — after this change, the real method replaces the mock, so the mock assignments become unnecessary
- The `"not loaded"` assertion in the original `test_returns_not_loaded_when_tracking_not_loaded` test maps to `workflow.active = False` in the new version

## Security considerations

N/A: test-only changes, no production code impact.

## Rollback considerations

- Revert: restore the original three tests with `MagicMock` assignments
- Safe rollback: the old tests still work if the orchestrator's `workflow_status` attribute is mocked

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|---|---|---|---|
| All TestGetWorkflowStatus tests | Unit — verify all assertions pass | `uv run pytest tests/agent/test_repl.py::TestGetWorkflowStatus -v` | All 3 tests pass |

## Completion criteria

- `test_returns_enabled_when_tracking_enabled` uses `workflow.active = True` instead of `MagicMock`
- New `test_returns_not_loaded_when_active_false` test exists and passes
- `test_returns_unknown_when_orchestrator_is_none` remains unchanged
- All 3 tests pass when run together

## Out of scope

- Adding additional test cases beyond the two active/inactive scenarios
- Modifying other test classes in `test_repl.py`
- Changing test infrastructure (fixtures, helpers like `_make_bare_repl`)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update test_returns_enabled_when_tracking_enabled | Pending | — | — | |
| 2 | Add test_returns_not_loaded_when_active_false | Pending | — | — | |
| 3 | Verify all 3 tests pass | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260911-153000_replbanner01_orchestrator-workflow-status-unimplemented.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-214126_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-082804
- **Related target files**: tests/agent/test_repl.py::TestGetWorkflowStatus
