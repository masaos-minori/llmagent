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

# RAG Ingestion Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 2. WebCrawler (`scripts/rag/ingestion/crawler.py`)

### 2.1 Class overview

`WebCrawler` — BFS-crawls from a start URL within the same origin up to `max_depth` levels; saves each page as
a JSON file in `rag-src/`. Supports conditional GET (ETag/Last-Modified), local files,
and per-page CJK-ratio language auto-detection (`--lang auto`). Uses asyncio.Semaphore for concurrency control.

**Typed dict**

| TypedDict | Purpose |
|---|---|
| `CrawlPayload` | Typed dict for crawl output JSON files (url, title, lang, fetched_at, content, code_blocks, etag, last_modified, schema_version, artifact_type [ingestion-only], created_by) |

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | Load `crawler.toml`; AsyncClient created in `crawl_site()` method |
| `crawl` | `async (targets: list[tuple[str, str]] \| None = None) -> None` | Crawl all given targets, or config target_urls when targets is None |
| `crawl_site` | `async (start_url: str, hint_lang: str) -> None` | Async BFS crawl within the same origin up to max_depth levels via asyncio.Semaphore concurrency and FIRST_COMPLETED loop |
| `crawl_file` | `(path: Path, lang: str) -> int` | Save a local file as a crawl result JSON in rag-src/; .py files stored as code blocks; returns 1 on success, 0 on failure |

**Module-level utilities**

| Function | Description |
|---|---|
| `url_to_slug(url)` | Convert URL to filesystem-safe ASCII slug (max 80 chars) |
| `normalize_url(url)` | Remove fragment and trailing slash |
| `same_origin(url, base)` | True if scheme + hostname match |

### 2.1.1 Configuration parameters

| Parameter | Default | Description |
|---|---|---|
| `crawl_delay` | 1.5 | Request interval during BFS crawl in seconds; minimum 1.0 recommended |
| `max_depth` | 3 | Maximum BFS crawl depth (URL hops from seed URL); code reads directly from config with no fallback |
| `min_chunk` | 40 | Minimum chunk character count; chunks below this are discarded as noise |
| `fetch_retry` | 3 | Retry limit for HTTP fetch failures (exponential backoff) |
| `fetch_timeout` | 15 | HTTP request timeout in seconds |
| `crawl_concurrency` | 3 | Max concurrent fetch tasks via asyncio.Semaphore |
| `max_pages` | 500 | Maximum pages to crawl per start URL |
| `skip_nofollow` | False | Skip links with rel="nofollow" |
| `skip_external` | True | Skip cross-origin links (same-origin only by default) |

### 2.1.2 crawl_file behavior

`crawl_file(path, lang)` reads a local file and writes a crawl JSON to `rag-src/`.
Unlike web URLs, no HTTP round-trip occurs. Python files (.py) are stored as code blocks
so the code chunker applies. Non-Python files store their content directly in the `content` field.
Local files include `schema_version`, `artifact_type` [ingestion-only], `created_by` metadata fields in the payload.

The method resolves "auto" lang by CJK-ratio detection on the file content when `lang == "auto"`.

### 2.2 Behavior details

- **Text extraction:** `crawler_utils.extract_text()` for body text; BeautifulSoup4 `<pre>` for code blocks
- **Language detection:** CJK ratio (hiragana + katakana + CJK unified ideographs ≥ 10%) → `ja`; else `en`.
  Pages < 100 chars use hint language. `--lang auto` always auto-detects; fallback to `en`.
- **Idempotency:** `visited` set prevents fetching same URL twice in one run
- **Conditional GET:** reads `documents.etag` / `documents.last_modified` from SQLite;
  sends `If-None-Match` / `If-Modified-Since`; skips file save on 304

### Local file ingestion

`crawl_file(path, lang)` reads a local file and writes a crawl JSON to `rag-src/`.
Unlike web URLs, no HTTP round-trip occurs.

#### Freshness detection (automatic)

`crawl_file()` computes mtime (ISO string) and SHA-256 of the file content and
stores both in the crawl payload as `last_modified` and `etag` respectively.
The URL is stored as `file://{absolute_path}`.

A freshness check is performed for `file://` URLs before deciding to skip or re-ingest:

| Condition | Decision |
|---|---|
| Same `etag` (SHA-256) | Skip — content unchanged |
| Different `etag` | Auto re-ingest (deletes old record, re-embeds) |
| `etag` missing in DB | Re-ingest (conservative) |

The `etag` column stores the raw SHA-256 hex digest for local files.
HTTP ETags are never set for `file://` URLs, so there is no collision.
`force=True` always re-ingests regardless of the stored hash.

Log messages: `"file:// unchanged (sha256 match)"` or `"file:// changed — auto re-ingesting"`.

#### Contrast with web ingestion

| Aspect | Web (HTTP) | Local file (file://) |
|---|---|---|
| Freshness signal | ETag / Last-Modified header | File mtime / SHA-256 |
| Skip mechanism | 304 Not Modified | Stored mtime or hash compare |
| Force re-index | `--force` flag | `--force` flag |
| Current state | Implemented | Implemented (SHA-256 hash comparison) |

### 2.3 CLI arguments

| Argument | Description | Default |
|---|---|---|
| `--url URL [URL ...]` | Target URLs (multiple allowed; omit to use `target_urls` from config) | — |
| `--lang {en,ja,auto}` | Hint language for per-page CJK-ratio detection | `en` |
| `--targets-file PATH` | Path to a TOML file with `target_urls = [[url, lang], ...]`; supports `http://`, `https://`, and `file://`; mutually exclusive with `--url` | — |

### 2.4 Output JSON format (`rag-src/yyyymmddhhmmss-{slug}.json`)

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

Local file payloads include `etag` (SHA-256 hex digest of file content) and `last_modified` (ISO mtime string).
Python files (.py) store their content in `code_blocks` with empty `content`; other file types store content directly.

### 2.5 Error handling

| Case | Action |
|---|---|
| HTTP request failure | Exponential backoff retry up to `fetch_retry` times (`min(2**i, 10)` sec) |
| URL-level exception | `WARNING` log; continue to next URL |
| Text < 100 chars | Use hint language (`en` fallback for `--lang auto`) |
| Language not `ja`/`en` | Skip URL silently (no log entry) |

### 2.6 Logging

- **File:** `/opt/llm/logs/crawl.log` + stderr
- **Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| Level | Timing | Structured fields |
|---|---|---|
| `INFO` | Crawl start, URL saved, skipped URL | `url`, `source_type` (on save); `url` (on skip) |
| `WARNING` | HTTP error, retry event | — |

### 2.7 Configuration (`config/rag_pipeline.toml`)

See [03_rag_05_1-configuration-reference.md §1.1](03_rag_05_1-configuration-reference.md).

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
