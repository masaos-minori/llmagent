# Implementation: H-4 — tests for ensure_ready start behavior (test_agent_factory.py)

## Goal

Add tests verifying that `_ServerLifecycleRouter.ensure_ready()` calls
`HttpServerLifecycleManager.start()` iff `verify_running()` returns False for a
subprocess-mode server, and that persistent-mode servers, unknown keys, and the shutdown
guard all prevent `start()` from being called.

## Scope

**Target**: `tests/test_agent_factory.py`

**Step covered**: Plan H-4 step 3.

**Out of scope**: source changes, other test files.

## Assumptions

1. `_ServerLifecycleRouter` is directly importable for unit testing.
2. `_http_mgr` can be replaced with an `AsyncMock`/`MagicMock` to control
   `verify_running()` return values and capture `start()` calls.
3. H-3 shutdown guard is included in `ensure_ready()`; the guard test from H-3 covers
   `_shutting_down=True → no start()`. A dedicated test here may overlap; include it
   anyway for clarity.

## Implementation

### Target file

`tests/test_agent_factory.py`

### Procedure

#### Setup helpers

```python
def make_router_with_mock_mgr(
    startup_mode: StartupMode = StartupMode.SUBPROCESS,
    verify_running_result: bool = False,
) -> tuple[_ServerLifecycleRouter, AsyncMock]:
    cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://localhost:9999",
        startup_mode=startup_mode,
        cmd=["echo", "hi"],
    )
    router = _ServerLifecycleRouter(
        server_configs={"srv": cfg},
        tool_executor=MagicMock(),
    )
    mock_mgr = AsyncMock()
    mock_mgr.verify_running.return_value = verify_running_result
    router._http_mgr = mock_mgr
    return router, mock_mgr
```

#### Test 1: verify_running() returns False → start() is called

```python
@pytest.mark.asyncio
async def test_ensure_ready_starts_when_not_running():
    router, mock_mgr = make_router_with_mock_mgr(verify_running_result=False)

    await router.ensure_ready("srv")

    mock_mgr.start.assert_awaited_once()
```

#### Test 2: verify_running() returns True → start() is NOT called

```python
@pytest.mark.asyncio
async def test_ensure_ready_skips_start_when_running():
    router, mock_mgr = make_router_with_mock_mgr(verify_running_result=True)

    await router.ensure_ready("srv")

    mock_mgr.start.assert_not_called()
```

#### Test 3: Persistent-mode server → start() is NOT called

```python
@pytest.mark.asyncio
async def test_ensure_ready_skips_persistent_mode():
    router, mock_mgr = make_router_with_mock_mgr(startup_mode=StartupMode.PERSISTENT)

    await router.ensure_ready("srv")

    mock_mgr.start.assert_not_called()
    mock_mgr.verify_running.assert_not_called()
```

#### Test 4: Unknown server key → no error, no start

```python
@pytest.mark.asyncio
async def test_ensure_ready_unknown_key_no_error():
    router, mock_mgr = make_router_with_mock_mgr()

    await router.ensure_ready("unknown_key")  # must not raise

    mock_mgr.start.assert_not_called()
```

#### Test 5: _shutting_down=True → start() is NOT called

```python
@pytest.mark.asyncio
async def test_ensure_ready_respects_shutdown_guard():
    router, mock_mgr = make_router_with_mock_mgr(verify_running_result=False)
    router._shutting_down = True

    await router.ensure_ready("srv")

    mock_mgr.start.assert_not_called()
```

### Method

- All tests instantiate `_ServerLifecycleRouter` directly with a controlled mock manager.
- `AsyncMock.verify_running` is synchronous in the production code; if the mock wraps it
  as async, use `MagicMock` for `verify_running` specifically:
  ```python
  mock_mgr.verify_running = MagicMock(return_value=verify_running_result)
  ```
- `assert_awaited_once()` confirms `start()` was awaited exactly once.

### Details

- Test 3 verifies that `verify_running` is never called for persistent-mode servers
  (the `startup_mode` check must come before `verify_running()`).
- Test 5 is a subset of the H-3 guard test; include it here as documentation that H-4
  does not bypass the guard.
- If `_shutting_down` is not yet a field (H-3 not merged), set it directly:
  `router._shutting_down = True` — this forces the guard even before H-3 is merged.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Tests (targeted) | `uv run pytest tests/test_agent_factory.py -v` | all pass |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
