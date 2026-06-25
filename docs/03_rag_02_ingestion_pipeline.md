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
| `{rag_src_dir}/yyyymmddhhmmss-{slug}.json` | `crawler.py` | JSON (url, title, lang, fetched_at, content, code_blocks, etag, last_modified, schema_version, artifact_type, created_by) |
| `{rag_src_dir}/chunk/{stem}-{idx:04d}.json` | `chunk_splitter.py` | JSON (url, title, lang, source_file, chunk_index, chunk_type, content, normalized_content, etag, last_modified, schema_version, artifact_type, created_by, chunking_strategy) |
| `{rag_src_dir}/registered/{stem}-{idx:04d}.json` | `ingester.py` (moved) | Same as chunk file |

> **Artifact format note:** All `.json` files listed above contain JSON payloads.
> Always parse with `orjson.loads()` or `json.loads()`. To inspect a file:
> ```
> python -c "import orjson; print(orjson.loads(open('FILE', 'rb').read()))"
> ```

Production config: `rag_src_dir = "/opt/llm/rag-src"`. The default value `rag-src` is used only when no config is present.

---

## 2. WebCrawler (`scripts/rag/ingestion/crawler.py`)

### 2.1 Class overview

`WebCrawler` — BFS-crawls from a start URL within the same origin; saves each page as
a JSON file in `rag-src/`. Supports conditional GET (ETag/Last-Modified), local files,
and per-page CJK-ratio language auto-detection (`--lang auto`).

**Class-level constants**

| Constant | Description |
|---|---|
| `_USER_AGENT` | `"Mozilla/5.0 (compatible; RAG-bot/1.0; +local)"` |
| `_HEADERS` | Shared headers dict: User-Agent, Accept-Language (ja,en;q=0.9), Accept-Encoding, Connection |

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | Load `rag_pipeline.toml`; init httpx.AsyncClient |
| `crawl` | `async (targets: list[tuple[str,str]] \| None = None) -> None` | Crawl all targets; uses config `target_urls` if None |
| `crawl_site` | `async (start_url: str, hint_lang: str) -> None` | Single-origin BFS crawl with asyncio.Semaphore concurrency |
| `crawl_file` | `(path: Path, lang: str) -> int` | Save local file as crawler JSON; returns 1 on success, 0 on failure |

**Private methods**

| Method | Signature | Description |
|---|---|---|
| `_get_conditional_headers` | `(url: str) -> dict[str,str]` | Return If-None-Match/If-Modified-Since headers from SQLite |
| `_make_crawl_filepath` | `(url: str) -> Path` | Generate output path in yyyymmddhhmmss-{slug}.json format |
| `_fetch_html_async` | `async (url, client, extra_headers) -> tuple[str,str\|None,str\|None]\|None` | Fetch HTML with conditional request; returns None on 304 or retry exhaustion |
| `_extract_code_blocks` | `(soup: BeautifulSoup) -> list[str]` | Extract <pre> blocks, remove from DOM |
| `_extract_content` | `(html: str, url: str) -> tuple[str,str,list[str]]` | Return (title, body text, code blocks) |
| `_save_crawl_file` | `(url, title, lang, content, code_blocks, etag\|None, last_modified\|None) -> Path` | Save crawl results as JSON to rag-src/ |
| `_fetch_and_extract_async` | `async (url, client, extra_headers) -> tuple[str,str,str,list[str],str\|None,str\|None]\|None` | Fetch HTML and extract content; returns None when unavailable or 304 |
| `_enqueue_links` | `(html, current_url, start_url, depth, queue) -> None` | Parse links from HTML and enqueue; nofollow/external filtering applies |
| `_resolve_lang` | `(text: str, hint_lang: str) -> str` | Determine page language; 'auto' uses CJK-ratio detection with 'en' fallback for short texts |
| `_drain_queue_to_tasks` | `async (queue, visited, start_url, hint_lang, client, sem) -> set[Task]` | Dequeue pending URLs and create fetch tasks |

**Module-level utilities**

