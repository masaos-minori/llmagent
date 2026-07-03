# Implementation: Create `scripts/shared/plugin_tool_invoker.py`

## Goal

Create a new `PluginToolInvoker` class in `scripts/shared/plugin_tool_invoker.py` that encapsulates
plugin tool lookup, execution, return-value validation, and error handling, extracted from
`ToolExecutor.execute()`.

## Scope

- In-Scope: New file `scripts/shared/plugin_tool_invoker.py` with `PluginToolInvoker` class and
  `_PLUGIN_RESULT_TUPLE_LENGTH` constant moved from `tool_executor.py`.
- Out-of-Scope: No changes to `tool_executor.py` in this step (covered by separate doc).

## Assumptions

1. `PluginToolInvoker` has no constructor arguments; reads `plugin_registry.get_tool()` at call time.
2. `_PLUGIN_RESULT_TUPLE_LENGTH = 2` moves here from `tool_executor.py`; nothing else imports it directly.
3. `PluginToolInvoker` imports only from `shared.*` (no agent/), consistent with shared/ layer contract.
4. The `shared → shared` direction is always allowed by `.importlinter`.
5. `deploy/deploy.sh` uses `rsync -av --delete scripts/`, so the new file is deployed automatically.

## Implementation

### Target file

`scripts/shared/plugin_tool_invoker.py` (new file)

### Procedure

1. Create `scripts/shared/plugin_tool_invoker.py` with the content below.
2. Run `uv run ruff format scripts/shared/plugin_tool_invoker.py`.
3. Run `uv run ruff check scripts/shared/plugin_tool_invoker.py` — expect 0 errors.
4. Run `uv run mypy scripts/shared/plugin_tool_invoker.py` — expect 0 errors.
5. Run `PYTHONPATH=scripts uv run lint-imports` — expect 0 violations.

### Method

```python
#!/usr/bin/env python3
"""shared/plugin_tool_invoker.py — Plugin tool execution layer."""

import logging
from typing import Any

from shared import plugin_registry
from shared.transport_dto import ToolCallResult

logger = logging.getLogger(__name__)

_PLUGIN_RESULT_TUPLE_LENGTH = 2


class PluginToolInvoker:
    """Executes plugin tools registered via plugin_registry.register_tool().

    Returns None if no plugin tool is registered for the given name.
    Converts plugin exceptions to ToolCallResult(is_error=True) to keep errors local.
    Performs defensive runtime validation of return value contract even though
    registration-time annotation checks are canonical.
    """

    async def try_execute(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult | None:
        """Execute a plugin tool; return None if not a plugin tool."""
        plugin_fn = plugin_registry.get_tool(tool_name)
        if plugin_fn is None:
            return None
        try:
            result_raw = await plugin_fn(args)
        except Exception as e:  # noqa: BLE001 — plugin errors must not propagate
            msg = f"[plugin error] {tool_name}: {e}"
            logger.error(msg)
            return ToolCallResult(
                output=msg,
                is_error=True,
                request_id="",
                server_key="",
                error_type="tool",
            )
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
        return ToolCallResult(
            output=output,
            is_error=is_error,
            request_id="",
            server_key="",
            error_type="tool" if is_error else "",
        )
```

### Details

- The `# noqa: BLE001` on the `except Exception` line is required because `ruff` flags bare
  `except Exception` under the BLE001 rule. The inline comment explains the suppression reason.
- `_PLUGIN_RESULT_TUPLE_LENGTH = 2` is a module-level constant (not a class attribute) so that
  `plugin_tool_invoker.py` is self-contained without importing from `tool_executor.py`.
- `ToolCallResult` is imported from `shared.transport_dto` (the canonical source), not from
  `shared.tool_executor` (which re-exports it for backward compat only).

## Validation plan

```bash
# Lint
uv run ruff check scripts/shared/plugin_tool_invoker.py
# Expected: 0 errors

# Type check
uv run mypy scripts/shared/plugin_tool_invoker.py
# Expected: 0 errors

# Architecture
PYTHONPATH=scripts uv run lint-imports
# Expected: 0 violations

# Confirm file created
python -c "from shared.plugin_tool_invoker import PluginToolInvoker; print('OK')"
```
