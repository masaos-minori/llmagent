# Implementation: H-3 — tests for shutdown guard (test_agent_factory.py)

## Goal

Add tests for `_ServerLifecycleRouter._shutting_down` guard: verify that after
`shutdown_all()`, `restart()` and `ensure_ready()` do not delegate to
`HttpServerLifecycleManager`; repeated `shutdown_all()` does not raise; and an ignored
`restart()` emits a warning log.

## Scope

**Target**: `tests/test_agent_factory.py`

**Step covered**: Plan H-3 step 4.

**Out of scope**: source changes, other test files.

## Assumptions

1. `_ServerLifecycleRouter` can be instantiated directly in tests with a fake/stub
   `server_configs` dict and a `ToolExecutor` stub.
2. `HttpServerLifecycleManager` can be replaced with a `MagicMock` or `AsyncMock` on
   the router instance to verify delegation.
3. `McpServerConfig` with `startup_mode="subprocess"` can be constructed for test
   configs.

## Implementation

### Target file

`tests/test_agent_factory.py`

### Procedure

#### Setup helper

```python
def make_router(server_key: str = "srv") -> _ServerLifecycleRouter:
    cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://localhost:9999",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=["echo", "hi"],
    )
    router = _ServerLifecycleRouter(
        server_configs={server_key: cfg},
        tool_executor=MagicMock(),
    )
    # Replace internal manager with a mock to track calls
    router._http_mgr = AsyncMock()
    return router
```

#### Test 1: After shutdown_all, restart() does not call _http_mgr.restart()

```python
@pytest.mark.asyncio
async def test_shutdown_guard_blocks_restart():
    router = make_router()
    await router.shutdown_all()

    await router.restart("srv")

    router._http_mgr.restart.assert_not_called()
```

#### Test 2: After shutdown_all, ensure_ready() does not call _http_mgr.start()

```python
@pytest.mark.asyncio
async def test_shutdown_guard_blocks_ensure_ready():
    router = make_router()
    await router.shutdown_all()

    await router.ensure_ready("srv")

    router._http_mgr.start.assert_not_called()
```

#### Test 3: Repeated shutdown_all() does not raise

```python
@pytest.mark.asyncio
async def test_repeated_shutdown_all_is_idempotent():
    router = make_router()
    await router.shutdown_all()
    await router.shutdown_all()  # must not raise
```

#### Test 4: Ignored restart() emits a warning log

```python
@pytest.mark.asyncio
async def test_shutdown_guard_restart_emits_warning(caplog):
    import logging
    router = make_router()
    await router.shutdown_all()

    with caplog.at_level(logging.WARNING, logger="agent.factory"):
        await router.restart("srv")

    assert any("shutting down" in r.message for r in caplog.records)
    assert any(r.levelno == logging.WARNING for r in caplog.records)
```

### Method

- Import `_ServerLifecycleRouter` from `agent.factory` (it is a private class; import
  directly for testing).
- Use `AsyncMock` for `_http_mgr` to allow `await` calls without real async execution.
- `caplog` is a built-in pytest fixture; no extra dependencies.

### Details

- `_http_mgr.shutdown_all` is also an `AsyncMock`; `await router.shutdown_all()` calls
  `self._shutting_down = True` then `await self._http_mgr.shutdown_all()` — the mock
  returns immediately.
- If `_ServerLifecycleRouter` is not directly importable (e.g. not exported from
  `agent.factory` module), import using `from agent import factory as _factory_mod` and
  access `_factory_mod._ServerLifecycleRouter`.
- These tests do NOT require `build_agent_context()` — they test the router class
  directly.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Tests (targeted) | `uv run pytest tests/test_agent_factory.py -v` | all pass |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