| Function | Description |
|---|---|
| `url_to_slug(url)` | Convert URL to filesystem-safe ASCII slug (max 80 chars) |
| `normalize_url(url)` | Remove fragment and trailing slash |
| `same_origin(url, base)` | True if scheme + hostname match |

### 2.1.1 Configuration parameters

| Parameter | Default | Description |
|---|---|---|
| `fetch_timeout` | 15 | HTTP request timeout in seconds |
| `crawl_concurrency` | 3 | Max concurrent fetch tasks via asyncio.Semaphore |
| `max_pages` | 500 | Maximum pages to crawl per start URL |
| `skip_nofollow` | False | Skip links with rel="nofollow" |
| `skip_external` | True | Skip cross-origin links (same-origin only by default) |

### 2.1.2 crawl_file behavior

`crawl_file(path, lang)` reads a local file and writes a crawl JSON to `rag-src/`.
Unlike web URLs, no HTTP round-trip occurs. Python files (.py) are stored as code blocks
so the code chunker applies. Local files include `schema_version`, `artifact_type`, `created_by`
metadata fields in the payload.

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
| `--url URL [URL ...]` | Target URLs (omit to use `target_urls` in config) | — |
| `--lang {en,ja,auto}` | Hint language | `en` |

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

### 2.5 Error handling

| Case | Action |
|---|---|
| HTTP request failure | Exponential backoff retry up to `fetch_retry` times (`min(2**i, 10)` sec) |
| URL-level exception | `WARNING` log; continue to next URL |
| Text < 100 chars | Use hint language (`en` fallback for `--lang auto`) |
| Language not `ja`/`en` | Skip URL |

### 2.6 Logging

- **File:** `/opt/llm/logs/crawl.log` + stderr
- **Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| Level | Timing | Structured fields |
|---|---|---|
| `INFO` | Crawl start, URL saved, skipped URL count | `url`, `source_type` (on save) |
| `WARNING` | HTTP error, retry event | — |

### 2.7 Configuration (`config/rag_pipeline.toml`)

See [03_rag_05_configuration_and_operations.md §1.1](03_rag_05_configuration_and_operations.md).

---

## 3. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`)

### 3.1.1 Markdown heading chunking configuration

| Parameter | Default | Description |
|---|---|---|
| `md_index_enable` | False | Enable heuristic Markdown detection for non-.md files |
| `md_snippet_max_chars` | 600 | Max characters per markdown heading section before falling back to sentence-level chunking |

### 3.1 Class overview

`ChunkSplitter` — splits `rag-src/*.json` files into chunks by language and content type;
saves to `rag-src/chunk/`. Idempotent: skips if `{stem}-0000.json` exists (`--force` overrides).

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | Load `rag_pipeline.toml`; init Sudachi tokenizer (SplitMode.C, `core` dict) |
| `process_all` | `(target: Path \| None = None, force: bool = False) -> int` | Process all `rag-src/*.json`; returns total chunk count |
| `process_file` | `(src_path: Path, force: bool = False) -> int` | Process single file; returns chunk count |

### 3.1.2 _is_markdown_source behavior

`.md` / `.markdown` / `.mdx` files always use heading chunking regardless of `md_index_enable`.
Non-`.md` files use heuristic detection (≥2 heading lines) only when `md_index_enable=true`.

### 3.1.3 _chunk_markdown_by_heading behavior

Sections exceeding `md_snippet_max_chars` are further split via `_chunk_english` sentence-level chunking.

### 3.1 Class overview

`ChunkSplitter` — splits `rag-src/*.json` files into chunks by language and content type;
saves to `rag-src/chunk/`. Idempotent: skips if `{stem}-0000.json` exists (`--force` overrides).

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | Load `rag_pipeline.toml`; init Sudachi tokenizer (SplitMode.C, `core` dict) |
| `process_all` | `(target: Path \| None = None, force: bool = False) -> int` | Process all `rag-src/*.json`; returns total chunk count |
| `process_file` | `(src_path: Path, force: bool = False) -> int` | Process single file; returns chunk count |

### 3.2 Splitting strategies

