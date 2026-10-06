## Goal

Add regression tests verifying that tracking entries are preserved on getpgid failure and removed only after confirmed process exit.

## Scope

- Create `tests/agent/test_http_lifecycle.py` with tests for getpgid failure scenarios

## Assumptions

- The test framework uses pytest
- The HTTP lifecycle manager is importable from `scripts.agent.http_lifecycle`

## Design decisions

- Use `pytest.raises` context manager to assert specific exceptions are raised
- Mock `os.getpgid` to raise PermissionError on getpgid failure
- Verify tracking entries remain accessible after failed shutdown attempt
- Verify PID is logged when termination fails

## Alternatives considered

- Using `unittest.TestCase.assertRaises` — pytest's `raises` is more concise
- Testing via integration with real subprocesses — too brittle, slow

## Implementation
### Target file
`tests/agent/test_http_lifecycle.py`

### Procedure
Create a new test file with regression tests for getpgid failure scenarios.

### Method
1. Create `tests/agent/test_http_lifecycle.py`
2. Add test for tracking entry persistence on getpgid failure (REQ-004)
3. Add test for PID logging on termination failure (REQ-002)

### Details
```python
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from scripts.agent.http_lifecycle import HttpServerLifecycleManager

class TestHttpServerLifecycleGetPgidFailureScenarios:
    """Tests for REQ-003, REQ-004: Verify tracking entry handling on getpgid failure."""

    @pytest.mark.asyncio
    async def test_tracking_entry_persists_on_termination_failure(self):
        """REQ-004: Tracking entry persists when termination fails after getpgid failure."""
        manager = HttpServerLifecycleManager()
        server_key = "test-server-key"
        
        # Setup mock terminator
        mock_terminator = MagicMock()
        mock_terminator.terminate_with_timeout = AsyncMock(side_effect=PermissionError("Operation not permitted"))
        manager._terminator = mock_terminator
        
        # Setup mock manager for tracking
        mock_manager = MagicMock()
        mock_manager.cleanup_server_key = MagicMock()
        manager._managers[server_key] = mock_manager
        
        # Mock proc object
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_proc.poll.return_value = None  # Process still running
        
        # Patch _create_and_validate_proc to simulate getpgid failure
        with patch.object(manager, '_create_and_validate_proc', side_effect=OSError("getpgid failed")):
            with pytest.raises(OSError, match="getpgid failed"):
                await manager.start_server(server_key, "/nonexistent")
            
            # Verify cleanup_server_key was NOT called (tracking entry retained)
            mock_manager.cleanup_server_key.assert_not_called()

    @pytest.mark.asyncio
    async def test_pid_logged_on_termination_failure(self):
        """REQ-002: PID is logged when termination fails."""
        manager = HttpServerLifecycleManager()
        server_key = "test-server-key"
        
        # Setup mock terminator
        mock_terminator = MagicMock()
        mock_terminator.terminate_with_timeout = AsyncMock(side_effect=PermissionError("Operation not permitted"))
        manager._terminator = mock_terminator
        
        # Setup mock manager for tracking
        mock_manager = MagicMock()
        mock_manager.cleanup_server_key = MagicMock()
        manager._managers[server_key] = mock_manager
        
        # Capture log output
        with patch('scripts.agent.http_lifecycle.logger') as mock_logger:
            with patch.object(manager, '_create_and_validate_proc', side_effect=OSError("getpgid failed")):
                with pytest.raises(OSError, match="getpgid failed"):
                    await manager.start_server(server_key, "/nonexistent")
                
                # Verify error message contains PID
                mock_logger.error.assert_called_once()
                call_args = str(mock_logger.error.call_args)
                assert "PID=" in call_args
```

## Compatibility considerations

N/A: This is a new test file, no compatibility concerns.

## Security considerations

N/A: Tests do not introduce security risks.

## Rollback considerations

Delete the test file if the http_lifecycle change is reverted.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_http_lifecycle.py | Unit test — verify tracking persistence on termination failure | uv run pytest tests/agent/test_http_lifecycle.py | New tests pass |

## Completion criteria

- [ ] Test verifies no orphaned process after getpgid failure scenario (REQ-003)
- [ ] Test verifies tracking entry persists when termination fails (REQ-004)
- [ ] All new tests pass when run individually

## Out of scope

- Modifying `http_lifecycle.py` (handled in separate document)

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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/20261004-143005_hlm006_orphaned_process_on_getpgid.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-105000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-080000
- **Related target files**: tests/agent/test_http_lifecycle.py
