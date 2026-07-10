---
title: "Major Default Values"
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

# Major Default Values

## Major Default Values

| Parameter | Default | Config file |
|---|---|---|
| Max response bytes | 512 KB | hardcoded in `mcp/server.py` |
| call_timeout_sec | 60.0 sec | `McpServerConfig.call_timeout_sec` |
| Tool cache TTL | 300 sec | `config/agent.toml::tool_cache_ttl` |
| Tool cache max size | 200 entries | `config/agent.toml::tool_cache_max_size` |
| Watchdog interval | `0` (disabled, LOCAL default; PRODUCTION default is `30.0`) | `config/agent.toml::mcp_watchdog_interval` |
| Health registry threshold | 3 failures | hardcoded in `shared/mcp_config.py` |
| startup_timeout_sec | 30 sec | `McpServerConfig.startup_timeout_sec` |
| github default_per_page | 20 | `config/github_mcp_server.toml` |
| github max_per_page | 100 | `config/github_mcp_server.toml` |
| shell max_timeout_sec | 300 sec | `config/shell_mcp_server.toml` |
| shell sandbox_backend | `"none"` (local) / `"firejail"` (prod) | `config/shell_mcp_server.toml` |
| git max_log_entries | 50 | `config/git_mcp_server.toml` |

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
