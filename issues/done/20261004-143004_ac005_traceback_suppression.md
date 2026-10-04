# AgentContext.__init__: Original traceback suppressed with `from None`

## Background

`AgentContext.__init__()` in `scripts/agent/context.py` loads the agent configuration via `build_agent_config()`. On failure, it wraps the exception in a `RuntimeError` with context about the config directory.

## Problem

The `from None` clause suppresses the original traceback, making it impossible to determine the root cause of configuration loading failures.

## Evidence

- File: `scripts/agent/context.py`
- Lines 307-313:

```python
try:
    self.cfg = build_agent_config()
except Exception as e:
    config_dir = Path(__file__).resolve().parent.parent / "config"
    raise RuntimeError(
        f"Failed to load agent config ({config_dir}): {e.__class__.__name__}: {e}"
    ) from None
```

## Impact

- Debugging configuration errors requires manual inspection of logs
- Stack traces show only the wrapper exception, not the actual failure
- CI/CD pipelines cannot parse the real error from test output

## Recommended action

Remove `from None` to preserve the original traceback chain:

```python
raise RuntimeError(
    f"Failed to load agent config ({config_dir}): {e.__class__.__name__}: {e}"
) from e  # Keep original traceback for debugging
```

If the concern is log verbosity, use `logging.exception()` at the caller level instead of suppressing the traceback.

## Acceptance criteria

- [ ] Original exception chain is preserved in stack traces
- [ ] Test verifies traceback includes both wrapper and original frames
- [ ] Existing error handling at callers reviewed for compatibility

## Out of scope

- Changes to `build_agent_config()` error messages
- Changes to logging format
