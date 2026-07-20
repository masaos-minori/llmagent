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

| パラメータ | デフォルト | Production推奨 | Configファイル |
|---|---|---|---|
| 最大レスポンスバイト数 | 512 KB | — | `scripts/mcp_servers/server.py`（`MCP_MAX_RESPONSE_BYTES`）にハードコード |
| call_timeout_sec | 60.0秒 | — | `McpServerConfig.call_timeout_sec`（`shared/mcp_config.py`） |
| Toolキャッシュ TTL | 300秒 | — | `config/agent.toml::tool_cache_ttl`（`ToolConfig.tool_cache_ttl` のデフォルトも同値） |
| Toolキャッシュ最大サイズ | 200エントリ | — | `config/agent.toml::tool_cache_max_size`（`ToolConfig.tool_cache_max_size` のデフォルトも同値） |
| ヘルスレジストリの閾値 | 3回失敗 | — | `shared/mcp_health.py`（`McpServerHealthRegistry.__init__` の `failure_threshold` 引数）にハードコード；`shared/mcp_config.py` は当該クラスを re-export するのみ (Explicit in code) |
| startup_timeout_sec | 30秒 | — | `McpServerConfig.startup_timeout_sec`（`shared/mcp_config.py`） |
| github default_per_page | 10（モジュール定数 `DEFAULT_PER_PAGE`、`models_config.py`） | — | ハードコード。`config/github_mcp_server.toml::default_per_page` は2026-07-13に削除済み（未参照のデッド設定だったため。詳細: [04_mcp_04_01](04_mcp_04_01_web-search-file-read-github.md)） |
| github max_per_page | 100 | — | `config/github_mcp_server.toml`(こちらは実際に `per_page` のクランプに使用される有効な設定) |
| shell max_timeout_sec | 300秒 | — | `config/shell_mcp_server.toml` |
| shell sandbox_backend | `"none"` | **`"firejail"`** （`none` = sandbox disabled） | `config/shell_mcp_server.toml` |
| git max_log_entries | 50 | — | `config/git_mcp_server.toml` |

**補足:** `config/shell_mcp_server.toml` 内のコメントには「production環境では `shell_sandbox_backend = "firejail"` を設定し、firejailバイナリをPATHに用意すること」という運用ガイドが記載されている（未設定時にfirejailが見つからないと `RuntimeError` になる: `mcp_servers/shell/service_static_helpers.py`）。ただし当該値はconfigファイルの値であり、`security_profile` に連動して自動切替される値ではない (Explicit in code)。

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
