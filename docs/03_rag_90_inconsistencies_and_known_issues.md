# RAG Inconsistencies and Known Issues

This file catalogs known bugs, spec conflicts, document inconsistencies, and open questions
discovered during the restructuring of RAG documentation.

Each entry uses: Type / Impact / Description / Safe interpretation / Recommended action / Source.

**Resolved entries removed from this file:**
- BUG-1/2/3 (chunk field drop via `dataclasses.asdict`): fixed — `_read_chunk_json()` now uses raw `orjson` parsing, preserving all fields including `chunking_strategy`, `normalized_content`, and `chunk_index`.
- OQ-2 (MDQ vs RAG boundary): resolved — boundary defined in `docs/04_mcp_07_mdq_rag_boundary.md`.
- OQ-3 (`test_ingester.py` missing): addressed — `tests/test_rag_ingester.py` exists with 9 tests.
- OQ-7 (`_augment_http()` fallback trigger condition): documented in-file (2026-06-20 removed).
- DOC-01 (`SemanticCache` import path): fixed in doc (2026-06-16).
- DOC-02 (`PipelineContext.observers` non-existent): fixed in doc (2026-06-16, updated 2026-06-18).
- DOC-03 (embedding dimension dataclass default 768 vs production 384): fixed in doc (2026-06-16).

---

## Open Questions

### OQ-4: `use_refiner=True` edge cases

- **Type:** RESOLVED
- **Impact scope:** `RagPipeline.augment()` (refined via `refine_context()`)
- **Description:** When the refiner returns an empty string, the caller returns raw
  chunks. The condition that produces empty string output (vs exception) is documented in `scripts/rag/pipeline_refiner.py`.
- **Resolution:** Documented — `refiner_returned_empty` when LLM response content is `""` or whitespace-only; `refiner_exception: {e}` on HTTP/parse errors.

---

### OQ-6: `chunks_fts` COALESCE trigger behavior for `normalized_content=None`

- **Type:** RESOLVED
- **Impact scope:** `chunks_fts`, FTS5 for English/code chunks
- **Description:** The `chunks_ai` trigger uses `COALESCE(normalized_content, content)`.
  For English and code chunks, `normalized_content` is NULL. Verify FTS5 correctly falls
  back to `content` for indexing and querying in all SQLite versions used.
- **Recommended action:** Add an integration test asserting English chunk FTS search works
  when `normalized_content` is NULL.
- **Resolution:** Validated by `tests/test_fts_fallback.py` — 8 integration tests
  covering English chunks, code chunks, NULL/empty COALESCE semantics, and mixed-language
  documents. All tests use trigger-backed indexing path (INSERT INTO chunks → trigger fires
  → chunks_fts populated; no direct FTS5 inserts). Verified on runtime SQLite version
  (Python built-in sqlite3 module). Recommended action in this entry is complete.

---

## Design Notes (Required Explicit Items)

### DESIGN-1: ETag/Last-Modified and Conditional GET relationship

- **Type:** Needs confirmation
- **Impact scope:** `crawler.py`, `ingester.py`, `documents` table (`etag`, `last_modified` columns)
- **Description:** Two components share `documents.etag` and `documents.last_modified`. Crawler reads them and sends Conditional GET headers (`If-None-Match`/`If-Modified-Since`). On HTTP 304, crawler skips file save. Ingester writes/updates these fields even when skipping a URL (`force=False`, already registered) to keep values current for the next crawl cycle. This creates a data dependency: crawler benefits from Conditional GET only after at least one ingester run has stored ETag values.
- **Current safe interpretation:** The design is: ingester stores ETag/Last-Modified → crawler uses them on subsequent crawls for 304 optimization. The UPDATE on skip is intentional, not a side effect.
- **Recommended action:** Verify that ingester's ETag UPDATE on skip does not overwrite a valid ETag with a stale value from a chunk file written before a newer crawl.
- **Notes for AI reference:** Do not remove the ETag/Last-Modified UPDATE in ingester's skip path — it is required for Conditional GET to function on the next crawl cycle. Sources: `03_rag-ref-crawler.md §2.3`, `03_rag-ref-ingester.md §4.2`.

