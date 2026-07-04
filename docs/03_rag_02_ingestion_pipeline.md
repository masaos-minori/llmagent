# RAG Ingestion Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_configuration_and_operations.md](03_rag_05_configuration_and_operations.md)

---

## 1. Execution Guide

### Prerequisites

```bash
curl -s http://127.0.0.1:8003/health   # confirm embed-llm is running
```

### Step 1: Crawl

```bash
# All target_urls from config/rag_pipeline.toml
nohup uv run python scripts/rag/ingestion/crawler.py > logs/crawl.log 2>&1 &
tail -f logs/crawl.log

# Single URL (with per-page language auto-detection)
uv run python scripts/rag/ingestion/crawler.py --url "https://ziglang.org/documentation/master/" --lang en

# Multiple URLs (same --lang applied to all)
uv run python scripts/rag/ingestion/crawler.py \
    --url "https://ziglang.org/documentation/master/" \
          "https://zig.guide/" \
    --lang en

# Per-page CJK-ratio language detection
uv run python scripts/rag/ingestion/crawler.py --url "https://example.com/page" --lang auto
```

# Load targets (http:// and file://) from a TOML file
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml

The targets TOML file format:
```toml
target_urls = [
    ["https://ziglang.org/documentation/master/", "en"],
    ["file:///opt/llm/scripts/rag/ingestion/crawler.py", "en"],
]
```

**Note:** All file paths (`rag_src_dir`) are resolved from `config/rag_pipeline.toml`. Production default: `/opt/llm/rag-src/`.

### Step 2: Chunk split

```bash
# All unprocessed .json files in {rag_src_dir}/
uv run python scripts/rag/ingestion/chunk_splitter.py

# Single file only (path relative to rag_src_dir)
uv run python scripts/rag/ingestion/chunk_splitter.py --file /opt/llm/rag-src/20240101120000-ziglang.json

# Regenerate existing chunks
uv run python scripts/rag/ingestion/chunk_splitter.py --force
```

### Step 3: Embed and store

```bash
# Confirm embed-llm is running
curl -s http://127.0.0.1:8003/health

uv run python scripts/rag/ingestion/ingester.py

# Force re-register existing URLs
uv run python scripts/rag/ingestion/ingester.py --force
```

### File lifecycle

| Path | Created by | Format |
|---|---|---|
| `{rag_src_dir}/yyyymmddhhmmss-{slug}.json` | `crawler.py` | JSON (url, title, lang, fetched_at, content, code_blocks, etag, last_modified, schema_version, artifact_type [ingestion-only], created_by) |
| `{rag_src_dir}/chunk/{stem}-{idx:04d}.json` | `chunk_splitter.py` | JSON (url, title, lang, source_file, chunk_index, chunk_type, content, normalized_content, etag, last_modified, schema_version, artifact_type [ingestion-only], created_by, chunking_strategy) |
| `{rag_src_dir}/registered/{stem}-{idx:04d}.json` | `ingester.py` (moved from chunk/) | Same as chunk file |

> **Artifact format note:** All `.json` files listed above contain JSON payloads.
> Always parse with `orjson.loads()` or `json.loads()`. To inspect a file:
> ```
> python -c "import orjson; print(orjson.loads(open('FILE', 'rb').read()))"
> ```

Production config: `rag_src_dir = "/opt/llm/rag-src"`. The default value `rag-src` is used only when no config is present.

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

**Class-level constants**

| Constant | Description |
|---|---|
| `_USER_AGENT` | `"Mozilla/5.0 (compatible; RAG-bot/1.0; +local)"` |
| `_HEADERS` | Shared headers dict: User-Agent, Accept-Language (`ja,en;q=0.9`), Accept-Encoding (`gzip, deflate`), Connection (`keep-alive`) |

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | Load `rag_pipeline.toml`; init httpx.AsyncClient |
| `crawl` | `async (targets: list[tuple[str, str]] \| None = None) -> None` | Crawl all given targets, or config target_urls when targets is None |
| `crawl_site` | `async (start_url: str, hint_lang: str) -> None` | Async BFS crawl within the same origin up to max_depth levels via asyncio.Semaphore concurrency and FIRST_COMPLETED loop |
| `crawl_file` | `(path: Path, lang: str) -> int` | Save a local file as a crawl result JSON in rag-src/; .py files stored as code blocks; returns 1 on success, 0 on failure |

**Private methods**

| Method | Signature | Description |
|---|---|---|
| `_get_conditional_headers` | `(url: str) -> dict[str,str]` | Return If-None-Match/If-Modified-Since headers from SQLite |
| `_make_crawl_filepath` | `(url: str) -> Path` | Generate output path in yyyymmddhhmmss-{slug}.json format |
| `_fetch_html_async` | `async (url: str, client: httpx.AsyncClient, extra_headers: dict[str, str] \| None = None) -> tuple[str, str \| None, str \| None] \| None` | Fetch HTML with optional conditional request headers; returns None on 304 Not Modified or retry exhaustion; raises on other HTTP errors after retries |
| `_extract_code_blocks` | `(soup: BeautifulSoup) -> list[str]` | Extract <pre> blocks, remove from DOM |
| `_extract_content` | `(html: str, url: str) -> tuple[str,str,list[str]]` | Return (title, body text, code blocks) |
| `_save_crawl_file` | `(url, title, lang, content, code_blocks, etag\|None, last_modified\|None) -> Path` | Save crawl results as JSON to rag-src/ |
| `_fetch_and_extract_async` | `async (url: str, client: httpx.AsyncClient, extra_headers: dict[str, str] \| None = None) -> tuple[str,str,str,list[str],str\|None,str\|None]\|None` | Fetch HTML and extract content; returns None when unavailable or 304 Not Modified; returns (html, title, text, code_blocks, etag, last_modified) on success |
| `_enqueue_links` | `(html: str, current_url: str, start_url: str, depth: int, queue: asyncio.Queue) -> None` | Parse links from HTML and put URLs into the BFS queue; nofollow/external filtering applies; dedup happens at dequeue time |
| `_resolve_lang` | `(text: str, hint_lang: str) -> str` | Determine page language; 'auto' uses CJK-ratio detection with 'en' fallback for short/inconclusive texts; returns a _SUPPORTED_LANGS value |
| `_drain_queue_to_tasks` | `(queue: asyncio.Queue, visited: set[str], start_url: str, hint_lang: str, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> set[asyncio.Task]` | Dequeue all pending URLs and create fetch tasks for unvisited ones; visited check is safe because no await occurs between check and add |
| `_should_enqueue_link` | `(a_tag: Tag, current_url: str, start_url: str) -> bool` | Check if a link should be enqueued based on nofollow and cross-origin rules; skips rel="nofollow" links when skip_nofollow=True; skips cross-origin links when skip_external=True |
| `_process_crawl_url_async` | `async (url: str, depth: int, start_url: str, hint_lang: str, queue: asyncio.Queue, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> None` | Fetch, extract, save one URL and enqueue its outbound links; semaphore caps concurrency; crawl_delay throttles; ETag/Last-Modified enable 304 skip |

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
| `max_depth` | 6 | Maximum BFS crawl depth (URL hops from seed URL) |
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

