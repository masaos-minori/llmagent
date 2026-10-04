# retry_once_with_delay: Second-failure exception type masking

## Background

The shared retry helper `retry_once_with_delay` in `scripts/agent/shared/retry_helper.py` catches all exceptions from the first attempt and retries once. On second failure it always raises `RuntimeError` regardless of the original exception type.

## Problem

When the first attempt raises `TimeoutError` and the retry raises `ConnectionRefusedError`, both are silently converted to `RuntimeError`. The caller cannot distinguish between transient network errors and configuration errors.

## Evidence

- File: `scripts/agent/shared/retry_helper.py`
- Line 39: `except Exception:` — catches all exceptions uniformly
- Lines 54-59: second failure always raises `RuntimeError(masked_msg)` regardless of original exception type

```python
try:
    return await fn()
except Exception as retry_err:
    msg = f"{fatal_prefix} {_mask_secrets(str(retry_err))}"
    masked_msg = _mask_secrets(msg)
    logger.error(masked_msg)
    raise RuntimeError(masked_msg) from retry_err
```

## Impact

- Error diagnosis becomes impossible — the root cause is lost
- Callers cannot implement targeted recovery logic based on exception type
- Monitoring/alerting systems cannot differentiate error categories

## Recommended action

Preserve the original exception type on second failure. Instead of wrapping in `RuntimeError`, re-raise the original exception after logging:

```python
except Exception as retry_err:
    msg = f"{fatal_prefix} {_mask_secrets(str(retry_err))}"
    masked_msg = _mask_secrets(msg)
    logger.error(masked_msg)
    # Re-raise the original exception to preserve type information
    raise retry_err
```

If callers need a consistent wrapper, they can catch and wrap at their level.

## Acceptance criteria

- [ ] Original exception type is preserved through retry
- [ ] Test verifies `TimeoutError` remains `TimeoutError` after retry failure
- [ ] Test verifies `ConnectionRefusedError` remains `ConnectionRefusedError` after retry failure
- [ ] Existing callers reviewed for compatibility (some may rely on `RuntimeError`)

## Out of scope

- Changing the retry count or delay behavior
- Adding exponential backoff
