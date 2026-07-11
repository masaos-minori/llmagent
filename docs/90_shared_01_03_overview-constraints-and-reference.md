---
title: "Shared and DB Layer Overview - Constraints and Reference"
category: shared
tags:
  - shared
  - db
  - import-direction
  - constraints
  - executive-summary
  - ai-reference
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_01_overview-purpose-and-scope.md
  - 90_shared_01_02_overview-layer-responsibilities.md
source:
  - 90_shared_01_01_overview-purpose-and-scope.md
---

# Shared and DB Layer Overview

- Document guide → [90_shared_00_document-guide.md](90_shared_00_document-guide.md)

## 7. インポート方向の制約

**規則:** `shared/` → 外部ライブラリのみ。`agent/`、`mcp/`、`rag/`、`db/` からのインポートは**禁止**。

**規則:** `db/` → `shared/` のみ。`agent/`、`mcp/`、`rag/` からのインポートは**禁止**。

`.importlinter` により強制される(違反すると `PYTHONPATH=scripts uv run lint-imports` が失敗する)。

重要な制約: `orjson.dumps()` は `bytes` を返す(`str` ではない)。`str` が必要な場合は必ず `.decode()` を呼ぶこと。非同期HTTPには(`requests` ではなく)`httpx.AsyncClient` を使うこと。

---

## 8. 永続データの全体像

| DBファイル | テーブル | 用途 |
|---|---|---|
| `rag.sqlite` | `documents`、`chunks`、`chunks_fts`、`chunks_vec` | RAGドキュメント索引 + ベクトル + FTS検索 |
| `session.sqlite` | `sessions`、`messages`、`memories`、`memories_fts`、`memories_vec`、`memory_links` | Agentの会話状態 + メモリ層 |
| `workflow.sqlite` | `tasks`、`attempts`、`processed_events`、`approvals`、`artifacts` | ワークフローエンジンのタスク追跡 |

3つのDBはすべてWALモードと `busy_timeout` を使用する。sqlite-vec は `rag.sqlite`(target=`"rag"`)のみでロードされる。

---

## 9. 主要な制約

| 制約 | 値 |
|---|---|
| インポート方向 | `shared/` → 外部のみ、`db/` → `shared/` のみ |
| JSONライブラリ | `orjson`(標準の`json`ではない）; `orjson.dumps()` は `bytes` を返す |
| HTTPクライアント | `httpx`(`requests`ではない）; 非同期は `httpx.AsyncClient` |
| 設定形式 | `/opt/llm/config/` 配下のTOML / JSON;`_`始まりのキーは除外される |
| ログメッセージ | 英語のみ(コードコメント・ログに日本語は使わない） |
| SQLite WAL | 全接続で `PRAGMA journal_mode=WAL` を使用 |
| `agent.toml` | 所有権テーブル全体は [90_shared_03](90_shared_03_01_runtime_and_execution-config-and-logging.md) §2a Config Ownership を参照 |
| 埋め込み次元 | `agent.toml` の `embedding_dims`(デフォルト384） |

---

## 10. まとめ

`shared/` は最下層の依存レイヤーであり、設定、ロギング、型、ルーティング、プラグインサポート、DTOを提供する。`shared/` 内のコードは上位レイヤーをインポートしてはならない。

`db/` は型付けされたWAL対応SQLiteアクセスをFTS5・sqlite-vec連携込みで提供する。スキーマ定義の正典ソースである。`db/` は `shared/` のみに依存する。

すべての永続データは3つのSQLiteファイルに存在する: `rag.sqlite`(RAG索引）、`session.sqlite`(会話 + メモリ）、`workflow.sqlite`(タスク追跡）。

---

## 11. AIリファレンスガイド

| 質問 | 参照先 |
|---|---|
| shared/にはどんな型/DTOが定義されているか | [90_shared_02_01_types_and_protocols-core-types.md](90_shared_02_01_types_and_protocols-core-types.md) |
| ConfigLoaderはどう動作するか | [90_shared_03_01_runtime_and_execution-config-and-logging.md](90_shared_03_01_runtime_and_execution-config-and-logging.md) |
| どんなSQLiteスキーマが存在するか | [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md) |
| SQLiteHelperのAPIは何か | [90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md) |
| どんな不具合・不整合が存在するか | [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) |

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_01_01_overview-purpose-and-scope.md`
- `90_shared_01_02_overview-layer-responsibilities.md`

## Keywords

import direction
constraints
persistent data
executive summary
ai reference guide
