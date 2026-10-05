## Goal

Add regression tests verifying that `retry_once_with_delay` preserves original exception types after retry failure.

## Scope

- Create `tests/agent/test_retry_helper.py` with tests for exception type preservation

## Assumptions

- The test framework uses pytest
- The retry helper is importable from `scripts.agent.shared.retry_helper`

## Design decisions

- Use `pytest.raises` context manager to assert specific exception types are raised
- Mock the underlying function to raise different exceptions on first and second attempts
- Test both `TimeoutError` and `ConnectionRefusedError` as specified in REQ-002 and REQ-003

## Alternatives considered

- Using `unittest.TestCase.assertRaises` — pytest's `raises` is more concise
- Testing via integration with real network calls — too brittle, slow

## Implementation
### Target file
`tests/agent/test_retry_helper.py`

### Procedure
Create a new test file with regression tests for exception type preservation.

### Method
1. Create `tests/agent/test_retry_helper.py`
2. Add test for `TimeoutError` preservation
3. Add test for `ConnectionRefusedError` preservation
4. Add test for `RuntimeError` preservation (to ensure existing behavior is maintained)

### Details
```python
import pytest
from unittest.mock import patch, MagicMock
from scripts.agent.shared.retry_helper import retry_once_with_delay

class TestRetryHelperExceptionPreservation:
    """Tests for REQ-002, REQ-003: Verify exception type preservation through retry."""

    def test_timeout_error_preserved(self):
        """REQ-002: TimeoutError raised on second attempt propagates as TimeoutError."""
        call_count = 0
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("First attempt timeout")
            else:
                raise TimeoutError("Second attempt timeout")
        
        with patch('scripts.agent.shared.retry_helper.time.sleep', return_value=None):
            with pytest.raises(TimeoutError, match="Second attempt timeout"):
                retry_once_with_delay(failing_func, delay=0.01)

    def test_connection_refused_error_preserved(self):
        """REQ-003: ConnectionRefusedError raised on second attempt propagates as ConnectionRefusedError."""
        call_count = 0
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionRefusedError("First attempt refused")
            else:
                raise ConnectionRefusedError("Second attempt refused")
        
        with patch('scripts.agent.shared.retry_helper.time.sleep', return_value=None):
            with pytest.raises(ConnectionRefusedError, match="Second attempt refused"):
                retry_once_with_delay(failing_func, delay=0.01)

    def test_runtime_error_preserved(self):
        """Ensure RuntimeError is also preserved (not just wrapped)."""
        call_count = 0
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("First attempt runtime error")
            else:
                raise RuntimeError("Second attempt runtime error")
        
        with patch('scripts.agent.shared.retry_helper.time.sleep', return_value=None):
            with pytest.raises(RuntimeError, match="Second attempt runtime error"):
                retry_once_with_delay(failing_func, delay=0.01)
```

## Compatibility considerations

N/A: This is a new test file, no compatibility concerns.

## Security considerations

N/A: Tests do not introduce security risks.

## Rollback considerations

Delete the test file if the retry helper change is reverted.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_retry_helper.py | Unit test — verify exception type propagation | uv run pytest tests/agent/test_retry_helper.py | New tests pass |

## Completion criteria

- [ ] Test verifies `TimeoutError` remains `TimeoutError` after retry failure (REQ-002)
- [ ] Test verifies `ConnectionRefusedError` remains `ConnectionRefusedError` after retry failure (REQ-003)
- [ ] All new tests pass when run individually

## Out of scope

- Modifying `retry_helper.py` (handled in separate document)
- Modifying `startup_mcp_starter.py` (handled in separate document)

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Deviation: origin/master already ships tests/agent/test_retry_helper.py; did not create a new file. Fixed test_startup_rollback mock-exhaustion regression and updated test_startup_approval_recovery OSError assertion to reflect preserved-type contract. |
| 2 | Add or update tests per Validation plan | Completed | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — |  |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20261004-143000_rh001_retry_exception_type_masking.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182808_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-194143
- **Related target files**: tests/agent/test_retry_helper.py