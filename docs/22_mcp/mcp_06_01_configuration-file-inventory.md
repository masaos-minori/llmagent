---
title: "Configuration File Inventory"
area: mcp
tags:
  - mcp
  - configuration
  - defaults
related:
  - mcp_00_document-guide.md
  - adr_02_01_002_platform-config-isolation.md
  - shared_03_01_runtime_and_execution-config-and-logging.md
  - mcp_06_07_mcp-failure-diagnosis.md
  - agent_10_01_operations-and-observability-startup-and-health.md
  - deployment_01_deployment.md
  - mcp_04_01_web-search-file-read-github.md
---

# Configuration File Inventory

This document and its siblings cover all MCP configuration files, per-server config keys, startup validation, health probes, how to read audit logs, and the new server addition checklists.

## Process Isolation Policy

Each MCP server is an independent process and **only reads its own configuration file (`*_mcp_server.toml`)**. It does not read `agent.toml`. Even when values such as DB paths or external service URLs need to be shared with other processes, they must be described individually in each configuration file rather than using a common file.

The rule is enforced at runtime by `ConfigLoader.restrict_to(own_config_file)`, which raises `ConfigPermissionError` upon violation. The Agent-launched binaries and `mcp_launcher.py` apply it before the server module is imported, so no config is read ahead of the restriction; `python -m <server module>` is a development path that applies it in `MCPServer.run_http()`. A server never imports another server module.

→ Details: [ADR-002](../10_adr/adr_02_01_002_platform-config-isolation.md) / [Process Separation Policy](../40_shared/shared_03_01_runtime_and_execution-config-and-logging.md#2a-process-separation-policy-config-isolation-policy)

## Layer 1 — Agent Process Configuration (`config/agent.toml`)

Only the agent process reads `config/agent.toml` via `ConfigLoader().load_all()`.

| Key | Scope |
|---|---|
| `config/agent.toml` → `[mcp_servers.*]` | Transport settings for all servers (McpServerConfig) — used by the agent to manage connections to MCP servers |
| `config/agent.toml` → `[mcp_servers.*].auth_token` | Bearer token sent by the agent to that server; must be a non-empty `"${ENV:MCP_<SERVER_KEY>_AUTH_TOKEN}"` reference (resolved by `shared.config_utils.resolve_env_ref()`) — `McpServerConfig` rejects an empty value at construction time unless the server is disabled; the receiving server verifies it, including mdq-mcp; and `agent.startup_validation` re-checks it before tool discovery |
| `config/agent.toml` → `tool_definitions` | Tool names exposed to the LLM |
| `config/agent.toml` → `tool_safety_tiers` | Risk tier per tool (READ_ONLY/WRITE_SAFE/WRITE_DANGEROUS/ADMIN) |
| `config/agent.toml` → `security_profile` | Global agent security profile — `production` only |

**Reload vs. restart:** `/reload` never modifies `[mcp_servers.*]` at
runtime — MCP server definition changes (URL, startup mode,
transport, command, environment) are always reported as restart-required
and require a full agent restart to take effect. Authentication tokens
are resolved from secrets (env vars or secret files), not from config files.
There is no background auto-restart process (see [mcp_06_07_mcp-failure-diagnosis.md](mcp_06_07_mcp-failure-diagnosis.md) for manual recovery).
A crashed subprocess-mode server is retried automatically only on the next
tool dispatch via `ensure_ready()` (`agent/lifecycle_router.py`); it does not read or
apply any pending `/reload` config change either. See
[Agent Operations: MCP restart requirement](../23_agent/agent_10_01_operations-and-observability-startup-and-health.md)
for the full explanation.

**`cmd` target invariant:** for every `[mcp_servers.<name>]` entry with
`startup_mode = "subprocess"`, the last element of `cmd` must point to a valid
launch target. `ConfigLoader` does not verify this at load time, so a stale or
renamed path loads silently and fails only when the subprocess is spawned. The
production target is the compiled binary `/opt/llm/bin/mcp_<server key>`; binaries
are build-host artifacts absent from the development environment, so the guarding
test (`tests/agent/test_mcp_server_cmd_paths.py`) asserts the binary naming
convention against the real `config/agent.toml` instead of file existence.

## Layer 2 — MCP Server Local Application Configuration (`config/*_mcp_server.toml`)

Each server owns exactly one `config/<key>_mcp_server.toml`; the file list is the
`config/` directory itself. Servers do not read `agent.toml`, so values needed on both sides
(DB paths, external URLs) are duplicated per file by design.

Bearer-token constraint: every HTTP MCP server carries its own server-side `auth_token`
as an `"${ENV:...}"` reference, and the agent presents the matching token from
`agent.toml`'s `[mcp_servers.*].auth_token`. Both sides must resolve to one shared-secret
value, so the agent and the server reference the same environment variable
(`MCP_<SERVER_KEY>_AUTH_TOKEN`). See [mcp_06_14](mcp_06_14_mcp-authentication-setup.md).

## API key env files (`conf.d/`)

`conf.d/<server>-mcp` files hold server-side secrets (for example `GITHUB_TOKEN` for
github-mcp and cicd-mcp). The web-search placeholders (`BRAVE_API_KEY`, `BING_API_KEY`) are
not read by the server code (see `deployment_01_deployment.md`).

## Configuration Value Ownership

Default values live in the config models and config files, not in this document
(`McpServerConfig` in `shared/mcp_config.py` for transport timeouts; `McpServerHealthRegistry`
in `shared/mcp_health.py` for the consecutive-failure threshold, which is a code constant and
not a configuration key). Per-server limits (GitHub `max_per_page`, shell `max_timeout_sec`,
git `max_log_entries`) are set in the owning `config/*_mcp_server.toml`.

**Sandbox note:** `shell_sandbox_backend` in `config/shell_mcp_server.toml` is a plain config
parameter and does not switch automatically with `security_profile`. Production requires
`"firejail"` explicitly. If `"firejail"` is configured and the binary is not on `PATH`, the
server raises `RuntimeError` (`scripts/mcp_servers/shell/shell_service_static_helpers.py`).

## Keywords

- configuration
- defaults
