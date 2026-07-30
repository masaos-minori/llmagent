---
title: "RagIngester Detail (Part 1)"
category: rag
tags:
  - ingester
  - embedding
  - sqlite
  - etag-manager
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler-part1.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_02_05_ingestion_pipeline-document-manager.md
  - 03_rag_02_06_ingestion_pipeline-supporting-components.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_04_ingestion_pipeline-ingester-part1.md
---

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 4. RagIngester (`scripts/rag/ingestion/ingester.py`)

### 4.1 クラス概要

`RagIngester` — チャンクファイルを読み込み、`embed-llm`（ポート8081）経由で埋め込みを生成し、
SQLite（`documents` / `chunks` / `chunks_vec`）へupsertする。処理済みチャンクは
`rag-src/registered/` へ移動する。

**Dataclass**

| クラス | 用途 |
|---|---|
| `IngestUrlResult` | `ingest_url_group()` が返すURL単位のインジェクション結果。フィールド: `url`、`n_success`、`n_failed`、`skipped`、`n_embed_failed`（デフォルト0） |

**公開メソッド**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | `ingester.toml` をロードし、`httpx.Client` を初期化する |
| `ingest_all` | `(force: bool = False, on_ingest_complete: Callable[[], None] \| None = None) -> RagConsistencyReport \| None` | チャンクファイルをURLごとにグループ化し、各グループを処理する。整合性レポートを返すか、インジェクション後の整合性チェックが失敗した場合（チェック中にDBエラーが発生する稀な失敗ケース）はNoneを返す。チャンクファイルが存在しない場合もNoneを返す。`on_ingest_complete` コールバックは整合性チェック完了後に呼び出される（ただし、chunk_dirに*.jsonファイルがない場合は呼び出されない）。CLI `main()` は現在このパラメータを渡さないため、CLIパスではこのコールバックは実行されない |
| `ingest_url_group` | `(doc_mgr: DocumentManager, db: SQLiteHelper, url: str, chunk_files: list[Path], force: bool) -> IngestUrlResult` | 1つのURLグループをchunk_indexの昇順で処理する。処理後（スキップした場合も含む）にファイルをregistered/へ移動する。`{n_success, n_failed, n_embed_failed, skipped}` を返す |
| `close` | `() -> None` | 内部の `httpx.Client` を閉じる |
| `__del__` | `() -> None` | 安全のためのクリーンアップ: 未クローズであればhttpx.Clientを閉じる（明示的なcloseの呼び忘れに対応） |

### 4.2 動作の詳細

- **E5プレフィックス:** 埋め込み前に `passage: {text}` を先頭に付加する（クエリ時は `query: `） 
- **ベクトルエンコーディング:** `struct.pack(f"<{N}f", *values)` → リトルエンディアンのfloat32 BLOB
- **並列埋め込み:** URLグループごとに `ThreadPoolExecutor(embed_workers)` を使用する。
  各スレッドは独立した `SQLiteHelper().open()` を使用する
- **WALモード:** 並行読み書きの安全性のため `PRAGMA journal_mode=WAL` を使用する
- **Upsert（`--force`）:** `chunks_vec` → `chunks` → `documents` の順で削除し、再INSERTする。`chunking_strategy` は元ファイルの値が保持される

### 4.2.1 削除順序の不変条件

以下の削除順序は設計上の不変条件であり、ドキュメントレコードを削除するすべてのコードパスで維持されなければならない。

``` text
chunks_vec（明示的に削除）→ documents（削除するとON DELETE CASCADEでchunksが連鎖削除される）
```

**理由:** `chunks_vec` はsqlite-vecの仮想テーブルであり、`chunks` を指す外部キー制約を持たない。そのため`chunks_vec`のみ明示的な削除が必要であり、`chunks`自体への明示DELETE文はコード上存在しない(`documents`削除のCASCADEに委ねられる)。

1. その文書のchunk_idsに対応する `chunks_vec` の行を明示的に削除する
2. `documents` の行を削除する(`ON DELETE CASCADE`により`chunks`が連鎖削除され、`chunks_fts`の同期トリガーも発火する)

**影響を受けるコードパス:**
- `DocumentManager.delete_existing_document()`(`scripts/rag/ingestion/document_manager.py`) — 取り込みパイプライン経路。内部的に共有ヘルパー`delete_document_chain()`を呼び出す
- `DocumentManager.delete_document(url)`(`scripts/mcp_servers/rag_pipeline/document_manager.py`) — MCPツール(`rag_delete_document`)経路
- 孤立したベクトルレコードを防ぐため、両経路とも同じ順序に従う(詳細は`docs/03_rag_91_design_notes-part1.md` DESIGN-3を参照)
- **冪等性:** URLが既に `documents` に存在する場合はスキップする。ただし後述のスキップ経路のガードにより `etag`/`last_modified` はUPDATEされる。スキップ時は `chunking_strategy` は更新されない
- **スキップ経路の古さガード:** 入力された `fetched_at`（チャンクペイロード）を、格納済みの `documents.fetched_at` と比較する。入力側が古い場合は更新をスキップする（より新しいクロールが優先される — 古いチャンクファイルがより新しいメタデータを上書きすることを防ぐ）。`fetched_at` が欠落している場合（鮮度情報を持たない旧形式のチャンク）は、埋め込みのみのセマンティクスを使用する: `COALESCE(etag, ?)` — 現在NULLの場合にのみ値を設定し、NULL以外の値を上書きすることはない。これにより、古いチャンクファイルのメタデータが、より新しいクロールで格納された値を置き換えてしまうことを防ぐ。
- **埋め込み失敗の追跡:** チャンクと埋め込みの結果はタプルとして返される。
  `n_embed_failed` は、パース/DBエラーとは別に埋め込み固有の失敗をカウントする
- **ローカルファイルの未変更判定:** `file://` URLについてはSHA-256のetagを比較する

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler-part1.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_02_05_ingestion_pipeline-document-manager.md`
- `03_rag_02_06_ingestion_pipeline-supporting-components.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_04_ingestion_pipeline-ingester-part2.md`

## Keywords

ingester
embedding
sqlite
rag
