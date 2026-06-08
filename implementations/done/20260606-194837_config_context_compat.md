# Implementation: Remove Backward-Compat Flat Access from AgentConfig and AgentContext

## Goal

Remove the `__getattr__`/`__setattr__` backward-compatibility layer from `AgentConfig` and the equivalent flat-access compat from `AgentContext`, forcing all callers to use nested structured access (`cfg.llm.llm_url`, `ctx.conv.history`, etc.).

## Scope

**In:**
- Remove `AgentConfig.__getattr__` and `AgentConfig.__setattr__` from `scripts/agent/config.py`
- Remove flat-access compatibility from `AgentContext` in `scripts/agent/context.py`
- Fix all call sites that use flat access

**Out:**
- Splitting `AgentConfig` and `DbConfig` into separate files (deferred — reduces blast radius for this step)
- Changing the behavior of any config field (values unchanged)

## Assumptions

- `scripts/agent/config.py` line ~376-400: `AgentConfig` dataclass with `__getattr__`/`__setattr__` that delegate to sub-configs
- `scripts/agent/context.py` line ~119: "Composite context with backward-compat flat attribute access"
- All callers that use `cfg.llm_url` (instead of `cfg.llm.llm_url`) must be updated before deletion

## Implementation

### Step A — Identify all flat-access call sites

Run these searches before making any changes:

```bash
# Find flat cfg access patterns
grep -rn "cfg\.\(llm_url\|http_timeout\|llm_max_retries\|llm_temperature\|llm_max_tokens\)" scripts/
grep -rn "cfg\.\(top_k_search\|web_search_url\|embed_url\)" scripts/
grep -rn "cfg\.\(tool_cache_ttl\|serial_tool_calls\|tool_definitions\)" scripts/
grep -rn "cfg\.\(mcp_servers\|mcp_watchdog\|github_url\)" scripts/
grep -rn "cfg\.\(use_memory_layer\|memory_jsonl_dir\)" scripts/
grep -rn "cfg\.\(otel_enabled\|audit_log_file\)" scripts/

# Find flat ctx access patterns
grep -rn "ctx\.\(llm_url\|tool_cache_ttl\|http_timeout\)" scripts/
```

### Step B — Convert each call site

Replace each flat access with the corresponding nested access:

| Old (flat) | New (nested) |
|---|---|
| `cfg.llm_url` | `cfg.llm.llm_url` |
| `cfg.http_timeout` | `cfg.llm.http_timeout` |
| `cfg.llm_max_retries` | `cfg.llm.llm_max_retries` |
| `cfg.llm_temperature` | `cfg.llm.llm_temperature` |
| `cfg.llm_max_tokens` | `cfg.llm.llm_max_tokens` |
| `cfg.top_k_search` | `cfg.rag.top_k_search` |
| `cfg.web_search_url` | `cfg.rag.web_search_url` |
| `cfg.embed_url` | `cfg.rag.embed_url` |
| `cfg.tool_cache_ttl` | `cfg.tool.tool_cache_ttl` |
| `cfg.serial_tool_calls` | `cfg.tool.serial_tool_calls` |
| `cfg.tool_definitions` | `cfg.tool.tool_definitions` |
| `cfg.mcp_servers` | `cfg.mcp.mcp_servers` |
| `cfg.mcp_watchdog_interval` | `cfg.mcp.mcp_watchdog_interval` |
| `cfg.use_memory_layer` | `cfg.memory.use_memory_layer` |
| `cfg.otel_enabled` | `cfg.obs.otel_enabled` |
| `cfg.audit_log_file` | `cfg.obs.audit_log_file` |

### Step C — Remove `__getattr__`/`__setattr__` from `AgentConfig`

After all call sites are updated, delete the compatibility methods from `AgentConfig`:

```python
# Delete these two methods entirely:
def __getattr__(self, name: str) -> Any: ...
def __setattr__(self, name: str, value: Any) -> None: ...
```

### Step D — Remove flat access from `AgentContext`

Apply the same pattern to `scripts/agent/context.py`. Find the backward-compat section (line ~119) and remove it, then fix any remaining call sites that use `ctx.flat_attr`.

### Step E — Remove `factory.py` global `_audit_logger_instance`

In `scripts/agent/factory.py`:
1. Remove `_audit_logger_instance = Logger(__name__, "/opt/llm/logs/agent.log")` module-level declaration
2. Replace `_audit_logger_instance.info(...)` calls with `_build_audit_logger(ctx).info(...)` or pass the logger as a local variable within `build_agent_context()`

The existing `_build_audit_logger(ctx)` function already exists and returns the correct logger. Use it consistently instead of the module-level instance.

## Validation plan

```bash
uv run ruff check scripts/agent/config.py scripts/agent/context.py scripts/agent/factory.py
uv run mypy scripts/
uv run pytest -v
PYTHONPATH=scripts uv run lint-imports
```

Confirm:
- No `AttributeError: 'AgentConfig' object has no attribute 'llm_url'` in tests
- `mypy` reports no new errors
- All tests pass
- Architecture check passes
