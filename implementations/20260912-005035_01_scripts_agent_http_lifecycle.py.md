# Implementation: scripts/agent/http_lifecycle.py

## Goal

Remove inline implementations (`_terminate_with_timeout()`, `_wait_exited()`, `shutdown_all()`, `_build_snapshot_dict()`, `list_processes()`); delegate to concern-specific components; unify `verify_running()` and `verify_running_async()` into consistent HTTP health-check semantics.

## Scope

- Modify `scripts/agent/http_lifecycle.py` only.
- Remove `_terminate_with_timeout()` (~40 lines) and replace callers with `self._process_terminator.terminate_with_timeout()`.
- Remove `_wait_exited()` (~15 lines) and replace callers with `self._process_terminator.wait_exited()`.
- Remove `shutdown_all()` (~45 lines) and replace callers with `ShutdownCoordinator.shutdown_all()`.
- Remove `_build_snapshot_dict()` (~18 lines) and replace callers with `ProcessSnapshotProvider.get_snapshot()`.
- Remove `list_processes()` (~7 lines) and replace callers with `ProcessSnapshotProvider.list_processes()`.
- Unify `verify_running()` and `verify_running_async()` — keep HTTP check semantics, remove `proc.poll()` shortcut.

## Assumptions

- `ProcessTerminator.terminate_with_timeout()` covers all behaviors previously handled by `_terminate_with_timeout()` (early-exit check, pgid fallback warning, SIGKILL escalation).
- `ShutdownCoordinator.shutdown_all()` can accept the same parameters as the current `shutdown_all()` method.
- `ProcessSnapshotProvider.get_snapshot()` returns a JSON-serializable dict compatible with existing consumers.
- `ProcessSnapshotProvider.list_processes()` accepts an `HttpServerLifecycleManager` instance and produces snapshots matching the original `list_processes()` output format.
- The public API contract (`start()`, `restart()`, `verify_running()`, `verify_running_async()`, `get_process_info()`, `get_process_snapshot()`, `list_processes()`) must remain compatible (REQ-012).

## Design decisions

- **Terminate**: Replace `_terminate_with_timeout()` calls with `self._process_terminator.terminate_with_timeout()`. Add missing behaviors (early-exit check, pgid fallback warning) to `ProcessTerminator` first before replacing callers.
- **Shutdown**: Replace `shutdown_all()` calls with `ShutdownCoordinator.shutdown_all(manager=self)` or equivalent. Move SIGINT absorption logic into the coordinator.
- **Snapshot**: Replace `_build_snapshot_dict()` calls with `ProcessSnapshotProvider.get_snapshot(server_key, proc, pgid)`. Replace `list_processes()` calls with `ProcessSnapshotProvider.list_processes(manager=self)`.
- **Liveness**: Unify `verify_running()` to always perform HTTP health check (same as `verify_running_async()`). Remove the `proc.poll()` shortcut.

## Alternatives considered

- **Keep both liveness methods**: Would preserve backward compatibility but perpetuate the inconsistency bug where callers cannot know which liveness model applies.
- **Deprecate rather than remove**: Would allow gradual migration but adds maintenance burden for deprecated methods.

## Implementation

### Target file

`scripts/agent/http_lifecycle.py`

### Procedure

1. Read `ProcessTerminator.terminate_with_timeout()` to verify it covers all behaviors of `_terminate_with_timeout()`. If missing behaviors exist, add them first (see Phase 1).
2. Replace all calls to `self._terminate_with_timeout(proc, server_key, timeout=...)` with `self._process_terminator.terminate_with_timeout(proc, server_key, timeout=...)`.
3. Replace all calls to `self._wait_exited(proc, timeout)` with `await self._process_terminator.wait_exited(proc, server_key, poll_interval=..., timeout=timeout)`.
4. Replace all calls to `self.shutdown_all()` with `ShutdownCoordinator.shutdown_all(manager=self)`.
5. Replace all calls to `self._build_snapshot_dict(server_key)` with `ProcessSnapshotProvider.get_snapshot(server_key, proc, pgid)`.
6. Replace all calls to `self.list_processes()` with `ProcessSnapshotProvider.list_processes(manager=self)`.
7. Unify `verify_running()` to always perform HTTP health check (same as `verify_running_async()`).
8. Remove `_terminate_with_timeout()` method definition.
9. Remove `_wait_exited()` method definition.
10. Remove `shutdown_all()` method definition.
11. Remove `_build_snapshot_dict()` method definition.
12. Remove `list_processes()` method definition.

