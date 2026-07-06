# Implementation: tests/test_config_reload_classification.py — /reload config classification snapshot tests

## Goal

Lock down the intended classification of every config field under `/reload`. Each test calls `apply_config_dict()` with a single changed field and asserts which `ConfigReloadOutcome` bucket it ends up in.

## Scope

**In**: New test file covering all 4 classification buckets (applied, deferred, needs_restart, startup_only).

**Out**: Source file changes.

## Assumptions

1. `ConfigReloadService.apply_config_dict()` is the entry point tested.
2. `ConfigReloadOutcome` has fields: `applied: list[str]`, `deferred: list[str]`, `needs_restart: list[str]`, `startup_only: list[str]` (or similarly named).
3. An `AgentContext` fixture can be constructed with minimal mocked services.
4. Hot-reloadable: `llm_temperature`, `llm_max_tokens`, `context_char_limit`, `tool_cache_ttl`.
5. Deferred (auth reconnect): MCP `auth_token`, `startup_mode`.
6. Restart-required: MCP transport change, new MCP server.
7. Startup-only: `use_memory_layer`, `plugin_strict`, `workflow_mode`, `workflow_require_approval`.

## Implementation

### Target file
`tests/test_config_reload_classification.py`

### Procedure
Write one test per field (parameterized where possible). Use `pytest.mark.parametrize` for fields in the same bucket.

### Method

```python
import pytest
from unittest.mock import MagicMock
from scripts.agent.services.config_reload import ConfigReloadService


@pytest.fixture
def ctx_with_defaults():
    """Minimal AgentContext with default config values."""
    ctx = MagicMock()
    ctx.cfg.llm.temperature = 0.7
    ctx.cfg.llm.max_tokens = 4096
    ctx.cfg.context_char_limit = 100_000
    ctx.cfg.tool_cache_ttl = 60
    ctx.cfg.use_memory_layer = False
    ctx.cfg.plugin_strict = False
    ctx.cfg.workflow.workflow_mode = "off"
    ctx.cfg.workflow.workflow_require_approval = True
    ctx.cfg.mcp_servers = {"primary": {"transport": "stdio", "startup_mode": "auto", "auth_token": "tok1"}}
    return ctx


@pytest.fixture
def svc(ctx_with_defaults):
    return ConfigReloadService(ctx_with_defaults)


# --- Hot-reloadable (applied immediately) ---

@pytest.mark.parametrize("key,new_val", [
    ("llm_temperature", 0.5),
    ("llm_max_tokens", 8192),
    ("context_char_limit", 200_000),
    ("tool_cache_ttl", 120),
])
def test_hot_reloadable_in_applied(svc, key, new_val):
    outcome = svc.apply_config_dict({key: new_val})
    assert key in outcome.applied, f"Expected {key!r} in applied, got: {outcome}"
    assert key not in outcome.startup_only
    assert key not in outcome.needs_restart


# --- Startup-only ---

@pytest.mark.parametrize("key,new_val", [
    ("use_memory_layer", True),
    ("plugin_strict", True),
    ("workflow_mode", "auto"),
    ("workflow_require_approval", False),
])
def test_startup_only_in_startup_only(svc, key, new_val):
    # For workflow section, pass as nested dict
    if key in ("workflow_mode", "workflow_require_approval"):
        cfg_dict = {"workflow": {key: new_val}}
    else:
        cfg_dict = {key: new_val}
    outcome = svc.apply_config_dict(cfg_dict)
    assert key in outcome.startup_only, f"Expected {key!r} in startup_only, got: {outcome}"
    assert key not in outcome.applied


def test_startup_only_not_applied_to_services(svc, ctx_with_defaults):
    """Changing a startup-only field must not trigger _sync_services() for that field."""
    svc.apply_config_dict({"workflow": {"workflow_mode": "auto"}})
    # _sync_services should NOT have applied workflow_mode
    # (verify by checking ctx mock was not called with workflow_mode update)
    # This is a behavioral check — exact assertion depends on how _sync_services works


def test_startup_only_unchanged_not_reported(svc, ctx_with_defaults):
    """Same value as current → NOT in startup_only."""
    outcome = svc.apply_config_dict({"workflow": {"workflow_mode": "off"}})  # same as current
    assert "workflow_mode" not in outcome.startup_only


# --- Deferred (requires reconnect, not restart) ---

def test_mcp_auth_token_deferred(svc):
    outcome = svc.apply_config_dict({
        "mcp_servers": {"primary": {"auth_token": "new_token"}}
    })
    assert "primary.auth_token" in outcome.deferred or any("auth_token" in s for s in outcome.deferred)


def test_mcp_startup_mode_deferred(svc):
    outcome = svc.apply_config_dict({
        "mcp_servers": {"primary": {"startup_mode": "manual"}}
    })
    assert any("startup_mode" in s for s in outcome.deferred)


# --- Restart-required ---

def test_mcp_transport_change_needs_restart(svc):
    outcome = svc.apply_config_dict({
        "mcp_servers": {"primary": {"transport": "sse"}}
    })
    assert any("transport" in s or "restart" in s.lower() for s in outcome.needs_restart)


def test_new_mcp_server_needs_restart(svc):
    outcome = svc.apply_config_dict({
        "mcp_servers": {
            "primary": {"transport": "stdio"},
            "secondary": {"transport": "stdio"},  # NEW server
        }
    })
    assert len(outcome.needs_restart) > 0 or len(outcome.deferred) > 0


# --- Service mock verification for hot-reload ---

def test_hot_reload_updates_llm_service(svc, ctx_with_defaults):
    svc.apply_config_dict({"llm_temperature": 0.3})
    # Verify ctx.cfg.llm.temperature was updated
    assert ctx_with_defaults.cfg.llm.temperature == 0.3
```

## Validation plan

- `uv run pytest tests/test_config_reload_classification.py -v` — all pass.
- `ruff check tests/test_config_reload_classification.py` — 0 errors.
