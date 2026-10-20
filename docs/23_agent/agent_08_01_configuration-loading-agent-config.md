---
title: "Agent Configuration - Loading and AgentConfig Structure"
area: agent
tags:
  - agent
  - configuration
  - config-loading
related:
  - agent_00_document-guide.md
  - agent_08_02_configuration-llm-rag.md
  - agent_08_03_configuration-tools-memory.md
  - agent_08_04_configuration-mcp-approval-obs.md
  - agent_10_01_operations-and-observability-startup-and-health.md
---

# Agent Configuration

- Operations → [agent_10_01_operations-and-observability-startup-and-health.md](agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

Documents the `AgentConfig` structure, configuration file ownership, and classification of hot-reloads.

## Design Intent

### Configuration Loading

`build_agent_config()` merges all configuration files through `ConfigLoader.load_all()` and then constructs the `AgentConfig` dataclass. Loading and assembly (including production validation) are separated from per-section construction, so the loader owns no per-section key reading (Explicit in code — `scripts/agent/config_builders.py`, `scripts/agent/config_section_builders.py`).

**Canonical Configuration File:** `config/agent.toml` (LLM/RAG/DB/Tools/Memory/Observability/Approval/MCP Lifecycle/Diagnostics)

**Fail-closed behavior:** When `agent.toml` is missing, `ConfigLoader.load_all()` raises `ConfigMissingError` (inherits `ValueError`), which `load_config()` re-raises as `ConfigLoadError` (inherits `RuntimeError`). Execution aborts before the security profile is resolved, so production config validation never runs on incomplete configuration.

### Configuration File Ownership

| File | Responsibility | Hot-Reloadable |
|---|---|---|
| `config/agent.toml` | Agent process settings | Mostly possible; `use_memory_layer`/`memory_embed_enabled` are startup-only; `diagnostics.*` is not applied by `/reload` but takes effect without restart on every `DiagnosticStore` save/fetch and is reported as `[LIVE]` |
| `config/*_mcp_server.toml` | MCP server specific settings | Requires restart (on add/remove/rename) |

### Settings Requiring Restart

- Changes to MCP server URL, authentication tokens, startup modes, commands, or environment variables.
- `use_memory_layer` — Enabling/disabling the memory subsystem (startup only).
- `memory_embed_enabled` — Enabling/disabling embedding generation and KNN search (startup only).
- `routing_drift_strict` — Fatal handling for routing drift (startup only).

### Hot-Reloadable Scope

- LLMClient: temperature, max_tokens, max_retries, retry_base_delay, SSE parameters
- HistoryManager: context_char_limit, context_compress_turns, context_token_limit, tokenize_url
- System Prompt: system_prompt_tool → `ctx.conv.system_prompt_content`

### Operational Impact of Changes

Check the `[OK]` / `[RESTART]` / `[STARTUP-ONLY]` / `[SKIP]` / `[LIVE]` categories reported after `/reload`; their meaning is defined in [agent_07_06](agent_07_06_cli-and-commands-hot-reload.md).

### Security-Related Settings

Changes to MCP server `auth_token` and to allowlists/denylists require a restart.

## Responsibility Boundary

- **Configuration Files**: `config/agent.toml` is the canonical source.
- **Field-level Mapping**: `agent/services/config_reload.py` is the canonical per-field classification.

## Keywords

- configuration loading
- config file ownership
- hot-reload eligibility
