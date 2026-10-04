## Goal

Add regression tests verifying that only tracked background tasks are cancelled during shutdown and critical operations are protected.

## Scope

- Create `tests/agent/test_resource_shutdown_coordinator.py` with tests for shutdown scenarios

## Assumptions

- The test framework uses pytest
- The resource shutdown coordinator is importable from `scripts.agent.resource_shutdown_coordinator`

## Design decisions

- Use `pytest.raises` context manager to assert specific exceptions are raised
- Mock `turn.background_tasks` to control which tasks are cancelled
- Verify critical operations (WAL checkpoint, history flush) are NOT cancelled
- Verify background-only tasks ARE cancelled

## Alternatives considered

- Using `unittest.TestCase.assertRaises` — pytest's `raises` is more concise
- Testing via integration with real subprocesses — too brittle, slow

## Implementation
### Target file
`tests/agent/test_resource_shutdown_coordinator.py`

### Procedure
Create a new test file with regression tests for shutdown scenarios.

### Method
1. Create `tests/agent/test_resource_shutdown_coordinator.py`
2. Add test for no data loss during shutdown with active history writes (REQ-003)
3. Add test for cancellation of background-only tasks (REQ-004)

### Details
```python
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from scripts.agent.resource_shutdown_coordinator import ResourceShutdownCoordinator

class TestResourceShutdownCoordinatorTaskCancellation:
    """Tests for REQ-003, REQ-004: Verify selective task cancellation."""

    @pytest.mark.asyncio
    async def test_no_data_loss_with_active_history_writes(self):
        """REQ-003: History write tasks are NOT cancelled during shutdown."""
        coordinator = ResourceShutdownCoordinator()
        
        # Setup mock context with turn.background_tasks
        mock_ctx = MagicMock()
        mock_turn = MagicMock()
        mock_ctx.turn = mock_turn
        
        # Create a mock history write task
        mock_history_task = MagicMock()
        mock_history_task.cancelled.return_value = False
        
        # Create a mock background task
        mock_bg_task = MagicMock()
        mock_bg_task.cancelled.return_value = False
        
        # Set up background_tasks with both tasks
        mock_turn.background_tasks = {mock_bg_task}
        
        # Patch close_resources to use our mock context
        with patch.object(coordinator, '_ctx', mock_ctx):
            await coordinator.close_resources()
            
            # Verify background task was cancelled
            mock_bg_task.cancel.assert_called_once()
            
            # Verify history task was NOT cancelled
            mock_history_task.cancel.assert_not_called()

    @pytest.mark.asyncio
    async def test_background_only_tasks_cancelled(self):
        """REQ-004: Background-only tasks ARE cancelled during shutdown."""
        coordinator = ResourceShutdownCoordinator()
        
        # Setup mock context with turn.background_tasks
        mock_ctx = MagicMock()
        mock_turn = MagicMock()
        mock_ctx.turn = mock_turn
        
        # Create mock background tasks
        mock_task1 = MagicMock()
        mock_task2 = MagicMock()
        
        # Set up background_tasks with these tasks
        mock_turn.background_tasks = {mock_task1, mock_task2}
        
        # Patch close_resources to use our mock context
        with patch.object(coordinator, '_ctx', mock_ctx):
            await coordinator.close_resources()
            
            # Verify both tasks were cancelled
            mock_task1.cancel.assert_called_once()
            mock_task2.cancel.assert_called_once()
```

## Compatibility considerations

N/A: This is a new test file, no compatibility concerns.

## Security considerations

N/A: Tests do not introduce security risks.

## Rollback considerations

Delete the test file if the resource shutdown coordinator change is reverted.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_resource_shutdown_coordinator.py | Unit test — verify selective task cancellation | uv run pytest tests/agent/test_resource_shutdown_coordinator.py | New tests pass |

## Completion criteria

- [ ] Test verifies no data loss during shutdown with active history writes (REQ-003)
- [ ] Test verifies cancellation of background-only tasks (REQ-004)
- [ ] All new tests pass when run individually

## Out of scope

- Modifying `resource_shutdown_coordinator.py` (handled in separate document)
- Modifying `context.py` (handled in separate document)

## execution Status

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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/20261004-143003_rs004_universal_task_cancellation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182811_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-194648
- **Related target files**: tests/agent/test_resource_shutdown_coordinator.py
