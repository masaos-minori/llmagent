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

# Single URL
uv run python scripts/rag/ingestion/crawler.py --url "https://ziglang.org/documentation/master/" --lang en

# Multiple URLs (same --lang applied to all)
uv run python scripts/rag/ingestion/crawler.py \
    --url "https://ziglang.org/documentation/master/" \
          "https://zig.guide/" \
    --lang en
```

**Note:** All file paths (`rag_src_dir`) are resolved from `config/rag_pipeline.toml`. Production default: `/opt/llm/rag-src/`.

### Step 2: Chunk split

```bash
# All unprocessed .txt files in {rag_src_dir}/
uv run python scripts/rag/ingestion/chunk_splitter.py

# Single file only (path relative to rag_src_dir)
uv run python scripts/rag/ingestion/chunk_splitter.py --file /opt/llm/rag-src/20240101120000-ziglang.txt

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
|---|---|---|---|
| `{rag_src_dir}/yyyymmddhhmmss-{slug}.txt` | `crawler.py` | JSON (url, title, lang, fetched_at, content, code_blocks) |
| `{rag_src_dir}/chunk/{stem}-{idx:04d}.txt` | `chunk_splitter.py` | JSON (url, title, lang, source_file, chunk_index, chunk_type, content, normalized_content, etag, last_modified) |
| `{rag_src_dir}/registered/{stem}-{idx:04d}.txt` | `ingester.py` (moved) | Same as chunk file |

> **Artifact format note:** All `.txt` files listed above contain JSON payloads,
> not plain text. The `.txt` extension is retained for historical/compatibility reasons.
> Always parse with `orjson.loads()` or `json.loads()`. Plain-text tools (grep, wc,
> editors that assume UTF-8 text) will work on the raw bytes but will not interpret
> the structure. To inspect a file:
> ```
> python -c "import orjson; print(orjson.loads(open('FILE', 'rb').read()))"
> ```
> Do NOT pass `.txt` artifacts to tools that assume plain-text format.

> **Future compatibility note (Needs confirmation):** Renaming artifacts to `.json` is
> feasible but requires updating all `glob("*.txt")` calls in `ingester.py` and
> `chunk_splitter.py`, the sentinel filename check (`{stem}-0000.txt`), and a migration
> script for existing files in `rag-src/registered/`. Not implemented; requires
> explicit confirmation before proceeding.

Production config: `rag_src_dir = "/opt/llm/rag-src"`. The default value `rag-src` is used only when no config is present.

---

## 2. WebCrawler (`scripts/rag/ingestion/crawler.py`)

### 2.1 Class overview

`WebCrawler` — BFS-crawls from a start URL within the same origin; saves each page as
a JSON file in `rag-src/`. Supports conditional GET (ETag/Last-Modified) and local files.

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | Load `rag_pipeline.toml`; init httpx.AsyncClient |
| `crawl` | `async (targets: list[tuple[str,str]] \| None = None) -> None` | Crawl all targets; uses config `target_urls` if None |
| `crawl_site` | `async (start_url: str, hint_lang: str) -> None` | Single-origin BFS crawl |
| `crawl_file` | `(path: Path, lang: str) -> int` | Save local file as crawler JSON; returns 1 on success |

**Module-level utilities**

| Function | Description |
|---|---|
| `url_to_slug(url)` | Convert URL to filesystem-safe ASCII slug (max 80 chars) |
| `normalize_url(url)` | Remove fragment and trailing slash |
| `same_origin(url, base)` | True if scheme + hostname match |

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
| Current state | Implemented | Not yet implemented |

### 2.3 CLI arguments

| Argument | Description | Default |
|---|---|---|
| `--url URL [URL ...]` | Target URLs (omit to use `target_urls` in config) | — |
| `--lang {en,ja,auto}` | Hint language | `en` |

### 2.4 Output JSON format (`rag-src/yyyymmddhhmmss-{slug}.txt`)

```json
{
  "url": "https://example.com/page",
  "title": "Page title",
  "lang": "ja",
  "fetched_at": "2024-01-01T12:00:00",
  "content": "body text",
  "code_blocks": ["block1", "block2"]
}
```

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

