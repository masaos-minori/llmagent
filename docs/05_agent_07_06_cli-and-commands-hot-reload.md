---
title: "Agent CLI and Commands - Hot-Reload Scope"
category: agent
tags:
  - agent
  - cli
  - hot-reload
  - reload-classification
related:
  - 05_agent_00_document-guide.md
  - 05_agent_07_01_cli-and-commands-cli-reference.md
  - 05_agent_07_02_cli-and-commands-cliview.md
  - 05_agent_07_03_cli-and-commands-command-registry.md
  - 05_agent_07_04_cli-and-commands-purpose.md
  - 05_agent_07_05_cli-and-commands-repl-io.md
  - 05_agent_07_07_cli-and-commands-migration-notes.md
  - 05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md
  - 05_agent_07_09_cli-and-commands-slash-commands-context-db.md
  - 05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md
  - 05_agent_07_11_cli-and-commands-slash-commands-memory-other.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## ホットリロードの範囲 (`/reload`)

`/reload`はベース設定ファイル(`shared.config_loader._BASE_CONFIG_FILES`が定義する集合、詳細は[設定ドキュメント](05_agent_08_01_configuration-loading-agent-config-part1.md)参照)を読み込み、可能な限り変更を適用する。起動時のみの設定は検出されるが適用はされない。

> **注記:** `scripts/shared/config_loader.py`の`_BASE_CONFIG_FILES`は現状`("agent.toml",)`の1件のみであり、「12個のベース設定ファイル」という記述は実装と一致しない。エージェントプロセスの設定は`config/agent.toml`に集約されており、個別の`common.toml`等の分割ファイルは存在しない(根拠: Explicit in code — `config_loader.py`)。旧来の複数ファイル構成を前提にした記述が残っていた可能性がある。件数の記述は削除し、実装ファイルへの参照に置き換えた。

### 出力フォーマット

```
Config reloaded — some changes require restart
WARNING: Some settings require restart to take effect.
Restart required: [4 items]
  [RESTART] - server1
  [RESTART] - mcp_servers/github.url
  [RESTART] - mcp_servers/github.startup_mode
  [RESTART] - mcp_servers/server2.auth_token
Applied (runtime): [3 items]
  [OK] - llm
  [OK] - hist_mgr
  [OK] - tools
Startup-only (ignored): [1 items]
  [STARTUP-ONLY] - use_memory_layer
```

`[RESTART] - mcp_servers/server.url` の部分はプレースホルダで、実際の出力では `{server_key}` に置き換わる（例: `mcp_servers/github.url`）。

何も変更がない場合: `No changes detected.`
すべての変更が適用された場合: `Config reloaded — all changes applied`
ファイルが読み込めない場合: `Reload failed (I/O error): <message>`

### リロード分類サマリー

| Category | `/reload` output tag | Description |
|---|---|---|
| Hot-reloadable | `[OK]` | 実行中のプロセスに即座に適用される |
| Restart-required | `[RESTART]` | エージェントの完全な再起動が必要 |
| Startup-only | `[STARTUP-ONLY]` | 起動時に一度だけ読み込まれる。変更されても`/reload`では無視される |
| Skipped | `[SKIP]` | 意図的に無視される変更。MCPサーバー定義ではない — Restart-requiredを参照 |

各フィールドごとの完全な分類表については[Configuration: Config file reload eligibility](05_agent_08_01_configuration-loading-agent-config-part1.md#config-file-ownership-and-hot-reload-eligibility)を参照。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

hot-reload scope
/reload
output format
reload classification summary
_BASE_CONFIG_FILES
config_loader.py