`_get_or_create_document()` in the ingester performs a freshness check for
`file://` URLs before deciding to skip or re-ingest:

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

See [03_rag_05_configuration_and_operations.md §1.1](03_rag_05_configuration_and_operations.md).

---

## 3. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`)

### 3.1 Class overview

`ChunkSplitter` — splits `rag-src/*.json` files into chunks by language and content type;
saves to `rag-src/chunk/`. Idempotent: skips if `{stem}-0000.json` sentinel exists (`--force` overrides).

**Module-level constants**

| Constant | Value | Description |
|---|---|---|
| `MIN_HEADING_LINES_FOR_MARKDOWN` | 2 | Minimum heading lines to trigger heuristic Markdown detection for non-.md files |
| `MARKDOWN_HEADING_RE` | `r"^#{1,6}"` | Regex pattern for matching Markdown headings (1-6 levels) |

**Typed dicts**

| TypedDict | Purpose |
|---|---|
| `CrawlFilePayload` | Typed dict for crawl output JSON files (url, title, lang, content, code_blocks required; etag, last_modified optional via NotRequired) |
| `ChunkOutputPayload` | Typed dict for chunk output JSON files (schema_version, artifact_type, created_by, url, title, lang, source_file, chunk_index, chunk_type, content required; normalized_content optional via NotRequired) |
| `ChunkMetadata` | Optional metadata dict for ** spreading into output payload (total=False); all fields optional including url, title, lang, etag, last_modified, source_file, chunking_strategy |

**Inheritance**

`ChunkSplitter` inherits from both `ChunkEnglishMixin` and `ChunkJapaneseMixin` via multiple inheritance.
Method resolution order: `ChunkSplitter → ChunkEnglishMixin → ChunkJapaneseMixin → object`.
The `_chunk_english` method is called first in MRO for English text; Sudachi-based `_chunk_japanese` is called for Japanese text.

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(config: dict \| None = None) -> None` | Load `rag_pipeline.toml`; init Sudachi tokenizer (SplitMode.C, `core` dict) |
| `process_all` | `(target: Path \| None = None, force: bool = False) -> int` | Process all *.json files in rag-src/ (or a single target); returns total chunks written |
| `process_file` | `(src_path: Path, force: bool = False) -> int` | Read a crawler JSON file, split into chunks, and write to chunk_dir; returns chunk count; skips already-chunked files when force=False |

**Private methods**

| Method | Signature | Description |
|---|---|---|
| `_chunk_code` | `(code: str) -> list[str]` | Split a code block at blank lines (function/class boundaries); not subject to stopword removal or morphological analysis |
| `_read_source_data` | `(src_path: Path) -> ChunkDocument \| None` | Read and parse a JSON crawl file; returns ChunkDocument or None on failure |
| `_build_chunk_list` | `(data: ChunkDocument) -> list[tuple[str, str, str]]` | Extract content from a crawl record and split into (chunk_type, content, normalized_content) triples |
| `_build_text_triples` | `(data: ChunkDocument, lang: str, content: str) -> list[tuple[str, str, str]]` | Build text triples from content; delegates to markdown/English/Japanese chunkers |
| `_build_code_triples` | `(code_blocks: list[str]) -> list[tuple[str, str, str]]` | Build code triples from each code block independently |
| `_write_chunk_files` | `(chunks: list[tuple[str, str, str]], data: ChunkDocument, src_path: Path, chunking_strategy: str = "text") -> int` | Write (chunk_type, content, normalized_content) triples to chunk_dir; returns written count |
| `_extract_chunk_metadata` | `(data: ChunkDocument, src_path: Path, chunking_strategy: str) -> dict[str, object]` | Extract document-level metadata shared across all chunk files |
| `_collect_targets` | `(target: Path \| None) -> list[Path]` | Return source files to process; delegates to pipeline_utils |
| `_chunk_markdown_by_heading` | `(text: str) -> list[str]` | Split text at Markdown headings (# through ######); sections exceeding md_snippet_max_chars are further split via sentence-level chunking |
| `_is_markdown_source` | `(data: ChunkDocument \| ChunkJsonRaw) -> bool` | Return True when source should use heading-based snippet chunking; .md/.markdown/.mdx files always use heading chunking regardless of md_index_enable; non-.md files use heuristic detection (≥2 heading lines) only when md_index_enable=true |
| `_build_chunk_payload` | `(metadata: ChunkMetadata, idx: int, chunk_type: str, chunk_content: str, norm_content: str \| None) -> dict[str, object]` | Build a single chunk JSON payload from shared metadata and chunk-specific fields; includes schema_version, artifact_type, created_by |

### 3.1.1 Markdown heading chunking configuration

| Parameter | Default | Description |
|---|---|---|
| `md_index_enable` | False | Enable heuristic Markdown detection for non-.md files |
| `md_snippet_max_chars` | 600 | Max characters per markdown heading section before falling back to sentence-level chunking |

### 3.1.2 Chunking parameters (shared with crawler)

| Parameter | Default | Description |
|---|---|---|
| `min_chunk` | 40 | Minimum chunk character count; chunks below this are discarded as noise |
| `max_chunk` | 500 | Maximum chunk character count; longer text is split |
| `chunk_overlap` | 50 | Sliding window chunk overlap (chars); prepends this many chars from previous chunk tail; 0 = disabled |
| `en_stopwords` | — | English stop words excluded from chunking (see config/rag_pipeline.toml) |
| `ja_stop_pos` | — | Sudachi part-of-speech categories treated as stop words in Japanese (see config/rag_pipeline.toml) |

### 3.1.3 _is_markdown_source behavior

URLs ending with `.md`, `.markdown`, or `.mdx` always use heading chunking regardless of `md_index_enable`.
Non-`.md` files use heuristic detection (≥2 heading lines in content) only when `md_index_enable=true`.

### 3.1.4 _chunk_markdown_by_heading behavior

Split text at Markdown headings (# through ######); sections exceeding `md_snippet_max_chars` characters are further split via `_chunk_english` sentence-level chunking.

### 3.2 Splitting strategies

| Content type | Strategy |
|---|---|
| Japanese text | Sudachi SplitMode.C morphological analysis; `(original_sentence, normalized_form_space_joined)` pairs |
| English text | Regex sentence boundary split (`(?<=[.!?])\s+`); merges short paragraphs, discards chunks below min_chunk after stopword removal |
| `.md`/`.markdown`/`.mdx` URL | Heading boundary split (`#`/`##`/`###`); always applied regardless of `md_index_enable` |
| Non-`.md` content with ≥2 heading lines | Heading boundary split; applied only when `md_index_enable=true` |
| Code blocks | Blank-line split (language-agnostic); not subject to stopword removal or morphological analysis |

