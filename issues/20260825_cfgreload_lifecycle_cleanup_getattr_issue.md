# Config reload's server-removal cleanup path calls a method _ServerLifecycleRouter does not define

## Priority
High

## Summary
`ConfigReloadService.apply_config_dict()` cleans up removed MCP servers via `getattr(lifecycle, "_cleanup_server_resources")(server_key)`. `ctx.services_required.lifecycle` is typed `LifecycleManagerProtocol`, whose production implementation is `_ServerLifecycleRouter` (`scripts/agent/factory.py`) — and `_ServerLifecycleRouter` does not define `_cleanup_server_resources` and has no `__getattr__` delegation to the object that does (`HttpServerLifecycleManager` in `http_lifecycle.py`). Removing a server via `/reload` today raises `AttributeError`.

## Background
N/A: covered by Summary.

## Problem
Verified against current source:
- `scripts/agent/services/config_reload.py`, inside `apply_config_dict()`:
  ```
  lifecycle = ctx.services_required.lifecycle
  if lifecycle is not None:
      getattr(lifecycle, "_cleanup_server_resources")(server_key)
  ```
- `scripts/agent/lifecycle_protocol.py`'s `LifecycleManagerProtocol` (the declared type of `ctx.services_required.lifecycle`) does not declare `_cleanup_server_resources`.
- `scripts/agent/factory.py`'s `_ServerLifecycleRouter` (the production implementation, per its own docstring "Delegates subprocess management to HttpServerLifecycleManager (_http_mgr)") does not define `_cleanup_server_resources` and has no `__getattr__` override — confirmed by grep, no match in `factory.py`.
- `_cleanup_server_resources(self, server_key: str) -> str` is defined only on `HttpServerLifecycleManager` (`scripts/agent/http_lifecycle.py:239`), which `_ServerLifecycleRouter` holds as a private `self._http_mgr` and does not expose.

This is a confirmed, unconditional bug given the current type wiring — not merely a risk. Any `/reload` call that removes an MCP server from the config will raise `AttributeError`, since `_ServerLifecycleRouter` has no `_cleanup_server_resources` attribute at all.

Also note: the real method returns `str` (captured stderr), not `None` — any typed replacement must account for that return value or explicitly discard it.

## Reason for Change
This is a string-based dynamic call that bypasses type checking, is invisible to `LifecycleManagerProtocol`, and breaks on the very first exercised call rather than silently. It should be replaced with a typed protocol method before the next `/reload` that removes a server is exercised in any environment.

## Implementation Intent
Add a public method to `LifecycleManagerProtocol` and implement it on `_ServerLifecycleRouter`, delegating to `HttpServerLifecycleManager._cleanup_server_resources()`. Replace the `getattr(...)` call in `config_reload.py` with a direct typed call.

## Target Files or Areas
- `scripts/agent/services/config_reload.py`
- `scripts/agent/lifecycle_protocol.py`
- `scripts/agent/factory.py` (`_ServerLifecycleRouter`)
- `scripts/agent/http_lifecycle.py` (`HttpServerLifecycleManager._cleanup_server_resources`, confirmed as the concrete implementation)

## Required Changes
- Add `cleanup_server_resources(self, server_key: str) -> str` (or `-> None` if the caller does not need the captured stderr — decide during implementation) to `LifecycleManagerProtocol`.
- Implement it on `_ServerLifecycleRouter`, delegating to `self._http_mgr._cleanup_server_resources(server_key)`.
- Replace `getattr(lifecycle, "_cleanup_server_resources")(server_key)` in `config_reload.py` with `lifecycle.cleanup_server_resources(server_key)`.

## Constraints
- Preserve the existing return value (`str`, captured stderr) unless the config-reload caller genuinely has no use for it — do not silently drop diagnostic information without confirming it is unused elsewhere.

## Acceptance Criteria
- [ ] No `getattr(lifecycle, "_cleanup_server_resources")` remains anywhere in the codebase.
- [ ] The cleanup method is declared on `LifecycleManagerProtocol` and type-checks (`mypy`).
- [ ] Removing a server via `/reload` triggers cleanup without `AttributeError`.

## Testing Expectations
- Add or adjust a unit test that removes a server config via `/reload` and asserts cleanup is invoked without raising.
- `uv run mypy scripts/agent/` passes with the new protocol method.

## Documentation Impact
N/A: internal implementation detail, not part of any documented public behavior.

## Out of Scope
- Broader lifecycle-state refactoring beyond this one method.
- Changing `HttpServerLifecycleManager._cleanup_server_resources()`'s own behavior.

## Dependencies
- N/A: none.

## Unresolved Questions
- Whether the new protocol method should return `str` (preserving the captured stderr for logging) or `None` (if `config_reload.py` never uses the return value). Confirm by checking whether `apply_config_dict()`'s call site is ever going to log or report this value.

## AI Implementation Instruction
Confirm during implementation that `_ServerLifecycleRouter` is the only production implementer of `LifecycleManagerProtocol` that needs this method (check for other implementers, e.g. test doubles, via `grep -rn "LifecycleManagerProtocol" scripts/ tests/`). Keep the change minimal: add one protocol method, one implementation, one call-site replacement. Do not rename or restructure `HttpServerLifecycleManager`.
