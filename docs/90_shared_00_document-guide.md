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

これらのファイルは、`shared/` レイヤー（共通型、設定、ロギング、プラグイン、
OTel、ツールルーティング）と `db/` レイヤー（SQLite接続管理、スキーマ、ストア
プロトコル、メンテナンス）についてドキュメント化している。

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
| `shared/` はどのレイヤーに使われるか？／インポートルールは？ | `...purpose-and-scope.md` / `...constraints-and-reference.md` §7 |
| `shared/types.py` にはどんな型があるか？（`LLMMessage`、`RagConfig`） | `...core-types.md` §3-4 |
| どんなツールfrozensetが存在するか？ | `...reference.md` (02) §10 |
| `ConfigLoader.load_all()` は `agent.toml` を含むか？ | `...config-and-logging.md` §2 — **はい**、`_BASE_CONFIG_FILES` のインデックス0。§2aを参照 |
| プラグインはどのようにロードされるか？ | `...plugin-and-tool-runtime.md` §4 |
| `ToolExecutor.execute()` はどう動作するか？`LLMClient` のドキュメントはあるか？ | `...llm-and-mcp-clients.md` §9/§10（+ `05_agent_05_llm-and-streaming.md`） |
| どんなSQLite DBが存在するか？`SQLiteHelper` は `workflow.sqlite` に対応しているか？ | `...overview-and-config.md` (04) §2/§4（対応している；仕様書には未記載） |
| `rag.sqlite` / `session.sqlite` のスキーマは？ | `...schema-reference.md` §5/§6 |
| RAGアーキテクチャのスケーリング上限は？ | `...migration-and-scaling.md` §11 |
| DB接続の開き方は？モジュール境界は？ | `...module-boundaries-and-helper.md` §2/§1a |
| ストアプロトコルとは何か？ | `...protocol-and-backend.md` §3 |
| 古いメモリの削除方法は？RAG整合性チェックは？ | `...maintenance-and-rotation.md` §7/§7b |
| DB破損からの復旧方法は？DBの再作成方法は？ | `...recovery-and-reference.md` §9/§11 |
| 何が壊れている、あるいは未記載か？ | `90_shared_90_inconsistencies_and_known_issues.md` |

---

## Navigation to Major Known Issues

DOCREF-01（`90_shared.md` が存在しない `06_ref-sqlite.md` を参照している）や DOCFIELD-01（`LLMMessage` のフィールド数の不一致、5 対 7）を含む完全なカタログは、[90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) を参照。`ArtifactEvent` にイベントバスが存在しない点は対象外——データ定義のみであり、ランタイム統合の予定はない。

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
| [90_shared_02_02_types_and_protocols-tool-and-execution-dto.md](90_shared_02_02_types_and_protocols-tool-and-execution-dto.md) | ToolCallResult, ActionResult, ToolSpec, CacheEntry, ArtifactEvent, ShellPolicy |
| [90_shared_02_03_types_and_protocols-reference.md](90_shared_02_03_types_and_protocols-reference.md) | DbConfig、ツール定数、CallToolRequest/Response、Protocol と DTO の違い |

### Runtime and Execution（実行時とランタイム）

| File | Description |
|---|---|
| [90_shared_03_01_runtime_and_execution-config-and-logging.md](90_shared_03_01_runtime_and_execution-config-and-logging.md) | ConfigLoader、Config Isolation Policy、Logger |
| [90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md](90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md) | plugin_registry, token_counter, otel_tracer, git_helper, formatters |
| [90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md](90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md) | ToolExecutor、LLMClient、McpServerConfig、実行フロー |
| [90_shared_03_04_runtime_and_execution-caching-and-reference.md](90_shared_03_04_runtime_and_execution-caching-and-reference.md) | LlmRetryHandler, ToolResultCache, ToolSpec, PluginToolInvoker |

### DB Architecture and Schema（DBアーキテクチャとスキーマ）

| File | Description |
|---|---|
| [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md) | DBレイヤー構造、DbConfig、SQLiteHelper |
| [90_shared_04_02_db_architecture_and_schema-schema-reference.md](90_shared_04_02_db_architecture_and_schema-schema-reference.md) | rag/session/workflow.sqlite のスキーマ、タイムスタンプ方針 |
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
| [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) | DOCREF-01, CONFIG-01/02/03, GLOBAL-01, PLUGIN-01, IMPORT-01, DOCFIELD-01、他 |

---

## Guidance for Safe AI Use

1. **`load_all()` は `agent.toml` を含む**（`_BASE_CONFIG_FILES` のインデックス0）。詳細は `90_shared_03_01_runtime_and_execution-config-and-logging.md` §2a を参照。明示的にロードが必要なのは `rag_pipeline.toml` のみ。
2. **`orjson.dumps()` は `bytes` を返す。** 文字列として使う前に `.decode()` を呼ぶこと。
3. **`ArtifactEvent` はデータのみ。** イベントバスは存在しない。
4. **`LLMMessage` は7フィールドを持つ**（`importance` と `pinned` を含む。旧 `90_shared.md` の5フィールドではない）。
5. **DBトリガーが `chunks_fts` を自動同期する。** `chunks_fts` へ手動でINSERTしないこと。
6. **`SQLiteHelper("workflow")` は有効** —— `90_shared_04_01_db_architecture_and_schema-overview-and-config.md` にドキュメントあり。
7. **`LLMClient` の詳細については**、`05_agent_05_llm-and-streaming.md` を参照——本ドキュメントの対象外。

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
