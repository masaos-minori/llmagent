
title: "DESIGN-2 FTS5 Content Separation"
category: rag
tags:
  - rag
  - design-decision
  - fts5
related:
  - 03_rag_00_document-guide.md


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
  - `chunks_fts`の同期: トリガーベース (`chunks_ai`/`chunks_au`/`chunks_ad`) で行われ、直接のINSERT/UPDATEは行わない。`chunks_fts`への手動編集は禁止されており、代わりに`/session rag-rebuild-fts`を使用する。
  - `chunks_vec`の同期: 取り込み時のINSERTと明示的なDELETEによって行われる。外部キー制約はない (sqlite-vecの制約による)。
  - 強制再挿入時の削除順序: `chunks_vec` を明示的に削除した後、`documents` を削除する（`ON DELETE CASCADE` により `chunks` が削除される）。`write_mode=True` の接続でのみ有効（`PRAGMA foreign_keys=ON` を有効化するため）。なお、`chunks_vec_ad` トリガーは `chunks` への直接削除に対する防御的なバックストップであり、上記の主経路ではない。
  - RAG整合性チェック (`/session rag-consistency`) は、正規の`chunks`と派生インデックスである`chunks_fts`および`chunks_vec`との同期を検証する。
- **Description:**
  - `documents`: 正規のURL/ドキュメントメタデータ (url、title、lang、fetched_at、etag、last_modified、chunking_strategy)。URLごとに1行。
  - `chunks`: 正規のチャンクテキストと位置情報 (content、normalized_content、chunk_index、chunk_type)。`doc_id`を介して`documents`への外部キー (ON DELETE CASCADE)。
  - `chunks_fts`: 派生FTS5/BM25全文検索インデックス。`COALESCE(normalized_content, content)`を使用してトリガーにより自動同期される。BM25検索専用。手動で編集してはならず、修復には`/session rag-rebuild-fts`を使用する。
  - `chunks_vec`: 派生sqlite-vec KNNベクトルインデックス。float32埋め込みBLOB。KNN検索専用。
- **RAG consistency checks:** 正規データと派生インデックス間の同期を検証する:
  - `fts_gap`: `chunks_fts`に欠落しているチャンク数 (修復: `/session rag-rebuild-fts`)
  - `fts_orphan_count`: 対応するチャンクを持たないFTSエントリ (データ損失のリスク; 修復: `/session rag-rebuild-fts`)
  - `orphan_vec_count`: 対応するチャンクを持たないベクトル行 (修復: `ingester.py --force`)
- **Notes for AI reference:** sqlite-vecの仮想テーブルは標準的な外部キー制約をサポートしない。RAG整合性チェック (`/session rag-consistency`) は、正規の`chunks`と派生インデックスである`chunks_fts`および`chunks_vec`との同期を検証する。Source: `03_rag_04_05_dto-types.md §DB Schema`、`03_rag_05_1-configuration-reference.md §RAG index consistency checks`。

---

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

**2026-07-12実装確認:** 上表の全テストクラス・関数 (`tests/test_fts_fallback.py`の`TestEnglishFtsFallback`/`TestCodeFtsFallback`/`TestNormalizedContentEdgeCases`、`tests/test_rag_pipeline.py::TestFormatChunksDesign2`、`tests/test_rag_pipeline_stage.py::TestAugmentStage`) の存在を確認した。DESIGN-2の不変条件・トリガーSQL・テスト状況に記載との齟齬はない。根拠分類: Explicit in code。

---


## Related Documents

- [03_rag_91_design_notes.md](03_rag_91_design_notes.md)

## Keywords

design-decision
fts5
content-separation

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
  - `chunks_fts`の同期: トリガーベース (`chunks_ai`/`chunks_au`/`chunks_ad`) で行われ、直接のINSERT/UPDATEは行わない。`chunks_fts`への手動編集は禁止されており、代わりに`/session rag-rebuild-fts`を使用する。
  - `chunks_vec`の同期: 取り込み時のINSERTと明示的なDELETEによって行われる。外部キー制約はない (sqlite-vecの制約による)。
  - 強制再挿入時の削除順序: `chunks_vec` を明示的に削除した後、`documents` を削除する（`ON DELETE CASCADE` により `chunks` が削除される）。`write_mode=True` の接続でのみ有効（`PRAGMA foreign_keys=ON` を有効化するため）。なお、`chunks_vec_ad` トリガーは `chunks` への直接削除に対する防御的なバックストップであり、上記の主経路ではない。
  - RAG整合性チェック (`/session rag-consistency`) は、正規の`chunks`と派生インデックスである`chunks_fts`および`chunks_vec`との同期を検証する。
