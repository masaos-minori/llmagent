---
title: "Documentation Overview"
category: overview
tags:
  - documentation
  - navigation
  - overview
  - index
  - knowledge-base
related:
  - 01_overview.md
  - 02_deployment-part1.md
  - 03_rag_00_document-guide.md
  - 04_mcp_00_document-guide.md
  - 05_agent_00_document-guide.md
  - 06_eventbus_00_document-guide.md
  - 90_shared_00_document-guide.md
---

# ドキュメント概要

プロジェクトドキュメント全体のトップレベルナビゲーションハブ。各トップレベルカテゴリとその入口ファイルへのリンクを一覧化する。`01_overview.md` は引き続きシステム全体のアーキテクチャ概要として存在し、本ファイルに置き換わるものではない。

## カテゴリ

- [概要](01_overview.md) — システム全体のアーキテクチャとファイル構成
- [デプロイ](02_deployment-part1.md) — 環境構築とデプロイ手順
- [RAG](03_rag_00_document-guide.md) — Retrieval-Augmented Generation パイプライン
- [MCP](04_mcp_00_document-guide.md) — Model Context Protocol サーバ群
- [Agent](05_agent_00_document-guide.md) — Agent REPL システムと動作
- [Event Bus](06_eventbus_00_document-guide.md) — Event Bus インフラ
- [Shared/DB](90_shared_00_document-guide.md) — 共有インフラとデータベース層
- [既知の問題](#既知の問題) — カテゴリごとの既知の不整合

## 推奨読書順序

1. [システム概要](01_overview.md) — まずここからシステム全体像を把握する
2. [デプロイガイド](02_deployment-part1.md) — 環境をセットアップする
3. 関心領域を選択する:
   - [RAGパイプライン](03_rag_00_document-guide.md)
   - [MCPサーバ](04_mcp_00_document-guide.md)
   - [Agentシステム](05_agent_00_document-guide.md)
   - [Event Bus](06_eventbus_00_document-guide.md)
   - [共有インフラ](90_shared_00_document-guide.md)
4. 関心領域の既知の問題を確認する

## 既知の問題

各カテゴリはそれぞれ既知の不整合・未解決事項を管理している:

- [RAG](03_rag_90_inconsistencies_and_known_issues.md)
- [MCP](04_mcp_90_inconsistencies_and_known_issues.md)
- [Agent](05_agent_90_inconsistencies_and_known_issues.md)
- [Event Bus](06_eventbus_90_inconsistencies_and_known_issues.md)
- [Shared/DB](90_shared_90_inconsistencies_and_known_issues.md)

## タスク別ドキュメント参照

`routing.md` から移管。タスクの種類に応じて必要なドキュメントのみを読み込む。`docs/*.md` を全件読み込まないこと。

### Domain specs

| Task scope | Reference docs |
|---|---|
| Agent spec (overview, design, known issues) | `05_agent_00_document-guide.md` + `05_agent_01_system-overview.md` |
| Agent known issues / inconsistencies | `05_agent_90_inconsistencies_and_known_issues.md` |
| MCP server spec (overview, design, known issues) | `04_mcp_00_document-guide.md` + `04_mcp_01_system_overview.md` |
| RAG pipeline spec (overview, design, known issues) | `03_rag_00_document-guide.md` + `03_rag_01_system_overview-part1.md` |
| MDQ vs RAG boundary | `04_mcp_05_01_access-control-and-allowlists.md` §MDQ vs RAG Boundary |
| DB layer spec (schema, ops, known issues) | `90_shared_04_01_db_architecture_and_schema-overview-and-config.md` + `90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` |
| Shared infra spec (config, logging, types, constants) | `90_shared_00_document-guide.md` + `90_shared_01_01_overview-purpose-and-scope.md` |

### Implementation reference

#### System overview

| Task scope | Reference docs |
|---|---|
| System-wide architecture overview | `01_overview.md` (indexes `01_overview-arch-*.md`) |
| File / module layout | `01_overview.md` (indexes `01_overview-files-*.md`) |
| `tools/` scripts overview (CI checks, doc formatting, historical doc migration) | `tools/01_overview.md` |
| Documentation set index / navigation | `00_index.md` |
| Deployment / env setup | `02_deployment-part1.md` + `rules/env.md` |

#### Agent

| Task scope | Reference docs |
|---|---|
| Memory layer (types / store / retriever / extract / jsonl_store / services.py) | `05_agent_04_01_state-and-persistence-state-model-part1.md` + `05_agent_08_01_configuration-loading-agent-config-part1.md` + `05_agent_12_03_memory-module-ref-core-and-store.md` + `05_agent_12_04_memory-module-ref-retrieval-and-injection.md` |
| OTel observability (otel_tracer.py) | `05_agent_10_01_operations-and-observability-startup-and-health.md` + `05_agent_08_01_configuration-loading-agent-config-part1.md` |
| Agent REPL slash commands (`CommandRegistry`) | `05_agent_07_01_cli-and-commands-cli-reference.md` |
| Agent startup / verification / troubleshooting | `05_agent_10_01_operations-and-observability-startup-and-health.md` |
| Agent features / slash commands / tool calling | `05_agent_01_system-overview.md` + `05_agent_07_01_cli-and-commands-cli-reference.md` |
| Agent REPL class structure | `05_agent_02_runtime-architecture-part1.md` + `05_agent_13_reference-api-part1.md` |
| Agent REPL flow / tool execution | `05_agent_03_01_turn-processing-flow-overview.md` + `05_agent_06_01_tool-execution-and-approval-execution.md` |
| AgentContext / DI hub | `05_agent_02_runtime-architecture-part1.md` + `05_agent_04_01_state-and-persistence-state-model-part1.md` |
| AgentConfig / config constants | `05_agent_08_01_configuration-loading-agent-config-part1.md` |
| Session / DB persistence | `05_agent_09_01_data-layer-session-db.md` + `90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` |
| LLM client (streaming/retry) | `05_agent_05_llm-and-streaming-part1.md` |
| CLI view / readline | `05_agent_07_01_cli-and-commands-cli-reference.md` |

#### MCP

| Task scope | Reference docs |
|---|---|
| MCP server implementation | `04_mcp_02_01_endpoints-and-transport.md` + `04_mcp_03_01_dispatch-and-routing.md` |
| MCP transport / startup_mode / lifecycle | `04_mcp_03_01_dispatch-and-routing.md` + `05_agent_08_01_configuration-loading-agent-config-part1.md` |
| ToolRouteResolver / route_resolver.py | `04_mcp_03_01_dispatch-and-routing.md` + `05_agent_08_01_configuration-loading-agent-config-part1.md` |
| ServerLifecycleManager / lifecycle.py | `04_mcp_03_01_dispatch-and-routing.md` + `05_agent_02_runtime-architecture-part1.md` |
| ToolSpec / tool_spec.py (execution metadata DAG) | `05_agent_08_01_configuration-loading-agent-config-part1.md` |
| tool_cache.py (_CacheEntry LRU cache) | `05_agent_08_01_configuration-loading-agent-config-part1.md` |
| TransportType / StartupMode / HealthcheckMode enums (mcp_config.py) | `04_mcp_03_01_dispatch-and-routing.md` + `04_mcp_06_02_configuration-file-inventory.md` |
| MCP security model (allowlist / denylist / fail-closed) | `04_mcp_05_01_access-control-and-allowlists.md` |
| Any MCP server (catalog only) | `04_mcp_04_01_web-search-file-read-github.md` |
| mdq-mcp specifics | `04_mcp_04_04_mdq.md` + `04_mcp_90_inconsistencies_and_known_issues.md` |
| MCP known bugs / inconsistencies | `04_mcp_90_inconsistencies_and_known_issues.md` |

#### RAG

| Task scope | Reference docs |
|---|---|
| RAG pipeline modification | `03_rag_03_01_query_pipeline-overview.md` + `03_rag_04_05_dto-types.md` + `90_shared_02_01_types_and_protocols-core-types.md` |
| RAG types / repository / LLM utils | `03_rag_04_05_dto-types.md` + `90_shared_02_01_types_and_protocols-core-types.md` |
| Ingestion pipeline run (execute commands, file lifecycle) | `03_rag_02_01_ingestion_pipeline-overview.md` + `03_rag_05_1-configuration-reference.md` |
| crawler.py changes / API reference | `03_rag_02_02_ingestion_pipeline-crawler-part1.md` |
| chunk_splitter.py changes / API reference | `03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md` |
| ingester.py changes / API reference | `03_rag_02_04_ingestion_pipeline-ingester-part1.md` |
| RAG known bugs / inconsistencies | `03_rag_90_inconsistencies_and_known_issues-part1.md` |
| RAG configuration parameters | `03_rag_05_1-configuration-reference.md` |

#### DB / Shared

| Task scope | Reference docs |
|---|---|
| SQLite / DB connection / WAL / transactions | `90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` |
| Config / logger / formatters / rag_utils | `90_shared_03_01_runtime_and_execution-config-and-logging.md` |
| Shared layer / DB layer known issues / inconsistencies | `90_shared_90_inconsistencies_and_known_issues.md` |

#### Event Bus

| Task scope | Reference docs |
|---|---|
| Event Bus (overview) | `06_eventbus_01_system-overview.md` |
| Event Bus (HTTP API) | `06_eventbus_02_01_publish-replay.md` |
| Event Bus (persistence) | `06_eventbus_03_persistence_schema_and_replay.md` |
| Event Bus (DLQ/offsets) | `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` |
| Event Bus (config/ops) | `06_eventbus_05_01_config-env-and-fields.md` |
| Event Bus (API ref) | `06_eventbus_06_01_reference-api-core-modules.md` |
| Event Bus (issues) | `06_eventbus_90_inconsistencies_and_known_issues.md` |

## Related Documents

- `01_overview.md`
- `02_deployment-part1.md`
- `03_rag_00_document-guide.md`
- `04_mcp_00_document-guide.md`
- `05_agent_00_document-guide.md`
- `06_eventbus_00_document-guide.md`
- `90_shared_00_document-guide.md`

## Keywords

documentation
navigation
overview
index
knowledge-base
