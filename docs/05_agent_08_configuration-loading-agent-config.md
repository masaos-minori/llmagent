---
title: "Agent Configuration"
category: agent
tags:
  - agent
  - agent
  - configuration
  - config
  - settings
related:
  - 05_agent_00_document-guide.md
---

# Agent Configuration

ng

`build_agent_config()` (`agent/config_builders.py`) calls `ConfigLoader.load_all()`
(`shared/config_loader.py`) which merges all config files into a dict, then constructs
the `AgentConfig` dataclass.

**Files loaded by `load_all()`:**

| File | Sub-config |
|---|---|
| `config/agent.toml` | All sub-configs (LLMConfig, RAGConfig, DbConfig, ToolConfig, MemoryConfig, ObservabilityConfig, ApprovalConfig, MCPConfig) |

Historical note: Earlier versions loaded 12 separate files (`common.toml`, `llm.toml`, `http.toml`, `context.toml`, `rag.toml`, `tools.toml`, `memory.toml`, `otel.toml`, `security.toml`, `system_prompts.toml`, `tools_definitions.toml`, plus per-server `*_mcp_server.toml`). These were consolidated into `agent.toml`; the split files no longer exist.

For the canonical config ownership table (owning layer per file), see
[90_shared_03 §2a Config Ownership](90_shared_03_runtime_and_execution-config-and-logging.md#2a-config-ownership).

`ctx.cfg` holds the config. `/reload` calls `ConfigLoader().load_all()` to
re-read all base config files, then passes the merged dict to
`ConfigReloadService.apply_config_dict(new_cfg)` which updates `ctx.cfg`
fields and syncs live service instances.

The call chain is:
1. `ConfigLoader().load_all()` — re-reads all files from `config/`
2. `ConfigReloadService.apply_config_dict(new_cfg)` — updates `ctx.cfg`
   fields and propagates changes to services
3. `ConfigReloadOutcome` — returned to the caller with `applied`,
   `needs_restart`, `skipped`, and `source_files` fields

### Config file ownership and hot-reload eligibility

`/reload` reads all base config files — the same set loaded at startup.
`ConfigReloadService` classifies each changed key into one of four categories.

All configuration keys are defined in `config/agent.toml`. There is no separate `common.toml` or other split file providing defaults.

| File | Purpose | Classification |
|---|---|---|
| `config/agent.toml` | All sub-configs | Hot-reloadable (most); `use_memory_layer`, `plugin_strict` are startup-only |
| `config/*_mcp_server.toml` | MCP server transport/URL config (via `[mcp_servers.<key>]`) | Restart-required: every field (`transport`, `url`, `startup_mode`, `healthcheck_mode`, `call_timeout_sec`, `startup_timeout_sec`, `tool_names`, `auth_token`, `role`, `cmd`, `env`), plus server add/remove/rename |

**Classification definitions:**

- **Hot-reloadable** — applied immediately to the running agent; no restart needed.
- **Restart-required** — the subsystem must be restarted for the change to apply.
  `/reload` output shows these as `[RESTART]`.
- **Startup-only** — read once at agent start; never touched by `/reload`.
  `/reload` emits `[STARTUP-ONLY]` only when the field value differs from the
  running config.

**Restart-required settings** (`needs_restart` in `ConfigReloadOutcome`):
- Any `McpServerConfig` field change, new servers, removed servers, and
  renames (remove-old + add-new). Example entries:
  `mcp/<server>.url`, `mcp/<server>.auth_token`, `mcp/<server>.startup_mode`,
  `mcp/<server>.cmd`, `mcp/<server>.env`.

**Startup-only settings** (not touched by `apply_config_dict()`):
- `use_memory_layer` — enables/disables the memory subsystem at boot
- `plugin_strict` — enables fail-fast on plugin import errors at boot

**Removed keys** (rejected at config load, `ConfigLoadError`; verified 2026-07-09 — see
`build_agent_config()`'s `_FORBIDDEN_KEYS`): `workflow_mode`, `workflow_require_approval`,
`use_tool_summarize`, `tool_summarize_threshold`. These are no longer valid config keys at
all — not startup-only settings that merely can't be hot-reloaded.

All configuration keys are defined in `config/agent.toml`. There is no separate `common.toml` or other split file providing defaults.

### Reload execution pipeline

`ConfigReloadService` (`agent/services/config_reload.py`) applies the reloaded
config to live service instances:

| Service | Method called | Config fields propagated |
|---|---|---|
| `LLMClient` | `.apply_config()` | temperature, max_tokens, max_retries, retry_base_delay, SSE params |
| `HistoryManager` | `.apply_config()` | context_char_limit, context_compress_turns, context_token_limit, tokenize_url |
| `ToolExecutor` | `.apply_config()` | tool_cache_ttl |
| System prompt | direct write | system_prompt_tool → `ctx.conv.system_prompt_content` |

**`ConfigReloadOutcome` fields:**

| Field | Type | Description |
|---|---|---|
| `applied` | `list[str]` | Changes applied at runtime (hot-reloaded) |
| `needs_restart` | `list[str]` | Changes that require a full agent restart |
| `skipped` | `list[str]` | Changes intentionally ignored, not MCP server definitions — see `needs_restart` |
| `source_files` | `list[str]` | Config files that were reloaded |
| `startup_only` | `list[str]` | Startup-only fields that differ from running config |

See `agent/services/config_reload.py` for the full field-level mapping.

---

## AgentConfig Structu

re

`AgentConfig` composes 7 domain sub-configs accessed as `cfg.llm.*`, `cfg.rag.*`, etc.,
plus two top-level scalar fields.

```python
@dataclass
class AgentConfig:
    llm:      LLMConfig
    rag:      RAGConfig
    tool:     ToolConfig
    memory:   MemoryConfig
    mcp:      MCPConfig
    approval: ApprovalConfig
    obs:      ObservabilityConfig
    security_lockdown_enabled:  bool = False
```

`security_lockdown_enabled` suppresses DENY-ALL approval warnings for intentional
lockdown deployments.

**`workflow_mode` and `workflow_require_approval` no longer exist** (verified 2026-07-09
against `scripts/agent/config_dataclasses.py::AgentConfig` — neither field is present).
Both keys are now rejected at config load: `build_agent_config()` raises `ConfigLoadError`
if either appears anywhere in the merged config
(`_FORBIDDEN_KEYS = {"workflow_mode", "workflow_require_approval", "use_tool_summarize",
"tool_summarize_threshold"}`). There is no "auto" / "disabled" degraded mode and no
workflow-level approval-gate toggle — see the next section.

**Current behavior:** the agent unconditionally requires a valid workflow definition.
`StartupOrchestrator._initialize()` calls `_check_workflow_definition()`
(`agent/startup.py:84`, wrapping `check_workflow_definition()` in `agent/repl_health.py`)
as a preflight check **before** `Orchestrator.__init__()`; if
`config/workflows/default.json` is missing, this raises `RuntimeError` with an actionable
message naming the expected path. `Orchestrator.__init__()` itself
(`agent/orchestrator.py:123-129`) then unconditionally calls `WorkflowLoader().load()` and
raises `RuntimeError` on any failure (`WorkflowLoadError` or otherwise) — there is no mode
that skips or degrades this. Neither check is caught by `StartupOrchestrator.run()`; the
failure propagates to the REPL and aborts startup. The failure occurs during agent boot,
not at the first turn. This is startup-only in the sense that it always runs once at boot —
not because it is a config toggle that merely can't be hot-reloaded.

Cross-field validation:
- `rag.use_semantic_cache=True` → `rag.embed_url` must be non-empty
- `memory.use_memory_layer=True` → `memory.memory_jsonl_dir` must be non-empty
- `memory.memory_embed_enabled=True` → `rag.embed_url` must be non-empty

---

## LLMConfig (`cfg.llm

## Related Documents

- `agent`
- `configuration`
- `config`

## Keywords

agent
configuration
config
settings
