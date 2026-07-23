---
title: "RAG Inconsistencies and Known Issues (Part 1)"
category: rag
tags:
  - rag
  - inconsistencies
  - known-issues
  - bugs
  - open-questions
related:
  - 03_rag_00_document-guide.md
  - 03_rag_91_design_notes-part1.md
  - 03_rag_91_design_notes-part2.md
source:
  - 03_rag_90_inconsistencies_and_known_issues.md
---

## 移行ノート

- 移行日: 2026-07-23
- 移行元フォーマット: 既存のバレット形式（Type, Impact scope, Statement A/B, Current safe interpretation, Recommended action, Notes for AI reference）
- 移行先フォーマット: 共通テンプレート（17フィールド）
- 注: 既存のエントリ内容は維持。不足フィールドは「未確認」で埋める。

# RAGの不整合と既知の問題

このファイルは、RAGドキュメントの再構成中に発見された既知のバグ、仕様の矛盾、
ドキュメント間の不整合、および未解決の疑問点をまとめたものである。

各エントリは以下の形式を使用する: Type / Impact / Description / Safe interpretation / Recommended action / Source。

---

### RAG-001: FTS5はnormalized_contentを使用し、LLMはcontentを受け取る

- **ID**: RAG-001
- **Title**: FTS5はnormalized_contentを使用し、LLMはcontentを受け取る
- **Status**: fixed
- **Severity**: High
- **Area**: RAG
- **Type**: design-gap
- **Source**: scripts/db/schema_sql.py, scripts/rag/repository.py, scripts/rag/stages/augment.py
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: chunksテーブル、chunks_fts仮想テーブル
- **Related**: docs/03_rag_02_01_ingestion_pipeline-overview.md, docs/03_rag_03_01_query_pipeline-overview.md
- **Summary**: 日本語チャンクの2種類のテキスト表現の分離 — normalized_contentはFTS5専用、contentはLLMコンテキスト専用
- **Current Description**: chunks.contentは元のチャンクテキスト、chunks.normalized_contentはSudachi正規化済みテキスト
- **Observed Implementation**: COALESCE(normalized_content, content)でFTS5インデックス化、AugmentStageはcontentのみを出力
- **Impact**: 誤ってnormalized_contentをLLMコンテキストに含めると検索品質に影響
- **Recommended Action**: Augmentステージの出力でcontentをnormalized_contentに置き換えないように注意
- **Resolution Notes**: 完了済み

---

### RAG-002: documents、chunks、chunks_fts、chunks_vec間の責務分離

- **ID**: RAG-002
- **Title**: documents、chunks、chunks_fts、chunks_vec間の責務分離
- **Status**: fixed
- **Severity**: High
- **Area**: RAG
- **Type**: design-gap
- **Source**: scripts/db/schema_sql.py, scripts/db/rag_consistency.py
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: DBスキーマ、すべての取り込みおよびクエリ処理コード
- **Related**: docs/03_rag_04_05_dto-types.md, docs/03_rag_05_1-configuration-reference.md
- **Summary**: 正規データストア（documents/chunks）と派生インデックス（chunks_fts/chunks_vec）の明確な分離
- **Current Description**: chunks_ftsはトリガーベースで同期、chunks_vecは明示的INSERT/DELETEで同期
- **Observed Implementation**: RAG整合性チェックが正規データと派生インデックス間の同期を検証
- **Impact**: 派生インデックスの手動編集は禁止、修正には/db rag rebuild-ftsを使用
- **Recommended Action**: chunks_ftsへの手動編集を避け、/db rag rebuild-ftsを使用
- **Resolution Notes**: 完了済み

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_91_design_notes-part1.md`
- `03_rag_91_design_notes-part2.md`


## Keywords

rag
inconsistencies
known-issues
bugs
open-questions
