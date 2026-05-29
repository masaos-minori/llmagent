# 取込パイプライン — rag_ingester.py API リファレンス

実行ガイド → [`03_ingestion-run.md`](03_ingestion-run.md)  
共通実装注意事項 → [`03_ref-ingestion.md`](03_ref-ingestion.md)

## 4. rag_ingester.py

### 4.1 クラス概要

`RagIngester` クラス。`/opt/llm/rag-src/chunk/*.txt` のチャンクファイルを読み込み、`embed-llm` サービス (multilingual-E5-small, ポート 8003) で埋込ベクトルを生成して SQLite の 4 テーブル (`documents` / `chunks` / `chunks_vec` / `chunks_fts`) に登録する。処理済みチャンクファイルは `/opt/llm/rag-src/registered/` に移動する。

**公開メソッド**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | `common.json` と `rag_pipeline.json` をマージして読み込みインスタンスを初期化する。`requests.Session` も生成する |
| `ingest_all` | `(force: bool = False) -> None` | `chunk_dir` の全チャンクファイルを URL 単位でグループ化して投入する |
| `ingest_url_group` | `(db: SQLiteHelper, url: str, chunk_files: list[Path], force: bool) -> None` | 1 URL 分のチャンクファイル群を SQLite に投入し、処理後ファイルを `registered/` に移動する |

### 4.2 機能概要

`rag-src/chunk/*.txt` のチャンクファイルを URL 単位でグループ化し、`embed-llm` API でベクトルを生成して SQLite の 4 テーブルに登録。登録済みファイルは `rag-src/registered/` に移動。

- E5 プレフィックス: 埋込 API リクエスト時に `passage: {text}` を付与 (クエリ時の `query: ` と区別)
- ベクトル格納: `struct.pack("<{N}f", ...)` で little-endian float32 BLOB に変換して `chunks_vec` に INSERT
- upsert: `--force` 指定時は `chunks_vec` → `chunks` → `documents` の順に削除してから再登録
- 冪等性: `--force` 未指定の場合、`documents.url` が既登録の URL はスキップ
- ETag/Last-Modified 更新: `--force` 未指定でスキップした場合でも、チャンクファイルから読み取った `etag` / `last_modified` を `documents` テーブルに UPDATE し、次回 Crawler の条件付き GET で使用可能
- ローカルファイル対応: `file://` スキームの URL をチャンクグループとして受け付け

### 4.3 実装方式

| 機能 | 実装 |
|---|---|
| 埋込 API 呼び出し | `requests.Session()` で `POST http://127.0.0.1:8003/embedding` を呼び出す |
| E5 モデルプレフィックス | 取込時は `passage: {text}` を付与 (クエリ時は `query: {text}`) |
| ベクトル格納 | `struct.pack(f"<{N}f", *values)` でリトルエンディアン float32 BLOB に変換 (sqlite-vec の `MATCH` 演算子要件) |
| 埋込並列化 | `_ingest_chunk_files()` が `ThreadPoolExecutor(embed_workers)` でチャンクを並列投入する。ドキュメントレコードを `db.commit()` してから並列開始し、各スレッドは独立した `SQLiteHelper().open()` を使用する |
| WAL モード | `PRAGMA journal_mode=WAL` を設定し並行読み書きを安全に処理 |
| upsert | `--force` 指定時は `chunks_vec` → `chunks` → `documents` の順に削除してから再登録 |
| ETag/Last-Modified 保存 | チャンクファイルの `etag` / `last_modified` フィールドを `documents` テーブルに保存する。スキップ時も UPDATE して最新値を維持する |

### 4.4 入出力インタフェース

**CLI 引数**

| 引数 | 説明 | デフォルト |
|---|---|---|
| `--force` | 既登録 URL のレコードを削除して最新コンテンツで再登録 | false |

**埋込 API**

```
POST http://127.0.0.1:8003/embedding
リクエスト : {"content": "passage: {テキスト}"}
レスポンス : {"embedding": [float, ...]}  # 384 次元 (llama.cpp レガシーエンドポイント)
```

**DB 更新テーブル**

| テーブル | 操作 |
|---|---|
| `documents` | `SELECT` で既登録を確認 → `force=False` のときスキップ、`force=True` のとき削除して `INSERT` |
| `chunks` | `doc_id` FK (ON DELETE CASCADE) → `INSERT` でチャンクを登録 |
| `chunks_vec` | `chunk_id` PK → `INSERT` でベクトル BLOB を登録 |
| `chunks_fts` | `chunks_ai` トリガが `COALESCE(normalized_content, content)` を自動 INSERT。日本語は正規化形、英語・コードは原文でインデックス |

### 4.5 エラーハンドリング

| ケース | 対処 |
|---|---|
| 埋込 API 失敗 | `embed_retry` 回まで指数バックオフでリトライ |
| チャンク単位の埋込失敗 (リトライ全失敗) | `WARNING` ログを出力してそのチャンクをスキップし次チャンクに継続 |
| `chunks_vec` 削除順序 | `chunks_vec` → `chunks` → `documents` の順で削除 (`chunks_vec` は sqlite-vec 仮想テーブルのため外部キー制約なし、先行削除しないと孤立レコードが残る) |
| `lang` 不正値 (`ja`/`en` 以外) | `_get_or_create_document` が `ValueError` を送出し、該当 URL グループをスキップする (`ERROR` ログ; スタックトレースあり) |

### 4.6 ログ出力

- **ファイル:** `/opt/llm/logs/ingest.log` + 標準エラー出力
- **フォーマット:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング |
|---|---|
| `INFO` | 処理チャンク数、DB 登録件数、ファイル移動完了 |
| `WARNING` | 埋込 API エラー、リトライ発生、埋込スキップ |
| `ERROR` | チャンクファイル読み込みエラー、ファイル移動エラー、URL グループ処理失敗 (スタックトレースあり) |

### 4.7 設定項目

`config/common.json` と `config/rag_pipeline.json` を参照する。

| パラメータ | 設定ファイル | デフォルト | 説明 |
|---|---|---|---|
| `embed_url` | `config/common.json` | `http://127.0.0.1:8003/embedding` | 埋込 API のエンドポイント (llama.cpp レガシー形式) |
| `rag_db_path` | `config/common.toml` | `/opt/llm/db/rag.sqlite` | SQLite データベースのパス |
| `sqlite_vec_so` | `config/common.json` | `/opt/llm/sqlite-vec/vec0.so` | sqlite-vec 拡張 (.so) のパス |
| `rag_src_dir` | `config/rag_pipeline.json` | `/opt/llm/rag-src` | チャンクファイル入力ディレクトリ (`{rag_src_dir}/chunk/*.txt`) および登録済みファイル移動先 (`{rag_src_dir}/registered/`) |
| `embed_retry` | `config/rag_pipeline.json` | `3` | 埋込 API 失敗時の指数バックオフリトライ上限回数 |
| `embed_workers` | `config/rag_pipeline.json` | `4` | 埋込並列実行数。`ThreadPoolExecutor(embed_workers)` でチャンクを並列投入する |
