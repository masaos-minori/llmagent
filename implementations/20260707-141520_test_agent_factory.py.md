# Implementation: H-2 — tests for shared health registry (test_agent_factory.py)

## Goal

Add tests asserting that `build_agent_context()` creates a single `McpServerHealthRegistry`
instance that is wired into both `ToolExecutor` (via `set_health_registry`) and
`AppServices` (via `health_registry` field), so that health state is shared between the
two.

## Scope

**Target**: `tests/test_agent_factory.py`

**Step covered**: Plan H-2 step 4.

**Out of scope**: source changes, other test files.

## Assumptions

1. `tests/test_agent_factory.py` already exists with factory build tests.
2. A helper or fixture produces a minimal `AgentContext` with stubs for config fields.
3. `ToolExecutor._health_registry` is the attribute set by `set_health_registry()`.

## Implementation

### Target file

`tests/test_agent_factory.py`

### Procedure

#### Test 1: health_registry is not None after build

```python
def test_build_agent_context_has_health_registry(make_ctx, make_view):
    ctx = make_ctx()
    view = make_view()
    build_agent_context(ctx, view)

    assert ctx.services.health_registry is not None
    assert isinstance(ctx.services.health_registry, McpServerHealthRegistry)
```

#### Test 2: Same registry object in ToolExecutor and AppServices

```python
def test_health_registry_shared_between_tool_executor_and_services(make_ctx, make_view):
    ctx = make_ctx()
    view = make_view()
    build_agent_context(ctx, view)

    registry_in_services = ctx.services.health_registry
    registry_in_tools = ctx.services.tools._health_registry

    assert registry_in_services is registry_in_tools
```

#### Test 3: Health state recorded in ToolExecutor reflects in AppServices registry

```python
def test_health_state_shared_via_registry(make_ctx, make_view):
    ctx = make_ctx()
    view = make_view()
    build_agent_context(ctx, view)

    registry = ctx.services.health_registry
    # Simulate recording a transport error via the registry directly
    registry.record_error("test_server")

    # The same state must be visible from tools' registry reference
    tools_registry = ctx.services.tools._health_registry
    state = tools_registry.get_state("test_server")
    assert state != McpServerHealthState.HEALTHY
```

### Method

- Use existing `make_ctx` and `make_view` fixtures (or equivalent) that produce stub
  contexts.
- Import: `McpServerHealthRegistry`, `McpServerHealthState` from `shared.mcp_health`
  (or `shared.mcp_config`).
- Import: `build_agent_context` from `agent.factory`.

### Details

- Test 3 depends on the specific API of `McpServerHealthRegistry.record_error()` and
  `get_state()`. Read `shared/mcp_health.py` to confirm method names before writing.
- If `record_error` does not exist, use whatever mutation method the registry exposes
  (e.g. `_record_transport_error`, `set_state`, or direct dict mutation).
- The goal is object identity assertion (`is`), not deep equality; this test cannot pass
  if two separate registries are instantiated.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Tests (targeted) | `uv run pytest tests/test_agent_factory.py -v` | all pass |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