- **Description:**
  - `documents`: 正規のURL/ドキュメントメタデータ (url、title、lang、fetched_at、etag、last_modified、chunking_strategy)。URLごとに1行。
  - `chunks`: 正規のチャンクテキストと位置情報 (content、normalized_content、chunk_index、chunk_type)。`doc_id`を介して`documents`への外部キー (ON DELETE CASCADE)。
  - `chunks_fts`: 派生FTS5/BM25全文検索インデックス。`COALESCE(normalized_content, content)`を使用してトリガーにより自動同期される。BM25検索専用。手動で編集してはならず、修復には`/session rag-rebuild-fts`を使用する。
  - `chunks_vec`: 派生sqlite-vec KNNベクトルインデックス。float32埋め込みBLOB。KNN検索専用。
- **RAG consistency checks:** 正規データと派生インデックス間の同期を検証する:
  - `fts_gap`: `chunks_fts`に欠落しているチャンク数 (修復: `/session rag-rebuild-fts`)
  - `fts_orphan_count`: 対応するチャンクを持たないFTSエントリ (データ損失のリスク; 修復: `/session rag-rebuild-fts`)
  - `orphan_vec_count`: 対応するチャンクを持たないベクトル行 (修復: `ingester.py --force`)
- **Notes for AI reference:** sqlite-vecの仮想テーブルは標準的な外部キー制約をサポートしない。RAG整合性チェック (`/session rag-consistency`) は、正規の`chunks`と派生インデックスである`chunks_fts`および`chunks_vec`との同期を検証する。Source: `03_rag_04_05_dto-types.md §DB Schema`、`03_rag_05_1-configuration-reference.md §RAG index consistency checks`。

---

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

**2026-07-12実装確認:** 上表の全テストクラス・関数 (`tests/test_fts_fallback.py`の`TestEnglishFtsFallback`/`TestCodeFtsFallback`/`TestNormalizedContentEdgeCases`、`tests/test_rag_pipeline.py::TestFormatChunksDesign2`、`tests/test_rag_pipeline_stage.py::TestAugmentStage`) の存在を確認した。DESIGN-2の不変条件・トリガーSQL・テスト状況に記載との齟齬はない。根拠分類: Explicit in code。

---


## Related Documents

- [03_rag_91_design_notes.md](03_rag_91_design_notes.md)

## Keywords

design-decision
fts5
content-separation



# DESIGN-3 テーブルの責務


## DESIGN-3 リグレッションテストの期待値

**既存のテスト:**

| Test | File | Coverage |
|------|------|----------|
| FTS5トリガー同期の検証 | `tests/test_fts_fallback.py` | ✓ INSERT/UPDATE/DELETEトリガーがCOALESCEを使用していることを確認 |
| ベクトル孤立検出 | `scripts/db/maintenance.py:check_rag_consistency()` | ✓ `orphan_vec_count`が報告される |

**リグレッションテスト:**

| Test ID | Description | File | Status |
|---------|-------------|------|--------|
| TEST-DESIGN3-01 | FTS再構築がCOALESCE(normalized_content, content)を使用する | `tests/test_rag_index_integrity.py` | ✓ 追加済み |
| TEST-DESIGN3-02 | `chunks_fts`は`chunks`から同期される (独立して維持されるものではない) | `tests/test_rag_index_integrity.py` | ✓ 追加済み |
| TEST-DESIGN3-03 | 強制再取り込みは孤立したベクトルレコードを残さない | `tests/test_rag_index_integrity.py` | ✓ 追加済み |
| TEST-DESIGN3-04 | 削除順序の不変条件: `chunks_vec` → `documents`（`ON DELETE CASCADE` により `chunks` を削除） | `tests/test_rag_index_integrity.py` | ✓ 追加済み |
| TEST-DESIGN3-05 | 整合性チェックが派生インデックスの非同期を検出する | `tests/test_rag_index_integrity.py` | ✓ 追加済み |

**バグ修正 — reconcile_url()のFTS削除:**

`RagMaintenanceService.reconcile_url()`は`DELETE FROM chunks_fts WHERE chunk_id IN (...)`を
使用していたが、これはFTS5コンテンツテーブルでは無効である。
`scripts/agent/services/rag_maintenance_service.py`で修正し、正しい行単位のFTS5削除コマンド構文
`INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', ?, ?)`を使用するようにした。
リグレッションテスト: `tests/test_rag_index_integrity.py::test_reconcile_url_fts_deletion`。

**TEST-DESIGN3-01: FTS再構築がCOALESCEを使用する**

