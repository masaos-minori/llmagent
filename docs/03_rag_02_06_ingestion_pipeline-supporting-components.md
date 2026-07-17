---
title: "RAG Ingestion Pipeline - Supporting Components"
category: rag
tags:
  - etag-manager
  - ingestion-configuration
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler-part1.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md
  - 03_rag_02_04_ingestion_pipeline-ingester-part1.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_02_05_ingestion_pipeline-document-manager.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 4.8 ETagManager (`scripts/rag/ingestion/etag_manager.py`)

`ETagManager` — 既存ドキュメントのETag/Last-Modifiedの更新を管理する。古さガードを提供する: new_fetched_at が stored fetched_at より古い場合、入力データは古いものと判断され、既存のDBの値が保持される。2つの更新モードがある。
- 鮮度モード: 鮮度が確認できた場合にETag/Last-Modifiedを上書きする（fetched_atにはCOALESCEを使用）
- Null埋めモード: NULLのみを埋める；既存の値は上書きしない（etagとlast_modifiedの両方にCOALESCEを使用）

**公開メソッド**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `update` | `(etag: str \| None, last_modified: str \| None, new_fetched_at: str \| None = None)` | 既存ドキュメントのETag/Last-Modifiedを更新する；etagとlast_modifiedの両方がNoneの場合は早期リターンする |

**境界条件:**
- 古さ判定（`_is_stale_update`）は `new_fetched_at` と保存済み `fetched_at` を文字列比較で行う（ISO 8601形式であることを前提とする）。値がNone、または保存済み行が存在しない場合は「古くない」とみなして更新を進める。(Explicit in code)
- `ETagManager` 自身は `__init__` で受け取った `doc_id` に対してのみSQLを発行する。呼び出し元が正しい `doc_id` を渡す責務を負う。[03_rag_02_05_ingestion_pipeline-document-manager.md](03_rag_02_05_ingestion_pipeline-document-manager.md) に記載の通り、`DocumentManager` のETag更新処理は `existing_doc_id` ではなく固定値 `0` を渡しており、既存ドキュメント再取得時のETag更新が意図通り機能しない可能性がある（Needs confirmation）。

## 4.9 設定（`config/ingester.toml`）

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `embed_url` | `http://127.0.0.1:8081/embedding` | 埋め込みAPIのエンドポイントURL |
| `embed_retry` | 3 | 埋め込みAPI失敗時のリトライ上限（指数バックオフ） |
| `embed_workers` | 4 | ThreadPoolExecutorによる最大並行埋め込みスレッド数 |
| `embedding_dims` | 384 | 想定される埋め込みベクトルの次元数；APIレスポンスと照合して検証される |

[03_rag_05_1-configuration-reference.md §1.2](03_rag_05_1-configuration-reference.md) を参照。

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler-part1.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md`
- `03_rag_02_04_ingestion_pipeline-ingester-part1.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

etag-manager
ingestion-configuration
rag
