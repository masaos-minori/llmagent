---
title: "Agent CLI and Commands - Slash Commands: Session, MCP, Config/Stats"
category: agent
tags:
  - agent
  - cli
  - slash-commands
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Session、MCP、Config/Statsカテゴリのスラッシュコマンドの目的と副作用について文書化する。

## Design Intent

### Sessionカテゴリ

セッション管理と履歴操作に関するコマンド群。`/clear new`は新しいDBセッションを開始する。`/undo`は履歴+DBから直近のuser+assistantターンをpopする。

#### Session DB操作サブコマンド

旧`/db session <subcmd>`サブコマンドはすべて`/session <subcmd>`へ移管された。詳細は[Context/DBカテゴリ](05_agent_07_09_cli-and-commands-slash-commands-context-db.md)を参照。

### MCPカテゴリ

`/mcp` / `/mcp status`は**現在実行中の**MCPサーバー設定のヘルスビューであり、保留中の`/reload`変更のプレビューではない。

`/mcp status`の出力にはサーバー一覧テーブル、DEGRADED/UNAVAILABLE状態のサーバー一覧、直列化イベント統計が含まれる。

### Config / statsカテゴリ

設定ファイルの表示と監視に関するコマンド群。`/reload`はすべての設定ファイルをリロードし、`ctx.cfg`を更新してサービスに同期する。

## Responsibility Boundary

- **Session**: セッションと履歴のライフサイクル管理
- **MCP**: MCPサーバーのヘルスとツール一覧
- **Config/Stats**: 設定とメトリクスの表示

## Key Constraints

- 不明

## Operational Notes

- 不明

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `04_mcp_06_12_watchdog-configuration-monitoring.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

slash command reference
session category
mcp category
config/stats category
