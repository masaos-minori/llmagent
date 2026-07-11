---
title: "RAG Documentation Guide"
category: rag
tags:
  - rag
  - documentation
  - guide
  - routing
  - file-index
related:
  - 03_rag_01_system_overview-part1.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
  - 03_rag_90_inconsistencies_and_known_issues-part1.md
  - 03_rag_91_design_notes-part1.md
  - 03_rag_91_design_notes-part2.md
---

# RAG ドキュメントガイド

これは再構成されたRAGシステムドキュメントのエントリポイントである。
どの章を開くべきか判断するため、最初にこのファイルを読むこと。

---

## 読む順序

```
01 システム概要 → 02 インジェクションパイプライン → 03 クエリパイプライン → 04 データモデル → 05 設定 → 90 既知の問題 → 91 設計ノート
```

---

## AIクエリルーティングテーブル

| 質問 | ファイル |
|---|---|
| RAGシステムとは何か、全体としてどう動作するか | `03_rag_01` |
| インジェクションパイプラインのスクリプトは何か、どう実行するか | `03_rag_02`, `03_rag_05` |
| `WebCrawler` / `ChunkSplitter` / `RagIngester` は何をするか（API） | `03_rag_02` |
| クエリパイプラインはどう動作するか（ステージ、RRF、リランク） | `03_rag_03` |
| `RagPipeline` のAPIとは何か | `03_rag_03` |
| `use_rrf` はフュージョンモードにどう影響するか | `03_rag_03` |
| RAGデータベースのSQLiteスキーマとは何か | `03_rag_04` |
| `RawHit`、`MergedHit`、`RankedHit` とは何か | `03_rag_04` |
| 設定パラメータには何があるか | `03_rag_05` |
| 既知のバグや動作の不整合はあるか | `03_rag_90` |
| FTS5/LLMコンテンツ分離やテーブル責務についての確定した設計上の不変条件は何か | `03_rag_91` |

---

## 正典ソースのルール

以下のファイル索引に記載された再構成後のドキュメントのみが、有効な仕様のソースである。

| 領域 | 正典ソース |
|---|---|
| システムの目的、インジェクション/クエリパイプラインの概要 | `03_rag_01_system_overview-part1.md` |
| ファイル形式（JSON構造、フィールド名） | `03_rag_02_01_ingestion_pipeline-overview.md`, `03_rag_04_01_dto-models_data.md` |
| クエリパイプラインの動作（ステージ、RRF、リランク、HTTPモード） | `03_rag_03_01_query_pipeline-overview.md` |
| 設定パラメータと運用コマンド | `03_rag_05_1-configuration-reference.md` |
| 既知のバグ、仕様の矛盾、未解決の課題 | `03_rag_90_inconsistencies_and_known_issues-part1.md` |
| 確定した設計上の不変条件とリグレッションテストのギャップ | `03_rag_91_design_notes-part1.md`, `03_rag_91_design_notes-part2.md` |

**コンフリクト解決**: 2つのドキュメントで事実が一致せず、すぐに解決できない場合は、`03_rag_90_inconsistencies_and_known_issues-part1.md` にDOC-Nラベルを付けたエントリとして記録し、その後、責任を持つドキュメント側で根本原因を修正すること。ローカルチェックは `python scripts/checks/check_docs_consistency.py [対象ファイル...]` を使用。

---

## ファイル索引

