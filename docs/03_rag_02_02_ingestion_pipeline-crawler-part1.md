---
title: "WebCrawler Detail (Part 1)"
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

### 2.1 クラス概要

`WebCrawler` — 開始URLから同一オリジン内を `max_depth` の階層までBFSでクロールし、各ページを
`rag-src/` 内のJSONファイルとして保存する。条件付きGET（ETag/Last-Modified）、ローカルファイル、
ページごとのCJK比率による言語自動判定（`--lang auto`）に対応する。並行数制御には asyncio.Semaphore を使用する。

**Typed dict**

| TypedDict | 用途 |
|---|---|
| `CrawlPayload` | クロール出力JSONファイル用の型付きdict（url, title, lang, fetched_at, content, code_blocks, etag, last_modified, schema_version, artifact_type [ingestion-only], created_by） |

**公開メソッド** — 詳細は `scripts/rag/ingestion/crawler.py` を参照してください。

**モジュールレベルのユーティリティ** — 詳細は `scripts/rag/ingestion/crawler.py` を参照してください。

### 2.1.1 設定パラメータ

| パラメータ | コードフォールバック値 | 本番環境値 (config/crawler.toml) |
|---|---|---|
| max_depth | なし | 3 |
| max_pages | 500 | 200 |
| skip_nofollow | False | true |

> 全パラメータ一覧は [§1.1 Configuration Reference](../03_rag_05_1-configuration-reference.md) を参照してください。

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

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md`
- `03_rag_02_04_ingestion_pipeline-ingester-part1.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_02_ingestion_pipeline-crawler-part2.md`

## Keywords

web-crawler
bfs-crawl
conditional-get
local-file-ingestion
crawler
rag