```python
# Pseudocode for integration test
def test_fts_rebuild_uses_cascade(db):
    """RagMaintenanceService.rebuild_fts() must use COALESCE(normalized_content, content)."""
    # Insert chunk with NULL normalized_content
    insert_chunk(
        doc_id=1,
        content="english text",
        normalized_content=None,
        chunk_index=0,
    )
    # Delete all FTS entries
    db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('delete-all')")
    # Rebuild using the maintenance service
    RagMaintenanceService().rebuild_fts()
    # Verify: content is indexed (not NULL)
    results = fts_search("english")
    assert len(results) == 1
    assert results[0].content == "english text"
```

**TEST-DESIGN3-02: chunks_ftsは派生であり、正規ではない**

```python
# Pseudocode for integration test - chunks_fts_derived_index
def test_chunks_fts_is_derived_index(db):
    """chunks_fts must not be directly INSERTed/UPDATEed by application code."""
    # Insert chunk via canonical path (INSERT into chunks)
    insert_chunk(doc_id=1, content="test", normalized_content=None, chunk_index=0)
    # Verify: FTS entry exists (trigger-synced)
    results = fts_search("test")
    assert len(results) == 1
```

**TEST-DESIGN3-03: 強制再取り込みで孤立ベクトルが発生しないこと**

```python
# Pseudocode for integration test - force_reingest_no_orphan_vectors
def test_force_reingest_no_orphan_vectors(db):
    """Force re-ingestion must not leave orphan chunks_vec records."""
    # Insert document and chunks
    insert_doc(url="http://example.com")
    insert_chunk(doc_id=1, content="text", normalized_content=None, chunk_index=0)
    # Force re-ingestion (deletes chunks_vec first, then documents; CASCADE removes chunks)
    RagMaintenanceService().delete_document("http://example.com")
    # Verify: no orphan vec rows remain
    orphan_count = db.execute(
        "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
    ).fetchone()[0]
    assert orphan_count == 0
```

**TEST-DESIGN3-04: 削除順序の不変条件**

```python
# Pseudocode for integration test - deletion_order_invariant
def test_deletion_order_invariant(db):
    """Deletion must follow: chunks_vec → documents (CASCADE removes chunks)."""
    # Insert document with chunks and vectors
    insert_doc(url="http://order-test.com")
    chunk_id = insert_chunk(doc_id=1, content="test", normalized_content=None, chunk_index=0)
    db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
    # Delete via canonical path
    delete_document_chain(db, doc_id=1)
    # Verify: no orphan vec rows remain
    orphan_count = db.execute(
        "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
    ).fetchone()[0]
    assert orphan_count == 0
```

**TEST-DESIGN3-05: 整合性チェックが非同期を検出する**

```python
# Pseudocode for integration test - consistency_checks_detect_fts_gap
def test_consistency_checks_detect_fts_gap(db):
    """check_rag_consistency() must detect FTS index desync."""
    # Insert chunk without triggering FTS (simulate trigger failure)
    insert_chunk(doc_id=1, content="test", normalized_content=None, chunk_index=0)
    # Manually remove the FTS-synced row to simulate desync
    db.execute("DELETE FROM chunks_fts WHERE rowid = 1")
    # Verify: check_rag_consistency() reports the gap
    result = check_rag_consistency(db)
    assert result.fts_gap > 0
```

対応する実装(`test_consistency_check_detects_fts_gap`)は `tests/test_rag_index_integrity.pyのtest_consistency_check_detects_fts_gap関数` に実在する。(Explicit in code)

## Related Documents

- [03_rag_91_design_notes.md](03_rag_91_design_notes.md)

## Keywords

design-decision
database
responsibilities

# DESIGN-3 テーブルの責務


## DESIGN-3 リグレッションテストの期待値

**既存のテスト:**

| Test | File | Coverage |
|------|------|----------|
| FTS5トリガー同期の検証 | `tests/test_fts_fallback.py` | ✓ INSERT/UPDATE/DELETEトリガーがCOALESCEを使用していることを確認 |
| ベクトル孤立検出 | `scripts/db/maintenance.py:check_rag_consistency()` | ✓ `orphan_vec_count`が報告される |

**リグレッションテスト:**

| Test ID | Description | File | Status |
|---------|-------------|------|--------|
| TEST-DESIGN3-01 | FTS再構築がCOALESCE(normalized_content, content)を使用する | `tests/test_rag_index_integrity.py` | ✓ 追加済み |
| TEST-DESIGN3-02 | `chunks_fts`は`chunks`から同期される (独立して維持されるものではない) | `tests/test_rag_index_integrity.py` | ✓ 追加済み |
| TEST-DESIGN3-03 | 強制再取り込みは孤立したベクトルレコードを残さない | `tests/test_rag_index_integrity.py` | ✓ 追加済み |
| TEST-DESIGN3-04 | 削除順序の不変条件: `chunks_vec` → `documents`（`ON DELETE CASCADE` により `chunks` を削除） | `tests/test_rag_index_integrity.py` | ✓ 追加済み |
| TEST-DESIGN3-05 | 整合性チェックが派生インデックスの非同期を検出する | `tests/test_rag_index_integrity.py` | ✓ 追加済み |

