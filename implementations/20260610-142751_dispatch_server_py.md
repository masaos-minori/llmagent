# Implementation: dispatch.py + server.py — except Exception removal, exception strategy

## Goal

1. `dispatch.py`: remove `except Exception` from `dispatch_tool()`. Catch `ValueError`
   (validation/user errors) only; all other exceptions propagate to the caller.
   Remove `_handle_tool_exception()` helper.
2. `server.py`: split `run_stdio()` `except Exception` into `orjson.JSONDecodeError`
   and a narrower handler for dispatch errors.

## Scope

- `scripts/mcp/dispatch.py` — remove broad except, keep ValueError handling
- `scripts/mcp/server.py` — split run_stdio except

## Implementation

### dispatch.py

Remove `_handle_tool_exception()`. In `dispatch_tool()`:

```python
async def dispatch_tool(
    table: Mapping[str, Callable[[ToolArgs], Awaitable[str]]],
    name: str,
    args: ToolArgs,
) -> tuple[str, bool]:
    if not isinstance(name, str) or not name.strip():
        logger.warning("dispatch_tool called with empty tool name")
        return "Tool name must be a non-empty string", True

    handler = table.get(name)
    if handler is None:
        logger.warning(f"Unknown tool requested: {name}")
        return f"Unknown tool: {name}", True

    try:
        result = await handler(args)
        return result, False
    except ValueError as e:
        # Validation / user-input errors: return as tool error, not server fault
        logger.warning(f"Tool '{name}' validation error: {e}")
        return f"Validation error: {e}", True
    # All other exceptions (RuntimeError, IOError, etc.) propagate to the caller.
```

### server.py run_stdio

Replace the single `except Exception as e:` block with two handlers:

```python
except orjson.JSONDecodeError as e:
    logger.error(f"run_stdio JSON decode error: {e}")
    result = f"JSON decode error: {e}"
    is_error = True
except Exception as e:
    logger.error(f"run_stdio dispatch error: {e}")
    result = f"Internal server error: {e}"
    is_error = True
```

Note: keeping `except Exception` in run_stdio for stdio transport safety
(stdio transport must always write a response; crashing silently would break the protocol).
The `dispatch()` method itself now propagates non-ValueError exceptions from handlers,
but run_stdio catches them at the transport boundary as a last resort.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/mcp/dispatch.py scripts/mcp/server.py` | 0 errors |
| Type | `uv run mypy scripts/mcp/dispatch.py` | no new errors |
| Tests | `uv run pytest tests/ -k "mcp or server" -x -q` | all pass |
| No _handle_tool_exception | `grep "_handle_tool_exception" scripts/mcp/dispatch.py` | 0 hits |