| Content type | Strategy |
|---|---|
| Japanese text | Sudachi SplitMode.C morphological analysis; `(original_sentence, normalized_form_space_joined)` pairs |
| English text | Regex sentence boundary split (`(?<=[.!?])\s+`) |
| `.md`/`.markdown`/`.mdx` URL | Heading boundary split (`#`/`##`/`###`); always applied regardless of `md_index_enable` |
| Non-`.md` content with ≥2 heading lines | Heading boundary split; applied only when `md_index_enable=true` |
| Code blocks | Blank-line split (language-agnostic) |

- Japanese chunks: `content` = original text, `normalized_content` = Sudachi normalized forms
- English/code chunks: `normalized_content = null`
- `chunk_type`: `"text"` or `"code"`
- `chunking_strategy`: `"text"` or `"heading"`

### 3.3 CLI arguments

| Argument | Description | Default |
|---|---|---|
| `--file PATH` | Process single file only | all unprocessed `.json` |
| `--force` | Regenerate existing chunks | false |

### 3.4 Output JSON format (`rag-src/chunk/{stem}-{idx:04d}.json`)

```json
{
  "schema_version": "1",
  "artifact_type": "chunk",
  "created_by": "chunk_splitter",
  "url": "https://example.com/page",
  "title": "Page title",
  "lang": "ja",
  "source_file": "20240101120000-example.txt",
  "chunk_index": 0,
  "chunk_type": "text",
  "chunking_strategy": "text",
  "content": "original chunk text",
  "normalized_content": "normalized form (JA only; null for EN/code)",
  "etag": "optional-etag",
  "last_modified": "optional-http-date"
}
```

The `source_file` field retains the original `.txt` extension from the crawler output filename.

### 3.5 Error handling

| Case | Action |
|---|---|
| Sudachi tokenize error | Catch; return `""`; skip that chunk |
| File-level failure | `ERROR` log (with traceback); continue to next file |
| Existing chunk (`{stem}-0000.txt`) | Skip unless `--force` |

### 3.6 Logging

- **File:** `/opt/llm/logs/chunk.log` + stderr
- **Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| Level | Timing |
|---|---|
| `INFO` | Files processed, chunks generated, skipped count |
| `WARNING` | Sudachi error |
| `ERROR` | File read error, file-level failure (with traceback) |

### 3.7 Configuration

See [03_rag_05_configuration_and_operations.md §1.1](03_rag_05_configuration_and_operations.md).

---

## 4. RagIngester (`scripts/rag/ingestion/ingester.py`)

**BUG-1/2/3 resolved:** `_read_chunk_json()` now reads raw bytes and parses with `orjson` directly,
returning a raw `dict` that preserves all fields including `chunking_strategy`, `normalized_content`,
and `chunk_index`. The earlier `dataclasses.asdict(read_json_file(path))` approach (which dropped
fields not in `ChunkDocument`) is no longer used. See [03_rag_90](03_rag_90_inconsistencies_and_known_issues.md)
for resolution details.

### 4.1 Class overview

`RagIngester` — reads chunk files, generates embeddings via `embed-llm` (port 8003),
and upserts to SQLite (`documents` / `chunks` / `chunks_vec`). Moves processed chunks to
`rag-src/registered/`.

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | Merge `common.toml` + `rag_pipeline.toml`; init `httpx.Client` |
| `ingest_all` | `(force: bool = False, on_ingest_complete: Callable[[], None] \| None = None) -> RagConsistencyReport \| None` | Group chunk files by URL; call `ingest_url_group` for each. `on_ingest_complete` is called after ingestion completes (e.g., to invalidate semantic cache). Returns consistency report or None if check failed. |
| `ingest_url_group` | `(db: SQLiteHelper, url: str, chunk_files: list[Path], force: bool) -> IngestUrlResult` | Process one URL group; returns `{n_success, n_failed, n_embed_failed, skipped}` |
| `close` | `() -> None` | Close the underlying `httpx.Client` |

**Private methods**