### Method

```python
# Step 2: Replace terminate_with_timeout calls
# In _create_and_validate_proc() (line ~349):
# Before: await self._terminate_with_timeout(proc, server_key, timeout=TERMINATE_TIMEOUT_SEC)
# After: await self._process_terminator.terminate_with_timeout(proc, server_key, timeout=TERMINATE_TIMEOUT_SEC)

# In _health_poll_until_ready() (line ~446):
# Before: await self._terminate_with_timeout(proc, server_key, timeout=TERMINATE_TIMEOUT_SEC)
# After: await self._process_terminator.terminate_with_timeout(proc, server_key, timeout=TERMINATE_TIMEOUT_SEC)

# In restart() (line ~514):
# Before: await self._terminate_with_timeout(proc, server_key)
# After: await self._process_terminator.terminate_with_timeout(proc, server_key)

# In shutdown_all() (line ~554):
# Before: await self._terminate_with_timeout(proc, key, timeout=TERMINATE_TIMEOUT_SEC)
# After: await self._process_terminator.terminate_with_timeout(proc, key, timeout=TERMINATE_TIMEOUT_SEC)

# Step 3: Replace wait_exited calls
# In _terminate_with_timeout() (lines ~150, ~169):
# Before: if await self._wait_exited(proc, timeout):
# After: if await self._process_terminator.wait_exited(proc, server_key, poll_interval=_TERMINATE_POLL_INTERVAL_SEC, timeout=timeout):

# Step 4: Replace shutdown_all calls
# In factory.py line ~171:
# Before: await self._http_mgr.shutdown_all()
# After: await ShutdownCoordinator.shutdown_all(manager=self._http_mgr)

# Step 5: Replace _build_snapshot_dict calls
# In get_process_info() (line ~238):
# Before: d = self._build_snapshot_dict(server_key)
# After: snap = ProcessSnapshotProvider.get_info(server_key, self._http_procs[server_key], self._http_pgids.get(server_key))

# In get_process_snapshot() (line ~253):
# Before: return self._build_snapshot_dict(server_key)
# After: return ProcessSnapshotProvider.get_snapshot(server_key, self._http_procs[server_key], self._http_pgids.get(server_key))

# Step 6: Replace list_processes calls
# In factory.py line ~240:
# Before: processes: list[ProcessInfoSnapshot] = self._http_mgr.list_processes()
# After: processes: list[ProcessInfoSnapshot] = ProcessSnapshotProvider.list_processes(manager=self._http_mgr)

# Step 7: Unify verify_running()
# Before (line ~175-184):
#     def verify_running(self, server_key: str) -> bool:
#         """Return True if the HTTP subprocess server is running, False if missing or exited."""
#         proc = self._http_procs.get(server_key)
#         if proc is None or proc.poll() is not None:
#             logger.warning(...)
#             return False
#         return True
# After:
#     async def verify_running(self, server_key: str, cfg: McpServerConfig | None = None) -> bool:
#         """Return True if the HTTP subprocess server is healthy via HTTP health check."""
#         if cfg is None:
#             return False
#         return await self.verify_running_async(server_key, cfg)

# Steps 8-12: Remove method definitions
# Remove _terminate_with_timeout() (lines 131-173)
# Remove _wait_exited() (lines 115-129)
# Remove shutdown_all() (lines 530-579)
# Remove _build_snapshot_dict() (lines 217-234)
# Remove list_processes() (lines 255-261)
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- Need to read `ProcessTerminator.terminate_with_timeout()` carefully to identify behavioral differences that must be reconciled (early-exit check, pgid fallback warning).
- The SIGINT absorption logic from `shutdown_all()` must be moved into `ShutdownCoordinator.shutdown_all()`.
- `verify_running()` signature change requires updating callers in `factory.py` (line 150-159) to pass `cfg` parameter.

## Compatibility considerations

- **Breaking change**: `verify_running()` signature changes from `(self, server_key: str) -> bool` to `(self, server_key: str, cfg: McpServerConfig | None = None) -> bool`. Callers must update.
- **Breaking change**: `verify_running()` now performs HTTP health check instead of process-existence check. External callers depending on `proc.poll()` behavior will see different results.
- **No breaking change** for `get_process_snapshot()` and `list_processes()` — they return the same types (`dict | None` and `list[ProcessInfoSnapshot]`).

## Security considerations

- No new security surface introduced. Replacing inline termination/shutdown logic with delegated components does not change the security model.
- The SIGINT absorption logic moved to `ShutdownCoordinator` maintains the same security properties.

## Rollback considerations

- Restore removed method definitions and revert caller updates.
- If behavioral differences between `_terminate_with_timeout()` and `ProcessTerminator.terminate_with_timeout()` cause regressions, add missing behaviors to `ProcessTerminator` first.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| Termination behavior | Unit test | `uv run pytest tests/agent/test_http_lifecycle_integration.py -v` | All existing tests pass without modification |
| Shutdown behavior | Integration test | `uv run pytest tests/agent/test_http_lifecycle_integration.py -v` | SIGINT absorbed during shutdown_all() |
| Snapshot output | Unit test | `uv run pytest tests/agent/ -v -k snapshot` | Snapshot output matches original format |
| Liveness semantics | Unit test | `uv run pytest tests/agent/ -v -k health` | Consistent HTTP health-check semantics |
| Type checking | Static | Type checker against modified files | No type errors |
| Lint checking | Static | Lint tool against modified files | No lint errors |

## Completion criteria

- [ ] All calls to `self._terminate_with_timeout()` replaced with `self._process_terminator.terminate_with_timeout()`.
- [ ] All calls to `self._wait_exited()` replaced with `self._process_terminator.wait_exited()`.
- [ ] All calls to `self.shutdown_all()` replaced with `ShutdownCoordinator.shutdown_all(manager=self)`.
- [ ] All calls to `self._build_snapshot_dict()` replaced with `ProcessSnapshotProvider.get_snapshot()`.
- [ ] All calls to `self.list_processes()` replaced with `ProcessSnapshotProvider.list_processes(manager=self)`.
- [ ] `verify_running()` unified to always perform HTTP health check.
- [ ] Removed methods: `_terminate_with_timeout()`, `_wait_exited()`, `shutdown_all()`, `_build_snapshot_dict()`, `list_processes()`.
- [ ] Existing tests pass without modification.
- [ ] No type/lint regressions.

## Out of scope

- Modifying `scripts/agent/http_lifecycle_process_terminator.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_shutdown_coordinator.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_process_snapshot.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_health_checker.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/factory.py` — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify ProcessTerminator covers all behaviors | Pending | — | — | |
| 2 | Replace terminate_with_timeout callers | Pending | — | — | |
| 3 | Replace wait_exited callers | Pending | — | — | |
| 4 | Replace shutdown_all callers | Pending | — | — | |
| 5 | Replace _build_snapshot_dict callers | Pending | — | — | |
| 6 | Replace list_processes callers | Pending | — | — | |
| 7 | Unify verify_running() | Pending | — | — | |
| 8 | Remove inline methods | Pending | — | — | |
| 9 | Run validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-006, REQ-007, REQ-008
- **Source issue**: issues/20260911-214848_refactor_http_lifecycle_eliminate_cross_module_duplication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-235117_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-005035
- **Related target files**: scripts/agent/http_lifecycle.py
