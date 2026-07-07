# Implementation: M-4 — Add optional snapshot method to LifecycleManagerProtocol (lifecycle_protocol.py)

## Goal

Add an optional `get_process_snapshot()` method to `LifecycleManagerProtocol` with a
default `return None` implementation so that existing mock implementations automatically
satisfy the updated protocol without modification.

## Scope

**Target**: `scripts/agent/lifecycle_protocol.py`

**Step covered**: Plan M-4 step 3 (protocol extension).

**Out of scope**: all other files.

## Assumptions

1. `LifecycleManagerProtocol` is `@runtime_checkable`; adding a method with a default
   body breaks the Protocol contract (Protocol methods must be abstract).
2. Alternative: define the method without a default body; existing concrete
   implementations (`_ServerLifecycleRouter`) must add the method before this lands.
3. Safest approach: add the method signature only (no default body) and update all
   concrete implementations simultaneously.

## Implementation

### Target file

`scripts/agent/lifecycle_protocol.py`

### Procedure

#### Option A (preferred): Add signature only

```python
@runtime_checkable
class LifecycleManagerProtocol(Protocol):
    """Protocol for MCP server lifecycle managers.

    _ServerLifecycleRouter in factory.py is the production implementation.
    HttpServerLifecycleManager is the low-level subprocess manager it delegates to.
    """

    async def ensure_ready(self, server_key: str) -> None: ...
    async def shutdown_all(self) -> None: ...
    async def restart(self, server_key: str) -> None: ...
    async def shutdown_idle(self) -> None: ...
    def get_transport_state(self, server_key: str) -> LifecycleState: ...
    async def start_http_subprocess(
        self, server_key: str, cfg: McpServerConfig
    ) -> None: ...
    def get_process_snapshot(self, server_key: str) -> dict | None: ...
```

#### Option B (if mocks break): Don't add to Protocol; use getattr in callers

If adding the method to the Protocol breaks test mocks, do NOT modify
`lifecycle_protocol.py`. Instead, `McpStatusService` uses:
```python
snapshot_fn = getattr(lifecycle, "get_process_snapshot", None)
if snapshot_fn is not None:
    snapshot = snapshot_fn(server_key)
```

This avoids protocol breakage entirely.

### Method

- Prefer Option B if any test uses `MagicMock(spec=LifecycleManagerProtocol)` — the
  spec mock will auto-add the new method and tests remain unaffected.
- Use Option A if `mypy` raises `Protocol member not implemented` errors on
  `_ServerLifecycleRouter` (it will if `get_process_snapshot` is added to Protocol but
  not the router — but M-4 step 3 adds it there too, so both land together).

### Details

- The docstring update in this file ("HttpServerLifecycleManager satisfies this
  protocol structurally" → `_ServerLifecycleRouter`) is also required by L-1 plan.
  Apply both changes in one edit to avoid a second pass.
- The `dict | None` return type in the Protocol must match the implementation.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check scripts/agent/lifecycle_protocol.py` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Architecture | `lint-imports` | 0 violations |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
