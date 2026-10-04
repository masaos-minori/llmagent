## Goal

Add regression tests verifying that SIGKILL failures are handled gracefully and process verification works correctly.

## Scope

- Create `tests/agent/test_http_lifecycle_process_terminator.py` with tests for SIGKILL failure scenarios

## Assumptions

- The test framework uses pytest
- The process terminator is importable from `scripts.agent.http_lifecycle_process_terminator`

## Design decisions

- Use `pytest.raises` context manager to assert specific exceptions are raised
- Mock `os.killpg` to raise PermissionError on SIGKILL failure
- Verify error is logged and swallowed (not propagated)
- Verify process verification after successful SIGKILL

## Alternatives considered

- Using `unittest.TestCase.assertRaises` — pytest's `raises` is more concise
- Testing via integration with real subprocesses — too brittle, slow

## Implementation
### Target file
`tests/agent/test_http_lifecycle_process_terminator.py`

### Procedure
Create a new test file with regression tests for SIGKILL failure scenarios.

### Method
1. Create `tests/agent/test_http_lifecycle_process_terminator.py`
2. Add test for SIGKILL failure handling (REQ-002)
3. Add test for post-SIGKILL verification (REQ-003)
4. Add test for normal SIGKILL path (REQ-004)

### Details
```python
import pytest
from unittest.mock import patch, MagicMock
from scripts.agent.http_lifecycle_process_terminator import ProcessTerminator

class TestProcessTerminatorSigKillFailureScenarios:
    """Tests for REQ-002, REQ-003, REQ-004: Verify SIGKILL failure handling."""

    def test_sigkill_failure_logs_error_and_returns_false(self):
        """REQ-002: SIGKILL failure is handled gracefully — error logged, False returned."""
        terminator = ProcessTerminator()
        proc = MagicMock()
        proc.pid = 12345
        
        with patch('scripts.agent.http_lifecycle_process_terminator.os') as mock_os:
            mock_os.getpgid.return_value = 12345
            mock_os.killpg.side_effect = PermissionError("Operation not permitted")
            
            result = terminator._escalate_to_sigkill(proc)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_post_sigkill_verification_called_on_success(self):
        """REQ-003: wait_exited() is called after successful SIGKILL."""
        terminator = ProcessTerminator()
        proc = MagicMock()
        proc.pid = 12345
        
        with patch('scripts.agent.http_lifecycle_process_terminator.os') as mock_os:
            mock_os.getpgid.return_value = 12345
            mock_os.killpg.return_value = None
            
            # Mock wait_exited to return True (process exited)
            terminator.wait_exited = MagicMock(return_value=True)
            
            result = await terminator._escalate_to_sigkill(proc)
            
            assert result is True
            terminator.wait_exited.assert_called_once_with(proc)

    @pytest.mark.asyncio
    async def test_normal_sigkill_path_no_regression(self):
        """REQ-004: Normal SIGKILL path works correctly — no regression."""
        terminator = ProcessTerminator()
        proc = MagicMock()
        proc.pid = 12345
        
        with patch('scripts.agent.http_lifecycle_process_terminator.os') as mock_os:
            mock_os.getpgid.return_value = 12345
            mock_os.killpg.return_value = None
            
            # Mock wait_exited to return True (process exited)
            terminator.wait_exited = MagicMock(return_value=True)
            
            result = await terminator._escalate_to_sigkill(proc)
            
            assert result is True
```

## Compatibility considerations

N/A: This is a new test file, no compatibility concerns.

## Security considerations

N/A: Tests do not introduce security risks.

## Rollback considerations

Delete the test file if the process terminator change is reverted.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_http_lifecycle_process_terminator.py | Unit test — verify SIGKILL failure handling | uv run pytest tests/agent/test_http_lifecycle_process_terminator.py | New tests pass |

## Completion criteria

- [ ] Test verifies SIGKILL failure is handled gracefully (REQ-002)
- [ ] Test verifies process verification after SIGKILL escalation (REQ-003)
- [ ] All new tests pass when run individually

## Out of scope

- Modifying `http_lifecycle_process_terminator.py` (handled in separate document)

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
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/20261004-143002_pt003_sigkill_failure_handling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182810_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-194513
- **Related target files**: tests/agent/test_http_lifecycle_process_terminator.py
