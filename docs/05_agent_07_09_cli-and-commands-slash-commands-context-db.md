---
title: "Agent CLI and Commands - Slash Commands: Context, DB, Plan"
category: agent
tags:
  - agent
  - cli
  - slash-commands
  - context
  - db
  - plan
related:
  - 05_agent_00_document-guide.md
  - 05_agent_07_01_cli-and-commands-cli-reference.md
  - 05_agent_07_02_cli-and-commands-cliview.md
  - 05_agent_07_03_cli-and-commands-command-registry.md
  - 05_agent_07_04_cli-and-commands-purpose.md
  - 05_agent_07_05_cli-and-commands-repl-io.md
  - 05_agent_07_06_cli-and-commands-hot-reload.md
  - 05_agent_07_07_cli-and-commands-migration-notes.md
  - 05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md
  - 05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md
  - 05_agent_07_11_cli-and-commands-slash-commands-memory-other.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

### Contextカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/context` | なし | 履歴サイズ、バジェット、システムプロンプト、ワークフローモード、承認待ち状態を表示 |
| `/compact` | LLM呼び出し(圧縮) | 履歴を即座に圧縮 |
| `/system [name]` | `history[0]`を更新 | `ctx.conv.system_prompt_name` |

### DBカテゴリ

#### `/db rag`サブコマンド

| Command | 副作用 | Notes |
|---|---|---|
| `/db rag stats` | なし | ドキュメント/チャンク数(RAGのみ) |
| `/db rag urls [--lang] [--limit]` | なし | rag-pipeline-mcp経由でドキュメント一覧を表示 |
| `/db rag clean <url>` | rag-pipeline-mcp経由でドキュメント+チャンクを削除 | カスケード削除 |
| `/db rag rebuild-fts` | `chunks_fts`インデックスを再構築 | FTS5再構築 |
| `/db rag vec-rebuild` | なし | ベクトルインデックスを再構築 |
| `/db rag reconcile-url <url>` | なし | 単一URLについてFTS/vecを再構築 |
| `/db rag recover [backup-path]` | 整合性チェック、破損時はバックアップから復元 | RAGのみ |
| `/db rag consistency` | なし | Chunks/FTS/ベクトルインデックスの同期チェック |

#### `/db session`サブコマンド

| Command | 副作用 | Notes |
|---|---|---|
| `/db session stats` | なし | セッション/メッセージ数 |
| `/db session health` | なし | journal_mode / 整合性 / ページ統計 |
| `/db session checkpoint [MODE]` | WALチェックポイント | WALをメインDBにフラッシュ |
| `/db session vacuum` | VACUUM | 空きページを回収 |
| `/db session purge [--max-sessions N] [--max-age-days N]` | 古いセッションをDELETE | 件数または経過日数に基づく |
| `/db session recover [backup-path]` | 整合性チェック、破損時はバックアップから復元 | Sessionのみ |

> **注記:** `/db rag urls`と`/db rag clean`は、エージェントのツールエグゼキュータ経由でrag-pipeline-mcpのMCPツール(`rag_list_documents`、`rag_delete_document`)を呼び出す。RAGメンテナンスコマンドは`RagMaintenanceService`を使用し、セッションメンテナンスコマンドは`DbMaintenanceService`を使用する。`session.sqlite`と`workflow.sqlite`は、コード内で`SQLiteHelper(target=...)`経由でアクセスされ、`/db`コマンド経由ではない。スキーマの詳細: `90_shared_04`。

### Planカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/plan` | なし | `ctx.conv.plan_mode`をトグル |

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

context category
DB category
/db rag subcommands
/db session subcommands
plan category
