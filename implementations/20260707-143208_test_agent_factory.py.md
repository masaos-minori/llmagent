# Implementation: H-9 — tests for LifecycleState tracking (test_agent_factory.py)

## Goal

Add tests verifying that `_ServerLifecycleRouter` transitions `LifecycleState` correctly
during `start_http_subprocess()`, `restart()`, and `shutdown_all()`, and that
`get_transport_state()` returns the correct state for known and unknown server keys.

## Scope

**Target**: `tests/test_agent_factory.py`

**Step covered**: Plan H-9 step 7.

**Out of scope**: source changes, other test files.

## Assumptions

1. `_ServerLifecycleRouter` is directly importable for unit testing.
2. `_http_mgr` is replaced with `AsyncMock` to control start/restart/shutdown behavior.
3. `LifecycleState` is importable from `agent.lifecycle`.

## Implementation

### Target file

`tests/test_agent_factory.py`

### Procedure

#### Setup helper

```python
def make_router_for_state_tests(startup_mode=StartupMode.SUBPROCESS):
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
    router._http_mgr = AsyncMock()
    return router
```

#### Test 1: After start_http_subprocess(), state is RUNNING

```python
@pytest.mark.asyncio
async def test_state_running_after_start():
    router = make_router_for_state_tests()
    cfg = router._server_configs["srv"]

    await router.start_http_subprocess("srv", cfg)

    assert router.get_transport_state("srv") == LifecycleState.RUNNING
```

#### Test 2: start_http_subprocess() raises → state is FAILED

```python
@pytest.mark.asyncio
async def test_state_failed_when_start_raises():
    router = make_router_for_state_tests()
    router._http_mgr.start.side_effect = RuntimeError("startup error")
    cfg = router._server_configs["srv"]

    with pytest.raises(RuntimeError):
        await router.start_http_subprocess("srv", cfg)

    assert router.get_transport_state("srv") == LifecycleState.FAILED
```

#### Test 3: After restart(), state is RUNNING

```python
@pytest.mark.asyncio
async def test_state_running_after_restart():
    router = make_router_for_state_tests()

    await router.restart("srv")

    assert router.get_transport_state("srv") == LifecycleState.RUNNING
```

#### Test 4: After shutdown_all(), state is STOPPED

```python
@pytest.mark.asyncio
async def test_state_stopped_after_shutdown():
    router = make_router_for_state_tests()

    await router.shutdown_all()

    assert router.get_transport_state("srv") == LifecycleState.STOPPED
```

#### Test 5: Unknown server key returns UNKNOWN

```python
def test_state_unknown_for_unknown_key():
    router = make_router_for_state_tests()

    assert router.get_transport_state("nonexistent") == LifecycleState.UNKNOWN
```

#### Test 6: STARTING state visible during start (intermediate state)

```python
@pytest.mark.asyncio
async def test_state_starting_before_start_completes():
    router = make_router_for_state_tests()
    states_during_start = []

    async def capture_state_start(server_key, cfg):
        states_during_start.append(router.get_transport_state(server_key))

    router._http_mgr.start.side_effect = capture_state_start
    cfg = router._server_configs["srv"]

    await router.start_http_subprocess("srv", cfg)

    assert LifecycleState.STARTING in states_during_start
    assert router.get_transport_state("srv") == LifecycleState.RUNNING
```

### Method

- Tests use `router._http_mgr = AsyncMock()` to avoid real subprocess interactions.
- Test 6 uses a side-effect coroutine that captures the router state at the moment
  `_http_mgr.start()` is awaited — this verifies `_set_state(STARTING)` is called
  before `_http_mgr.start()`.

### Details

- Import `LifecycleState` from `agent.lifecycle` in the test file.
- `restart()` requires `startup_mode == StartupMode.SUBPROCESS`; the default fixture
  sets this.
- Test 3 (`restart()`) checks state after the call; it does not check STARTING
  intermediate state (covered by Test 6 pattern for `start_http_subprocess()`).
- If H-3 (shutdown guard) is also merged, Test 4 must call `shutdown_all()` first
  without prior `start()` — state transitions from UNKNOWN via `_set_state()`.
  `_set_state()` allows UNKNOWN → STOPPED (UNKNOWN allows any transition per
  `_VALID_TRANSITIONS`).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Tests (targeted) | `uv run pytest tests/test_agent_factory.py -v` | all pass |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