**バグ修正 — reconcile_url()のFTS削除:**

`RagMaintenanceService.reconcile_url()`は`DELETE FROM chunks_fts WHERE chunk_id IN (...)`を
使用していたが、これはFTS5コンテンツテーブルでは無効である。
`scripts/agent/services/rag_maintenance_service.py`で修正し、正しい行単位のFTS5削除コマンド構文
`INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', ?, ?)`を使用するようにした。
リグレッションテスト: `tests/test_rag_index_integrity.py::test_reconcile_url_fts_deletion`。

**TEST-DESIGN3-01: FTS再構築がCOALESCEを使用する**

```python
# Pseudocode for integration test
def test_fts_rebuild_uses_cascade(db):
    """RagMaintenanceService.rebuild_fts() must use COALESCE(normalized_content, content)."""
    # Insert chunk with NULL normalized_content
    insert_chunk(
        doc_id=1,
        content="english text",
        normalized_content=None,
        chunk_index=0,
    )
    # Delete all FTS entries
    db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('delete-all')")
    # Rebuild using the maintenance service
    RagMaintenanceService().rebuild_fts()
    # Verify: content is indexed (not NULL)
    results = fts_search("english")
    assert len(results) == 1
    assert results[0].content == "english text"
```

**TEST-DESIGN3-02: chunks_ftsは派生であり、正規ではない**

```python
# Pseudocode for integration test - chunks_fts_derived_index
def test_chunks_fts_is_derived_index(db):
    """chunks_fts must not be directly INSERTed/UPDATEed by application code."""
    # Insert chunk via canonical path (INSERT into chunks)
    insert_chunk(doc_id=1, content="test", normalized_content=None, chunk_index=0)
    # Verify: FTS entry exists (trigger-synced)
    results = fts_search("test")
    assert len(results) == 1
```

**TEST-DESIGN3-03: 強制再取り込みで孤立ベクトルが発生しないこと**

```python
# Pseudocode for integration test - force_reingest_no_orphan_vectors
def test_force_reingest_no_orphan_vectors(db):
    """Force re-ingestion must not leave orphan chunks_vec records."""
    # Insert document and chunks
    insert_doc(url="http://example.com")
    insert_chunk(doc_id=1, content="text", normalized_content=None, chunk_index=0)
    # Force re-ingestion (deletes chunks_vec first, then documents; CASCADE removes chunks)
    RagMaintenanceService().delete_document("http://example.com")
    # Verify: no orphan vec rows remain
    orphan_count = db.execute(
        "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
    ).fetchone()[0]
    assert orphan_count == 0
```

**TEST-DESIGN3-04: 削除順序の不変条件**

```python
# Pseudocode for integration test - deletion_order_invariant
def test_deletion_order_invariant(db):
    """Deletion must follow: chunks_vec → documents (CASCADE removes chunks)."""
    # Insert document with chunks and vectors
    insert_doc(url="http://order-test.com")
    chunk_id = insert_chunk(doc_id=1, content="test", normalized_content=None, chunk_index=0)
    db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
    # Delete via canonical path
    delete_document_chain(db, doc_id=1)
    # Verify: no orphan vec rows remain
    orphan_count = db.execute(
        "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
    ).fetchone()[0]
    assert orphan_count == 0
```

**TEST-DESIGN3-05: 整合性チェックが非同期を検出する**

```python
# Pseudocode for integration test - consistency_checks_detect_fts_gap
def test_consistency_checks_detect_fts_gap(db):
    """check_rag_consistency() must detect FTS index desync."""
    # Insert chunk without triggering FTS (simulate trigger failure)
    insert_chunk(doc_id=1, content="test", normalized_content=None, chunk_index=0)
    # Manually remove the FTS-synced row to simulate desync
    db.execute("DELETE FROM chunks_fts WHERE rowid = 1")
    # Verify: check_rag_consistency() reports the gap
    result = check_rag_consistency(db)
    assert result.fts_gap > 0
```

対応する実装(`test_consistency_check_detects_fts_gap`)は `tests/test_rag_index_integrity.pyのtest_consistency_check_detects_fts_gap関数` に実在する。(Explicit in code)

## Related Documents

- [03_rag_91_design_notes.md](03_rag_91_design_notes.md)

## Keywords

design-decision
database
responsibilities

