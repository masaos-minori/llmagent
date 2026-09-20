## Goal

Update tests in `tests/agent/test_agent_factory.py` to work with the new two-class architecture where `_SubprocessLifecycleManager` owns subprocess operations and `_ServerLifecycleRouter` delegates to it.

## Scope

- Update all references to `_ServerLifecycleRouter` in this file to work with the new architecture
- Update `_FACTORY_PATCHES` to include `_SubprocessLifecycleManager` alongside `_ServerLifecycleRouter`
- Update test fixtures (`_make_router`, `_make_router_with_mock_mgr`, `_make_lifecycle_router`) to work with the new architecture
- Preserve existing test coverage and behavior verification

## Assumptions

- Both `_ServerLifecycleRouter` and `_SubprocessLifecycleManager` implement `LifecycleManagerProtocol` per Plan's stated intent
- `_build_tool_executor()` creates both classes: `_SubprocessLifecycleManager` for subprocess ops, `_ServerLifecycleRouter` as coordinator
- Tests that mock `_ServerLifecycleRouter` directly must now also account for `_SubprocessLifecycleManager` delegation
- `AppServices` constructor signature remains compatible after builder standardization (verified in context.py procedure)

## Design decisions

1. **Update `_FACTORY_PATCHES`**: Add `"agent.factory._SubprocessLifecycleManager"` alongside existing `"agent.factory._ServerLifecycleRouter"`. This ensures `build_agent_context()` calls are properly intercepted during testing.

2. **Two-phase test update**: First update existing tests to use the new architecture; then add new tests specifically for `_SubprocessLifecycleManager` behavior.

3. **Preserve test structure**: Keep existing test class/method names and assertions where possible — only change what breaks due to the split.

4. **Fixture updates**:
   - `_make_router()`: Now returns a tuple `(router, subprocess_mgr)` or sets `router._subprocess_mgr`
   - `_make_router_with_mock_mgr()`: Same pattern — mock on correct instance
   - `_make_lifecycle_router()`: May need to return both instances

## Alternatives considered

- **Keep single mock for lifecycle**: Could keep mocking just `_ServerLifecycleRouter` and have it delegate internally. Trade-off: less precise control over which class handles which operation. Decision: mock both separately for clarity.
- **Create entirely new test file for `_SubprocessLifecycleManager`**: Would require cross-file imports and coordination. Too disruptive for a refactor that doesn't change public API.

## Implementation
### Target file

tests/agent/test_agent_factory.py

### Procedure

1. Update `_FACTORY_PATCHES` to include `_SubprocessLifecycleManager` alongside `_ServerLifecycleRouter`.
2. Update test fixtures (`_make_router`, `_make_router_with_mock_mgr`, `_make_lifecycle_router`) to work with two-class architecture.
3. Update tests accessing `mgr._http_mgr` directly to reference correct instance.
4. Update `build_agent_context()` mock assertions to handle dataclass wrapper returns.
5. Run test suite and verify all pass.

### Method

#### Step 1: Update _FACTORY_PATCHES

Current list (lines 90-98):
```python
_FACTORY_PATCHES = [
    "agent.factory.Logger",
    "agent.factory.httpx.AsyncClient",
    "agent.factory.LLMClient",
    "agent.factory.ToolExecutor",
    "agent.factory._ServerLifecycleRouter",
    "agent.factory.HistoryManager",
    "agent.factory.build_tracer",
]
```

After update:
```python
_FACTORY_PATCHES = [
    "agent.factory.Logger",
    "agent.factory.httpx.AsyncClient",
    "agent.factory.LLMClient",
    "agent.factory.ToolExecutor",
    "agent.factory._ServerLifecycleRouter",
    "agent.factory._SubprocessLifecycleManager",
    "agent.factory.HistoryManager",
    "agent.factory.build_tracer",
]
```

#### Step 2: Update test fixtures

Update fixture functions in `test_agent_factory.py` that instantiate `_ServerLifecycleRouter`:

a. `_make_router()` (line 332-345):
```python
def _make_router(server_key: str = "srv") -> tuple[_ServerLifecycleRouter, _SubprocessLifecycleManager]:
    cfg = McpServerConfig(...)
    subprocess_mgr = _SubprocessLifecycleManager(
        server_configs={server_key: cfg},
        tool_executor=MagicMock(),
    )
    router = _ServerLifecycleRouter(
        server_configs={server_key: cfg},
        tool_executor=MagicMock(),
    )
    router._subprocess_mgr = subprocess_mgr
    router._http_mgr = AsyncMock()  # or subprocess_mgr._http_mgr = AsyncMock()
    return router, subprocess_mgr
```

b. `_make_router_with_mock_mgr()` (line 384-402):
```python
def _make_router_with_mock_mgr(
    startup_mode: StartupMode = StartupMode.SUBPROCESS,
    verify_running_result: bool = False,
) -> tuple[_ServerLifecycleRouter, _SubprocessLifecycleManager, AsyncMock]:
    cfg = McpServerConfig(...)
    subprocess_mgr = _SubprocessLifecycleManager(
        server_configs={"srv": cfg},
        tool_executor=MagicMock(),
    )
    router = _ServerLifecycleRouter(
        server_configs={"srv": cfg},
        tool_executor=MagicMock(),
    )
    router._subprocess_mgr = subprocess_mgr
    mock_mgr = AsyncMock()
    mock_mgr.verify_running = MagicMock(return_value=verify_running_result)
    subprocess_mgr._http_mgr = mock_mgr
    return router, subprocess_mgr, mock_mgr
```

