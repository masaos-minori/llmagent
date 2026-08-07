---
title: "Agent CLI and Commands - Slash Commands: Workflow, Debug/Audit, Compact/Export"
category: agent
tags:
  - agent
  - cli
  - slash-commands
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Workflow、Debug/Audit、Git/Diff、Compact/Exportカテゴリのスラッシュコマンドの目的と副作用について文書化する。

## Design Intent

### Workflowカテゴリ

ワークフローレベルの承認ゲートに関するコマンド群。

| コマンド | 副作用 | 関連する状態 |
|---|---|---|
| `/approve <approval_id> [reason]` | 保留中のワークフロー承認を「承認済み」として解決 | `approval_id` は必須引数 — 省略時は検証エラー（DB検索フォールバックは存在しない） |
| `/reject <approval_id> [reason]` | 保留中のワークフロー承認を「却下」として解決 | `approval_id` は必須引数 — 省略時は検証エラー（DB検索フォールバックは存在しない） |

> **適用範囲:** `/approve`と`/reject`は**ワークフローレベルの承認ゲートのみ**(`approvals`DBレコード)を解決する。ツールごとのインタラクティブな承認プロンプトには影響しない。正式な承認モデルについては[Tool Execution and Approval](05_agent_06_01_tool-execution-and-approval-execution.md)を参照。

#### 起動時のリカバリ

ワークフローレベルの承認が保留中の状態でエージェントが再起動した場合、その保留状態は`StateStore.find_latest_pending_approval()`によって`approvals`データベーステーブルから起動時に自動検出される。

**セッションをまたぐ保証:** `/approve`と`/reject`は、メモリ上の`ctx.turn.pending_approval_id`がNone（クラッシュ後など）であっても、`approvals`DBテーブルから最新の保留中承認を解決する。

**上書き警告:** `/approve`は`ctx.turn.pending_approval_task_id`に既存の値がある状態で新しい値を設定する場合、`cmd_workflow.py`のロガーへ`WARNING`レベルでログを出力する。これは単一フィールドのみをハンドオフに使うキュー未実装の現状の設計上の既知の制約であり、操作者が取りこぼしを追跡できるようにするための可観測性目的の警告である。

### Debug / Auditカテゴリ

デバッグと監査ログに関するコマンド群。

### Git/Diffカテゴリ

`/diff`は現在のセッションの`ctx.conv.history`に残っているツール呼び出ししか見えない。セッション中に`/compact`または`/clear`を実行すると、それ以前に書き込み/編集されたファイルは`/diff`の対象から外れる（設計上の割り切り。DBベースの変更追跡は行わない）。

### Compact / Exportカテゴリ

RAG検索はスラッシュコマンドとしては提供されていない — 通常の会話中にLLMが`rag_run_pipeline`ツールとして自動的に呼び出す（MCP経由）。ユーザーが直接呼び出す専用スラッシュコマンドは存在しない。

## Responsibility Boundary

- **Workflow**: ワークフローレベルの承認ゲート管理
- **Debug/Audit**: デバッグモードと監査ログ
- **Git/Diff**: セッション内のファイル変更表示
- **Compact/Export**: 履歴圧縮とエクスポート

## Key Constraints

- 不明

## Operational Notes

- 不明

## Known Limitations

- `/diff`は現在のセッションの`ctx.conv.history`に残っているツール呼び出ししか見えない

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

workflow category
debug/audit category
git/diff category
compact/export category
