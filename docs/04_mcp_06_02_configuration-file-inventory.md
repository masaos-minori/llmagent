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

## Configuration File Inventory

### プロセス分離方針

各 MCP サーバーは独立したプロセスであり、**自身の設定ファイル (`*_mcp_server.toml`) のみを読み込む**。`agent.toml` は読み込まない。DB パスや外部サービス URL など他プロセスと同じ値が必要な場合でも、共通ファイルを作らず各設定ファイルに個別に記述する。

`MCPServer.run_http()` は uvicorn 起動前に `ConfigLoader.restrict_to(own_config_file)` を呼び出してこのルールをランタイムで強制する。違反時は `ConfigPermissionError` が発生する。

→ 詳細: [90_shared_03 §2a](90_shared_03_01_runtime_and_execution-config-and-logging.md#2a-プロセス分離方針-config-isolation-policy)

### Agent-level (agent.toml のみが読み込む設定)

`config/agent.toml` はエージェントプロセスのみが `ConfigLoader().load_all()` で読み込む。

| File | Affects |
|---|---|
| `config/agent.toml` → `[mcp_servers.*]` | All server transport settings (`McpServerConfig`) — エージェントが MCP サーバーへの接続を管理するために使用 |
| `config/agent.toml` → `tool_definitions` | Tool names exposed to LLM |
| `config/agent.toml` → `tool_safety_tiers` | Per-tool risk tier (READ_ONLY/WRITE_SAFE/WRITE_DANGEROUS/ADMIN) |
| `config/agent.toml` → `mcp_watchdog_interval` | Watchdog poll interval (0 = disabled) |
| `config/agent.toml` → `mcp_watchdog_max_restarts` | Watchdog max restart count |

**Reload vs. restart:** `/reload` never modifies `[mcp_servers.*]` at
runtime — MCP server definition changes (URL, auth token, startup mode,
transport, command, environment) are always reported as restart-required
and require a full agent restart to take effect. The watchdog
(`mcp_watchdog_interval`, `mcp_watchdog_max_restarts` above) restarts a
*failed* subprocess using its existing startup config; it does not read or
apply any pending `/reload` config change. See
[Agent Operations: MCP restart requirement](05_agent_10_01_operations-and-observability-startup-and-health.md)
for the full explanation.

### Per-server config files

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

### API key env files (`conf.d/`)

| File | Key |
|---|---|
| `/etc/conf.d/github-mcp` | `GITHUB_TOKEN` |
| `/etc/conf.d/cicd-mcp` | `GITHUB_TOKEN` |

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
