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
- `shared/` は横断的なインフラを提供する：設定ロード、ロギング、型、ツールルーティング、プラグイン、OTel、DTO
- `db/` は永続ストレージを提供する：SQLite接続管理、スキーマ作成、ストアプロトコル、メンテナンス
- 両者はいずれも最下層の依存関係であり、他のすべてのレイヤー（`agent/`、`mcp/`、`rag/`）から利用される

---

## 2. Scope

**対象範囲:**
- All modules under `shared/`: `config_loader`, `config_errors`, `config_validator`, `logger`, `types`, `llm_types`, `transport_dto`, `action_result`, `events`, `protocols/shell`, `tool_constants`, `route_resolver`, `mcp_config`, `mcp_health`, `tool_executor`, `http_transport`, `plugin_registry`, `plugin_auto_discover`, `plugin_result`, `otel_tracer`, `otel_noop`, `token_counter`, `token_estimation`, `git_helper`, `formatters`, `json_utils`, `llm_exceptions`, `llm_transport_errors`, `llm_sse_stream`, `llm_sse_helpers`, `llm_reconnect`, `llm_retry`, `llm_payload`, `llm_hot_config`, `sse_parser`, `tool_registry`, `tool_routing_validation`, `tool_transport_invoker`, `tool_lifecycle`, `tool_executor_helpers`, `tool_spec`, `tool_cache`, `plugin_tool_invoker`
- All modules under `db/`: `config.py`, `helper.py`, `create_schema.py`, `models.py`, `schema_sql.py`, `store.py`, `store_impl.py`, `store_protocols.py`, `maintenance.py`, `rotation.py`, `recovery.py`, `rag_consistency.py`
- DB files: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`

**対象外:**
- MCPサーバー実装（`mcp/`）
- RAGパイプラインのロジック（`rag/`）
- エージェントREPL（`agent/`）
- LLMおよび埋め込みサーバー（外部プロセス）

---

## 3. Out of Scope

- 分散または複製SQLite構成
- 外部ベクトルデータベース（プロセス内のsqlite-vecのみ対応）
- LLM通信プロトコルの詳細（`05_agent_05_llm-and-streaming.md` で扱う）

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_01_02_overview-layer-responsibilities.md`
- `90_shared_01_03_overview-constraints-and-reference.md`

## Keywords

shared
purpose
scope
out of scope
layer overview
