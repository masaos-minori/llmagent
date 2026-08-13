---
title: "Shared and DB Layer Overview - Purpose and Scope"
category: shared
tags:
  - shared
  - overview
  - purpose
  - scope
  - out-of-scope
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_02_overview-layer-responsibilities.md
  - 90_shared_01_03_overview-constraints-and-reference.md
source:
  - 90_shared_01_01_overview-purpose-and-scope.md
---

# Shared and DB Layer Overview

- Document guide → [90_shared_00_document-guide.md](90_shared_00_document-guide.md)

## 1. Purpose

本ドキュメントは、`shared/` および `db/` レイヤーの全体像を提供する。
目的、スコープ、依存関係、インポート制約、および永続データの全体像を扱う。

**要点:**
- `shared/` は横断的なインフラを提供する：設定ロード、ロギング、型、ツールルーティング、OTel、DTO
- `db/` は永続ストレージを提供する：SQLite接続管理、スキーマ作成、ストアプロトコル、メンテナンス
- 両者はいずれも最下層の依存関係であり、他のすべてのレイヤー（`agent/`、`mcp_servers/`、`rag/`）から利用される

---

## 2. Scope

**対象範囲:**
- shared provides configuration types, DTOs, logging infrastructure, caching, client abstractions
- db provides schema management, migration, store protocols, backend implementations, recovery
- DB files: rag.sqlite, session.sqlite, workflow.sqlite

**対象外:**
- MCPサーバー実装（`mcp_servers/`）
- RAGパイプラインのロジック（`rag/`）
- エージェントREPL（`agent/`）
- LLMおよび埋め込みサーバー（外部プロセス）

---

## 3. Out of Scope

- 分散または複製SQLite構成
- 外部ベクトルデータベース（プロセス内のsqlite-vecのみ対応）
- LLM通信プロトコルの詳細（`05_agent_05_llm-and-streaming-part1.md` で扱う）

---


