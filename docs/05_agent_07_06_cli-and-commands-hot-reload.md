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
source:
  - 05_agent_07_cli-and-commands.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## ホットリロードの範囲 (`/reload`)

`/reload`は12個のベース設定ファイル(すべて、[設定ドキュメント](05_agent_08_01_configuration-loading-agent-config-part1.md)参照)を読み込み、可能な限り変更を適用する。起動時のみの設定は検出されるが適用はされない。

### 出力フォーマット

```
Config reloaded — some changes require restart
WARNING: Some settings require restart to take effect.
Restart required: [4 items]
  [RESTART] - server1
  [RESTART] - mcp/server.url
  [RESTART] - mcp/server.startup_mode
  [RESTART] - mcp/server2.auth_token
Applied (runtime): [3 items]
  [OK] - llm
  [OK] - hist_mgr
  [OK] - tools
Startup-only (ignored): [1 items]
  [STARTUP-ONLY] - use_memory_layer
```

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
