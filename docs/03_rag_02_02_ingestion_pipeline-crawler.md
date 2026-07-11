---
title: "WebCrawler Detail"
category: rag
tags:
  - web-crawler
  - bfs-crawl
  - conditional-get
  - local-file-ingestion
  - crawler
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_04_ingestion_pipeline-ingester.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 2. WebCrawler (`scripts/rag/ingestion/crawler.py`)

### 2.1 クラス概要

`WebCrawler` — 開始URLから同一オリジン内を `max_depth` の階層までBFSでクロールし、各ページを
`rag-src/` 内のJSONファイルとして保存する。条件付きGET（ETag/Last-Modified）、ローカルファイル、
ページごとのCJK比率による言語自動判定（`--lang auto`）に対応する。並行数制御には asyncio.Semaphore を使用する。

**Typed dict**

| TypedDict | 用途 |
|---|---|
| `CrawlPayload` | クロール出力JSONファイル用の型付きdict（url, title, lang, fetched_at, content, code_blocks, etag, last_modified, schema_version, artifact_type [ingestion-only], created_by） |

**公開メソッド**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | `crawler.toml` をロードする。AsyncClientは `crawl_site()` メソッド内で生成される |
| `crawl` | `async (targets: list[tuple[str, str]] \| None = None) -> None` | 指定されたすべての対象、または targets が None の場合は設定の target_urls をクロールする |
| `crawl_site` | `async (start_url: str, hint_lang: str) -> None` | asyncio.Semaphoreによる並行数制御とFIRST_COMPLETEDループを用いて、同一オリジン内をmax_depthの階層まで非同期BFSクロールする |
| `crawl_file` | `(path: Path, lang: str) -> int` | ローカルファイルをクロール結果JSONとしてrag-src/に保存する。.pyファイルはコードブロックとして格納される。成功時は1、失敗時は0を返す |

**モジュールレベルのユーティリティ**

| 関数 | 説明 |
|---|---|
| `url_to_slug(url)` | URLをファイルシステムで安全なASCIIスラグに変換する（最大80文字） |
| `normalize_url(url)` | フラグメントと末尾のスラッシュを除去する |
| `same_origin(url, base)` | スキームとホスト名が一致する場合にTrueを返す |

### 2.1.1 設定パラメータ

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `crawl_delay` | 1.5 | BFSクロール中のリクエスト間隔（秒）。最小1.0を推奨 |
| `max_depth` | 3 | BFSクロールの最大深度（起点URLからのURLホップ数）。コードは設定から直接読み込み、フォールバックはない |
| `min_chunk` | 40 | チャンクの最小文字数。これ未満のチャンクはノイズとして破棄される |
| `fetch_retry` | 3 | HTTP取得失敗時のリトライ上限（指数バックオフ） |
| `fetch_timeout` | 15 | HTTPリクエストのタイムアウト（秒） |
| `crawl_concurrency` | 3 | asyncio.Semaphoreによる最大並行取得タスク数 |
| `max_pages` | 500 | 開始URLごとにクロールする最大ページ数 |
| `skip_nofollow` | False | rel="nofollow"が付いたリンクをスキップする |
| `skip_external` | True | クロスオリジンのリンクをスキップする（デフォルトでは同一オリジンのみ） |

### 2.1.2 crawl_fileの動作

`crawl_file(path, lang)` はローカルファイルを読み込み、クロールJSONを `rag-src/` に書き込む。
WebのURLと異なり、HTTPの往復は発生しない。Pythonファイル（.py）はコードブロックとして格納され、
コード用のチャンカーが適用される。Python以外のファイルは内容を `content` フィールドに直接格納する。
ローカルファイルのペイロードには `schema_version`、`artifact_type`（ingestion-onlyの値）、`created_by` のメタデータフィールドが含まれる。

`lang == "auto"` の場合、このメソッドはファイル内容に対するCJK比率判定によって「auto」を解決する。

### 2.2 動作の詳細

- **テキスト抽出:** 本文テキストには `crawler_utils.extract_text()`、コードブロックにはBeautifulSoup4の `<pre>` を使用
- **言語判定:** CJK比率（ひらがな + カタカナ + CJK統合漢字が10%以上）→ `ja`；それ以外は `en`。
  100文字未満のページはヒント言語を使用する。`--lang auto` は常に自動判定を行い、フォールバックは `en`。
