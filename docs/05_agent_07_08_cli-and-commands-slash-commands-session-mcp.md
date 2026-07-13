---
title: "Agent CLI and Commands - Slash Commands: Session, MCP, Config/Stats"
category: agent
tags:
  - agent
  - cli
  - slash-commands
  - session
  - mcp
  - config
related:
  - 05_agent_00_document-guide.md
  - 05_agent_07_01_cli-and-commands-cli-reference.md
  - 05_agent_07_02_cli-and-commands-cliview.md
  - 05_agent_07_03_cli-and-commands-command-registry.md
  - 05_agent_07_04_cli-and-commands-purpose.md
  - 05_agent_07_05_cli-and-commands-repl-io.md
  - 05_agent_07_06_cli-and-commands-hot-reload.md
  - 05_agent_07_07_cli-and-commands-migration-notes.md
  - 05_agent_07_09_cli-and-commands-slash-commands-context-db.md
  - 05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md
  - 05_agent_07_11_cli-and-commands-slash-commands-memory-other.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## スラッシュコマンドリファレンス

### Sessionカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/session list [n]` | なし | `sessions`テーブルを読み取り |
| `/session load <id>` | `ctx.conv.history`を置き換え | `ctx.session.session_id`が更新される |
| `/session rename <title>` | `sessions.title`をUPDATE | なし |
| `/session delete <id>` | セッション+メッセージをDELETE(CASCADE) | 現在のセッションは削除不可 |
| `/clear [new]` | 履歴をリセット、統計情報とキャッシュをクリア | `new` → 新しいDBセッションを開始 |
| `/undo` | 履歴+DBから直近のuser+assistantターンをpop | メモリ注入も削除される |
| `/history [n]` | なし | 直近N件のuser/assistantメッセージを表示 |
| `/export [md\|json] [file]` | ファイル書き込み(ファイル名指定時) | なし |

### MCPカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/mcp` | 全MCPサーバーへのHTTPプローブ | ヘルステーブルを表示(実行中の設定のみ) |
| `/mcp status` | 全MCPサーバーへのHTTPプローブ | ヘルステーブルを表示(実行中の設定のみ) |

`/mcp` / `/mcp status`は**現在実行中の**MCPサーバー設定のヘルスビューであり、
保留中の`/reload`変更のプレビューではない。
`/reload`が`[RESTART]`項目を報告した後も、`/mcp`はエージェントが実際に
再起動されるまで、リロード前のサーバー・URL・認証状態を表示し続ける。

`/mcp status`の出力にはサーバー一覧テーブルに加え、Watchdogの有効/無効状態
(`mcp_watchdog_interval`, `mcp_watchdog_max_restarts`)、DEGRADED/UNAVAILABLE状態の
サーバー一覧(`ServerHealthRegistry`経由)、直列化(serialization)イベント統計
(発生回数・平均影響ツール数・理由別内訳・上位トリガー)が含まれる
(根拠: Explicit in code — `agent/commands/cmd_mcp.py::_cmd_mcp_status()`)。

### Config / statsカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/config` | なし | 設定ファイルのパスと値を表示 |
| `/stats` | なし | セッションのメトリクスを表示 |
| `/set temperature <f>` | `ctx.cfg.llm.llm_temperature`とLLMサービス内部のtemperatureフィールドを更新 | LLMに即座に反映 |
| `/set max_tokens <n>` | `ctx.cfg.llm.llm_max_tokens`を更新 | LLMに即座に反映 |
| `/reload` | すべての設定ファイルをリロード | `ctx.cfg`を更新しサービスに同期 |

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

slash command reference
session category
mcp watchdog status
serialization events
MCP category
config/stats category