| Method | Signature | Description |
|---|---|---|
| `_get_embedding` | `(text: str) -> list[float] \| None` | Return embedding vector; validates dimension against embedding_dims config. Returns None on empty input, network failure, or dimension mismatch. |
| `_validate_artifact` | `(payload: dict, expected_type: str) -> None` | Validate artifact_type field; lenient for backward compatibility (missing artifact_type accepted) |
| `_is_file_unchanged` | `(existing_etag, existing_last_modified, new_etag, new_last_modified) -> bool` | Return True when file SHA-256 hash is unchanged |
| `_delete_existing_document` | `(db: SQLiteHelper, doc_id: int) -> None` | Delete document and chunks; chunks_vec removed first |
| `_update_etag` | `(db: SQLiteHelper, doc_id: int, etag, last_modified, new_fetched_at\|None) -> None` | Refresh ETag/Last-Modified for existing document with stale guard |
| `_get_or_create_document` | `(db, url, title, lang, force, etag\|None, last_modified\|None, chunking_strategy, fetched_at\|None) -> int \| None` | Register URL in documents; returns doc_id or None when already registered |
| `_insert_chunk` | `(db, doc_id, idx, content, normalized_content, embedding, chunk_type, source_file) -> None` | Insert chunk and embedding vector |
| `_read_chunk_json` | `(path: Path) -> dict \| None` | Read and parse chunk JSON as raw dict |
| `_embed_and_store` | `(doc_id: int, path: Path) -> tuple[bool, bool]` | Embed one chunk and insert; returns (chunk_ok, embed_ok) |
| `_ingest_chunk_files` | `(doc_id: int, chunk_files: list[Path]) -> tuple[int, int, int]` | Embed and insert in parallel; returns (n_inserted, n_failed, n_embed_failed) |
| `_group_chunks_by_url` | `(chunk_files: list[Path]) -> dict[str, list[Path]]` | Group chunk files by URL field |
| `_process_url_groups` | `(db, url_groups: dict, force: bool) -> list[IngestUrlResult]` | Iterate over URL groups and ingest each |
| `_move_to_registered` | `(paths: list[Path]) -> None` | Move ingested chunk files to registered/ |

### 4.2 Behavior details

- **E5 prefix:** prepend `passage: {text}` before embedding (vs `query: ` at query time)
- **Vector encoding:** `struct.pack(f"<{N}f", *values)` → little-endian float32 BLOB
- **Parallel embed:** `ThreadPoolExecutor(embed_workers)` per URL group;
  each thread uses an independent `SQLiteHelper().open()`
- **WAL mode:** `PRAGMA journal_mode=WAL` for concurrent read/write safety
- **Upsert (`--force`):** delete in order `chunks_vec` → `chunks` → `documents`, then re-INSERT
- **Idempotency:** skip URL if already in `documents`; still UPDATE `etag`/`last_modified` via skip-path guard (see below)
- **Embedding dimension validation:** `_get_embedding()` validates embedding dimension against `embedding_dims` config (default 384); returns None on mismatch
- **Skip-path stale guard:** `_update_etag()` compares incoming `fetched_at` (chunk payload) against stored `documents.fetched_at`; if incoming < stored the update is skipped (newer crawl wins — prevents stale chunk files from overwriting fresher metadata). Missing `fetched_at` (legacy chunks without a freshness signal) uses fill-only semantics: `COALESCE(etag, ?)` — only populates the stored field if currently NULL; never overwrites a non-NULL value. This prevents stale chunk-file metadata from replacing fresher values stored by a more recent crawl.
- **Embed failure tracking:** `_embed_and_store()` returns `(chunk_ok, embed_ok)` tuple;
  `n_embed_failed` counts embedding-specific failures separately from parse/DB errors
- **Local file unchanged detection:** `_is_file_unchanged()` compares SHA-256 etags for `file://` URLs

### 4.3 CLI arguments

| Argument | Description | Default |
|---|---|---|
| `--force` | Delete existing records and re-register | false |

### 4.4 Embedding API

```
POST http://127.0.0.1:8003/embedding
Request:  {"content": "passage: {text}"}
Response: {"embedding": [float, ...]}   # 384-dim (multilingual-E5-small; config/common.toml::embedding_dims)
```

