# Implementation: agent/lifecycle_protocol.py — new Protocol definition

## Goal

Create a new `LifecycleManagerProtocol` in `agent/lifecycle_protocol.py` to replace the `ServerLifecycleManager` type in `AgentContext.services.lifecycle`. This allows `factory.py` to inject either `HttpServerLifecycleManager` or `StdioServerLifecycleManager` directly without depending on the facade.

## Scope

- New file: `scripts/agent/lifecycle_protocol.py`
- Defines `LifecycleManagerProtocol(Protocol)` with the common public methods.
- No changes to existing callers yet (that's subsequent steps).

## Assumptions

- Protocol (structural subtyping) is preferred over Union type per the plan's recommendation (Option A).
- `HttpServerLifecycleManager` and `StdioServerLifecycleManager` both implement the protocol's interface.

## Implementation

### Target file

`scripts/agent/lifecycle_protocol.py` (new)

### Procedure

1. Create `scripts/agent/lifecycle_protocol.py` with:
   - `from typing import Protocol, runtime_checkable`
   - `@runtime_checkable` decorator
   - `class LifecycleManagerProtocol(Protocol)` with async methods
2. Include all public methods from `ServerLifecycleManager` (from `scripts/agent/lifecycle.py` lines 45–133):
   - `ensure_ready(server_key: str) -> None`
   - `shutdown_all() -> None`
   - `start_http_subprocess(server_key: str, cfg: McpServerConfig) -> None`
   - `restart(server_key: str) -> None`
   - `shutdown_idle() -> None`
   - `get_transport_state(server_key: str) -> LifecycleState`
   - `restart_stdio(server_key: str) -> None`
3. Import `LifecycleState` from `agent.lifecycle` (or define separately — check if `LifecycleState` is still needed).
4. Import `McpServerConfig` from `shared.mcp_config`.

### Method

New file creation using Protocol structural typing.

### Details

```python
"""agent/lifecycle_protocol.py
LifecycleManager protocol type for structural subtyping.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from shared.mcp_config import McpServerConfig
from agent.lifecycle import LifecycleState


@runtime_checkable
class LifecycleManagerProtocol(Protocol):
    """Protocol for MCP server lifecycle managers.

    Both HttpServerLifecycleManager and StdioServerLifecycleManager
    satisfy this protocol structurally.
    """

    async def ensure_ready(self, server_key: str) -> None: ...
    async def shutdown_all(self) -> None: ...
    async def start_http_subprocess(
        self, server_key: str, cfg: McpServerConfig
    ) -> None: ...
    async def restart(self, server_key: str) -> None: ...
    async def shutdown_idle(self) -> None: ...
    def get_transport_state(self, server_key: str) -> LifecycleState: ...
    async def restart_stdio(self, server_key: str) -> None: ...
```

## Validation plan

1. `uv run python -c "from agent.lifecycle_protocol import LifecycleManagerProtocol"` — import succeeds.
2. `uv run ruff check scripts/agent/lifecycle_protocol.py` — no errors.
3. `uv run mypy scripts/agent/lifecycle_protocol.py` — no errors.
