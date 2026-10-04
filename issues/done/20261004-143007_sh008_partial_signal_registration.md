# SignalHandler: Partial signal handler registration on non-POSIX platforms

## Background

`SignalHandler.register()` in `scripts/agent/signal_handler.py` registers SIGTERM/SIGINT handlers using `loop.add_signal_handler()` on POSIX systems. On non-POSIX platforms, it falls back to Windows console control handlers.

## Problem

When `loop.add_signal_handler()` raises `NotImplementedError`, the fallback path requires pywin32. If pywin32 is not installed, the warning is logged but NO signal handler is registered. This means the agent receives no graceful shutdown notification on Windows without pywin32.

## Evidence

- File: `scripts/agent/signal_handler.py`
- Lines 61-98:

```python
for sig in (signal.SIGTERM, signal.SIGINT):
    try:
        loop.add_signal_handler(sig, _sigterm_handler)
    except NotImplementedError:
        try:
            import sys
            if hasattr(sys, "frozen"):
                try:
                    import win32api
                    import win32con
                    def _console_ctrl_handler(ctrl_type: int) -> bool:
                        if ctrl_type == win32con.CTRL_CLOSE_EVENT:
                            loop.call_soon_threadsafe(_sigterm_handler)
                        return True
                    win32api.SetConsoleCtrlHandler(_console_ctrl_handler, True)
                except ImportError:
                    logger.warning("pywin32 not available; signal handling disabled...")
                ...
        except Exception:
            pass  # Silent failure — no handler registered
```

## Impact

- On Windows without pywin32: Ctrl+C/Ctrl+Break produces no graceful shutdown
- Process terminates abruptly, losing in-memory state
- No warning is visible to the user about missing signal handling

## Recommended action

1. Register a minimal fallback handler even without pywin32:

```python
except ImportError:
    logger.warning(
        "pywin32 not available; signal handling disabled on Windows. "
        "Install pywin32 for Ctrl+C/Ctrl+Break support."
    )
    # Register a basic handler using ctypes as alternative
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        SetConsoleCtrlHandler = kernel32.SetConsoleCtrlHandler
        SetConsoleCtrlHandler.argtypes = [ctypes.c_void_p, ctypes.c_long]
        SetConsoleCtrlHandler.restype = ctypes.c_long
        # ... register handler via ctypes
    except Exception:
        logger.error("Cannot install any signal handler on Windows")
```

2. Document the requirement explicitly in the README or configuration docs.

## Acceptance criteria

- [ ] Signal handler is registered even without pywin32 (via ctypes or similar)
- [ ] Error message clearly indicates the limitation
- [ ] Test verifies handler registration on Windows without pywin32
- [ ] Documentation updated to reflect platform requirements

## Out of scope

- Adding cross-platform signal handling abstraction
- Changes to POSIX signal handler behavior
