---
title: "Agent Data Layer - Access Patterns"
category: agent
tags:
  - agent
  - data-layer
  - rag-mcp
  - document-access
  - memory-tables
related:
  - 05_agent_00_document-guide.md
  - 05_agent_09_01_data-layer-session-db.md
  - 05_agent_09_03_data-layer-indexing-boundaries.md
source:
  - 05_agent_09_01_data-layer-session-db.md
---

# エージェントデータ層

- 状態と永続化 → [05_agent_04_01_state-and-persistence-state-model-part1.md](05_agent_04_01_state-and-persistence-state-model-part1.md)

## rag.sqlite Tables (Agent-facing)(rag.sqlite のテーブル。エージェントから見た視点)

エージェント層はrag.sqliteを所有していない。これらのテーブルはRAG層が所有する。
エージェントはドキュメントレベルのデータには `rag-pipeline-mcp` を通じてアクセスし(`/db rag urls` と `/db rag clean` の場合)、
件数取得には `DbMaintenanceService.stats()` または `RagMaintenanceService.stats_rag()` を使用する(`/db rag stats` の場合)。

| Table | エージェントによる用途 |
|---|---|
| `documents` | `/db rag urls`(`rag_list_documents` MCP経由)、`/db rag clean`(`rag_delete_document` MCP経由) |
| `chunks` | `/db rag stats`、`/db rag rebuild-fts` |
| `chunks_fts` | `/db rag rebuild-fts`(FTS5仮想テーブル) |
| `chunks_vec` | `/db rag stats` |

**責任境界:** `/db rag urls` と `/db rag clean` は rag-pipeline-mcp 経由で `rag_list_documents` と
`rag_delete_document` を呼び出す。`DbMaintenanceService` は、一覧取得や削除に関するRAG
ドキュメントアクセスをもはや所有していない。

---

## RAG MCP Internal Path(RAG MCP内部パス)

`RagPipelineMCPService` は `list_documents()` と `delete_document()` を、内部で保持する
`DocumentManager`(`scripts/mcp_servers/rag_pipeline/document_manager.py`)に委譲する。
`DocumentManager` が `SQLiteHelper("rag")`(または設定された `rag_db_path` があればそちらのパス)を通じて
`rag.sqlite` に直接アクセスする。これはRAG MCPサービス所有者の内部操作であり、
エージェント層による直接DBアクセスではない。

**現在の実装挙動:** `RagPipelineMCPService.__init__` は `DocumentManager()` を保持し、設定ロード後は
`DocumentManager(rag_db_path=cfg.rag_db_path)` で再生成される。DB直接アクセスの実体クラスは
`RagPipelineMCPService` 自身ではなく `DocumentManager` である点に注意。(Explicit in code)

**許可されるもの:** `RagPipelineMCPService` / `DocumentManager`(scripts/mcp_servers/rag_pipeline/service.py, document_manager.py) — RAG MCPサービスは
これらの操作をその責任境界の一部として所有する。

**許可されないもの:** エージェントのアプリケーションコード、他のMCPサービス、共有層コードが
`rag.sqlite` に直接アクセスすること。これらはMCPツール呼び出しまたは承認済みのメンテナンスサービスを使用しなければならない。

### 削除順序の安全性

`delete_document()` は孤立レコードを防ぐため、厳格な削除順序を強制する:

1. まず `chunks_vec` の行(埋め込みベクトル)を削除する
2. `documents` の行(親ドキュメント)を削除する

この順序が必要なのは、`chunks_vec` が `documents` を指す外部キー制約を持たないためである。
ドキュメントを先に削除すると、埋め込みベクトルの行が孤立して残ってしまう。

```python
# delete_document() — order matters
db.execute(
    "DELETE FROM chunks_vec"
    " WHERE chunk_id IN"
    " (SELECT chunk_id FROM chunks WHERE doc_id = ?)",
    (doc_id,),
)
db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
```

その他の派生レコード(例: `chunks` テーブルの行)は、適用可能な場合は
カスケード削除やトリガーに依存する。

---

## Agent-Side Document Access Patterns(エージェント側のドキュメントアクセスパターン)

エージェントは3つの経路でドキュメントデータにアクセスする:

| Path | Mechanism | 使用場面 |
|---|---|---|
| MCPツール(基本) | `ToolRouteResolver` → MCPサーバ(rag-pipeline-mcp または mdq-mcp) | 通常運用。すべてのエージェントターン |
| `/db` コマンド(管理用) | `/db rag urls`+`/db rag clean` → rag-pipeline-mcp; `/db rag stats`+メンテナンス → `DbMaintenanceService`/`RagMaintenanceService` | 管理タスクのみ |
| DB直接アクセス | 推奨されない | アプリケーションコードでは使用しない |

MCPツールが推奨かつサポートされる経路である。`rag.sqlite` や `mdq.sqlite` に対する `sqlite3` の直接インポートは、通常のアプリケーションコードでは許可されない。`/db` の管理コマンドは、明示的なメンテナンス例外として `RagMaintenanceService` を使用する([04_mcp_05 §Agent Access Patterns](04_mcp_05_04_mdq-rag-boundary.md#agent-access-patterns) を参照)。RAGとMDQシステムの境界については [04_mcp_05 §MDQ vs RAG Boundary](04_mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary) を参照。

- **MDQ**: Markdownクエリサーバ。`mdq-mcp` ツール経由でのみアクセスする。FTS5検索とインデックス化が実装されている。RAG/MDQの境界については [04_mcp_05 §MDQ vs RAG Boundary](04_mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary) を参照。

## Memory Tables (optional)(メモリテーブル。任意)

`use_memory_layer=True` の場合、メモリサブシステムはJSONLとSQLiteの両方を使用する:

| Storage | Path | Contents |
|---|---|---|
| JSONL | `{memory_jsonl_dir}/memories.jsonl` | インポート/エクスポートおよび災害復旧用の追記専用アーカイブ |
| SQLite: `memories` | `session.sqlite`(sessions/messagesと同じDB) | 現在のメモリ状態の正本 |
| SQLite: `memories_fts` | 同じDB | メモリ内容に対するFTS5インデックス |
| SQLite: `memory_links` | 同じDB | メモリ間の多対多リンク |
| SQLite: `memories_vec` | 同じDB | 任意のKNN埋め込み |

データ所有権: メモリ層がこれらのテーブルを所有する。エージェントは `ctx.services.memory` を通じてアクセスする。

実装上の補足: SQLiteのメモリテーブルが現在のメモリ状態の正本である。JSONLはインポート/エクスポートおよび災害復旧用の追記専用アーカイブとして保持される。削除およびpin/unpin状態の変更はJSONLから再生されない。

すべてのメモリ用SQLiteテーブル(`memories`、`memories_fts`、`memory_links`、`memories_vec`)は `session.sqlite` 内に存在する。独立したメモリ用SQLiteデータベースは使用されない。

**設定:** `use_memory_layer` は `agent.toml` の設定項目(`config_builders.py` 経由、既定値 `False`)。`memory_jsonl_dir` の既定値は `/opt/llm/memory`。`use_memory_layer=True` の場合、`memory_jsonl_dir` が非空であることが起動時バリデーションで強制される(`config_dataclasses.py`)。JSONLファイルの実パスは `{memory_jsonl_dir}/memories.jsonl`(`agent/factory.py` で組み立て)。(Explicit in code)

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_09_01_data-layer-session-db.md`
- `05_agent_09_03_data-layer-indexing-boundaries.md`

## Keywords

RAG MCP internal path
document access patterns
memory tables
context manager pattern
