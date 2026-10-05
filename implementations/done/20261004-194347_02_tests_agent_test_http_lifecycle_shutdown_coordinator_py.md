## Goal

Add regression tests verifying that tracking entries are preserved on shutdown failure and removed only after confirmed termination.

## Implementation outcome

Deviation from procedure: the inline draft was NOT applied. It calls
`coordinator.shutdown_all([server_key], timeout=5)` and sets a nonexistent
`coordinator._managers[...]`, neither of which matches the real API
(`shutdown_all(self, manager, terminator=None, fields=None)`). Origin/master already
ships a correct test file in commit `10308ed7` using the real API; it passes (2 passed).
No new file was created and no code was changed. Accepting the upstream implementation
and closing the workflow.

## Scope

- Create `tests/agent/test_http_lifecycle_shutdown_coordinator.py` with tests for shutdown failure scenarios

## Assumptions

- The test framework uses pytest
- The shutdown coordinator is importable from `scripts.agent.http_lifecycle_shutdown_coordinator`

## Design decisions

- Use `pytest.raises` context manager to assert specific exceptions are raised
- Mock `terminate_with_timeout()` to raise OSError on failure
- Verify `cleanup_server_key()` is not called when termination fails
- Verify tracking entry remains accessible after failed shutdown attempt

## Alternatives considered

- Using `unittest.TestCase.assertRaises` — pytest's `raises` is more concise
- Testing via integration with real subprocesses — too brittle, slow

## Implementation
### Target file
`tests/agent/test_http_lifecycle_shutdown_coordinator.py`

### Procedure
Create a new test file with regression tests for shutdown failure scenarios.

### Method
1. Create `tests/agent/test_http_lifecycle_shutdown_coordinator.py`
2. Add test for tracking entry persistence on shutdown failure (REQ-004)
3. Add test for tracking entry removal on successful shutdown (REQ-001)

### Details
```python
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from scripts.agent.http_lifecycle_shutdown_coordinator import ShutdownCoordinator

class TestShutdownCoordinatorFailureScenarios:
    """Tests for REQ-003, REQ-004: Verify tracking entry handling on shutdown failure."""

    @pytest.mark.asyncio
    async def test_tracking_entry_persists_on_termination_failure(self):
        """REQ-004: Tracking entry persists when termination fails."""
        coordinator = ShutdownCoordinator()
        server_key = "test-server-key"
        
        # Setup mock manager
        mock_manager = MagicMock()
        mock_manager.terminate_with_timeout = AsyncMock(side_effect=OSError("Connection refused"))
        mock_manager.cleanup_server_key = MagicMock()
        coordinator._managers[server_key] = mock_manager
        
        # Attempt shutdown
        with pytest.raises(OSError, match="Connection refused"):
            await coordinator.shutdown_all([server_key], timeout=5)
        
        # Verify cleanup_server_key was NOT called
        mock_manager.cleanup_server_key.assert_not_called()

    @pytest.mark.asyncio
    async def test_tracking_entry_removed_on_success(self):
        """REQ-001: Tracking entry is removed after confirmed termination."""
        coordinator = ShutdownCoordinator()
        server_key = "test-server-key"
        
        # Setup mock manager
        mock_manager = MagicMock()
        mock_manager.terminate_with_timeout = AsyncMock(return_value=None)
        mock_manager.cleanup_server_key = MagicMock()
        coordinator._managers[server_key] = mock_manager
        
        # Attempt shutdown
        await coordinator.shutdown_all([server_key], timeout=5)
        
        # Verify cleanup_server_key WAS called
        mock_manager.cleanup_server_key.assert_called_once_with(server_key)
```

## Compatibility considerations

N/A: This is a new test file, no compatibility concerns.

## Security considerations

N/A: Tests do not introduce security risks.

## Rollback considerations

Delete the test file if the shutdown coordinator change is reverted.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_http_lifecycle_shutdown_coordinator.py | Unit test — verify cleanup ordering | uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py | New tests pass |

## Completion criteria

- [ ] Test verifies no zombie process after shutdown failure scenario (REQ-003)
- [ ] Test verifies tracking entry persists on termination failure (REQ-004)
- [ ] All new tests pass when run individually

## Out of scope

- Modifying `http_lifecycle_shutdown_coordinator.py` (handled in separate document)

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
- **Source issue**: issues/20261004-143001_sc002_tracking_data_cleanup_on_failure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-194347
- **Related target files**: tests/agent/test_http_lifecycle_shutdown_coordinator.py
