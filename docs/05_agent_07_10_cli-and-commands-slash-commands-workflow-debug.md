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
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Workflowカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/approve <approval_id> [reason]` | 保留中のワークフロー承認を「承認済み」として解決 | `approval_id` は必須引数 — 省略時は検証エラー（DB検索フォールバックは存在しない） |
| `/reject <approval_id> [reason]` | 保留中のワークフロー承認を「却下」として解決 | `approval_id` は必須引数 — 省略時は検証エラー（DB検索フォールバックは存在しない） |

> **適用範囲:** `/approve`と`/reject`は**ワークフローレベルの承認ゲートのみ**(`approvals`DBレコード)を解決する。
> ツールごとのインタラクティブな承認プロンプト(`tool_approval.run_approval_checks`)には影響しない。
> 正式な承認モデルについては[Tool Execution and Approval](05_agent_06_01_tool-execution-and-approval-execution.md)を参照。

### 起動時のリカバリ

### Startup recovery

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

### Git/Diffカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/diff` | なし（読み取り専用；`git_diff` MCPツールを呼び出す） | `ctx.conv.history`内の`write_file`/`edit_file`ツール呼び出しをスキャンして対象パスを収集 |

> **既知の制限:** `/diff`は現在のセッションの`ctx.conv.history`に残っているツール呼び出ししか見えない。
> セッション中に`/compact`または`/clear`を実行すると、それ以前に書き込み/編集されたファイルは
> `/diff`の対象から外れる（設計上の割り切り。DBベースの変更追跡は行わない）。
>
> **前提条件:** `git_diff`は`config/git_mcp_server.toml`の`allowed_repo_paths`にリポジトリの絶対パスが
> 含まれている場合のみ実際の diff を返す。デフォルトは空リスト（`[]`）— fail-closed設計のため、
> 未設定の状態では全てのリポジトリで `[DENIED] repo_path ... is not in allowed_repo_paths` という
> 明確な拒否メッセージが表示される（エラーやクラッシュではない）。

### Exportカテゴリ

RAG検索はスラッシュコマンドとしては提供されていない — 通常の会話中にLLMが
`rag_run_pipeline`ツールとして自動的に呼び出す(MCP経由)。ユーザーが直接呼び出す
専用スラッシュコマンドは存在しない。(Explicit in code — `command_defs_list.py`の
`_COMMANDS`に該当する`CommandDef`エントリなし)

| Command | 副作用 | 関連する状態 |
|---|---|---|
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
git/diff category
RAG/export category
