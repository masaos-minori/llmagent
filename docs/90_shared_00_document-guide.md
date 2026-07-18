---
title: "Shared/DB Documentation Guide"
category: shared
tags:
  - shared
  - db
  - documentation
  - guide
  - routing
  - ai reference
related:
  - 90_shared_90_inconsistencies_and_known_issues.md
source:
  - 90_shared_00_document-guide.md
---

# Shared/DB Documentation Guide

再構成された `shared/` および `db/` レイヤードキュメントのエントリポイント。
どの章を開くべきか判断するため、まずこのファイルを読むこと。

---

## Purpose of This Document Set

`shared/`レイヤー(共通型、設定、ロギング、OTel、ツールルーティング)と`db/`レイヤー(SQLite接続管理、スキーマ、ストアプロトコル、メンテナンス)をドキュメント化。

---

## Recommended Reading Order (Human)

```
01 Overview → 02 Types and Protocols → 03 Runtime and Execution
  → 04 DB Architecture/Schema → 05 DB API and Operations → 90 Inconsistencies
```

---

## AI Query Routing Table

以下のファイルサフィックスはFile Indexと対応する。完全なファイル名は、そこに示す `90_shared_0N_<topic>-` プレフィックスから始まる。

| 質問 | File suffix §Section |
|---|---|
| `shared/`の用途・インポートルールは | `...purpose-and-scope.md` / `...constraints-and-reference.md` §7 |
| `shared/types.py`の型、ツールfrozensetは | `...core-types.md` §3-4 / `...reference.md`(02) §10 |
| `ConfigLoader.load_all()`は`agent.toml`を含むか | `...config-and-logging.md` §2 |
| `ToolExecutor`/`LLMClient`の動作は | `...llm-and-mcp-clients.md` §9/§10 |
| SQLite DBの種類、`workflow.sqlite`対応、スキーマ、スケーリング上限は | `...overview-and-config.md`(04) / `...schema-reference.md` / `...migration-and-scaling.md` |
| DB接続・モジュール境界・ストアプロトコルは | `...module-boundaries-and-helper.md` §2/§1a / `...protocol-and-backend.md` §3 |
| メモリ削除・RAG整合性チェック・DB破損復旧・再作成は | `...maintenance-and-rotation.md` §7/§7b / `...recovery-and-reference.md` §9/§11 |
| 何が壊れている、あるいは未記載か | `90_shared_90_inconsistencies_and_known_issues.md` |
---

## Navigation to Major Known Issues

既知の不整合の全カタログは [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) を参照(現時点でオープンな項目はない)。`ArtifactEvent`にイベントバスがない点は対象外(データ定義のみ)。

---

## Canonical Source Rules

- `06_spec_shared.md` / `07_ref-sqlite.md` / `07_spec_db.md` / `90_shared.md` は削除済みのレガシーソースであり、その内容は上記の `90_shared_02_*` から `90_shared_05_*` の各ファイルに存在する
- ソースファイル間で内容が矛盾する場合は、新しい再構成後のファイルを信頼すること（すべての不一致については `90_shared_90` を参照）

---

## File Index

### Overview（概要）

| File | Description |
|---|---|
| [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md) | 目的、スコープ |
| [90_shared_01_02_overview-layer-responsibilities.md](90_shared_01_02_overview-layer-responsibilities.md) | レイヤー構造、`shared/`/`db/` の責務 |
| [90_shared_01_03_overview-constraints-and-reference.md](90_shared_01_03_overview-constraints-and-reference.md) | インポート制約、要旨、AIリファレンス |

### Types and Protocols（型とプロトコル）

| File | Description |
|---|---|
| [90_shared_02_01_types_and_protocols-core-types.md](90_shared_02_01_types_and_protocols-core-types.md) | LLMMessage, RagConfig, RawHit/MergedHit/RankedHit/RagHit |
| [90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md](90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md) | ToolCallResult, ActionResult, ToolSpec, CacheEntry, ArtifactEvent, ShellPolicy, RuntimeTool, RuntimeToolRegistry |
| [90_shared_02_03_types_and_protocols-reference.md](90_shared_02_03_types_and_protocols-reference.md) | DbConfig、ツール定数、CallToolRequest/Response、Protocol と DTO の違い |

### Runtime and Execution（実行時とランタイム）

| File | Description |
|---|---|
| [90_shared_03_01_runtime_and_execution-config-and-logging.md](90_shared_03_01_runtime_and_execution-config-and-logging.md) | ConfigLoader、Config Isolation Policy、Logger |
| [90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md](90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md) | ToolExecutor, ToolRegistry, LifecycleProtocol, token_counter, otel_tracer, git_helper, formatters |
| [90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md](90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md) | ToolExecutor、LLMClient、McpServerConfig、実行フロー |
| [90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md](90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md) | LlmRetryHandler, ToolResultCache, ToolSpec |

### DB Architecture and Schema（DBアーキテクチャとスキーマ）

| File | Description |
|---|---|
| [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md) | DBレイヤー構造、DbConfig、SQLiteHelper |
| [90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md](90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md) | rag/session/workflow.sqlite のスキーマ、タイムスタンプ方針 |
| [90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md](90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md) | マイグレーション方式、制約、スケーリング上限 |

### DB API and Operations（DB APIと運用）

| File | Description |
|---|---|
| [90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md) | モジュール境界、`SQLiteHelper`（`db/helper.py`） |
| [90_shared_05_02_db_api_and_operations-protocol-and-backend.md](90_shared_05_02_db_api_and_operations-protocol-and-backend.md) | プロトコル群、SQLiteバックエンド、メモリテーブル |
| [90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md](90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md) | メンテナンス関数、DBローテーション、RAG整合性 |
| [90_shared_05_04_db_api_and_operations-recovery-and-reference.md](90_shared_05_04_db_api_and_operations-recovery-and-reference.md) | 破損からの復旧、エラー処理、検証 |

### Inconsistencies（不整合）

| File | Description |
|---|---|
| [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) | 既知の不整合カタログ(現時点でオープンな項目はない) |

---

## Guidance for Safe AI Use

1. `load_all()`は`agent.toml`のみを含む(`_BASE_CONFIG_FILES = ("agent.toml",)`、詳細`90_shared_03_01`§2a)。`rag_pipeline.toml`という設定ファイルは存在しない — 各MCPサーバー(rag-pipeline-mcp含む)はプロセス分離方針により自身の`config/<key>_mcp_server.toml`のみを個別にロードし、エージェント側で明示ロードする必要はない(Explicit in code)。
2. `orjson.dumps()`は`bytes`を返す(要`.decode()`)。
3. `ArtifactEvent` はデータのみでイベントバスは存在しない。
4. `LLMMessage` は7フィールド(`importance`/`pinned`含む。旧`90_shared.md`の5ではない)。
5. DBトリガーが `chunks_fts` を自動同期するため手動INSERT禁止。
6. `SQLiteHelper("workflow")`は有効(`90_shared_04_01`参照)。
7. `LLMClient`詳細は`05_agent_05_llm-and-streaming-part1.md`参照(本書対象外)。

## Related Documents

- `90_shared_01_01_overview-purpose-and-scope.md`
- `90_shared_02_01_types_and_protocols-core-types.md`
- `90_shared_03_01_runtime_and_execution-config-and-logging.md`
- `90_shared_04_01_db_architecture_and_schema-overview-and-config.md`
- `90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md`
- `90_shared_90_inconsistencies_and_known_issues.md`

## Keywords

shared
db
documentation
guide
routing
ai reference
sqlite