| ファイル | 説明 |
|---|---|
| [03_rag_00_document-guide.md](03_rag_00_document-guide.md) | エントリポイントとルーティングガイド |
| [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md) | システム概要、アーキテクチャ、前提条件 |
| [03_rag_02_01_ingestion_pipeline-overview.md](03_rag_02_01_ingestion_pipeline-overview.md) | インジェクション実行ガイド |
| [crawler-part1](03_rag_02_02_ingestion_pipeline-crawler-part1.md) / [-part2](03_rag_02_02_ingestion_pipeline-crawler-part2.md) | WebCrawlerの詳細 |
| [chunksplitter-part1](03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md) / [-part2](03_rag_02_03_ingestion_pipeline-chunksplitter-part2.md) | ChunkSplitterの詳細 |
| [ingester-part1](03_rag_02_04_ingestion_pipeline-ingester-part1.md) / [-part2](03_rag_02_04_ingestion_pipeline-ingester-part2.md) | RagIngesterの詳細 |
| [03_rag_02_05_ingestion_pipeline-document-manager.md](03_rag_02_05_ingestion_pipeline-document-manager.md) | DocumentManagerの詳細 |
| [03_rag_02_06_ingestion_pipeline-supporting-components.md](03_rag_02_06_ingestion_pipeline-supporting-components.md) | ETagManager + 設定 |
| [03_rag_02_07_ingestion_pipeline-utils.md](03_rag_02_07_ingestion_pipeline-utils.md) | ユーティリティ関数 |
| [03_rag_02_08_ingestion_pipeline-shared.md](03_rag_02_08_ingestion_pipeline-shared.md) | 共有ユーティリティ |
| [03_rag_02_09_ingestion_pipeline-shared-utilities.md](03_rag_02_09_ingestion_pipeline-shared-utilities.md) | rag.utilsの詳細 |
| [03_rag_03_01_query_pipeline-overview.md](03_rag_03_01_query_pipeline-overview.md) | クエリパイプライン概要 |
| [rag-pipeline-class-part1](03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md) / [-part2](03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md) | RagPipelineクラス |
| [03_rag_03_03_query_pipeline-context-and-diagnostics.md](03_rag_03_03_query_pipeline-context-and-diagnostics.md) | コンテキスト + 診断 |
| [03_rag_03_04_query_pipeline-search-stages.md](03_rag_03_04_query_pipeline-search-stages.md) | 検索ステージ |
| [03_rag_03_05_query_pipeline-augment-stages.md](03_rag_03_05_query_pipeline-augment-stages.md) | 拡張ステージ |
| [helpers-and-cache-part1](03_rag_03_06_query_pipeline-helpers-and-cache-part1.md) / [-part2](03_rag_03_06_query_pipeline-helpers-and-cache-part2.md) | ヘルパー + キャッシュ |
| [03_rag_03_07_query_pipeline-tests.md](03_rag_03_07_query_pipeline-tests.md) | テスト |
| [03_rag_04_01_dto-models_data.md](03_rag_04_01_dto-models_data.md) | DTO: models_data |
| [03_rag_04_02_dto-models_result.md](03_rag_04_02_dto-models_result.md) | DTO: models_result |
| [03_rag_04_03_dto-models_audit.md](03_rag_04_03_dto-models_audit.md) | DTO: models_audit |
| [03_rag_04_04_dto-models_config.md](03_rag_04_04_dto-models_config.md) | DTO: models_config |
| [03_rag_04_05_dto-types.md](03_rag_04_05_dto-types.md) | DTO: types |
| [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md) | 設定リファレンス |
| [03_rag_05_2-execution-guide.md](03_rag_05_2-execution-guide.md) | 実行ガイド |
| [03_rag_05_3-logging.md](03_rag_05_3-logging.md) | ロギング |
| [03_rag_05_4-error-handling-reference.md](03_rag_05_4-error-handling-reference.md) | エラーハンドリング |
| [03_rag_05_5-constraints-reference.md](03_rag_05_5-constraints-reference.md) | 制約 |
| [03_rag_05_6-local-file-re-ingestion.md](03_rag_05_6-local-file-re-ingestion.md) | ローカル再インジェクション |
| [03_rag_05_7-rag-index-consistency-checks.md](03_rag_05_7-rag-index-consistency-checks.md) | 整合性チェック |
| [03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md](03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md) | MCP内部操作 |
| [03_rag_90_inconsistencies_and_known_issues-part1.md](03_rag_90_inconsistencies_and_known_issues-part1.md) | 既知の問題 |
| [03_rag_91_design_notes-part1.md](03_rag_91_design_notes-part1.md) | DESIGN-2ノート |
| [03_rag_91_design_notes-part2.md](03_rag_91_design_notes-part2.md) | DESIGN-3ノート |

---

## Related Documents

- `03_rag_01_system_overview-part1.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_90_inconsistencies_and_known_issues-part1.md`
- `03_rag_91_design_notes-part1.md`
- `03_rag_91_design_notes-part2.md`

## Keywords

rag
documentation
guide
routing
file-index
