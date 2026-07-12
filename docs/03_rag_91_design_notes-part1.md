---
title: "DESIGN-2 FTS5 Content Separation"
category: rag
tags:
  - rag
  - design-decision
  - fts5
related:
  - 03_rag_00_document-guide.md
---

# DESIGN-2 FTS5コンテンツ分離


## DESIGN-2: FTS5は`normalized_content`を使用し、LLMは`content`を受け取る

- **Type:** 確定済みの設計判断
- **Impact scope:** `chunks`テーブル、`chunks_fts`仮想テーブル、`scripts/rag/repository.py`、`scripts/rag/stages/augment.py`
- **Invariants (non-negotiable):**
  - `chunks.content`は元のチャンクテキストであり、LLMコンテキストに使用される**唯一**のテキストである。
  - `chunks.normalized_content`はSudachiで正規化された日本語テキストであり、FTS5検索インデックス**専用**に使用される。LLMコンテキストに含まれてはならない。
  - FTS5は`chunks_ai`トリガー経由で`COALESCE(normalized_content, content)`をインデックス化する。
  - 日本語チャンクはSudachiで正規化された空白区切りのテキストを`normalized_content`に格納する。英語/コードチャンクは`normalized_content = NULL`を保持し、FTS5は`content`にフォールバックする。
  - `AugmentStage`は常に`content`を出力し、`normalized_content`を出力してはならない。
- **Description:** 日本語チャンクは2種類のテキスト表現を保持する。`chunks.content` (元のテキスト) は`AugmentStage`によってLLMコンテキストに注入される。`chunks.normalized_content` (Sudachi正規化済み) は`chunks_ai`トリガーによって`chunks_fts`にインデックス化される。FTS5のクエリ側でも、Sudachiの品詞フィルタリングを用いて日本語の語を正規化する。この分離により、LLMは読みやすい元のテキストを受け取りつつ、BM25検索では形態素的に正規化された形式が使用される。
- **Notes for AI reference:** Augmentステージの出力において、`content`を`normalized_content`に置き換えてはならない。この分離は意図的なものであり、確定済みである。Source: `03_rag_02_01_ingestion_pipeline-overview.md §FTS5/LLM content separation`、`03_rag_03_01_query_pipeline-overview.md §5.5 AugmentStage`。

---



## DESIGN-3: `documents`、`chunks`、`chunks_fts`、`chunks_vec`間の責務分離

- **Type:** 確定済みの設計判断
- **Impact scope:** DBスキーマ、すべての取り込みおよびクエリ処理コード
- **Invariants (non-negotiable):**
  - `documents`と`chunks`は**正規のデータストア**であり、すべての変更操作はこれらを経由する。
  - `chunks_fts`と`chunks_vec`は**派生インデックス**であり、アプリケーションコードはこれらを読み取り専用として扱う必要がある。
  - `chunks_fts`の同期: トリガーベース (`chunks_ai`/`chunks_au`/`chunks_ad`) で行われ、直接のINSERT/UPDATEは行わない。`chunks_fts`への手動編集は禁止されており、代わりに`/db rag rebuild-fts`を使用する。
  - `chunks_vec`の同期: 取り込み時のINSERTと明示的なDELETEによって行われる。外部キー制約はない (sqlite-vecの制約による)。
  - 強制再挿入時の削除順序: `chunks_vec` を明示的に削除した後、`documents` を削除する（`ON DELETE CASCADE` により `chunks` が削除される）。`write_mode=True` の接続でのみ有効（`PRAGMA foreign_keys=ON` を有効化するため）。なお、`chunks_vec_ad` トリガーは `chunks` への直接削除に対する防御的なバックストップであり、上記の主経路ではない。
  - RAG整合性チェック (`/db consistency`) は、正規の`chunks`と派生インデックスである`chunks_fts`および`chunks_vec`との同期を検証する。
- **Description:**
  - `documents`: 正規のURL/ドキュメントメタデータ (url、title、lang、fetched_at、etag、last_modified、chunking_strategy)。URLごとに1行。
  - `chunks`: 正規のチャンクテキストと位置情報 (content、normalized_content、chunk_index、chunk_type)。`doc_id`を介して`documents`への外部キー (ON DELETE CASCADE)。
  - `chunks_fts`: 派生FTS5/BM25全文検索インデックス。`COALESCE(normalized_content, content)`を使用してトリガーにより自動同期される。BM25検索専用。手動で編集してはならず、修復には`/db rag rebuild-fts`を使用する。
  - `chunks_vec`: 派生sqlite-vec KNNベクトルインデックス。float32埋め込みBLOB。KNN検索専用。
- **RAG consistency checks:** 正規データと派生インデックス間の同期を検証する:
  - `fts_gap`: `chunks_fts`に欠落しているチャンク数 (修復: `/db rag rebuild-fts`)
  - `fts_orphan_count`: 対応するチャンクを持たないFTSエントリ (データ損失のリスク; 修復: `/db rag rebuild-fts`)
  - `orphan_vec_count`: 対応するチャンクを持たないベクトル行 (修復: `ingester.py --force`)
- **Notes for AI reference:** sqlite-vecの仮想テーブルは標準的な外部キー制約をサポートしない。RAG整合性チェック (`/db consistency`) は、正規の`chunks`と派生インデックスである`chunks_fts`および`chunks_vec`との同期を検証する。Source: `03_rag_04_05_dto-types.md §DB Schema`、`03_rag_05_1-configuration-reference.md §RAG index consistency checks`。

---



## DESIGN-2 リグレッションテストの期待値

**既存のテスト:**

| Test | File | Coverage |
|------|------|----------|
| NULLの`normalized_content`に対するCOALESCEフォールバック | `tests/test_fts_fallback.py` | ✓ `normalized_content`がNULLの場合、英語/コードチャンクは`content`でインデックス化される |
| 多言語混在ドキュメントのインデックス化 | `tests/test_fts_fallback.py` | ✓ 日本語チャンクは`normalized_content`を使用し、英語チャンクは`content`を使用する |
| 空文字列とNULLの`normalized_content`の区別 | `tests/test_fts_fallback.py` | ✓ `""` ≠ NULL (COALESCEのセマンティクス) |
| TEST-DESIGN2-01: チャンク出力には`content`フィールドのみが含まれる | `tests/test_rag_pipeline.py::TestFormatChunksDesign2` | ✓ `test_content_appears_in_output`、`test_normalized_content_does_not_appear` |
| TEST-DESIGN2-02: 日本語FTS検索は元の`content`を返す | `tests/test_fts_fallback.py` | ✓ `test_code_search_returns_original_content`および`test_mixed_japanese_english_document`でカバー |
| TEST-DESIGN2-03: `normalized_content`が`content`と異なる場合、LLMコンテキストに`normalized_content`が含まれない | `tests/test_rag_pipeline.py::TestFormatChunksDesign2`、`tests/test_rag_pipeline_stage.py::TestAugmentStage` | ✓ `test_normalized_differs_from_content_not_in_output`、`test_augment_stage_normalized_does_not_leak` |
| TEST-DESIGN2-01 (AugmentStage経路): AugmentStageは`content`のみを出力する | `tests/test_rag_pipeline_stage.py::TestAugmentStage` | ✓ `test_augment_stage_content_only_invariant`、`test_augment_stage_normalized_does_not_leak` |

**不足しているテスト:**

| Test ID | Description | Priority |
|---------|-------------|----------|
| _(なし — DESIGN-2に関するテストはすべて実装済み)_ | | |

---


## Related Documents

- [03_rag_91_design_notes.md](03_rag_91_design_notes-part1.md)

## Keywords

design-decision
fts5
content-separation