c. `_make_lifecycle_router()` (line 515-523):
```python
def _make_lifecycle_router(
    configs: dict[str, McpServerConfig] | None = None,
) -> tuple[_ServerLifecycleRouter, _SubprocessLifecycleManager]:
    if configs is None:
        configs = {}
    subprocess_mgr = _SubprocessLifecycleManager(
        server_configs=configs,
        tool_executor=MagicMock(),
    )
    router = _ServerLifecycleRouter(
        server_configs=configs,
        tool_executor=MagicMock(),
    )
    router._subprocess_mgr = subprocess_mgr
    return router, subprocess_mgr
```

#### Step 3: Update tests accessing mgr._http_mgr directly

Tests that currently do `router._http_mgr.restart.assert_not_called()` must now go through the correct instance:
- For subprocess operations: `router._subprocess_mgr._http_mgr.restart.assert_not_called()`
- For state/cooldown operations: `router._states`, etc.

Affected tests include:
- `TestShutdownGuard.test_shutdown_guard_blocks_restart` (line 354): `router._http_mgr.restart.assert_not_called()`
- `TestShutdownGuard.test_shutdown_guard_blocks_ensure_ready` (line 361): `router._http_mgr.start.assert_not_called()`
- `TestEnsureReadyAutoStart` tests (lines 408-416): `mock_mgr.start.assert_awaited_once()`, etc.

#### Step 4: Update build_agent_context() mock assertions

If builder standardization introduces dataclass wrappers, update assertions like:
```python
# Before:
mocks["agent.factory._ServerLifecycleRouter"].assert_called_once()

# After (if _ServerLifecycleRouter constructor signature changes):
# May need to adjust assertion based on new constructor parameters
```

#### Step 5: Run test suite

```bash
uv run pytest tests/agent/test_agent_factory.py -v
```

### Details

- **_FACTORY_PATCHES update**: Adding `_SubprocessLifecycleManager` ensures `build_agent_context()` calls are properly intercepted during testing.
- **Fixture updates**: All three fixture functions must be updated to create both instances and wire them together.
- **Two-phase approach**: First update existing tests; then add new tests for `_SubprocessLifecycleManager` behavior.
- **Preserve test coverage**: Keep existing test names and assertions where possible — only change what breaks due to the split.
- **Coordination**: Changes here must be coordinated with `test_lifecycle.py` updates.

## Compatibility considerations

- Tests that mock `_ServerLifecycleRouter` directly via `_FACTORY_PATCHES` must now also mock `_SubprocessLifecycleManager`.
- Tests that set `mgr._http_mgr._http_procs["srv"]` directly may need to set on the correct instance after split.
- Tests that verify `isinstance(mgr, LifecycleManagerProtocol)` must pass for both classes.
- `test_lifecycle.py` has 38+ references — coordinate changes between the two test files.

## Security considerations

- No security impact: test-only changes.

## Rollback considerations

- If split breaks backward compatibility, revert `_SubprocessLifecycleManager` extraction and restore single-class approach.
- If dataclass wrappers break callers, revert to tuple returns temporarily.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| All factory tests pass | Unit | `uv run pytest tests/agent/test_agent_factory.py -v` | All tests pass |
| Protocol conformance | Runtime check | `isinstance` checks against `LifecycleManagerProtocol` | Both classes pass |
| Behavior lock | Integration | Agent startup verification | Agent starts without errors |

## Completion criteria

- [x] All existing tests pass after refactor
- [x] `_FACTORY_PATCHES` includes both `_ServerLifecycleRouter` and `_SubprocessLifecycleManager`
- [x] `_build_tool_executor` mock returns both instances correctly
- [x] Tests that access `mgr._http_mgr` correctly reference the right instance after split
- [x] New tests added for `_SubprocessLifecycleManager` subprocess methods
- [x] `isinstance` checks against `LifecycleManagerProtocol` pass for both classes
- [x] Module docstring updated to reflect two-class architecture

## Out of scope

- Modifying `docs/*.md` files
- Adding new features or changing service initialization order
- Refactoring memory layer builders beyond type annotation fixes

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update _FACTORY_PATCHES list | Completed | — | — | REQ-006 |
| 2 | Update test fixtures (_make_router, etc.) | Completed | — | — | REQ-006 |
| 3 | Update tests accessing mgr._http_mgr directly | Completed | — | — | REQ-006 |
| 4 | Add tests for _SubprocessLifecycleManager | Completed | — | — | REQ-006 |
| 5 | Run test suite and verify all pass | Completed | — | — | REQ-006 |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260920-135039_refactor_factory_module_complexity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-140158_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-141711
- **Related target files**: tests/agent/test_agent_factory.py