- Japanese chunks: `content` = original text, `normalized_content` = Sudachi normalized forms
- English/code chunks: `normalized_content = null`
- `chunk_type`: `"text"` or `"code"`
- `chunking_strategy`: `"text"` or `"heading"`

### 3.3 CLI arguments

| Argument | Description | Default |
|---|---|---|
| `--file PATH` | Process single file only (path relative to rag_src_dir) | all unprocessed `.json` in rag-src/ |
| `--force` | Regenerate existing chunks (overrides sentinel check) | false |

### 3.4 Output JSON format (`rag-src/chunk/{stem}-{idx:04d}.json`)

```json
{
  "schema_version": "1",
  "artifact_type": "chunk",
  "created_by": "chunk_splitter",
  "url": "https://example.com/page",
  "title": "Page title",
  "lang": "ja",
  "source_file": "20240101120000-example.json",
  "chunk_index": 0,
  "chunk_type": "text",
  "chunking_strategy": "text",
  "content": "original chunk text",
  "normalized_content": "normalized form (JA only; null for EN/code)",
  "etag": "optional-etag",
  "last_modified": "optional-http-date"
}
```

The `source_file` field retains the original `.json` extension from the crawler output filename.
All fields from `ChunkMetadata` TypedDict (total=False) are included via `**metadata` spread in `_build_chunk_payload`.

### 3.5 Error handling

| Case | Action |
|---|---|
| Sudachi tokenize error | Catch; return `""`; skip that chunk |
| File-level failure | `ERROR` log (with traceback); continue to next file |
| Existing chunk (`{stem}-0000.json`) | Skip unless `--force` |

### 3.6 Logging

- **File:** `/opt/llm/logs/chunk.log` + stderr
- **Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| Level | Timing |
|---|---|
| `INFO` | Files processed, chunks generated, skipped files (with URL) |
| `WARNING` | Sudachi error |
| `ERROR` | File read error, file-level failure (with traceback) |

### 3.7 Configuration

See [03_rag_05_configuration_and_operations.md §1.1](03_rag_05_configuration_and_operations.md).

---

## 4. RagIngester (`scripts/rag/ingestion/ingester.py`)

### 4.1 Class overview

`RagIngester` — reads chunk files, generates embeddings via `embed-llm` (port 8003),
and upserts to SQLite (`documents` / `chunks` / `chunks_vec`). Moves processed chunks to
`rag-src/registered/`.

**Dataclass**

| Class | Purpose |
|---|---|
| `IngestUrlResult` | Per-URL ingestion outcome returned by `ingest_url_group()`; fields: `url`, `n_success`, `n_failed`, `skipped`, `n_embed_failed` (default 0) |

**Module-level constants**

| Constant | Value | Description |
|---|---|---|
| `_VALID_LANGS` | `frozenset({"en", "ja"})` | Accepted lang values enforced by the documents.lang CHECK constraint |

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | Merge `common.toml` + `rag_pipeline.toml`; init `httpx.Client` |
| `ingest_all` | `(force: bool = False, on_ingest_complete: Callable[[], None] \| None = None) -> RagConsistencyReport \| None` | Group chunk files by URL; call `_process_url_groups` for each. Returns consistency report or None if the post-ingest consistency check failed (rare failure case when DB errors occur during the check); also returns None when no chunk files exist |
| `ingest_url_group` | `(doc_mgr: DocumentManager, db: SQLiteHelper, url: str, chunk_files: list[Path], force: bool) -> IngestUrlResult` | Process one URL group in ascending chunk_index order; moves files to registered/ after processing including on skip; returns `{n_success, n_failed, n_embed_failed, skipped}` |
| `close` | `() -> None` | Close the underlying `httpx.Client` |
| `__del__` | `() -> None` | Safety cleanup: close httpx.Client if not already closed (handles missing explicit close) |

**Private methods**

