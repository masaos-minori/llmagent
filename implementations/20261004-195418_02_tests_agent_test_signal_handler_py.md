## Goal

Add regression test verifying that signal handler is registered on Windows without pywin32 via ctypes fallback.

## Scope

- Create `tests/agent/test_signal_handler.py` with test for Windows signal handler fallback

## Assumptions

- The test framework uses pytest
- The signal handler is importable from `scripts.agent.signal_handler`

## Design decisions

- Use `pytest.raises` context manager to assert specific exceptions are raised
- Mock `sys.frozen` and ImportError to simulate Windows without pywin32
- Verify ctypes handler is registered

## Alternatives considered

- Using `unittest.TestCase.assertRaises` — pytest's `raises` is more concise
- Testing via integration with real Windows console — too brittle, platform-specific

## Implementation
### Target file
`tests/agent/test_signal_handler.py`

### Procedure
Create a new test file with regression test for Windows signal handler fallback.

### Method
1. Create `tests/agent/test_signal_handler.py`
2. Add test for handler registration on Windows without pywin32 (REQ-003)

### Details
```python
import pytest
from unittest.mock import patch, MagicMock
from scripts.agent.signal_handler import SignalHandler

class TestSignalHandlerWindowsFallbackScenarios:
    """Tests for REQ-003: Verify Windows signal handler fallback."""

    @pytest.mark.asyncio
    async def test_ctypes_handler_registered_without_pywin32(self):
        """REQ-003: Handler is registered via ctypes when pywin32 is unavailable."""
        handler = SignalHandler()
        
        # Mock sys.frozen to simulate Windows environment
        with patch('sys.frozen', True):
            # Mock asyncio loop
            mock_loop = MagicMock()
            
            # Mock ctypes.windll.kernel32.SetConsoleCtrlHandler to succeed
            with patch('ctypes.windll.kernel32.SetConsoleCtrlHandler') as mock_set_ctrl:
                mock_set_ctrl.return_value = True
                
                # Patch loop.add_signal_handler to raise NotImplementedError
                with patch.object(mock_loop, 'add_signal_handler', side_effect=NotImplementedError()):
                    # Patch logger.warning to capture the call
                    with patch('scripts.agent.signal_handler.logger') as mock_logger:
                        await handler.register(mock_loop)
                        
                        # Verify SetConsoleCtrlHandler was called
                        mock_set_ctrl.assert_called_once()
                        
                        # Verify info-level log was emitted (not just warning)
                        mock_logger.info.assert_called_once()
                        assert "Registered console control handler via ctypes" in str(mock_logger.info.call_args)
```

## Compatibility considerations

N/A: This is a new test file, no compatibility concerns.

## Security considerations

N/A: Tests do not introduce security risks.

## Rollback considerations

Delete the test file if the signal handler change is reverted.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_signal_handler.py | Unit test — verify ctypes fallback registration | uv run pytest tests/agent/test_signal_handler.py | New tests pass |

## Completion criteria

- [ ] Test verifies handler registration on Windows without pywin32 (REQ-003)
- [ ] All new tests pass when run individually

## Out of scope

- Modifying `signal_handler.py` (handled in separate document)

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261004-143007_sh008_partial_signal_registration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182815_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-195418
- **Related target files**: tests/agent/test_signal_handler.py
