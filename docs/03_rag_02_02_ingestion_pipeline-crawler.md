---
title: "WebCrawler Detail (Part 1)"
area: rag
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
  - 03_rag_02_02_ingestion_pipeline-crawler.md
---


# RAG Ingestion Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 2. WebCrawler (`scripts/rag/ingestion/crawler.py`)

### 2.1 Class Overview

`WebCrawler` performs a BFS crawl from a starting URL within the same origin up to `max_depth` levels and saves each page as a JSON file in `rag-src/`. It supports Conditional GET (ETag/Last-Modified), local files, and automatic language detection by CJK ratio per page (`--lang auto`). Concurrency is controlled using `asyncio.Semaphore`.

**Typed dict**

| TypedDict | Purpose |
|---|---|
| `CrawlPayload` | Typed dictionary for crawl output JSON files (url, title, lang, fetched_at, content, code_blocks, etag, last_modified, schema_version, artifact_type [ingestion-only], created_by) |

**Public Methods** — See `scripts/rag/ingestion/crawler.py` for details.

**Module-level Utilities** — See `scripts/rag/ingestion/crawler.py` for details.

### 2.1.1 Configuration Parameters

| Parameter | Code Fallback Value | Production Value (config/crawler.toml) |
|---|---|---|
| max_depth | None | 3 |
| max_pages | 500 | 200 |
| skip_nofollow | False | true |

> For a full list of parameters, see [section 1.1 Configuration Reference](03_rag_05_1-configuration-reference.md).

### 2.1.2 `crawl_file` Behavior

`crawl_file(path, lang)` reads a local file and writes the crawl JSON to `rag-src/`. Unlike web URLs, no HTTP round-trips occur. Python files (.py) are stored as code blocks and subject to code-specific chunking. Other file types store their content directly in the `content` field. Local file payloads include metadata fields: `schema_version`, `artifact_type` (value for `ingestion-only`), and `created_by`.

If `lang == "auto"`, this method resolves the language based on the CJK ratio of the file content.

### 2.2 Detailed Behavior

- **Text Extraction:** Uses `crawler_utils.extract_text()` for body text and BeautifulSoup4's `<pre>` for code blocks.
- **Language Detection:** If CJK ratio (Hiragana + Katakana + CJK Unified Ideographs ≥ 10%) is detected → `ja`; otherwise `en`. Pages with fewer than 100 characters use the hint language. `--lang auto` always performs automatic detection, with `en` as fallback.
- **Idempotency:** A `visited` set prevents duplicate fetching of the same URL within a single execution.
- **Conditional GET:** Reads `documents.etag` / `documents.last_modified` from SQLite and sends `If-None-Match` / `If-Modified-Since`. If a 304 response is received, saving the file is skipped.

#### Local File Injection

`crawl_file(path, lang)` reads a local file and writes the crawl JSON to `rag-src/`. Unlike web URLs, no HTTP round-trips occur.

##### Generating Freshness Data (Note on Responsibility Boundaries)

`crawl_file()` only calculates the mtime (ISO string) and SHA-256 hash of the file content and stores them in the `last_modified` and `etag` fields of the crawl payload; it does not perform any skip/decision logic. The JSON payload is always output unconditionally. The URL is stored as `file://{absolute_path}`.

Decisions on whether to skip or re-ingest are made by `DocumentManager._is_file_unchanged()`/`_handle_existing_file()` in `scripts/rag/ingestion/document_manager.py`, NOT by `WebCrawler`.

| Condition | Decision (`DocumentManager` performs) |
|---|---|
| `etag` (SHA-256) is identical | Skip — Content has not changed |
| `etag` is different | Automatic re-ingestion (deletes old record and re-embeds) |
| No `etag` in DB | Re-ingestion (conservative decision) |

For local files, the `etag` column contains the hex digest of the SHA-256. Since `file://` URLs do not have HTTP ETags, collisions do not occur. Using `--force` bypasses the hash check and always triggers re-ingestion.

Log messages: `"file:// unchanged (sha256 match)"` or `"file:// changed — auto re-ingesting"`.

#### Comparison: Web vs. Local Injection

| Aspect | Web (HTTP) | Local Files (`file://`) |
|---|---|---|
| Freshness Basis | ETag / Last-Modified Header | File mtime / SHA-256 |
| Skipping Mechanism | 304 Not Modified | Comparison of saved mtime or hash |
| Forced Re-indexing | `--force` flag | `--force` flag |
| Current Status | Implemented | Implemented (SHA-256 hash comparison) |

### 2.3 CLI Arguments

| Argument | Description | Default |
|---|---|---|
| `--url URL [URL ...]` | Target URL(s) (multiple allowed. If omitted, uses `target_urls` from config) | — |
| `--lang {en,ja,auto}` | Hint language for per-page CJK ratio detection | `en` |
| `--targets-file PATH` | Path to a TOML file containing `target_urls = [[url, lang], ...]`. Supports `http://`, `https://`, and `file://`. Cannot be used with `--url`. | — |

### 2.4 Output JSON Format

`read_crawl_json()` (`scripts/rag/ingestion/pipeline_utils.py:100`) is the canonical
reader for crawl-stage JSON artifacts; `ChunkSplitter`
(`scripts/rag/ingestion/chunk_splitter.py:196`) is its sole caller. A crawl artifact
requires exactly 8 keys (`url`, `content`, `title`, `lang`, `code_blocks`, `etag`,
`last_modified`, `fetched_at`) — a missing key or an invalid field type raises
`ChunkFormatError` (see [03_rag_05_4-error-handling-reference.md](03_rag_05_4-error-handling-reference.md)).
For the full Required/Nullable/Conditional classification of these fields, see the
canonical crawl/chunk artifact-field contract table in
[03_rag_02_03_ingestion_pipeline-chunksplitter.md](03_rag_02_03_ingestion_pipeline-chunksplitter.md).
See also [docs/03_rag_04_01_dto-models_data.md](03_rag_04_01_dto-models_data.md) for
the `ChunkDocument` DTO this reader returns.

### 2.5 Error Handling

| Case | Action |
|---|---|
| HTTP request failure | Retries with exponential backoff up to `fetch_retry` times (e.g., `min(2**i, 10)` seconds) |
| Exception per URL | Logs a `WARNING` and continues to the next URL |
| Text < 100 characters | Uses hint language (falls back to `en` if `--lang auto`) |
| Language is not `ja`/`en` | Silently skips the URL without logging |

### 2.6 Logging

See [03_rag_05_3-logging.md](03_rag_05_3-logging.md) for details.

### 2.7 Configuration (`config/crawler.toml`)

See [03_rag_05_1-configuration-reference.md section 1.1](03_rag_05_1-configuration-reference.md).

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_04_01_dto-models_data.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_05_3-logging.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`

## Keywords

web-crawler
bfs-crawl
conditional-get
local-file-ingestion
crawler
rag