### 4.5 DB tables updated

| Table | Operation |
|---|---|
| `documents` | SELECT to check; DELETE+INSERT (`force=True`) or skip+UPDATE etag (`force=False`) |
| `chunks` | INSERT (FK → documents; ON DELETE CASCADE) |
| `chunks_vec` | INSERT BLOB vector |
| `chunks_fts` | Auto-synced by `chunks_ai` trigger (`COALESCE(normalized_content, content)`)

### 4.6 Error handling

| Case | Action |
|---|---|
| Embed API failure | Exponential backoff retry up to `embed_retry` times |
| Retry exhausted (single chunk) | `WARNING` log; skip chunk; continue |
| Invalid `lang` value | `ValueError`; skip URL group; `ERROR` log with traceback |
| `chunks_vec` delete order | Must delete `chunks_vec` first (no FK constraint on sqlite-vec virtual table) |
| Embedding dimension mismatch | `ValueError`; skip chunk; `WARNING` log |

### 4.7 Logging

- **File:** `/opt/llm/logs/ingest.log` + stderr
- **Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| Level | Timing | Structured fields |
|---|---|---|
| `INFO` | Chunks processed, DB inserts, file moves | `doc_id`, `source_type`, `stage_name` (on insert) |
| `WARNING` | Embed API error, retry, embed skip | `source_type`, `stage_name` |
| `ERROR` | Chunk file read error, file move error, URL group failure (with traceback) | — |

### 4.8 Configuration

See [03_rag_05_configuration_and_operations.md §1.2](03_rag_05_configuration_and_operations.md).

---

## 5. Crawler Utils (`scripts/rag/ingestion/crawler_utils.py`)

### 5.1 Module overview

`crawler_utils.py` — Pure-function utilities for WebCrawler: URL helpers, content extraction, language detection, and target URL parsing. Extracted from `crawler.py` to keep it under 400 lines.

**Module-level constants**

| Constant | Value | Description |
|---|---|---|
| `_SUPPORTED_LANGS` | `{"en", "ja"}` | Resolved (output) language codes |
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
| `extract_text` | `(soup: BeautifulSoup) -> str` | Remove noise tags (nav, footer, aside, script, style, noscript); extract body text via Trafilatura with `include_comments=False`, `include_tables=True`; fall back to BS4 `get_text(separator="\n", strip=True)` |
| `detect_lang` | `(text: str) -> str \| None` | CJK ratio detection; returns 'ja' if ratio ≥ 0.1, 'en' otherwise; None for texts < 100 chars |
| `parse_target_urls` | `(target_raw: list[Any]) -> list[tuple[str,str]]` | Validate and parse target_urls config into (url, lang) tuples; raises ValueError on invalid entries |

---

## 5. Chunk English Mixin (`scripts/rag/ingestion/chunk_english.py`)

### 5.1 Module overview

`chunk_english.py` — `ChunkEnglishMixin`: paragraph/sentence-level chunking for English text. Mixed into `ChunkSplitter` via multiple inheritance.

**Class: `ChunkEnglishMixin`**

| Method | Signature | Description |
|---|---|---|
| `_chunk_english` | `(text: str) -> list[str]` | Split at paragraph/sentence boundaries; merges short paragraphs, discards below min_chunk after stopword removal |
| `_merge_paragraphs_en` | `(paragraphs: list[str]) -> list[str]` | Accumulate paragraphs into ≤max_chunk chunks; split oversized paragraphs at sentence boundaries |
| `_split_sentences_en` | `(text: str) -> list[str]` | Split at sentence boundaries (. ! ?); oversized sentences kept as-is |
| `_filter_stopwords_en` | `(text: str) -> str` | Remove EN stopwords (case-insensitive); return space-joined tokens |

**Inherited attributes (declared for mypy; values set by `ChunkSplitter.__init__`)**

| Attribute | Type | Description |
|---|---|---|
| `_max_chunk` | `int` | Maximum chunk size in characters |
| `_min_chunk` | `int` | Minimum chunk size in characters |
| `_en_stopwords` | `frozenset[str]` | English stopwords from config |
| `_chunk_overlap` | `int` | Overlap between chunks in characters |