- **冪等性:** `visited` セットにより、同一実行内で同じURLを二重に取得することを防ぐ
- **条件付きGET:** SQLiteから `documents.etag` / `documents.last_modified` を読み込み、
  `If-None-Match` / `If-Modified-Since` を送信する。304の場合はファイル保存をスキップする

### ローカルファイルのインジェクション

`crawl_file(path, lang)` はローカルファイルを読み込み、クロールJSONを `rag-src/` に書き込む。
WebのURLと異なり、HTTPの往復は発生しない。

#### 鮮度判定（自動）

`crawl_file()` はmtime（ISO文字列）とファイル内容のSHA-256を計算し、
それぞれクロールペイロードの `last_modified` と `etag` として格納する。
URLは `file://{absolute_path}` として格納される。

`file://` URLに対しては、スキップするか再インジェクションするかを判断する前に鮮度チェックが行われる。

| 条件 | 判定 |
|---|---|
| `etag`（SHA-256）が同一 | スキップ — 内容は変化していない |
| `etag` が異なる | 自動で再インジェクション（旧レコードを削除し再埋め込み） |
| DBに `etag` がない | 再インジェクション（保守的な判断） |

`etag` カラムには、ローカルファイルの場合、SHA-256の16進ダイジェストがそのまま格納される。
`file://` URLに対してHTTPのETagが設定されることはないため、衝突は発生しない。
`force=True` の場合は、格納されているハッシュに関わらず常に再インジェクションする。

ログメッセージ: `"file:// unchanged (sha256 match)"` または `"file:// changed — auto re-ingesting"`。

#### Webインジェクションとの対比

| 観点 | Web（HTTP） | ローカルファイル（file://） |
|---|---|---|
| 鮮度の判定材料 | ETag / Last-Modifiedヘッダ | ファイルmtime / SHA-256 |
| スキップの仕組み | 304 Not Modified | 保存済みmtimeまたはハッシュの比較 |
| 強制再インデックス | `--force` フラグ | `--force` フラグ |
| 現在の状態 | 実装済み | 実装済み（SHA-256ハッシュ比較） |

### 2.3 CLI引数

| 引数 | 説明 | デフォルト |
|---|---|---|
| `--url URL [URL ...]` | 対象URL（複数指定可。省略時は設定の `target_urls` を使用） | — |
| `--lang {en,ja,auto}` | ページごとのCJK比率判定に使うヒント言語 | `en` |
| `--targets-file PATH` | `target_urls = [[url, lang], ...]` を記述したTOMLファイルのパス。`http://`、`https://`、`file://` に対応。`--url` とは併用不可 | — |

### 2.4 出力JSON形式（`rag-src/yyyymmddhhmmss-{slug}.json`）

```json
{
  "schema_version": "1",
  "artifact_type": "crawl",
  "created_by": "crawler",
  "url": "https://example.com/page",
  "title": "Page title",
  "lang": "ja",
  "fetched_at": "2024-01-01T12:00:00",
  "content": "body text",
  "code_blocks": ["block1", "block2"],
  "etag": "optional-http-etag",
  "last_modified": "optional-http-date"
}
```

ローカルファイルのペイロードには `etag`（ファイル内容のSHA-256十六進ダイジェスト）と `last_modified`（ISO形式のmtime文字列）が含まれる。
Pythonファイル（.py）は内容を `code_blocks` に格納し `content` は空にする。それ以外のファイル種別は内容を直接格納する。

### 2.5 エラーハンドリング

| ケース | 対応 |
|---|---|
| HTTPリクエスト失敗 | `fetch_retry` 回まで指数バックオフでリトライ（`min(2**i, 10)` 秒） |
| URL単位の例外 | `WARNING` ログを出力し、次のURLへ継続 |
| テキストが100文字未満 | ヒント言語を使用（`--lang auto` の場合は `en` にフォールバック） |
| 言語が `ja`/`en` でない | ログを出さずに黙ってURLをスキップ |

### 2.6 ロギング

- **ファイル:** `/opt/llm/logs/crawl.log` + stderr
- **フォーマット:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング | 構造化フィールド |
|---|---|---|
| `INFO` | クロール開始、URL保存、URLスキップ | `url`、`source_type`（保存時）；`url`（スキップ時） |
| `WARNING` | HTTPエラー、リトライ発生 | — |

### 2.7 設定（`config/rag_pipeline.toml`）

[03_rag_05_1-configuration-reference.md §1.1](03_rag_05_1-configuration-reference.md) を参照。

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

web-crawler
bfs-crawl
conditional-get
local-file-ingestion
crawler
rag
