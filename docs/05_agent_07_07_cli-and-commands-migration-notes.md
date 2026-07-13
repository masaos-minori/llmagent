---
title: "Agent CLI and Commands - Migration Notes"
category: agent
tags:
  - agent
  - cli
  - migration-notes
related:
  - 05_agent_00_document-guide.md
  - 05_agent_07_01_cli-and-commands-cli-reference.md
  - 05_agent_07_02_cli-and-commands-cliview.md
  - 05_agent_07_03_cli-and-commands-command-registry.md
  - 05_agent_07_04_cli-and-commands-purpose.md
  - 05_agent_07_05_cli-and-commands-repl-io.md
  - 05_agent_07_06_cli-and-commands-hot-reload.md
  - 05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md
  - 05_agent_07_09_cli-and-commands-slash-commands-context-db.md
  - 05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md
  - 05_agent_07_11_cli-and-commands-slash-commands-memory-other.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## 移行に関する注記

以下のスラッシュコマンド/サブコマンドは廃止済みであり、現在の`agent/commands/command_defs_list.py`(`_COMMANDS`)には存在しない。根拠: Explicit in code(コマンド定義の不在、`tests/test_agent_cmd_db.py::TestCmdDbFlatAliasesInvalid`等の回帰テストで検証済み)。

### `/note`コマンド群(削除)

`/note add <text>` / `/note list` / `/note delete <id>`は削除された。`cmd_notes.py`・`NoteRepository`・`auto_inject_notes`・`notes`テーブルが除去されている。長期記憶の代替は`/memory`コマンド群を参照(`05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`)。

### `/ingest`コマンド(削除)

`/ingest <url|path> [lang] [--snippets-only]`は削除された。`IngestWorkflowService`および関連DTO/例外が除去されている。ドキュメント投入はRAGパイプライン側(`rag/`配下)の仕組みを参照。

### `/debug audit`サブコマンド(削除)

`/debug audit`(audit.logの末尾表示)は削除された。監査ログの参照は`/audit`コマンド(`tail N | turn <task_id> | tool <name>`)を使う。`/debug`は未知のサブコマンドを明示的に拒否する(根拠: Explicit in code — `cmd_debug.py`)。

### `/db`フラットエイリアス(削除)

以下のスコープなしフラット形式は廃止され、`/db rag <subcmd>`または`/db session <subcmd>`のスコープ付き形式のみが有効である。

| 廃止された形式 | 置き換え |
|---|---|
| `/db urls [--lang] [--limit]` | `/db rag urls [--lang] [--limit]` |
| `/db clean <url>` | `/db rag clean <url>` |
| `/db rebuild-fts` | `/db rag rebuild-fts` |
| `/db recover [backup-path]` | `/db rag recover [backup-path]` または `/db session recover [backup-path]` |
| `/db stats` | `/db rag stats` または `/db session stats` |
| `/db health` | `/db session health` |
| `/db checkpoint [MODE]` | `/db session checkpoint [MODE]` |
| `/db vacuum` | `/db session vacuum` |
| `/db purge [--max-sessions N] [--max-age-days N]` | `/db session purge [--max-sessions N] [--max-age-days N]` |
| `/db consistency` | `/db rag consistency` |

フラット形式を入力すると使用方法(usage)メッセージが表示され、実行はされない(根拠: Explicit in code — `tests/test_agent_cmd_db.py`のフラットエイリアス無効テスト群)。後方互換は提供されていない。

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

migration notes
/note removal
/ingest removal
/debug audit removal
/db flat alias removal
