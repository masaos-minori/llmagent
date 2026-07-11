---
title: "Agent CLI and Commands - Slash Commands: Memory, MDQ, Plugin, Other"
category: agent
tags:
  - agent
  - cli
  - slash-commands
  - memory
  - mdq
  - plugin
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
  - 05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md
source:
  - 05_agent_07_cli-and-commands.md
---

# Agent CLI and Commands

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

### Memoryカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/memory list [semantic\|episodic] [n]` | なし | メモリエントリを表示 |
| `/memory search <query>` | なし | メモリに対するFTS5検索 |
| `/memory show <id>` | なし | メモリエントリの全文表示 |
| `/memory pin <id>` | pinnedフラグをUPDATE | セッション開始のたびにエントリが注入される |
| `/memory unpin <id>` | pinnedフラグをUPDATE | セッション開始時の注入を解除 |
| `/memory delete <id>` | エントリをDELETE | 即時反映 |
| `/memory prune [days]` | N日より古いエントリをDELETE | デフォルトは`memory_retention_days`を使用 |
| `/memory status` | なし | メモリモードのラベル(例: Hybrid mode / Degraded mode / Memory layer disabled)、埋め込みの状態、サーキットの状態、検索モードを表示。メモリ無効時にも動作する |
| `/memory check-consistency` | なし | JSONL、SQLite、FTS5、vecの行数を比較 |
| `/memory rebuild [--dry-run]` | JSONLから全メモリをDELETE + INSERT | JSONLが正典のソースであり、SQLiteをクリアして再挿入する |

### MDQカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/mdq status` | なし | ヘルスとインデックス統計を表示(`stats` MCPツールを呼び出す) |
| `/mdq index <path> [--force]` | ファイル/ディレクトリをインデックス | mdq.sqliteが更新される |
| `/mdq refresh <path> [--force]` | 変更されたファイルの差分更新 | mdq.sqliteが更新される |
| `/mdq search <query> [--limit N] [--path-prefix PATH] [--mode bm25\|grep]` | FTS5検索 | なし |
| `/mdq outline <path> [--max-depth N]` | なし | 見出し階層を表示 |
| `/mdq get <chunk_id> [--with-neighbors]` | なし | チャンクの内容を表示 |
| `/mdq grep <pattern> [--path PATH] [--max-chars N] [--context-before N] [--context-after N]` | チャンクに対する正規表現検索 | なし |

> **注記:** すべての/mdqコマンドは、エージェントのツールエグゼキュータ経由でmdq-mcpのMCPツール(ポート8013)を呼び出す。MDQは`mdq.sqlite`(`rag.sqlite`とは別)を使用する。MDQとRAGの使い分けについては[MDQ vs RAG Boundary](04_mcp_05_security_and_safety_model.md#mdq-vs-rag-boundary)を参照。

### Pluginカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/plugin status` | なし | プラグインの読み込み結果(loaded、failed、conflicts)を表示 |

### Otherカテゴリ

| Command | 副作用 | 関連する状態 |
|---|---|---|
| `/help` | なし | このヘルプ出力を表示 |

---

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
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`

## Keywords

memory category
MDQ category
plugin category
other category
