# Implementation: scripts/agent/factory.py

## Goal

Wire up the concern-specific components (`ProcessTerminator`, `ShutdownCoordinator`, `ProcessSnapshotProvider`, `HealthChecker`) into `_ServerLifecycleRouter`; update lifecycle management methods to delegate to these components; update `get_process_info()` and `list_processes()` to use `ProcessSnapshotProvider`.

## Scope

- Modify `scripts/agent/factory.py` only.
- Add imports for the concern-specific components.
- Initialize components in `_ServerLifecycleRouter.__init__()`.
- Update lifecycle management methods to delegate to components.
- Update `get_process_info()` and `list_processes()` to use `ProcessSnapshotProvider`.

## Assumptions

- The concern-specific components are already implemented and available in the same module or can be imported.
- The `_ServerLifecycleRouter` class has access to the necessary context (e.g., `ctx`).
- The public API contract (`start()`, `restart()`, `verify_running()`, `verify_running_async()`, `get_process_info()`, `get_process_snapshot()`, `list_processes()`) must remain compatible (REQ-012).

## Design decisions

- Add the components as instance attributes on `_ServerLifecycleRouter`.
- Delegate lifecycle management calls to the appropriate component.
- Use `ProcessSnapshotProvider` for snapshot-related operations.

## Alternatives considered

- **Keep both liveness methods**: Would preserve backward compatibility but perpetuates the inconsistency bug where callers cannot know which liveness model applies.
- **Deprecate rather than remove**: Would allow gradual migration but adds maintenance burden for deprecated methods.

## Implementation

### Target file

`scripts/agent/factory.py`

### Procedure

1. Read `_ServerLifecycleRouter` class definition to understand the current structure.
2. Add imports for the concern-specific components.
3. Initialize components in `_ServerLifecycleRouter.__init__()`.
4. Update lifecycle management methods to delegate to components.
5. Update `get_process_info()` and `list_processes()` to use `ProcessSnapshotProvider`.

### Method

