---
title: "Agent CLI and Commands - Slash Commands: Workflow, Debug/Audit, RAG/Export"
category: agent
tags:
  - agent
  - cli
  - slash-commands
  - workflow
  - debug
  - rag-export
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
  - 05_agent_07_09_cli-and-commands-slash-commands-context-db.md
  - 05_agent_07_11_cli-and-commands-slash-commands-memory-other.md
source:
  - 05_agent_07_cli-and-commands.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

### Workflowカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/approve <approval_id> [reason]` | 保留中のワークフロー承認を「承認済み」として解決 | `approval_id` は必須引数 — 省略時は検証エラー（DB検索フォールバックは存在しない） |
| `/reject <approval_id> [reason]` | 保留中のワークフロー承認を「却下」として解決 | `approval_id` は必須引数 — 省略時は検証エラー（DB検索フォールバックは存在しない） |

> **適用範囲:** `/approve`と`/reject`は**ワークフローレベルの承認ゲートのみ**(`approvals`DBレコード)を解決する。
> ツールごとのインタラクティブな承認プロンプト(`tool_approval.run_approval_checks`)には影響しない。
> 正式な承認モデルについては[Tool Execution and Approval](05_agent_06_01_tool-execution-and-approval-execution.md)を参照。

#### 起動時のリカバリ

ワークフローレベルの承認が保留中の状態でエージェントが再起動した場合、その保留状態は
`StateStore.find_latest_pending_approval()`によって`approvals`データベーステーブルから
起動時に自動検出される。起動時に以下の通知が表示される:

```
[workflow] Pending approval from previous session — task=<task_id> approval=<approval_id> reason=<reason>. Use /approve <approval_id> [reason] or /reject <approval_id> [reason].
```

ワークフローは承認ゲートから再開され、以前のステップの再実行は不要である。

**セッションをまたぐ保証:** `/approve`と`/reject`は、メモリ上の`ctx.turn.pending_approval_id`が
None(クラッシュ後など)であっても、`approvals`DBテーブルから最新の保留中承認を解決する。
`/approve`が成功すると、自動再開のために`ctx.turn.pending_approval_task_id`が
設定される — 以前のステップの再実行は不要である。

### Debug / auditカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/debug` | なし | `ctx.conv.debug_mode`をトグル |
| `/debug verbose\|normal` | ログレベルを変更 | `structlog`のレベル変更 |
| `/audit [tail N\|turn <id>\|tool <name>]` | なし | audit.logを読み取り |

### RAG / Exportカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/rag search <query> [--debug]` | rag-pipeline-mcpへのMCP呼び出し | なし |
| `/compact` | LLM呼び出し(圧縮) | 履歴を即座に圧縮 |
| `/export [md\|json] [file]` | 会話をファイルまたはstdoutに書き込み | Markdownまたは JSONエクスポート |

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
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

workflow category
startup recovery
debug/audit category
RAG/export category
