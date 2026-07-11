---
title: "DocumentManager Detail"
category: rag
tags:
  - document-manager
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler-part1.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md
  - 03_rag_02_04_ingestion_pipeline-ingester-part1.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 4.10 DocumentManager (`scripts/rag/ingestion/document_manager.py`)

`DocumentManager` — RagIngesterのためにドキュメントのライフサイクルを管理する。既存ドキュメントの検出、ETagの更新、インジェクション後の整合性レポートを扱う。クラスサイズを抑え関心を分離するため `RagIngester` から抽出された。

**モジュールレベルの関数**

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `delete_document_chain` | `(db: SQLiteHelper, doc_id: int) -> None` | `chunks_vec` → `chunks` → `documents` の順で削除する；chunks_vecはchunksへのFK制約がないため最初に削除する必要がある |

**クラス: `DocumentManager`**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `__init__` | `(db: SQLiteHelper) -> None` | DB接続の参照を保持する |
| `handle_existing_document` | `(url: str, existing_doc_id: int, force: bool, etag\|None, last_modified\|None, fetched_at\|None, is_file_url: Callable[[str], bool]) -> bool` | 既存ドキュメントを処理する；呼び出し元が挿入をスキップすべき場合にTrueを返す。force=False → ETagManagerでetagを更新；SHA-256が変化していないfile:// URL → スキップ；force=True → ドキュメントチェーンを削除しFalseを返して再挿入を許可 |
| `delete_existing_document` | `(doc_id: int) -> None` | ドキュメントとそのチャンクを削除する；chunks_vecはchunksへのFK制約がないため最初に削除される |
| `check_consistency` | `(embed_failed: int, on_ingest_complete: Callable[[], None]\|None = None) -> RagConsistencyReport \| None` | インジェクション後の整合性チェックとコールバックを実行する；レポートを返すか、チェックが失敗した場合（チェック中のDBエラー）はNoneを返す |

**コードから推測される意図:**
- `handle_existing_document` は `url.startswith("file://")` を直接チェックするのではなく `is_file_url` をcallableとして受け取る。これによりモック実装でのテスト容易性を確保している

**CLIエントリポイント:**

```bash
uv run python scripts/rag/ingestion/ingester.py --force
```

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

document-manager
rag
