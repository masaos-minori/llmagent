---
title: "Agent Configuration - Loading and AgentConfig Structure (Part 1)"
area: agent
tags:
  - agent
  - configuration
  - config-loading
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_08_01_configuration-loading-agent-config.md
---

# Agent Configuration

- Operations → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

Documents the `AgentConfig` structure, configuration file ownership, and classification of hot-reloads.

## Design Intent

### Configuration Loading

`build_agent_config()` calls `ConfigLoader.load_all()`, which merges all configuration files into a dictionary before constructing the `AgentConfig` dataclass.

**Canonical Configuration File:** `config/agent.toml` (LLM/RAG/DB/Tools/Memory/Observability/Approval/MCP Lifecycle/Diagnostics)

### Configuration File Ownership

| File | Responsibility | Hot-Reloadable |
|---|---|---|
| `config/agent.toml` | Agent process settings | Mostly possible; `use_memory_layer`/`memory_embed_enabled` are startup-only; `diagnostics.*` does not support `/reload` |
| `config/*_mcp_server.toml` | MCP server specific settings | Requires restart (on add/remove/rename) |

### Settings Requiring Restart

- Changes to MCP server URL, authentication tokens, startup modes, commands, or environment variables.
- `use_memory_layer` — Enabling/disabling the memory subsystem (startup only).
- `memory_embed_enabled` — Enabling/disabling embedding generation and KNN search (startup only).
- `routing_drift_strict` — Fatal handling for routing drift (startup only).

### Hot-Reloadable Scope

- LLMClient: temperature, max_tokens, max_retries, retry_base_delay, SSE parameters
- HistoryManager: context_char_limit, context_compress_turns, context_token_limit, tokenize_url
- ToolExecutor: tool_cache_ttl
- System Prompt: system_prompt_tool → `ctx.conv.system_prompt_content`

### Operational Impact of Changes

Check the following categories in the `ConfigReloadOutcome` output:
- `[APPLIED]` — Hot-reload applied successfully.
- `[RESTART]` — Subsystem restart required.
- `[STARTUP-ONLY]` — Fields that cannot be changed via `/reload`.

### Security-Related Settings

- Changes to MCP server `auth_token` require a restart.
- Changes to allowlist/denylist require a restart.

## Responsibility Boundary

- **Configuration Files**: `config/agent.toml` is the canonical source.
- **Field-level Mapping**: Refer to `agent/services/config_reload.py`.

## Key Constraints

- Unknown

## Operational Notes

- Unknown

## Known Limitations

- Unknown

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_03_configuration-tools-memory.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`
- `05_agent_08_01_configuration-loading-agent-config.md`

## Keywords

configuration loading
config file ownership
hot-reload eligibility
