# Implementation: shared/plugin_tool_invoker.py — Wrap runtime contract violations as ToolCallResult

## Goal

Wrap `ValueError`/`TypeError` from runtime tuple contract validation in `try_execute()` to return `ToolCallResult(is_error=True)` instead of raising, so invalid runtime returns produce error results rather than exceptions that propagate to the tool executor.

## Scope

**In**: Wrap the post-execution validation block in `try_execute()` with exception handling.

**Out**: Changes to `plugin_registry.py`, tests.

## Assumptions

1. Current code: after `result_raw = await plugin_fn(args)`, a sequence of `if not isinstance(...)` raises `ValueError`/`TypeError`. These are currently uncaught within `try_execute()` and propagate to callers.
2. Callers of `try_execute()` (in `tool_executor.py`) are not necessarily prepared to catch these exceptions.
3. Converting contract violations to `ToolCallResult(is_error=True)` is the right behavior — it surfaces the error as a tool result visible in the conversation, not a silent crash.
4. The function signature and return type remain unchanged: `-> ToolCallResult | None`.

## Implementation

### Target file
`scripts/shared/plugin_tool_invoker.py`

### Procedure
1. Wrap the post-`await` validation block with `try/except (ValueError, TypeError)`.
2. Return `ToolCallResult(is_error=True, ...)` with the error message.

### Method

**Current code (approx lines 44-60):**
```python
        if (
            not isinstance(result_raw, tuple)
            or len(result_raw) != _PLUGIN_RESULT_TUPLE_LENGTH
        ):
            raise ValueError(...)
        output, is_error = result_raw[0], result_raw[1]
        if not isinstance(output, str):
            raise TypeError(...)
        if not isinstance(is_error, bool):
            raise TypeError(...)
```

**Updated code:**
```python
        # Runtime contract validation — returns error result instead of raising
        try:
            if (
                not isinstance(result_raw, tuple)
                or len(result_raw) != _PLUGIN_RESULT_TUPLE_LENGTH
            ):
                raise ValueError(
                    f"Plugin tool {tool_name!r} must return exactly tuple[str, bool]"
                    f" (2 elements), got {type(result_raw).__name__}"
                    f" with len={len(result_raw) if isinstance(result_raw, tuple) else 'N/A'}"
                )
            output, is_error = result_raw[0], result_raw[1]
            if not isinstance(output, str):
                raise TypeError(
                    f"Plugin {tool_name!r}: output must be str, got {type(output).__name__}"
                )
            if not isinstance(is_error, bool):
                raise TypeError(f"Plugin {tool_name!r}: is_error must be bool")
        except (ValueError, TypeError) as contract_err:
            msg = f"[plugin contract violation] {tool_name}: {contract_err}"
            logger.error(msg)
            return ToolCallResult(
                output=msg,
                is_error=True,
                request_id="",
                server_key="",
                error_type="plugin_contract",
            )
```

### Details

- The `error_type` field is set to `"plugin_contract"` to distinguish contract violations from normal `"tool"` errors.
- The outer `except Exception` block for plugin function exceptions remains unchanged (catches errors raised by `await plugin_fn(args)`).
- This change makes runtime contract violations observable in the conversation output, which is better than a silent crash or an unhandled exception.

## Validation plan

- `uv run pytest tests/ -v -k "plugin_tool_invoker or plugin_contract"` — all pass.
- Verify: `tuple` of wrong length → `ToolCallResult(is_error=True)`.
- Verify: non-str first element → `ToolCallResult(is_error=True)`.
- Verify: non-bool second element → `ToolCallResult(is_error=True)`.
- `mypy scripts/shared/plugin_tool_invoker.py` — no new errors.
- `ruff check scripts/shared/plugin_tool_invoker.py` — 0 errors.
