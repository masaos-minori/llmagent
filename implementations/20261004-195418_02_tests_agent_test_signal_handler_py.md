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

## Implementation outcome

Deviation from procedure: the inline draft was NOT applied. It imports
`from scripts.agent.signal_handler import SignalHandler` (the real module is imported as
`agent.signal_handler`, per `scripts/agent/__init__.py` and `scripts/agent/repl.py`),
constructs `SignalHandler()` (no-arg; the real constructor is
`SignalHandler(ctx, shutdown_event)`), awaits `handler.register(...)` (the real method is
synchronous and returns `None`), and patches `scripts.agent.signal_handler.logger` and
`ctypes.windll.kernel32.SetConsoleCtrlHandler` (both raise AttributeError on POSIX —
`ctypes.windll` is absent). Origin/master did not create this separate file; it folded a
single skip-marked REQ-001 test into
`tests/agent/test_signal_handler_race.py::TestWindowsCtypesFallback`.

Implemented intent against the real API instead. Created `tests/agent/test_signal_handler.py`
(`TestWindowsCtypesFallback`):
- `test_complete_failure_logs_error` (REQ-002): runnable on POSIX — forces the
  `NotImplementedError` fallback path, sets `sys.frozen`, and injects a raising
  `ctypes.WINFUNCTYPE` via `patch.dict` so the complete-failure branch logs an error.
  Deterministic across repeated and reordered runs; leaves no `ctypes`/`sys` state behind.
- `test_registered_without_pywin32` (REQ-001/REQ-003): marked `skipif` because successful
  registration requires Windows-platform simulation — `ctypes.WINFUNCTYPE` and
  `ctypes.windll` are gated on `os.name == "nt"` and absent on POSIX CI (verified against
  `ctypes/__init__.py` line 112). Injecting them into global ctypes state proved
  order-dependent/flaky, so it is recorded as a skip rather than a fragile test.

Ruff clean; bandit findings are B101 (`assert_used`, Low severity), consistent with every
other file under `tests/agent/`. Full agent suite: 3167 passed, 10 skipped, 0 failed — no
regression (source unchanged; only a new test file added).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | Created `tests/agent/test_signal_handler.py` against real API (see outcome). |
| 2 | Add or update tests per Validation plan | Done | — | — | 1 passed (REQ-002) + 1 skip (REQ-001/REQ-003). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | ruff clean; bandit B101 (Low); full agent suite 3167 passed / 0 failed. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | Out of scope per procedure. |

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
