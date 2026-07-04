# Implementation: Create `scripts/shared/tool_lifecycle.py`

## Goal

Create a new file `scripts/shared/tool_lifecycle.py` containing only `LifecycleProtocol`, extracted
from `scripts/shared/tool_executor.py`. This resolves the circular import that would otherwise arise
when `tool_executor.py` imports from `tool_transport_invoker.py` and vice versa.

## Scope

- In-Scope: New file `scripts/shared/tool_lifecycle.py` with `LifecycleProtocol` only.
- Out-of-Scope: No changes to `tool_executor.py` in this step (covered by separate doc).
  No changes to any other file.

## Assumptions

1. `LifecycleProtocol` is currently defined in `scripts/shared/tool_executor.py` and exported
   from there. After extraction, `tool_executor.py` must import it from `tool_lifecycle.py`.
2. No other file outside `tool_executor.py` currently imports `LifecycleProtocol` directly from
   `tool_executor`. Verify: `grep -rn "LifecycleProtocol" scripts/ tests/`.
3. `shared → shared` direction is allowed by `.importlinter`.
4. `deploy/deploy.sh` uses `rsync scripts/` wholesale — no manual update needed.

## Implementation

### Target file

`scripts/shared/tool_lifecycle.py` (new file)

### Procedure

1. Create `scripts/shared/tool_lifecycle.py` with the content below.
2. Run `uv run ruff check scripts/shared/tool_lifecycle.py` — expect 0 errors.
3. Run `uv run mypy scripts/shared/tool_lifecycle.py` — expect 0 errors.

### Method

```python
#!/usr/bin/env python3
"""shared/tool_lifecycle.py — MCP server lifecycle protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LifecycleProtocol(Protocol):
    """Protocol for MCP server lifecycle managers injected into ToolExecutor."""

    async def ensure_ready(self, server_key: str) -> None:
        """Ensure the MCP server identified by server_key is ready to accept calls."""
        ...
```

### Details

- `@runtime_checkable` allows `isinstance(obj, LifecycleProtocol)` checks at runtime, matching
  the existing definition in `tool_executor.py`.
- The docstrings mirror those in the original `tool_executor.py` definition.
- No imports from other `shared.*` modules needed — `Protocol` and `runtime_checkable` are
  from `typing` (stdlib).

## Validation plan

```bash
# Lint
uv run ruff check scripts/shared/tool_lifecycle.py
# Expected: 0 errors

# Type check
uv run mypy scripts/shared/tool_lifecycle.py
# Expected: 0 errors

# Verify importable
python -c "from shared.tool_lifecycle import LifecycleProtocol; print('OK')"

# Architecture
PYTHONPATH=scripts uv run lint-imports
# Expected: 0 violations
```
