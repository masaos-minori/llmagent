---
title: "Agent CLI and Commands - CLIView"
category: agent
tags:
  - agent
  - cli
  - cliview
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_02_cli-and-commands-cliview.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

プレゼンテーション層のみを担当するCLIViewの責務と、各コンポーネントへのコールバック注入について文書化する。

## Design Intent

### CLIViewの責任分割

CLIViewは`agent/cli_view.py`にあり、**プレゼンテーション層のみ**を担当する。ステート管理やビジネスロジックを持たず、各コンポーネントにコールバックとして注入される。

### コールバック注入

| Callback | 注入先 | 呼び出しタイミング |
|---|---|---|
| `write_token(token)` | `LLMClient(on_token=...)` | SSEトークンが届くたびに |
| `write_compress_notice(n)` | `HistoryManager(on_compress=...)` | 履歴が圧縮されたとき |
| `write_turn_start()` | `Orchestrator(on_turn_start=...)` | 各ツールループのターン開始前 |
| `write_turn_end()` | `Orchestrator(on_turn_end=...)` | 最終的なLLM回答の後 |
| `write_llm_error(e)` | `Orchestrator(on_error=...)` | LLMリクエストが失敗したとき |

### スピナーとトークンの関係

`write_token()`はトークン出力の直前に`stop_spinner()`を呼び、スピナー表示中でもストリーミングトークンが割り込めるようにしている。

### 起動バナー

`write_startup_banner()`はセッションID、chunkカウント、ツール数、メモリモード、ワークフロー状態を表示する。

## Responsibility Boundary

- **プレゼンテーション層のみ**: ステート管理やビジネスロジックを持たない
- **テスト用プロトコル**: `Writer`(出力操作)と`Reader`(複数行入力)のプロトコル定義により、テスト時に別実装を注入可能

## Key Constraints

- `CLIView.__init__(slash_commands)`はスラッシュコマンド一覧を必須引数として受け取り、タブ補完候補として使用する。

## Operational Notes

- 不明

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

CLIView
responsibility boundary
callbacks
