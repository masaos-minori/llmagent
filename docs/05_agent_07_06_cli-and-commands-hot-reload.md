---
title: "Agent CLI and Commands - Hot-Reload Scope"
category: agent
tags:
  - agent
  - cli
  - hot-reload
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_06_cli-and-commands-hot-reload.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

`/reload`コマンドの適用範囲と、設定変更の分類について文書化する。

## Design Intent

### `/reload`の役割

`/reload`はベース設定ファイルを読み込み、可能な限り変更を適用する。起動時のみの設定は検出されるが適用はされない。

### 設定ファイル

`config_loader.py`の`_BASE_CONFIG_FILES`は`("agent.toml",)`の1件のみ。エージェントプロセスの設定は`config/agent.toml`に集約されている。旧来の複数ファイル構成を前提にした記述は削除済み。

### 変更分類

| カテゴリ | 出力タグ | 説明 |
|---|---|---|
| ホットリロード可能 | `[OK]` | 実行中のプロセスに即座に適用される |
| 再起動必要 | `[RESTART]` | エージェントの完全な再起動が必要 |
| 起動時のみ | `[STARTUP-ONLY]` | 起動時に一度だけ読み込まれる。変更されても`/reload`では無視される |
| スキップ | `[SKIP]` | 意図的に無視される変更 |

### 出力メッセージ

- 何も変更なし: `No changes detected.`
- 全て適用済み: `Config reloaded — all changes applied`
- I/Oエラー: `Reload failed (I/O error): <message>`

## Responsibility Boundary

- **ホットリロード可能**: LLM設定、履歴管理、ツール設定など
- **再起動必要**: MCPサーバー設定など
- **起動時のみ**: プロセス起動時のみ読み込まれる設定

## Key Constraints

- 不明

## Operational Notes

- 各フィールドごとの完全な分類については[Configuration: Config file reload eligibility](05_agent_08_01_configuration-loading-agent-config.md#config-file-ownership-and-hot-reload-eligibility)を参照。

## Known Limitations

- 不明

## Related Docs

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
change classification
