---
title: "Agent Data Layer - Access Patterns"
category: agent
tags:
  - agent
  - data-layer
  - rag-mcp
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_09_02_data-layer-access-patterns.md
---

# エージェントデータ層

- 状態と永続化 → [05_agent_04_01_state-and-persistence-state-model.md](05_agent_04_01_state-and-persistence-state-model.md)

## Purpose

RAG層との責任境界、エージェントからのドキュメントアクセスパターンについて文書化する。

## Design Intent

### RAG層との責任境界

エージェント層は `rag.sqlite` を所有していない。これらのテーブルはRAG層が所有する。

- エージェントはドキュメントレベルのデータには `rag-pipeline-mcp` を通じてアクセスする
- 件数取得には `DbMaintenanceService.stats()` または `RagMaintenanceService.stats_rag()` を使用する

**Design judgment**: `/db rag urls` と `/db rag clean` は rag-pipeline-mcp 経由で `rag_list_documents` と `rag_delete_document` を呼び出す。`DbMaintenanceService` は一覧取得や削除に関するRAGドキュメントアクセスをもはや所有していない。

### RAG MCP内部パス

`RagPipelineMCPService` は `list_documents()` と `delete_document()` を、内部で保持する `DocumentManager` に委譲する。`DocumentManager` が `SQLiteHelper("rag")` を通じて `rag.sqlite` に直接アクセスする。

**許可されるもの**: `RagPipelineMCPService` / `DocumentManager` — RAG MCPサービスはこれらの操作をその責任境界の一部として所有する。

**許可されないもの**: エージェントのアプリケーションコード、他のMCPサービス、共有層コードが `rag.sqlite` に直接アクセスすること。これらはMCPツール呼び出しまたは承認済みのメンテナンスサービスを使用しなければならない。

#### 削除順序の安全性

`delete_document()` は孤立レコードを防ぐため、厳格な削除順序を強制する:

1. まず `chunks_vec` の行(埋め込みベクトル)を削除する
2. `documents` の行(親ドキュメント)を削除する

**Design judgment**: この順序が必要なのは、`chunks_vec` が `documents` を指す外部キー制約を持たないためである。ドキュメントを先に削除すると、埋め込みベクトルの行が孤立して残ってしまう。

### エージェント側のドキュメントアクセスパターン

| Path | Mechanism | Use case |
|---|---|---|
| MCPツール(基本) | `ToolRouteResolver` → MCPサーバ(rag-pipeline-mcp または mdq-mcp) | 通常運用 |
| `/db` コマンド(管理用) | `/db rag urls`+`/db rag clean` → rag-pipeline-mcp; `/db rag stats`+メンテナンス → `DbMaintenanceService`/`RagMaintenanceService` | 管理タスクのみ |
| DB直接アクセス | 推奨されない | アプリケーションコードでは使用しない |

**Design judgment**: MCPツールが推奨かつサポートされる経路である。`rag.sqlite` や `mdq.sqlite` に対する `sqlite3` の直接インポートは、通常のアプリケーションコードでは許可されない。

## Responsibility Boundary

- **正典**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_document_manager.py`
- **Schema**: `schema_sql.py` (権威)

## Key Constraints

- エージェントのアプリケーションコード、他のMCPサービス、共有層コードが `rag.sqlite` に直接アクセスすることは禁止
- `chunks_vec` は `documents` を指す外部キー制約を持たないため、削除順序は重要

## Operational Notes

- 不明

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_09_01_data-layer-session-db.md`
- `05_agent_09_03_data-layer-indexing-boundaries.md`

## Keywords

RAG MCP internal path
document access patterns
responsibility boundary
