---
title: "WebCrawler Detail"
area: rag
tags:
  - web-crawler
  - bfs-crawl
  - conditional-get
  - local-file-ingestion
  - crawler
  - rag
related:
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_02_01_ingestion_pipeline-overview.md
  - rag_02_03_ingestion_pipeline-chunksplitter.md
  - rag_02_04_ingestion_pipeline-ingester.md
  - rag_02_07_ingestion_pipeline-utils.md
  - rag_05_01-configuration-reference.md
  - rag_04_dto-models-types.md
  - rag_05_03-logging.md
  - rag_05_04-error-handling-reference.md
---


# RAG Ingestion Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md)


## 2. WebCrawler (`scripts/rag/ingestion/crawler.py`)

### 2.1 Class Overview

`WebCrawler` performs a BFS crawl from a starting URL within the same origin up to `max_depth` levels and saves each page as a JSON file in `rag-src/`. It supports Conditional GET (ETag/Last-Modified), local files, and automatic language detection by CJK ratio per page (`--lang auto`). Concurrency is bounded by an `asyncio.Semaphore`. The crawl output payload shape is defined by `CrawlJsonPayload` in `scripts/rag/ingestion/pipeline_utils.py`.

### 2.1.1 Configuration Parameters

`max_depth` bounds the crawl's BFS traversal depth to prevent unbounded growth
in processing time, storage, and external-site load. `max_pages` bounds the
number of pages **persisted** by the crawl for the site: the BFS persists until
`max_pages` pages are written to `rag-src/` and then stops. Because 304 /
empty-content / language-rejected / failed fetches do not persist, the BFS
schedules up to `2 * max_pages` URLs per `crawl_site` call (fixed internal
scheduling headroom). A not-modified page below `max_depth` costs one extra
request for link discovery, and that request consumes scheduling headroom only,
never the persisted budget. The BFS logs a `BFS stop: scheduled=%d persisted=%d
max_pages=%d` summary line when the crawl stops. See
[Configuration Reference, `config/crawler.toml`](rag_05_01-configuration-reference.md)
for the current operational values. No historical rationale for the
specific limit values is recorded in this repository; `config/crawler.toml`'s
own inline comment states these are unvalidated heuristics.
`skip_nofollow` controls whether nofollow-marked links are excluded from
the BFS queue.

`respect_robots` opts into a per-host robots.txt policy. When enabled, the
start host's `robots.txt` is fetched and parsed once before the crawl begins,
and `LinkDiscovery` skips any URL whose path is `Disallow`ned for the crawler
user agent before it is enqueued. It defaults to disabled, so no `robots.txt`
request is issued and crawling behavior is unchanged when the flag is off. See
[Configuration Reference, `config/crawler.toml`](rag_05_01-configuration-reference.md).

### 2.1.2 `crawl_file` Behavior

`crawl_file(path, lang)` reads a local file and writes the crawl JSON to `rag-src/`. Unlike web URLs, no HTTP round-trips occur. Python files (.py) are stored as code blocks and subject to code-specific chunking. Other file types store their content directly in the `content` field.

`crawl_file` accepts `en`, `ja`, and `auto`. For `lang == "auto"`, the language is resolved by CJK-ratio detection on the file content, matching the resolution used for crawled web pages (see Language Detection below). An unsupported value other than `en`, `ja`, and `auto` is rejected (a warning is logged and nothing is written).

### 2.2 Detailed Behavior

- **Text Extraction:** Body text via `crawler_utils.extract_text()`; code blocks from BeautifulSoup4 `<pre>` elements.
- **Language Detection:** If the CJK ratio (Hiragana + Katakana + CJK Unified Ideographs) is at or above the threshold → `ja`; otherwise `en`. Pages shorter than the minimum detection length use the hint language. `--lang auto` always performs automatic detection, with `en` as fallback.
- **Idempotency:** A `visited` set prevents duplicate fetching of the same URL within a single execution.
- **Conditional GET:** Reads `documents.etag` / `documents.last_modified` from SQLite and sends `If-None-Match` / `If-Modified-Since`. A 304 response is neither extracted nor persisted. When the page's depth is below `max_depth`, the page is fetched once more without validators so that its links are still discovered, which costs one extra request per unchanged page; at the depth limit no second request is made. A failed fetch is logged separately and discovers nothing.
- **Robots.txt Policy:** Opt-in via `respect_robots`. When enabled, the start host's `robots.txt` is fetched once before the crawl and disallowed paths are filtered at enqueue time, so external crawls respect the target site's robots policy.
- **Redirect Handling:** Automatic redirect following is off (`httpx.AsyncClient` is built with `follow_redirects=False`); `fetch_html` follows redirects hop by hop, allowing only the start host (plus a single http-to-https upgrade) when `skip_external` is on and otherwise requiring every non-start host to resolve to a public address. A refused hop (cross-origin, loopback, link-local, reserved, multicast, unspecified, or a downgrade) is logged distinctly and enqueues nothing. An accepted page is persisted under its final URL and marked visited, so a redirected page is looked up under the requested URL on the next run and re-fetched by the freshness check. The address check resolves the host before the request but the resolution is not pinned to the connection, so a DNS-rebinding attacker is not fully excluded.

