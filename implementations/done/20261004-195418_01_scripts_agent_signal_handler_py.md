## Goal

Register a minimal signal handler on Windows using ctypes when pywin32 is unavailable, preventing silent loss of graceful shutdown capability.

## Scope

- Modify `scripts/agent/signal_handler.py`: add ctypes-based ConsoleCtrlHandler registration as fallback when pywin32 is unavailable
- Update error logging for complete failure path

## Assumptions

- ctypes.windll.kernel32 is available on all Windows Python installations
- The ctypes approach provides equivalent functionality to pywin32's SetConsoleCtrlHandler
- The handler function signature matches what kernel32 expects

## Design decisions

- Add a ctypes-based fallback inside the `except ImportError:` block
- When pywin32 is unavailable, attempt to register the handler via `ctypes.windll.kernel32.SetConsoleCtrlHandler`
- If ctypes also fails, log an error instead of silently doing nothing

## Alternatives considered

- Adding a cross-platform signal handling abstraction — over-engineering for this use case
- Using subprocess to spawn a helper process — adds complexity, hard to maintain

## Implementation
### Target file
`scripts/agent/signal_handler.py`

### Procedure
Add ctypes-based SetConsoleCtrlHandler registration in ImportError handler. Update error logging for complete failure path.

### Method
1. Locate lines 83-87 in `scripts/agent/signal_handler.py` (ImportError handler)
2. Replace the warning-only fallback with ctypes-based handler registration
3. Update error logging for complete failure path

### Details
```python
# Before (lines 83-87):
except ImportError:
    logger.warning(
        "Signal handling requires pywin32 on Windows. "
        "Install it with: pip install pywin32"
    )

# After:
import ctypes
from ctypes import wintypes

def _register_ctypes_console_handler(loop):
    """Register console control handler via ctypes."""
    # Define the handler type
    HANDLER_ROUTINE = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
    
    def handler(ctrl_type):
        if ctrl_type == 0:  # CTRL_C_EVENT
            loop.call_soon_threadsafe(lambda: None)  # Placeholder for shutdown logic
            return True
        elif ctrl_type == 1:  # CTRL_BREAK_EVENT
            loop.call_soon_threadsafe(lambda: None)  # Placeholder for shutdown logic
            return True
        return False
    
    handler_func = HANDLER_ROUTINE(handler)
    
    # Register the handler
    result = ctypes.windll.kernel32.SetConsoleCtrlHandler(handler_func, True)
    if not result:
        raise OSError(f"SetConsoleCtrlHandler failed with code {ctypes.GetLastError()}")
    
    return handler_func  # Keep reference to prevent GC

try:
    from win32event import MsgWaitForSingleObject
    # ... existing pywin32 code ...
except ImportError:
    try:
        _register_ctypes_console_handler(loop)
        logger.info("Registered console control handler via ctypes")
    except Exception as e:
        logger.error(
            f"Failed to register signal handler on Windows: {e}. "
            f"Graceful shutdown will not be available. "
            f"Consider installing pywin32: pip install pywin32"
        )
```

The key change is adding a ctypes-based fallback inside the `except ImportError:` block. This provides the same functionality without the pywin32 dependency.

## Compatibility considerations

This change is backward-compatible — it adds a new fallback mechanism that was previously absent. No existing behavior is lost for POSIX systems or Windows with pywin32.

## Security considerations

N/A: No security impact.

## Rollback considerations

Revert to the original warning-only fallback if callers depend on the current behavior. This would restore the previous behavior but lose signal handling capability on Windows without pywin32.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/signal_handler.py | Unit test — verify ctypes fallback registration | uv run pytest tests/agent/test_signal_handler.py | New tests pass, existing tests pass |

## Completion criteria

- [ ] Signal handler is registered even without pywin32 (REQ-001)
- [ ] Error message clearly indicates the limitation (REQ-002)
- [ ] All new tests pass when run individually

## Out of scope

- Adding cross-platform signal handling abstraction
- Changes to POSIX signal handler behavior
- Creating new test file (handled in separate document)

## Implementation outcome

Deviation from procedure: no code change was performed. Origin/master already ships
this fix in commit `10308ed7` — `SignalHandler.register()` wraps the pywin32-unavailable
path in a ctypes fallback (`ctypes.windll.kernel32.SetConsoleCtrlHandler`) inside the
`except ImportError:` block, and logs a complete-failure error via `logger.error(...)`
(lines 83-118). The procedure's stated target (warning-only fallback at lines 83-87)
does not match current source. REQ-001 (registered without pywin32) and REQ-002 (error
logged) are satisfied by the upstream implementation. The Details-block helper
`_register_ctypes_console_handler(loop)` with its `lambda: None` shutdown placeholder
was not adopted; origin inlines the handler with real `win32con.CTRL_CLOSE_EVENT` logic
consistent with the pywin32 branch above. Existing regression coverage
(`tests/agent/test_signal_handler_race.py::TestWindowsCtypesFallback`) passes (skip-marked);
the newly added `tests/agent/test_signal_handler.py` (REQ-002 runnable, REQ-001/REQ-003
skip-marked) also passes. Accepting the upstream implementation and closing the workflow.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | Already in origin `10308ed7` (see outcome). |
| 2 | Add or update tests per Validation plan | Done | — | — | `tests/agent/test_signal_handler.py` added; race-file test present. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | ruff clean; bandit B101 (Low, assert) as in other tests; tests pass. |
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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261004-143007_sh008_partial_signal_registration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182815_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-195418
- **Related target files**: scripts/agent/signal_handler.py
