---
title: "Shared and DB Layer Overview - Layer Responsibilities"
category: shared
tags:
  - shared
  - db
  - layer-structure
  - responsibilities
  - architecture
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_01_overview-purpose-and-scope.md
  - 90_shared_01_03_overview-constraints-and-reference.md
source:
  - 90_shared_01_01_overview-purpose-and-scope.md
---

# Shared and DB Layer Overview

- Document guide → [90_shared_00_document-guide.md](90_shared_00_document-guide.md)

## 4. レイヤー構造全体

``` text
External Libraries
        ↑
   shared/          ← 最下層。他の全レイヤーがこれに依存する
        ↑
       db/           ← shared/ のみに依存
        ↑
  rag/ | mcp_servers/   ← db/ と shared/ に依存
        ↑
    agent/           ← 全レイヤーに依存
```

インポート方向は `.importlinter` で強制される。違反すると `lint-imports` が失敗する。

---

## 5. `shared/` の責務

最下層レイヤー。他の全レイヤーがこれに依存する。

**所有権**: shared owns configuration types, DTOs, logging infrastructure, caching, client abstractions (LLM/MCP), token measurement, format utilities, OTel tracing, constants, streaming protocol.

**`shared/` に属さないもの**:
- スキーマ定義、クエリ実行、DB接続管理 → `db/`
- ツール呼び出しのビジネスロジック → `agent/`
- RAGパイプライン制御 → `rag/`

---

## 6. `db/` の責務

`db/` は `shared/` のみに依存する。

**所有権**: db owns schema management, migration, store protocols, backend implementations, recovery.

**`db/` に属さないもの**:
- 共通型定義 → `shared/`
- ツール実行ロジック → `shared/tool_executor.py`
- LLM通信 → `shared/llm_client.py`

---