| Method | Signature | Description |
|---|---|---|
| `_get_embedding` | `(text: str) -> list[float] \| None` | Return embedding vector; validates dimension against embedding_dims config. Returns None on empty input, network failure, or dimension mismatch. Embedding is also validated as a non-empty list. |
| `_validate_artifact` | `(payload: ChunkJsonRaw, expected_type: str, *, strict: bool = False) -> bool` | Validate artifact_type field (ingestion-only metadata); lenient mode accepts missing artifact_type; strict mode requires schema_version, artifact_type, and created_by. Returns True when validation passes, False when it fails. |
| `_get_or_create_document` | `(doc_mgr: DocumentManager, db: SQLiteHelper, url: str, title: str, lang: str, force: bool, etag\|None, last_modified\|None, chunking_strategy: str, fetched_at\|None) -> int \| None` | Register URL in documents; returns doc_id or None when already registered. Handles existing document detection via DocumentManager (see §4.10). |
| `_insert_chunk` | `(db: SQLiteHelper, doc_id: int, idx: int, content: str, normalized_content: str \| None, embedding: list[float], chunk_type: str = "", source_file: str = "") -> None` | Insert chunk and embedding vector; chunks_fts synced via trigger using COALESCE(normalized_content, content); embedding stored as float32 BLOB |
| `_read_chunk_json` | `(path: Path) -> ChunkJsonRaw \| None` | Read and parse chunk JSON file as a raw dict; returns None on failure |
| `_embed_and_store` | `(doc_id: int, path: Path) -> tuple[bool, bool]` | Embed one chunk and insert it using an independent DB connection; each call opens its own connection for safe parallel writes. Returns (chunk_ok, embed_ok). chunk_ok=False means total failure (parse/DB error or embed failure). embed_ok=False specifically means embedding failed (content was valid). |
| `_ingest_chunk_files` | `(doc_id: int, chunk_files: list[Path]) -> tuple[int, int, int]` | Embed and insert chunk files in parallel via ThreadPoolExecutor; returns (n_inserted, n_failed, n_embed_failed) |
| `_group_chunks_by_url` | `(chunk_files: list[Path]) -> dict[str, list[Path]]` | Group chunk files by URL read from their JSON 'url' field; skips files with missing or invalid URLs (including non-http/https/file:// schemes) |
| `_process_url_groups` | `(doc_mgr: DocumentManager, db: SQLiteHelper, url_groups: dict[str, list[Path]], force: bool) -> list[IngestUrlResult]` | Iterate over URL groups and ingest each; log exceptions without stopping |
| `_move_to_registered` | `(paths: list[Path]) -> None` | Move ingested chunk files to registered/; logs errors on file move failures |
| `_log_ingest_failure` | `(doc_id: int, path: Path, e: Exception) -> None` | Log a chunk ingestion failure with doc_id, url, source_type, stage_name structured fields |
| `_skip_result` | `(url: str) -> IngestUrlResult` | Return a skipped result for a URL |
| `_validation_failure_result` | `(url: str, chunk_files: list[Path]) -> IngestUrlResult` | Return a failure result when artifact validation fails |
| `_log_ingestion_result` | `(doc_id: int, url: str, inserted: int, total: int, failed: int, embed_failed: int) -> None` | Log the chunk ingestion result with doc_id, source_type, stage_name structured fields |
| `_validate_lang` | `(lang: str) -> bool` | Return True when lang is in _VALID_LANGS (en or ja); raises ValueError for invalid values |
| `_handle_existing_document` | `(db: SQLiteHelper, url: str, existing_doc_id: int, force: bool, etag\|None, last_modified\|None, fetched_at\|None) -> bool` | **Moved to DocumentManager** — see §4.10 |
| `_handle_existing_file` | `(db: SQLiteHelper, url: str, existing_doc_id: int, etag\|None, last_modified\|None) -> bool` | **Moved to DocumentManager** — see §4.10 |

### 4.2 Behavior details

- **E5 prefix:** prepend `passage: {text}` before embedding (vs `query: ` at query time)
- **Vector encoding:** `struct.pack(f"<{N}f", *values)` → little-endian float32 BLOB
- **Parallel embed:** `ThreadPoolExecutor(embed_workers)` per URL group;
  each thread uses an independent `SQLiteHelper().open()`
- **WAL mode:** `PRAGMA journal_mode=WAL` for concurrent read/write safety
- **Upsert (`--force`):** delete in order `chunks_vec` → `chunks` → `documents`, then re-INSERT; `chunking_strategy` is preserved from the source file

### 4.2.1 Deletion order invariant

The following deletion order is a design invariant — it must be maintained by all code paths that delete document records:

```
chunks_vec (first) → chunks → documents
```

**Reason:** `chunks_vec` is a sqlite-vec virtual table with no foreign key constraint pointing to `chunks`. Deleting `chunks` first would leave orphaned vector records. The order must be strictly enforced in every code path:

1. Delete `chunks_vec` rows for the document's chunk_ids
2. Delete `chunks` rows (triggers auto-sync `chunks_fts`)
3. Delete `documents` row

**Affected code paths:**
- `RagIngester._delete_existing_document()` — `delete_document_chain()`
- `RagMaintenanceService.delete_document()` — MCP tool path
- Both must follow the same order to prevent orphaned vector records
- **Idempotency:** skip URL if already in `documents`; still UPDATE `etag`/`last_modified` via skip-path guard (see below); `chunking_strategy` is not updated during skip
- **Embedding dimension validation:** `_get_embedding()` validates embedding dimension against `embedding_dims` config (default 384); returns None on mismatch
- **Skip-path stale guard:** `_update_etag()` compares incoming `fetched_at` (chunk payload) against stored `documents.fetched_at`; if incoming < stored the update is skipped (newer crawl wins — prevents stale chunk files from overwriting fresher metadata). Missing `fetched_at` (legacy chunks without a freshness signal) uses fill-only semantics: `COALESCE(etag, ?)` — only populates the stored field if currently NULL; never overwrites a non-NULL value. This prevents stale chunk-file metadata from replacing fresher values stored by a more recent crawl.
- **Embed failure tracking:** `_embed_and_store()` returns `(chunk_ok, embed_ok)` tuple;
  `n_embed_failed` counts embedding-specific failures separately from parse/DB errors
- **Local file unchanged detection:** `_is_file_unchanged()` compares SHA-256 etags for `file://` URLs

### 4.3 CLI arguments

| Argument | Description | Default |
|---|---|---|
| `--force` | Delete existing document/chunks/chunks_vec records and re-embed; always re-ingests regardless of etag (for `file://` URLs) | false |

### 4.4 Embedding API

```
POST http://127.0.0.1:8003/embedding
Request:  {"content": "passage: {text}"}
Response: {"embedding": [float, ...]}   # 384-dim (multilingual-E5-small; config/common.toml::embedding_dims)
```

### 4.5 DB tables updated

| Table | Operation |
|---|---|
| `documents` | SELECT to check; DELETE+INSERT (`force=True`) or skip+UPDATE etag (`force=False`); stores `url`, `title`, `lang`, `etag`, `last_modified`, `chunking_strategy`, `fetched_at` |
| `chunks` | INSERT (FK → documents; ON DELETE CASCADE) |
| `chunks_vec` | INSERT BLOB vector |
| `chunks_fts` | Auto-synced by `chunks_ai` trigger (`COALESCE(normalized_content, content)`) |

### 4.6 Error handling

| Case | Action |
|---|---|
| Embed API failure | Exponential backoff retry up to `embed_retry` times (capped at 10 seconds) |
| Retry exhausted (single chunk) | `WARNING` log; skip chunk; continue |
| Invalid `lang` value | `ValueError`; skip URL group; `ERROR` log with traceback |
| `chunks_vec` delete order | Must delete `chunks_vec` first (no FK constraint on sqlite-vec virtual table) |
| Embedding dimension mismatch | `ValueError`; skip chunk; `WARNING` log |
| Artifact validation failure | `WARNING` log; skip chunk as embed failure |
| File move failure | `ERROR` log with url, source_type, stage_name structured fields |

### 4.7 Logging

- **File:** `/opt/llm/logs/ingest.log` + stderr
- **Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| Level | Timing | Structured fields |
|---|---|---|
| `INFO` | Chunks processed, DB inserts, file moves, skipped URLs | `doc_id`, `source_type`, `stage_name` (on insert); `url` (on skip) |
| `WARNING` | Embed API error, retry, embed skip | `source_type`, `stage_name` |
| `ERROR` | Chunk file read error, file move error, URL group failure (with traceback) | — |

### 4.8 ETagManager (`scripts/rag/ingestion/etag_manager.py`)

`ETagManager` — Manages ETag/Last-Modified updates for existing documents. Provides stale guard: if new_fetched_at < stored fetched_at, the incoming data is older and the existing DB values are kept. Two update modes:
- `_update_with_freshness`: Overwrite ETag/Last-Modified when freshness is proven (uses COALESCE for fetched_at)
- `_update_null_fill`: Fill NULL only; never overwrite existing values (uses COALESCE for both etag and last_modified)

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `update` | `(etag: str \| None, last_modified: str \| None, new_fetched_at: str \| None = None)` | Refresh ETag/Last-Modified for an existing document; returns early if both etag and last_modified are None |

**Private methods**

| Method | Signature | Description |
|---|---|---|
| `_is_stale_update` | `(new_fetched_at: str \| None) -> bool` | Return True when the incoming data is older than stored fetched_at; returns False when new_fetched_at is None (no freshness signal means no stale check) |

### 4.9 Configuration (`config/rag_pipeline.toml`)

| Parameter | Default | Description |
|---|---|---|
| `embed_url` | `http://127.0.0.1:8003/embedding` | Embedding API endpoint URL |
| `embed_retry` | 3 | Retry limit for embedding API failures (exponential backoff) |
| `embed_workers` | 4 | Max concurrent embed threads via ThreadPoolExecutor |
| `embedding_dims` | 384 | Expected embedding vector dimension; validated against API response |
| `strict_artifact_validation` | False | Require `schema_version`, `artifact_type`, `created_by` in chunk JSON payloads |

See [03_rag_05_configuration_and_operations.md §1.2](03_rag_05_configuration_and_operations.md).

---

## 4.10 DocumentManager (`scripts/rag/ingestion/document_manager.py`)

`DocumentManager` — Manages document lifecycle for RagIngester. Handles existing document detection, ETag updates, and post-ingestion consistency reports. Extracted from `RagIngester` to reduce class size and separate concerns.

**Module-level function**

| Function | Signature | Description |
|---|---|---|
| `delete_document_chain` | `(db: SQLiteHelper, doc_id: int) -> None` | Delete `chunks_vec` → `chunks` → `documents` in order; chunks_vec must be deleted first because it has no FK constraint to chunks |

**Class: `DocumentManager`**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(db: SQLiteHelper) -> None` | Store DB connection reference |
| `handle_existing_document` | `(url: str, existing_doc_id: int, force: bool, etag\|None, last_modified\|None, fetched_at\|None, is_file_url: Callable[[str], bool]) -> bool` | Handle an existing document; return True when the caller should skip insertion. force=False → update etag via ETagManager; file:// URLs with unchanged SHA-256 → skip; force=True → delete document chain and return False to allow re-insertion |
| `_handle_existing_file` | `(url: str, existing_doc_id: int, etag\|None, last_modified\|None) -> bool` | Handle an existing file:// document; return True when unchanged (SHA-256 match) |
| `_update_etag` | `(etag\|None, last_modified\|None, new_fetched_at\|None) -> None` | Refresh ETag/Last-Modified for an existing document (skip-case); returns early if both etag and last_modified are None; delegates to ETagManager with doc_id=0 |
| `_is_file_unchanged` | `(existing_etag\|None, existing_last_modified\|None, new_etag\|None, new_last_modified\|None) -> bool` | Return True when the file SHA-256 hash is unchanged; returns False if either etag is None |
| `delete_existing_document` | `(doc_id: int) -> None` | Delete a document and its chunks; chunks_vec removed first because it has no FK constraint to chunks |
| `check_consistency` | `(embed_failed: int, on_ingest_complete: Callable[[], None]\|None = None) -> RagConsistencyReport \| None` | Run post-ingestion consistency check and callback; returns report or None if the check failed (DB errors during the check) |

**Intent inferred from code:**
- `handle_existing_document` receives `is_file_url` as a callable instead of checking `url.startswith("file://")` directly, allowing testability with mock implementations
- `_update_etag` passes `doc_id=0` to ETagManager because the skip-path update does not need the document ID for its COALESCE logic; the document is already in the DB

**CLI entry point:**

```bash
uv run python scripts/rag/ingestion/ingester.py --force
```

## 5. Crawler Utils (`scripts/rag/ingestion/crawler_utils.py`)

### 5.1 Module overview

`crawler_utils.py` — Pure-function utilities for WebCrawler: URL helpers, content extraction, language detection, and target URL parsing. Extracted from `WebCrawler` class to keep it under 400 lines.

**Module-level constants**

| Constant | Value | Description |
|---|---|---|
| `_SUPPORTED_LANGS` | `{"en", "ja"}` | Output language codes |
| `_VALID_HINT_LANGS` | `{"en", "ja", "auto"}` | Valid hint language values |
| `_CJK_RATIO_THRESHOLD` | `0.1` | CJK character ratio threshold for Japanese classification |
| `_TARGET_URL_ENTRY_LENGTH` | `2` | Expected element count for target_urls entries |
| `MIN_TEXT_LENGTH_FOR_DETECTION` | `100` (from `rag.utils`) | Minimum text length for language detection |

**Unicode code point ranges for CJK detection**

| Constant | Range | Description |
|---|---|---|
| `_HIRAGANA_KATAKANA_START/END` | "぀"–"ヿ" | Hiragana + Katakana |
| `_CJK_UNIFIED_START/END` | "一"–"鿿" | CJK Unified Ideographs |
| `_CJK_EXT_A_START/END` | "㐀"–"䶿" | CJK Extension A |

**Public functions**

| Function | Signature | Description |
|---|---|---|
| `url_to_slug` | `(url: str) -> str` | Convert URL to filesystem-safe ASCII slug (max 80 chars); strips scheme, replaces non-alphanumeric with hyphens |
| `normalize_url` | `(url: str) -> str` | Strip fragment and trailing slash |
| `same_origin` | `(url: str, base: str) -> bool` | True if scheme + hostname match |
| `extract_text` | `(soup: BeautifulSoup) -> str` | Remove noise tags (nav, footer, aside, script, style, noscript) from soup; extract body text via Trafilatura with `include_comments=False`, `include_tables=True`, `no_fallback=False`, `target_language=None`; fall back to BS4 `get_text(separator="\n", strip=True)` |
| `detect_lang` | `(text: str) -> str \| None` | CJK ratio detection; returns 'ja' if ratio ≥ 0.1, 'en' otherwise; None for texts < 100 chars |
| `parse_target_urls` | `(target_raw: list[Any]) -> list[tuple[str,str]]` | Validate and parse target_urls config into (url, lang) tuples; raises ValueError on invalid entries |
| `parse_targets_file` | `(path: Path) -> list[tuple[str,str]]` | Parse a TOML file containing target_urls = [[url, lang], ...] pairs; raises FileNotFoundError if file not found, ValueError on parse error |

**Private functions**

| Function | Signature | Description |
|---|---|---|
| `_validate_target_url` | `(url: str) -> bool` | Return True when url has an accepted scheme (http, https, or file); unlike `rag.utils.validate_url`, this also accepts file:// URIs |
| `_is_cjk_char` | `(c: str) -> bool` | Check if a character is CJK (Hiragana, Katakana, or CJK Unified Ideograph) using Unicode code point ranges |

---

## 6. Chunk English Mixin (`scripts/rag/ingestion/chunk_english.py`)

### 6.1 Module overview

`chunk_english.py` — `ChunkEnglishMixin`: paragraph/sentence-level chunking for English text with stopword filtering and sentence boundary splitting. Mixed into `ChunkSplitter` via multiple inheritance.

**Class: `ChunkEnglishMixin`**

| Method | Signature | Description |
|---|---|---|
| `_chunk_english` | `(text: str) -> list[str]` | Split at paragraph/sentence boundaries; merges short paragraphs, discards below min_chunk after stopword removal |
| `_merge_paragraphs_en` | `(paragraphs: list[str]) -> list[str]` | Accumulate paragraphs into ≤max_chunk chunks; split oversized paragraphs at sentence boundaries |
| `_split_sentences_en` | `(text: str) -> list[str]` | Split at sentence boundaries (. ! ?); oversized sentences kept as-is |
| `_filter_stopwords_en` | `(text: str) -> str` | Remove EN stopwords (case-insensitive); return space-joined tokens |

**Inherited attributes (declared here so mypy sees them; values come from `ChunkSplitter.__init__`)**

| Attribute | Type | Description |
|---|---|---|
| `_max_chunk` | `int` | Maximum chunk size in characters |
| `_min_chunk` | `int` | Minimum chunk size in characters |
| `_en_stopwords` | `frozenset[str]` | English stopwords from config |
| `_chunk_overlap` | `int` | Overlap between chunks in characters |

**Private helper methods**

| Method | Signature | Description |
|---|---|---|
| `_flush_and_split` | `(para: str, chunks: list[str]) -> None` | Flush buffer and split oversized paragraph at sentence boundaries |
| `_flush_and_merge` | `(buf: str, para: str, chunks: list[str]) -> None` | Flush buffer and start new buffer with overlap |

**Instance attributes (set during chunking)**

| Attribute | Type | Description |
|---|---|---|
| `_buf` | `str` | Running buffer for paragraph accumulation |

---

## 7. Chunk Utils (`scripts/rag/ingestion/chunk_utils.py`)

### 7.1 Module overview

`chunk_utils.py` — Shared buffer helpers for `ChunkEnglishMixin` and `ChunkJapaneseMixin`. Provides tail-overlap buffer management and item accumulation with min/max chunk size constraints. Imported by both mixin classes and `chunk_splitter.py`.

**Public functions**

| Function | Signature | Description |
|---|---|---|
| `start_next_buf` | `(prev: str, next_item: str, sep: str, chunk_overlap: int) -> str` | Start a new accumulation buffer with optional tail-overlap from prev. When `chunk_overlap=0`, returns next_item directly. Otherwise prepends the last N characters of prev (where N = chunk_overlap) to next_item |
| `merge_text_items` | `(items: list[str], sep: str, min_chunk: int, max_chunk: int, chunk_overlap: int) -> list[str]` | Accumulate items into chunks satisfying min_chunk ≤ len ≤ max_chunk. A short tail item is merged into the last chunk instead of discarded |

**Usage in mixins:**

| Mixin | Function used | Purpose |
|---|---|---|
| `ChunkEnglishMixin` | `merge_text_items` | Paragraph/sentence accumulation with overlap |
| `ChunkJapaneseMixin` | `start_next_buf`, `merge_text_items` | Sentence pair accumulation with overlap |
| `ChunkSplitter` | `merge_text_items` | Code block accumulation (blank-line split) |

---

## 8. Chunk Japanese Mixin (`scripts/rag/ingestion/chunk_japanese.py`)

### 8.1 Module overview

`chunk_japanese.py` — `ChunkJapaneseMixin`: morphological-analysis-based chunking for Japanese text using Sudachi SplitMode.C. Includes NFKC normalization, clause boundary splitting, and buffer-based accumulation with overlap. Mixed into `ChunkSplitter` via multiple inheritance.

**Class: `ChunkJapaneseMixin`**

| Method | Signature | Description |
|---|---|---|
| `_chunk_japanese` | `(text: str) -> list[tuple[str,str]]` | Split into (original, normalized) chunk pairs via NFKC normalization, sentence splitting, and Sudachi morphological analysis |
| `_split_into_ja_sentences` | `(text: str) -> list[tuple[str,str]]` | Split at clause boundaries (。！？ and newlines); returns (original, normalized) pairs; empty pairs discarded |
| `_normalize_ja_sentence` | `(text: str) -> str` | Run Sudachi SplitMode.C analysis; return space-joined normalized content words; raises `TokenizationError` on failure |
| `_merge_ja_sentence_pairs` | `(pairs: list[tuple[str,str]]) -> list[tuple[str,str]]` | Accumulate (original, normalized) pairs into chunk pairs by original text length; applies overlap from buffer tail |

**Inherited attributes (declared here so mypy sees them; values come from `ChunkSplitter.__init__`)**

| Attribute | Type | Description |
|---|---|---|
| `_max_chunk` | `int` | Maximum chunk size in characters |
| `_min_chunk` | `int` | Minimum chunk size in characters |
| `_chunk_overlap` | `int` | Overlap between chunks in characters |
| `_ja_stop_pos` | `frozenset[str]` | Japanese stop POS tags from config (excluded from normalized output) |
| `_sd_tkn` | Any | Sudachi tokenizer instance |
| `_split_c` | Any | Sudachi SplitMode.C |
| `_orig_buf` | `str` | Running buffer for original text during merge |
| `_norm_buf` | `str` | Running buffer for normalized text during merge |
| `_result` | `list[tuple[str, str]]` | Result list during merge |

**Private helper methods**

| Method | Signature | Description |
|---|---|---|
| `_append_to_buffer` | `(orig: str, norm: str) -> None` | Append sentence to the running buffer |
| `_emit_and_start_new` | `(orig: str, norm: str) -> None` | Emit buffer as chunk and start new buffer with overlap |
| `_reset_buffer` | `(orig: str, norm: str) -> None` | Discard buffer and start fresh from this sentence |
| `_merge_tail_into_last` | `(self) -> None` | Merge short tail into the last chunk to avoid losing content |

---

## 9. Pipeline Utils (`scripts/rag/ingestion/pipeline_utils.py`)

### 9.1 Module overview

`pipeline_utils.py` — Shared I/O utilities for the RAG ingestion pipeline: chunk JSON reading with validation, source file collection, and processing sentinel checks. Provides `ChunkJsonRaw` dataclass for raw chunk/crawl JSON payload fields.

**Module-level constants**

| Constant | Value | Description |
|---|---|---|
| `logger` | `Logger(__name__, "/opt/llm/logs/pipeline.log")` | Pipeline logging instance |

**TypedDict**

| TypedDict | Purpose |
|---|---|
| `ChunkJsonRaw` | Raw chunk JSON payload fields; required: `url`, `content`; optional: `title`, `lang`, `code_blocks`, `etag`, `last_modified`, `fetched_at`, `chunking_strategy`, `normalized_content`, `chunk_index`, `source_file`, `chunk_type`, `artifact_type`, `schema_version`, `created_by` |

**Private functions**

| Function | Signature | Description |
|---|---|---|
| `_read_chunk_json_raw` | `(path: Path) -> ChunkJsonRaw \| None` | Read and parse chunk JSON as raw dict; returns None on any failure (OSError, JSONDecodeError, missing url/content, or empty url/content values) |
| `_get_str` | `(data: ChunkJsonRaw, key: str) -> str \| None` | Get a string value from data; returns None if not a string |
| `_get_list` | `(data: ChunkJsonRaw, key: str) -> list[str] \| None` | Get a list value from data; returns None if not a list |
| `_get_str_or_none` | `(data: ChunkJsonRaw, key: str) -> str \| None` | Get a string value from data; returns the value if it's a string, otherwise None (same behavior as `_get_str`) |
| `_get_str_with_default` | `(data: ChunkJsonRaw, key: str, default: str) -> str` | Get a string value with default fallback; returns default if the key is missing or not a string |
| `_get_int_with_default` | `(data: ChunkJsonRaw, key: str, default: int) -> int` | Get an integer value with default fallback; handles None values and non-integer values (ValueError/TypeError) |

**Public functions**

| Function | Signature | Description |
|---|---|---|
| `read_json_file` | `(path: Path) -> ChunkDocument` | Read and parse JSON file into ChunkDocument; raises ChunkFormatError on failure |
| `collect_source_files` | `(rag_src_dir: Path, target: Path \| None = None) -> tuple[list[Path], list[SkipInfo]]` | Return (files_to_process, skipped); if target is given and exists, returns [target]; if target doesn't exist returns empty list with SkipInfo; otherwise glob *.json from rag_src_dir |
| `is_already_processed` | `(sentinel_path: Path, force: bool) -> bool` | True when sentinel file exists and force=False (skip signal for chunk_splitter) |

**read_json_file field mapping**

| JSON field | ChunkDocument field | Fallback |
|---|---|---|
| `url` | `url` | (required, no fallback) |
| `title` | `title` | `""` |
| `lang` | `lang` | `"en"` |
| `content` | `content` | (required, no fallback) |
| `code_blocks` | `code_blocks` | `[]` |
| `etag` | `etag` | `None` |
| `last_modified` | `last_modified` | `None` |
| `chunking_strategy` | `chunking_strategy` | `"text"` |
| `normalized_content` | `normalized_content` | `None` |
| `chunk_index` | `chunk_index` | `0` |
| `source_file` | `source_file` | `""` |
| `chunk_type` | `chunk_type` | `""` |

---

## 10. Shared Utilities (`scripts/rag/utils.py`)

```python
from rag.utils import (
    cosine_sim,
    floats_to_blob,
    normalize_unicode,
    sanitize_document,
    sanitize_document_full,
    validate_url,
)
```

| Function / Constant | Signature | Returns | Description |
|---|---|---|---|
| `normalize_unicode` | `(text: str) -> str` | `str` | NFKC normalization; converts full-width alphanumerics and variant chars |
| `floats_to_blob` | `(values: list[float]) -> bytes` | `bytes` | Little-endian float32 BLOB; sqlite-vec `MATCH` operator format. Raises TypeError/ValueError on invalid input |
| `validate_url` | `(url: str) -> bool` | `bool` | `True` if `http`/`https` scheme with non-empty netloc |
| `cosine_sim` | `(a: list[float], b: list[float]) -> float` | `float` | Cosine similarity; returns 0.0 when either vector has zero magnitude. Used by SemanticCache |
| `sanitize_document` | `(text: str) -> str` | `str` | Remove prompt injection patterns (e.g., "ignore instructions", "[SYSTEM OVERRIDE]"); replaces matches with `[REMOVED]` |
| `sanitize_document_full` | `(text: str) -> SanitizeResult` | `SanitizeResult` | Same as sanitize_document but returns audit trail (detected patterns, was_sanitized flag); returns SanitizeResult dataclass with `was_sanitized: bool`, `patterns: list[str]`, `sanitized_text: str` |

**Constants:**

| Constant | Value | Description |
|---|---|---|
| `MIN_TEXT_LENGTH_FOR_DETECTION` | `100` | Minimum text length for language detection; pages shorter than this use hint language; also used by `detect_lang()` in crawler_utils |
| `LOG_KEY_URL` | `"url"` | Structured log field key for URL |
| `LOG_KEY_DOC_ID` | `"doc_id"` | Structured log field key for document ID |
| `LOG_KEY_CHUNK_ID` | `"chunk_id"` | Structured log field key for chunk ID |
| `LOG_KEY_SOURCE_TYPE` | `"source_type"` | Structured log field key for source type (http/file) |
| `LOG_KEY_STAGE_NAME` | `"stage_name"` | Structured log field key for stage name |

**Prompt injection patterns (`_INJECTION_PATTERNS`):**

| Pattern | Regex | Description |
|---|---|---|
| Ignore instructions | `(?i)(ignore\s+(?:(?:all\|previous)\s+)*instructions?)` | Catch "ignore all instructions", "ignore previous instructions" etc. |
| System prefix | `(?i)(system\s*:\s*)` | Catch "system:" prefix |
| SYSTEM OVERRIDE | `(?i)\[SYSTEM\s*OVERRIDE\]` | Catch "[SYSTEM OVERRIDE]" |
| Disregard instructions | `(?i)(disregard\s+(?:(?:all\|prior\|previous)\s+)*instructions?)` | Catch "disregard all instructions" etc. |
| New instructions | `(?i)(new\s+instructions?:)` | Catch "new instructions:" etc. |

**Structured log keys (RAG lifecycle tracing):**

| Key | Value | Used by |
|---|---|---|
| `url` | URL string | crawler, ingester |
| `doc_id` | INTEGER document ID | ingester |
| `chunk_id` | INTEGER chunk ID | ingester (via chunks_vec insert) |
| `source_type` | `"http"` / `"file"` | crawler, ingester |
| `stage_name` | Script name ("ingester") | ingester |

**Used by:**

| Script | Functions used |
|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | `normalize_unicode` |
| `scripts/rag/ingestion/chunk_japanese.py` | `normalize_unicode` |
| `scripts/rag/ingestion/ingester.py` | `floats_to_blob`, `validate_url` |
| `scripts/rag/ingestion/crawler.py` | `validate_url` |
| `scripts/rag/pipeline.py` | `sanitize_document`, `floats_to_blob` |
| `scripts/rag/cache.py` | `cosine_sim` |

---

## 11. FTS5 Implementation Notes

### FTS5 / LLM content separation

Japanese chunks store two versions:
- `chunks.content` — original text (passed to LLM as context)
- `chunks.normalized_content` — Sudachi `normalized_form()` space-joined (used for FTS5 indexing)

The `chunks_ai` / `chunks_au` / `chunks_ad` triggers write `COALESCE(normalized_content, content)`
to `chunks_fts`. English and code chunks have `normalized_content = NULL`, so FTS5 uses `content` directly.

### FTS5 query tokenization

`scripts/rag/repository.py` `_build_fts_query()` processes Japanese queries via `_build_fts_tokens_ja()`:
extracts `normalized_form()` for nouns, verbs, and adjectives only (excludes particles, auxiliaries).
English queries use regex `[a-zA-Z0-9]+` tokenization. Sudachi tokenizer is lazily initialized in
`_SudachiTokenizer` class (zero import-time side effects).

### FTS5 query token limit

Maximum tokens in an FTS5 query: `_MAX_FTS_TOKENS = 20` (`repository.py:29`).
Excess tokens are silently truncated to prevent query explosion. Double-quotes (FTS5 metachar)
and whitespace are stripped from each token; empty tokens are dropped. If no valid tokens remain,
returns `'""'` (empty FTS5 query).