| Level | Timing |
|---|---|
| `INFO` | Crawl start, URL saved, skipped URL count |
| `WARNING` | HTTP error, retry event |

### 2.7 Configuration (`config/rag_pipeline.toml`)

See [03_rag_05_configuration_and_operations.md §1.1](03_rag_05_configuration_and_operations.md).

---

## 3. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`)

### 3.1 Class overview

`ChunkSplitter` — splits `rag-src/*.txt` files into chunks by language and content type;
saves to `rag-src/chunk/`. Idempotent: skips if `{stem}-0000.txt` exists (`--force` overrides).

**Public methods**

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(config: dict \| None = None)` | Load `rag_pipeline.toml`; init Sudachi tokenizer (SplitMode.C, `core` dict) |
| `process_all` | `(target: Path \| None = None, force: bool = False) -> int` | Process all `rag-src/*.txt`; returns total chunk count |
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
| `--file PATH` | Process single file only | all unprocessed `.txt` |
| `--force` | Regenerate existing chunks | false |

### 3.4 Output JSON format (`rag-src/chunk/{stem}-{idx:04d}.txt`)

```json
{
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
| `ingest_all` | `(force: bool = False) -> RagConsistencyReport \| None` | Group chunk files by URL; call `ingest_url_group` for each |
| `ingest_url_group` | `(db: SQLiteHelper, url: str, chunk_files: list[Path], force: bool) -> IngestUrlResult` | Process one URL group; returns `{n_success, n_failed, n_embed_failed, skipped}` |
| `close` | `() -> None` | Close the underlying `httpx.Client` |

### 4.2 Behavior details

- **E5 prefix:** prepend `passage: {text}` before embedding (vs `query: ` at query time)
- **Vector encoding:** `struct.pack(f"<{N}f", *values)` → little-endian float32 BLOB
- **Parallel embed:** `ThreadPoolExecutor(embed_workers)` per URL group;
  each thread uses an independent `SQLiteHelper().open()`
- **WAL mode:** `PRAGMA journal_mode=WAL` for concurrent read/write safety
- **Upsert (`--force`):** delete in order `chunks_vec` → `chunks` → `documents`, then re-INSERT
- **Idempotency:** skip URL if already in `documents`; still UPDATE `etag`/`last_modified` via skip-path guard (see below)
- **Skip-path stale guard:** `_update_etag()` compares incoming `fetched_at` (chunk payload) against stored `documents.fetched_at`; if incoming < stored the update is skipped (newer crawl wins — prevents stale chunk files from overwriting fresher metadata). Missing `fetched_at` (legacy chunks without a freshness signal) uses fill-only semantics: `COALESCE(etag, ?)` — only populates the stored field if currently NULL; never overwrites a non-NULL value. This prevents stale chunk-file metadata from replacing fresher values stored by a more recent crawl.
- **Embed failure tracking:** `_embed_and_store()` returns `(chunk_ok, embed_ok)` tuple;
  `n_embed_failed` counts embedding-specific failures separately from parse/DB errors

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
| `chunks_fts` | Auto-synced by `chunks_ai` trigger (`COALESCE(normalized_content, content)`) |

### 4.6 Error handling

| Case | Action |
|---|---|
| Embed API failure | Exponential backoff retry up to `embed_retry` times |
| Retry exhausted (single chunk) | `WARNING` log; skip chunk; continue |
| Invalid `lang` value | `ValueError`; skip URL group; `ERROR` log with traceback |
| `chunks_vec` delete order | Must delete `chunks_vec` first (no FK constraint on sqlite-vec virtual table) |

### 4.7 Logging

- **File:** `/opt/llm/logs/ingest.log` + stderr
- **Format:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| Level | Timing |
|---|---|
| `INFO` | Chunks processed, DB inserts, file moves |
| `WARNING` | Embed API error, retry, embed skip |
| `ERROR` | Chunk file read error, file move error, URL group failure (with traceback) |

### 4.8 Configuration

See [03_rag_05_configuration_and_operations.md §1.2](03_rag_05_configuration_and_operations.md).

---

## 5. Shared Utilities (`scripts/rag/utils.py`)

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

**Used by:**

| Script | Functions used |
|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | `normalize_unicode` |
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
