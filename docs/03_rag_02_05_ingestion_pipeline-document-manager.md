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
| `check_consistency` | `(embed_failed: int, on_ingest_complete: Callable[[], None]\|None = None) -> RagConsistencyReport \| None` | インジェクション後の整合性チェックとコールバックを実行する；レポートを返すか、チェックが失敗した場合（チェック中のDBエラー）はNoneを返す。整合性チェックが正常終了した場合（レポートに問題が含まれていても）、`on_ingest_complete` コールバックが呼び出される。整合性チェック自体が例外を投げた場合は、コールバックは呼び出されない |

**コードから推測される意図:**
- `handle_existing_document` は `url.startswith("file://")` を直接チェックするのではなく `is_file_url` をcallableとして受け取る。これによりモック実装でのテスト容易性を確保している

**現在の実装挙動（docsとコードの矛盾点）:**
- `handle_existing_document` は `existing_doc_id` を受け取るが、非file:// URLの更新パス（`_update_etag` 呼び出し）にはこの値が渡されていない。`_update_etag` 内部では `ETagManager(self._db, 0)` と `doc_id=0` を固定で生成しており、`existing_doc_id` を使っていない（`document_manager.py` 46-101行）。
- `ETagManager.update()` が発行するSQLはすべて `WHERE doc_id = ?` で `doc_id=0` を束縛するため、`doc_id=0` の行が存在しない限り更新は0件ヒットでサイレントに終わる（例外は発生しない）。結果として、force=Falseで既存の非file://ドキュメントを再取得した場合、ETag/Last-Modifiedの更新が実質的に無効化されている可能性が高い。
- 本挙動を裏付ける自動テストは `scripts/tests/` 配下に見当たらない。意図的な仕様か実装漏れか不明のため **Needs confirmation**。

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
etag-manager
doc_id
rag
