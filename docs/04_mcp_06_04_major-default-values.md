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

| パラメータ | デフォルト | Configファイル |
|---|---|---|
| 最大レスポンスバイト数 | 512 KB | `mcp/server.py` にハードコード |
| call_timeout_sec | 60.0秒 | `McpServerConfig.call_timeout_sec` |
| Toolキャッシュ TTL | 300秒 | `config/agent.toml::tool_cache_ttl` |
| Toolキャッシュ最大サイズ | 200エントリ | `config/agent.toml::tool_cache_max_size` |
| Watchdog間隔 | `0`（無効、LOCALのデフォルト；PRODUCTIONのデフォルトは `30.0`） | `config/agent.toml::mcp_watchdog_interval` |
| ヘルスレジストリの閾値 | 3回失敗 | `shared/mcp_config.py` にハードコード |
| startup_timeout_sec | 30秒 | `McpServerConfig.startup_timeout_sec` |
| github default_per_page | 20 | `config/github_mcp_server.toml` |
| github max_per_page | 100 | `config/github_mcp_server.toml` |
| shell max_timeout_sec | 300秒 | `config/shell_mcp_server.toml` |
| shell sandbox_backend | `"none"`（local）／`"firejail"`（prod） | `config/shell_mcp_server.toml` |
| git max_log_entries | 50 | `config/git_mcp_server.toml` |

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
