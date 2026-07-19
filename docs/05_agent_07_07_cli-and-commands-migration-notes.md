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

### `/db`コマンド(完全削除)

`/db`は、そのフラットエイリアス形式・`/db rag <subcmd>`形式・`/db session <subcmd>`形式のすべてを含めて廃止された。旧`/db session <subcmd>`の機能は`/session <subcmd>`へ移管されている。旧`/db rag <subcmd>`の機能に対する後継コマンドは提供されない。

| 廃止された形式 | 現在の状態 |
|---|---|
| `/db urls [--lang] [--limit]` | 後継コマンドなし(RAGパイプライン側のMCPツールを直接利用) |
| `/db clean <url>` | 後継コマンドなし |
| `/db rebuild-fts` | `/session rag-rebuild-fts` |
| `/db recover [backup-path]` | `/session recover [backup-path]` |
| `/db stats` | `/session stats` |
| `/db health` | `/session health` |
| `/db checkpoint [MODE]` | `/session checkpoint [MODE]` |
| `/db vacuum` | `/session vacuum` |
| `/db purge [--max-sessions N] [--max-age-days N]` | `/session purge [--max-sessions N] [--max-age-days N]` |
| `/db consistency` | `/session rag-consistency` |

`/db`はいかなる形式(フラット・`rag`スコープ・`session`スコープ)でももはや認識されるコマンドではなく、未知のスラッシュコマンドとして扱われる(根拠: Explicit in code — `agent/commands/command_defs_list.py`に`/db`の`CommandDef`が存在しない、および`tests/test_cmd_registry_ingest_removal.py`/`tests/test_command_def_sync.py`の回帰テスト)。後方互換は提供されていない。

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
/db removed entirely
