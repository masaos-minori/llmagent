---
title: "WebCrawler Detail (Part 2)"
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
  - 03_rag_01_system_overview-part1.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md
  - 03_rag_02_04_ingestion_pipeline-ingester-part1.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_02_ingestion_pipeline-crawler-part1.md
---

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 2. WebCrawler (`scripts/rag/ingestion/crawler.py`)

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

### 2.7 設定（`config/crawler.toml`）

[03_rag_05_1-configuration-reference.md §1.1](03_rag_05_1-configuration-reference.md) を参照。

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md`
- `03_rag_02_04_ingestion_pipeline-ingester-part1.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_02_ingestion_pipeline-crawler-part1.md`

## Keywords

web-crawler
bfs-crawl
conditional-get
local-file-ingestion
crawler
rag
