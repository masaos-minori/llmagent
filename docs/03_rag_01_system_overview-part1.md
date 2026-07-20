---
title: "RAG System Overview (Part 1)"
category: rag
tags:
  - rag
  - system
  - overview
  - architecture
  - pipeline
related:
  - 03_rag_00_document-guide.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_03_01_query_pipeline-overview.md
source:
  - 03_rag_01_system_overview-part1.md
---

# RAG システム概要

- ドキュメントガイド → [03_rag_00_document-guide.md](03_rag_00_document-guide.md)

## 目的

Webページとローカルファイルをクロールし、SQLiteにインデックスを構築し、各LLMターンに
関連するコンテキストブロックを注入することで、LLMエージェントに文書検索拡張を提供する。

---

## 対象範囲

**対象に含まれるもの:**
- インジェクションパイプライン: `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/ingester.py`
- クエリパイプライン: `scripts/rag/pipeline.py`, `scripts/rag/repository.py`, `scripts/rag/llm_client.py`, `scripts/rag/stages/`
- ユーティリティ: `scripts/rag/utils.py`
- MCPラッパー: `scripts/mcp_servers/rag_pipeline/server.py`（ポート8010）

**対象に含まれないもの:**
- MDQ（Markdown専用インデックス）— 別サービス。境界の定義は [04_mcp_05 §MDQ vs RAG Boundary](04_mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary) を参照
- エージェントREPL — MCPを介してパイプラインを呼び出すのみで、RAGロジックは持たない
- LLMおよび埋め込みサーバー — ポート8080および8081で動作する外部サービス

---

## システムアーキテクチャ

```
[Admin / Operator]
      |
      | crawler.py CLI
      v
+------------------+     rag-src/*.json     +-------------------+     rag-src/chunk/*.json
|  crawler.py      | -------------------->  | chunk_splitter.py | -------------------->
|  (WebCrawler)    |                         | (ChunkSplitter)   |
+------------------+                         +-------------------+
                                                                         |
                                                                         v
                                                               +------------------+
                                                               |  ingester.py     |
                                                               |  (RagIngester)   |
                                                               +------------------+
                                                                        |
                                                                        | embed (port 8081)
                                                                        | INSERT SQLite
                                                                        v
                                                              rag-src/registered/

[Agent turn]
      |
      | augment(query)
      v
+----------------------+    MCP :8010    +----------------------------------+
| scripts/mcp_servers/rag_pipeline/ | <-------------> | RagPipeline              |
| service.py           |                 | [1] MQE → [2] Search → [3] RRF →   
+----------------------+                 | [4] Rerank →                       |
                                         |          [5] Augment               |
                                         +----------------------------------+
                                                    |
                                           +--------+--------+
                                           | KNN + BM25      |
                                           | SQLite (rag.db) |
                                           +-----------------+
```

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_01_system_overview-part2.md`

## Keywords

rag
system
overview
architecture
pipeline