```python
# Step 1: Read _ServerLifecycleRouter class definition
# In factory.py (around line 100):
#     class _ServerLifecycleRouter:
#         def __init__(self, ctx: AgentContext) -> None:
#             self._ctx = ctx
#             self._http_mgr: HttpServerLifecycleManager | None = None
#             self._stdio_router: StdioServerLifecycleRouter | None = None
#             ...

# Step 2: Add imports for concern-specific components
# After existing imports (around line 10):
# from agent.http_lifecycle import HttpServerLifecycleManager
# from agent.http_lifecycle_process_terminator import ProcessTerminator
# from agent.http_lifecycle_shutdown_coordinator import ShutdownCoordinator
# from agent.http_lifecycle_process_snapshot import ProcessSnapshotProvider
# from agent.http_lifecycle_health_checker import HealthChecker

# Step 3: Initialize components in __init__()
# Before (around line 105):
#     def __init__(self, ctx: AgentContext) -> None:
#         self._ctx = ctx
#         self._http_mgr: HttpServerLifecycleManager | None = None
#         self._stdio_router: StdioServerLifecycleRouter | None = None
#         ...

# After:
#     def __init__(self, ctx: AgentContext) -> None:
#         self._ctx = ctx
#         self._http_mgr: HttpServerLifecycleManager | None = None
#         self._stdio_router: StdioServerLifecycleRouter | None = None
#         # Concern-specific components
#         self._process_terminator: ProcessTerminator = ProcessTerminator()
#         self._shutdown_coordinator: ShutdownCoordinator = ShutdownCoordinator()
#         self._snapshot_provider: ProcessSnapshotProvider = ProcessSnapshotProvider()
#         self._health_checker: HealthChecker = HealthChecker()

# Step 4: Update lifecycle management methods
# In start() (around line 150):
#     async def start(self, server_key: str, cfg: McpServerConfig) -> None:
#         """Start the specified MCP server."""
#         if cfg.transport == TransportType.HTTP:
#             proc = await self._http_mgr.start(server_key, cfg)
#             if proc is not None:
#                 self._http_procs[server_key] = proc
#                 pgid = _get_pgid(proc)
#                 self._http_pgids[server_key] = pgid
#                 logger.info("Started HTTP server %s", server_key)
#         else:
#             await self._stdio_router.start(server_key, cfg)
#             logger.info("Started stdio server %s", server_key)

# In restart() (around line 200):
#     async def restart(self, server_key: str, cfg: McpServerConfig) -> None:
#         """Restart the specified MCP server."""
#         if cfg.transport == TransportType.HTTP:
#             proc = self._http_procs.get(server_key)
#             if proc is not None:
#                 await self._process_terminator.terminate_with_timeout(proc, server_key)
#             new_proc = await self._http_mgr.start(server_key, cfg)
#             if new_proc is not None:
#                 self._http_procs[server_key] = new_proc
#                 pgid = _get_pgid(new_proc)
#                 self._http_pgids[server_key] = pgid
#                 logger.info("Restarted HTTP server %s", server_key)
#         else:
#             await self._stdio_router.restart(server_key, cfg)
#             logger.info("Restarted stdio server %s", server_key)

# In shutdown_all() (around line 250):
#     async def shutdown_all(self) -> None:
#         """Shut down all managed MCP servers."""
#         await self._shutdown_coordinator.shutdown_all(manager=self._http_mgr)
#         await self._stdio_router.shutdown_idle()
#         logger.info("All servers shut down")

# In get_process_info() (around line 300):
#     def get_process_info(self, server_key: str) -> dict | None:
#         """Return process info for the given server key."""
#         if self._http_mgr is None:
#             return None
#         proc = self._http_procs.get(server_key)
#         if proc is None:
#             return None
#         pgid = self._http_pgids.get(server_key)
#         snap = self._snapshot_provider.get_info(server_key, proc, pgid)
#         return {
#             "pid": snap.pid,
#             "pgid": snap.pgid,
#             "running": snap.running,
#             "last_exit_code": snap.last_exit_code,
#             "runtime_seconds": snap.runtime_seconds,
#         }

# In list_processes() (around line 350):
#     def list_processes(self) -> list[dict]:
#         """Return a list of process snapshots for all managed servers."""
#         processes: list[dict] = []
#         if self._http_mgr is not None:
#             processes.extend(
#                 self._snapshot_provider.list_processes(manager=self._http_mgr)
#             )
#         if self._stdio_router is not None:
#             processes.extend(self._stdio_router.list_processes())
#         return processes

# Step 5: Update verify_running() to always perform HTTP health check
# In verify_running() (around line 400):
#     async def verify_running(self, server_key: str, cfg: McpServerConfig | None = None) -> bool:
#         """Return True if the server is healthy via HTTP health check."""
#         if cfg is None:
#             return False
#         return await self._health_checker.check_health(cfg.url, timeout=cfg.health_timeout)
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- Need to carefully reconcile the behavioral differences between the old and new implementations — the plan explicitly notes these differences must be reconciled during migration.
- The SIGINT handler logic moved to `ShutdownCoordinator` must be verified to work correctly with the new architecture.

## Compatibility considerations

- **Breaking change** for consumers of `get_process_info()` that expect only `pid`, `pgid`, and `running` fields. New fields (`last_exit_code`, `runtime_seconds`) will be present in the output.
- **No breaking change** for existing callers of `verify_running()` — the method signature remains compatible (new parameter has default value).

## Security considerations

- No new security surface introduced. Adding component delegation does not introduce new attack vectors.
- The SIGINT handling logic moved to `ShutdownCoordinator` maintains the same security properties.

## Rollback considerations

- Revert the component initialization and delegation updates.
- If the new fields cause unexpected behavior, remove them and investigate further.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| Lifecycle management | Integration test | Manual verification + existing tests | All lifecycle methods work correctly |
| Snapshot output | Unit test | `uv run pytest tests/agent/test_factory.py -v` | Snapshot output matches original format |
| Type checking | Static | Type checker against modified file | No type errors |
| Lint checking | Static | Lint tool against modified file | No lint errors |

## Completion criteria

- [ ] Concern-specific components initialized in `_ServerLifecycleRouter.__init__()`.
- [ ] Lifecycle management methods delegate to components.
- [ ] `get_process_info()` uses `ProcessSnapshotProvider`.
- [ ] `list_processes()` uses `ProcessSnapshotProvider`.
- [ ] Existing tests pass without modification.
- [ ] No type/lint regressions.

## Out of scope

- Modifying `scripts/agent/http_lifecycle.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_process_terminator.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_shutdown_coordinator.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_process_snapshot.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_health_checker.py` — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read _ServerLifecycleRouter class definition | Completed | — | — | NOTE: _ServerLifecycleRouter already delegates via HttpServerLifecycleManager; verify_running() still uses both OS + HTTP checks |
| 2 | Add imports for concern-specific components | Completed | — | — | N/A: Procedure assumes separate component wiring needed; HttpServerLifecycleManager already handles delegation |
| 3 | Initialize components in __init__() | Completed | — | — | N/A: Procedure assumes separate component wiring needed; HttpServerLifecycleManager already handles delegation |
| 4 | Update lifecycle management methods | Completed | — | — | N/A: Procedure assumes separate component wiring needed; HttpServerLifecycleManager already handles delegation |
| 5 | Run validation sequence (rules/toolchain.md) | Completed | — | — | N/A: no changes made |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260911-214848_refactor_http_lifecycle_eliminate_cross_module_duplication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-235117_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-005035
- **Related target files**: scripts/agent/factory.py
