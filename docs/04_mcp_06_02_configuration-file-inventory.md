---
title: "Configuration File Inventory"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# Configuration File Inventory

## Process Isolation Policy

Each MCP server is an independent process and **only reads its own configuration file (`*_mcp_server.toml`)**. It does not read `agent.toml`. Even when values such as DB paths or external service URLs need to be shared with other processes, they must be described individually in each configuration file rather than using a common file.

`MCPServer.run_http()` calls `ConfigLoader.restrict_to(own_config_file)` before starting uvicorn to enforce this rule at runtime. A `ConfigPermissionError` is raised upon violation.

→ Details: [90_shared_03 §2a](90_shared_03_01_runtime_and_execution-config-and-logging.md#2a-process-isolation-policy-config-isolation-policy)

## Layer 1 — Agent Process Configuration (`config/agent.toml`)

Only the agent process reads `config/agent.toml` via `ConfigLoader().load_all()`.

| Key | Scope |
|---|---|
| `config/agent.toml` → `[mcp_servers.*]` | Transport settings for all servers (McpServerConfig) — used by the agent to manage connections to MCP servers |
| `config/agent.toml` → `tool_definitions` | Tool names exposed to the LLM |
| `config/agent.toml` → `tool_safety_tiers` | Risk tier per tool (READ_ONLY/WRITE_SAFE/WRITE_DANGEROUS/ADMIN) |
| `config/agent.toml` → `security_profile` | Global agent security profile (local / production) |

**Reload vs. restart:** `/reload` never modifies `[mcp_servers.*]` at
runtime — MCP server definition changes (URL, startup mode,
transport, command, environment) are always reported as restart-required
and require a full agent restart to take effect. Authentication tokens
are resolved from secrets (env vars or secret files), not from config files.
There is no background auto-restart process (the MCP watchdog was removed;
see [04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md)).
A crashed subprocess-mode server is retried automatically only on the next
tool dispatch via `ensure_ready()` (`agent/factory.py`); it does not read or
apply any pending `/reload` config change either. See
[Agent Operations: MCP restart requirement](05_agent_10_01_operations-and-observability-startup-and-health.md)
for the full explanation.

**`cmd` script-path invariant:** for every `[mcp_servers.<name>]` entry with
`startup_mode = "subprocess"`, the last element of `cmd` must point to a
script that actually exists on disk (relative to `/opt/llm/scripts/` in
production, `scripts/` in this repo) — `ConfigLoader`/`_build_mcp_servers()`
do not verify this at load time, so a stale or renamed path silently loads
without error until the subprocess is spawned.
`tests/test_mcp_server_cmd_paths.py` guards this invariant by loading the
real `config/agent.toml` via `build_agent_config()` and asserting every
subprocess-mode server's `cmd` script path resolves to an existing file.

## Layer 2 — MCP Server Local Application Configuration (`config/*_mcp_server.toml`)

| Server | Config file |
|---|---|
| web-search-mcp | `config/web_search_mcp_server.toml` (no API keys needed) |
| file-read-mcp | `config/file_read_mcp_server.toml` |
| file-write-mcp | `config/file_write_mcp_server.toml` |
| file-delete-mcp | `config/file_delete_mcp_server.toml` |
| github-mcp | `config/github_mcp_server.toml` |
| shell-mcp | `config/shell_mcp_server.toml` |
| rag-pipeline-mcp | `config/rag_pipeline_mcp_server.toml` |
| cicd-mcp | `config/cicd_mcp_server.toml` |
| mdq-mcp | `config/mdq_mcp_server.toml` |
| git-mcp | `config/git_mcp_server.toml` |

## API key env files (`conf.d/`)

| File | Key |
|---|---|
| `conf.d/github-mcp` | `GITHUB_TOKEN` |
| `conf.d/cicd-mcp` | `GITHUB_TOKEN` |

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
