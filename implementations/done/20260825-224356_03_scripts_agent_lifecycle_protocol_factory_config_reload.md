## Goal

Fix a deterministic bug where `ConfigReloadService.apply_config_dict()` calls a non-existent method on `_ServerLifecycleRouter` via `getattr()`, causing `AttributeError` on every `/reload` that removes a server. Add `cleanup_server_resources(server_key: str) -> str` to `LifecycleManagerProtocol`, implement it on `_ServerLifecycleRouter`, and replace the `getattr()` call with a typed direct call.

## Scope

**In-Scope**:
- `scripts/agent/lifecycle_protocol.py`: add `cleanup_server_resources` to `LifecycleManagerProtocol`.
- `scripts/agent/factory.py`: implement `cleanup_server_resources` on `_ServerLifecycleRouter` delegating to `self._http_mgr._cleanup_server_resources`.
- `scripts/agent/services/config_reload.py`: replace `getattr(lifecycle, "_cleanup_server_resources")(server_key)` with `lifecycle.cleanup_server_resources(server_key)`.
- Regression test adding.

**Out-of-Scope**:
- Changes to `HttpServerLifecycleManager._cleanup_server_resources` itself (introduced as internal refactoring in `plans/done/20260730-211410_plan.md`, not intended as public API).
- Lifecycle state management refactoring.

## Assumptions

- Only one production implementation exists (`_ServerLifecycleRouter`) — confirmed via repository-wide search.
- The caller does not use the return value (confirmed: no capture at call site).
- Return type should be `str` to match `HttpServerLifecycleManager._cleanup_server_resources` actual implementation.

## Design decisions

- Thin delegation method only — no logic duplication.
- Follows same pattern as other public methods on `_ServerLifecycleRouter` (`ensure_ready`, `shutdown_all`, etc.).
- Protocol uses structural subtyping — future implementations will be caught by `mypy`.

## Alternatives considered

- Keep `getattr()` but add `_cleanup_server_resources` to protocol: rejected because string-based dynamic dispatch defeats type checking and is inherently fragile.
- Inline cleanup logic directly in `config_reload.py`: rejected because it would duplicate `HttpServerLifecycleManager`'s cleanup logic and break encapsulation.

## Implementation

### Target files

| File | Change |
|---|---|
| `scripts/agent/lifecycle_protocol.py` | Add protocol method |
| `scripts/agent/factory.py` | Implement delegation method |
| `scripts/agent/services/config_reload.py` | Replace `getattr()` call |

### Procedure

1. **Phase 1: Preparation** — verify existing delegation patterns on `_ServerLifecycleRouter`.
2. **Phase 2: Core Logic**
   - Add `def cleanup_server_resources(self, server_key: str) -> str: ...` to `LifecycleManagerProtocol` (REQ-001).
   - Implement `cleanup_server_resources` on `_ServerLifecycleRouter` (REQ-002).
   - Replace `getattr()` call in `config_reload.py` (REQ-003).
3. **Phase 3: Deployment & Verification**
   - Add regression test (REQ-004).
   - Run `uv run mypy scripts/agent/`.

### Method

```python
# --- REQ-001: Add protocol method ---
# In scripts/agent/lifecycle_protocol.py, after line 60 (get_process_snapshot):

    def cleanup_server_resources(self, server_key: str) -> str:
        """Clean up resources for a removed MCP server. Returns stderr or empty string."""
        ...

# --- REQ-002: Implement on _ServerLifecycleRouter ---
# In scripts/agent/factory.py, after get_subprocess_server_configs() method (~line 250):

    def cleanup_server_resources(self, server_key: str) -> str:
        """Clean up resources for a removed MCP server. Delegates to HttpServerLifecycleManager."""
        return self._http_mgr._cleanup_server_resources(server_key)

# --- REQ-003: Replace getattr() call ---
# In scripts/agent/services/config_reload.py, line 133:
# Before:
#     getattr(lifecycle, "_cleanup_server_resources")(server_key)
# After:
#     lifecycle.cleanup_server_resources(server_key)
```

### Details

- **Protocol method**: Signature matches `HttpServerLifecycleManager._cleanup_server_resources(server_key: str) -> str`. Docstring added for clarity since this was previously private.
- **Delegation**: One-liner following the exact pattern used by other methods on `_ServerLifecycleRouter` (e.g., `get_process_snapshot`, `list_processes`).
- **Call replacement**: Direct attribute access replaces string-based `getattr()`. Return value remains unused (unchanged behavior).

## Compatibility considerations

- Public API unchanged (`ConfigReloadRequest`, `ConfigReloadOutcome`).
- Existing callers of `LifecycleManagerProtocol` methods unaffected.
- No config schema changes required.

## Security considerations

- No new secrets or credentials introduced.
- Cleanup path now correctly executes instead of raising `AttributeError` — this restores intended security behavior (resource cleanup on server removal).

## Rollback considerations

- Revert: remove protocol method, router method, and restore `getattr()` call.
- Git ref-safe rollback: `git checkout HEAD -- scripts/agent/lifecycle_protocol.py scripts/agent/factory.py scripts/agent/services/config_reload.py`.
- No database migration or config file changes.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit/Integration | `uv run pytest tests/agent/services/test_config_reload*.py -v` | Server deletion via `/reload` completes without exception |
| Repository | Type check | `uv run mypy scripts/agent/` | No new errors |

## Completion criteria

- [ ] `cleanup_server_resources` method exists on both `LifecycleManagerProtocol` and `_ServerLifecycleRouter`.
- [ ] `getattr(lifecycle, "_cleanup_server_resources")` pattern does not appear anywhere in repository.
- [ ] New regression test verifies `/reload` server deletion does not raise `AttributeError`.
- [ ] `mypy scripts/agent/` reports no new type errors.

## Out of scope

- Changes to `HttpServerLifecycleManager._cleanup_server_resources` internal logic.
- Lifecycle state management refactoring.
- Adding `gitops_push_blocked` field handling (tracked separately).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Preparation / Refactoring | Pending | — | — | Awaiting implementation |
| 2 | Core Logic Implementation | Pending | — | — | Awaiting implementation |
| 3 | Deployment & Verification | Pending | — | — | Awaiting implementation |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260825_cfgreload_lifecycle_cleanup_getattr_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-141919_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-08-25 22:43:56
- **Related target files**: scripts/agent/lifecycle_protocol.py, scripts/agent/factory.py, scripts/agent/services/config_reload.py
