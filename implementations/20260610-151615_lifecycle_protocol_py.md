# Implementation: lifecycle_protocol.py

## Goal

Tighten `LifecycleManagerProtocol` so that HTTP-specific methods (`start_http_subprocess`) are removed from the shared interface, leaving only methods both HTTP and stdio managers implement. HTTP-only methods move to a separate `HttpLifecycleProtocol`.

## Scope

- Target: `scripts/agent/lifecycle_protocol.py`
- Remove `start_http_subprocess` and `restart_stdio` from `LifecycleManagerProtocol`
- Add narrow `HttpLifecycleProtocol` with `start_http_subprocess`
- Add `StdioLifecycleProtocol` with `restart_stdio`
- `AppServices.lifecycle` type changes from `LifecycleManagerProtocol` to a union or composite
- Update `factory.py` to wire accordingly (factory.py doc handles the wiring change)

## Assumptions

1. `_ServerLifecycleRouter` in `factory.py` is the only concrete implementation of the combined protocol; it will implement all three protocols.
2. `repl.py` and `repl_health.py` only call the shared methods (`ensure_ready`, `shutdown_all`, `restart`, `shutdown_idle`, `get_transport_state`).
3. HTTP-specific calls (`start_http_subprocess`) come only from `repl.py._start_subprocess_servers`.
4. `restart_stdio` calls come only from `repl_health.py._watchdog_check_stdio`.

## Implementation

### Target file

`scripts/agent/lifecycle_protocol.py`

### Procedure

1. Keep `LifecycleManagerProtocol` with: `ensure_ready`, `shutdown_all`, `restart`, `shutdown_idle`, `get_transport_state`.
2. Add `HttpLifecycleProtocol(Protocol)` with: `start_http_subprocess(server_key, cfg) -> None`.
3. Add `StdioLifecycleProtocol(Protocol)` with: `restart_stdio(server_key) -> None`.
4. Remove `start_http_subprocess` and `restart_stdio` from `LifecycleManagerProtocol`.
5. In `context.py`, change `AppServices.lifecycle` type annotation to `LifecycleManagerProtocol` (shared subset only); cast to `HttpLifecycleProtocol` / `StdioLifecycleProtocol` at call sites.

### Method

Structural subtyping — `_ServerLifecycleRouter` in `factory.py` satisfies all three protocols without explicit `implements` declarations.

### Details

```python
@runtime_checkable
class LifecycleManagerProtocol(Protocol):
    async def ensure_ready(self, server_key: str) -> None: ...
    async def shutdown_all(self) -> None: ...
    async def restart(self, server_key: str) -> None: ...
    async def shutdown_idle(self) -> None: ...
    def get_transport_state(self, server_key: str) -> LifecycleState: ...


@runtime_checkable
class HttpLifecycleProtocol(Protocol):
    async def start_http_subprocess(self, server_key: str, cfg: McpServerConfig) -> None: ...


@runtime_checkable
class StdioLifecycleProtocol(Protocol):
    async def restart_stdio(self, server_key: str) -> None: ...
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/lifecycle_protocol.py` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Tests | `uv run pytest tests/ -k "lifecycle"` | all pass |