#### Local File Injection

##### Generating Freshness Data (Note on Responsibility Boundaries)

`crawl_file()` only calculates the mtime (ISO string) and SHA-256 hash of the file content and stores them in the `last_modified` and `etag` fields of the crawl payload; it does not perform any skip/decision logic. The JSON payload is always output unconditionally. The URL is stored as `file://{absolute_path}`.

Decisions on whether to skip or re-ingest are made by `DocumentManager` (`handle_existing_document()`, `scripts/rag/ingestion/document_manager.py`), NOT by `WebCrawler`.

| Condition | Decision (`DocumentManager` performs) |
|---|---|
| `etag` (SHA-256) is identical | Skip — Content has not changed |
| `etag` is different | Automatic re-ingestion (deletes old record and re-embeds) |
| No `etag` in DB | Re-ingestion (conservative decision) |

For local files, the `etag` column contains the hex digest of the SHA-256. Since `file://` URLs do not have HTTP ETags, collisions do not occur. Using `--force` bypasses the hash check and always triggers re-ingestion. For the operator-facing procedure, see [rag_05_06-local-file-re-ingestion.md](rag_05_06-local-file-re-ingestion.md).

This separation exists for two reasons: (1) **separation of concerns** — `crawl_file()` / `CrawlPersister.save()` handles I/O and metadata calculation (mtime, SHA-256), while `DocumentManager` handles business-logic decisions based on those values; (2) **testability** — each concern can be tested independently (calculation logic without a database, decision logic without file I/O), and the freshness-decision policy can evolve (e.g. changing the skip/re-ingest rule) without touching crawl-time file reading.

#### Comparison: Web vs. Local Injection

| Aspect | Web (HTTP) | Local Files (`file://`) |
|---|---|---|
| Freshness Basis | ETag / Last-Modified Header | File mtime / SHA-256 |
| Skipping Mechanism | 304 Not Modified | Comparison of saved mtime or hash |
| Forced Re-indexing | `--force` flag | `--force` flag |

### 2.3 CLI Arguments

Run `uv run python scripts/rag/ingestion/crawler.py --help` for the current argument
list.

### 2.4 Output JSON Format

`read_crawl_json()` (`scripts/rag/ingestion/pipeline_utils.py`) is the canonical
reader for crawl-stage JSON artifacts. A crawl artifact requires exactly its
defined key set — a missing key or an invalid field type raises
`ChunkFormatError` (see [rag_05_04-error-handling-reference.md](rag_05_04-error-handling-reference.md)).
For the full Required/Nullable/Conditional classification of these fields, see the
canonical crawl/chunk artifact-field contract table in
[rag_02_03_ingestion_pipeline-chunksplitter.md](rag_02_03_ingestion_pipeline-chunksplitter.md).
See also [rag_04_dto-models-types.md](rag_04_dto-models-types.md) for
the `ChunkDocument` DTO this reader returns.

### 2.5 Error Handling

See [rag_05_04-error-handling-reference.md](rag_05_04-error-handling-reference.md)'s
"Crawler" section for HTTP-failure retry, per-URL exception, and language-mismatch
handling. (The short-text hint-language fallback is covered in section 2.2's
"Language Detection" bullet, not an error case.)

### 2.6 Logging

See [rag_05_03-logging.md](rag_05_03-logging.md) for details.

### 2.7 Configuration (`config/crawler.toml`)

See [rag_05_01-configuration-reference.md, `config/crawler.toml`](rag_05_01-configuration-reference.md).


## Keywords

- web-crawler
- bfs-crawl
- conditional-get
- local-file-ingestion
- crawler
- rag