---

### DESIGN-2: FTS5 uses `normalized_content`; LLM receives `content`

- **Type:** Needs confirmation
- **Impact scope:** `chunks` table, `chunks_fts` virtual table, `scripts/rag/repository.py _build_fts_query()`, `scripts/rag/stages/augment.py`
- **Description:** Japanese chunks store two text representations. `chunks.content` (original text) is injected into the LLM context by `AugmentStage`. `chunks.normalized_content` (Sudachi `normalized_form()` space-joined) is indexed by the `chunks_ai` trigger via `COALESCE(normalized_content, content)` into `chunks_fts`. FTS5 query-side also normalizes Japanese terms in `_build_fts_tokens_ja()`. English and code chunks have `normalized_content=NULL`; FTS5 falls back to `content`. This separation ensures LLM receives readable original text while BM25 search uses morphologically normalized forms.
- **Current safe interpretation:** `normalized_content` is now correctly read from chunk JSON (BUG-2 fixed). FTS5 indexing uses Sudachi-normalized forms for Japanese chunks when present.
- **Notes for AI reference:** Never replace `content` with `normalized_content` in the Augment stage output. The separation is intentional. Source: `03_rag-ingestion-pipeline.md §FTS5/LLM content separation`.

---

### DESIGN-3: Separation of responsibilities among `documents`, `chunks`, `chunks_fts`, `chunks_vec`

- **Type:** Needs confirmation
- **Impact scope:** DB schema, all ingestion and query code
- **Description:**
  - `documents`: one row per URL; metadata only (url, title, lang, fetched_at, etag, last_modified, chunking_strategy).
  - `chunks`: one row per chunk; text and position data (content, normalized_content, chunk_index, chunk_type). FK to `documents` via `doc_id` (ON DELETE CASCADE).
  - `chunks_fts`: FTS5 virtual table; auto-synced by `chunks_ai`/`chunks_au`/`chunks_ad` triggers; BM25 search only; never INSERT/UPDATE directly.
  - `chunks_vec`: sqlite-vec virtual table; float32 embedding BLOB; KNN search only; no FK constraint (must delete before `chunks` on force-reinsertion).
  - Deletion order for force-reinsertion: `chunks_vec` first → `chunks` → `documents`.
- **Current safe interpretation:** `chunks_fts` and `chunks_vec` are derived; treat them as read-only from application code. Manage all mutations through `chunks` and `documents`.
- **Notes for AI reference:** sqlite-vec virtual tables do not support standard FK constraints. The deletion order (`chunks_vec` before `chunks`) is mandatory to avoid orphaned vector records. Source: `03_spec_rag.md §9.1`, `03_rag-ref-ingester.md §4.3`.

---

### DESIGN-4: Handling of `file://` local file ingestion

- **Type:** Resolved
- **Impact scope:** `crawler.py crawl_file()`, `ingester.py ingest_url_group()`
- **Description:** Both crawler and ingester support local file ingestion via the `file://` scheme. Crawler: `crawl_file(path, lang)` saves a JSON file to `rag-src/` with `url="file://{path}"`. Ingester: `ingest_url_group` accepts URL groups with `file://` URLs; these are processed identically to web URLs. Conditional GET does not apply to `file://` URLs (no ETag). When ingesting `.py` files, `crawl_file()` stores content as code blocks (not body text).
- **Current safe interpretation:** `file://` ingestion is supported and functional. The `--force` flag and idempotency behavior apply to `file://` URLs the same as web URLs. SHA-256 hash comparison is used for freshness detection instead of ETag/304.
- **Notes for AI reference:** `file://` URLs use SHA-256 hash as `etag` and file mtime as `last_modified`. The ingester auto-detects changed files by comparing stored vs. computed SHA-256. Conditional GET (304 Not Modified) is for HTTP only — `file://` uses hash comparison instead. Source: `ingester.py:_is_file_unchanged()`, `schema_sql.py:etag/last_modified`.

---