---

## 6. Chunk Japanese Mixin (`scripts/rag/ingestion/chunk_japanese.py`)

### 6.1 Module overview

`chunk_japanese.py` — `ChunkJapaneseMixin`: morphological-analysis-based chunking for Japanese text. Mixed into `ChunkSplitter` via multiple inheritance.

**Class: `ChunkJapaneseMixin`**

| Method | Signature | Description |
|---|---|---|
| `_chunk_japanese` | `(text: str) -> list[tuple[str,str]]` | Split into (original, normalized) chunk pairs via NFKC normalization, sentence splitting, and Sudachi morphological analysis |
| `_split_into_ja_sentences` | `(text: str) -> list[tuple[str,str]]` | Split at clause boundaries (。！？ and newlines); returns (original, normalized) pairs; empty pairs discarded |
| `_normalize_ja_sentence` | `(text: str) -> str` | Run Sudachi SplitMode.C analysis; return space-joined normalized content words; raises `TokenizationError` on failure |
| `_merge_ja_sentence_pairs` | `(pairs: list[tuple[str,str]]) -> list[tuple[str,str]]` | Accumulate (original, normalized) pairs into chunk pairs by original text length; applies overlap from buffer tail |

**Inherited attributes (declared for mypy; values set by `ChunkSplitter.__init__`)**

| Attribute | Type | Description |
|---|---|---|
| `_max_chunk` | `int` | Maximum chunk size in characters |
| `_min_chunk` | `int` | Minimum chunk size in characters |
| `_chunk_overlap` | `int` | Overlap between chunks in characters |
| `_ja_stop_pos` | `frozenset[str]` | Japanese stop POS tags from config (excluded from normalized output) |
| `_sd_tkn` | Any | Sudachi tokenizer instance |
| `_split_c` | Any | Sudachi SplitMode.C |

---

## 7. Pipeline Utils (`scripts/rag/ingestion/pipeline_utils.py`)

### 7.1 Module overview

`pipeline_utils.py` — Shared I/O utilities for the RAG ingestion pipeline: chunk JSON reading, source file collection, and processing sentinel checks.

**Module-level constants**

| Constant | Value | Description |
|---|---|---|
| `logger` | `Logger(__name__, "/opt/llm/logs/pipeline.log")` | Pipeline logging instance |

**Public functions**

| Function | Signature | Description |
|---|---|---|
| `_read_chunk_json_raw` | `(path: Path) -> dict[str, Any] \| None` | Read and parse chunk JSON as raw dict; returns None on any failure (OSError, JSONDecodeError, missing url/content) |
| `read_json_file` | `(path: Path) -> ChunkDocument` | Read and parse JSON file into ChunkDocument; raises ChunkFormatError on failure |
| `collect_source_files` | `(rag_src_dir: Path, target: Path \| None = None) -> tuple[list[Path], list[SkipInfo]]` | Return (files_to_process, skipped); if target is given and exists, returns [target]; otherwise glob *.json from rag_src_dir |
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

## 8. Shared Utilities (`scripts/rag/utils.py`)

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
| `sanitize_document_full` | `(text: str) -> SanitizeResult` | `SanitizeResult` | Same as sanitize_document but returns audit trail (detected patterns, was_sanitized flag) |

**Constants:**

| Constant | Value | Description |
|---|---|---|
| `MIN_TEXT_LENGTH_FOR_DETECTION` | `100` | Minimum text length for language detection; pages shorter than this use hint language |

**Structured log keys (RAG lifecycle tracing):**

| Key | Value | Used by |
|---|---|---|
| `url` | URL string | crawler, ingester |
| `doc_id` | INTEGER document ID | ingester |
| `chunk_id` | INTEGER chunk ID | chunk_splitter |
| `source_type` | `"http"` / `"file"` | crawler, ingester |
| `stage_name` | Stage name string | ingester |

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

## 6. FTS5 Implementation Notes

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
