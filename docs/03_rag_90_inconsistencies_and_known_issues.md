# RAG Inconsistencies and Known Issues

This file catalogs known bugs, spec conflicts, document inconsistencies, and open questions
discovered during the restructuring of RAG documentation.

Each entry uses: Type / Impact / Description / Safe interpretation / Recommended action / Source.

---

## Open Questions

### OQ-2: MDQ vs RAG boundary — migration criteria undefined

- **Type:** OPEN_QUESTION
- **Impact scope:** `mcp/mdq/`, `mcp/rag_pipeline/`
- **Description:** MDQ (Markdown-dedicated index) and RAG serve overlapping use cases for
  Markdown content. The boundary for when to use MDQ vs RAG is not defined.
- **Recommended action:** Define migration criteria in `docs/04_mcp-mdq.md`.

---

### OQ-3: `test_ingester.py` missing

- **Type:** Addressed
- **Impact scope:** Test coverage for `scripts/rag/ingestion/ingester.py`
- **Current state:** `tests/test_rag_ingester.py` created with 9 tests covering `_read_chunk_json()` field preservation (chunking_strategy, normalized_content, chunk_index), error handling (missing file, invalid JSON, missing url/content). DB write and `--force` behavior remain untested.

---

### OQ-4: `use_refiner=True` edge cases

- **Type:** OPEN_QUESTION
- **Impact scope:** `RagPipeline._augment_refiner()`
- **Description:** When `_augment_refiner()` returns an empty string, the caller returns raw
  chunks. The condition that produces empty string output (vs exception) is not documented.
- **Recommended action:** Add explicit documentation for the empty-output fallback path.

---

### OQ-6: `chunks_fts` COALESCE trigger behavior for `normalized_content=None`

- **Type:** OPEN_QUESTION
- **Impact scope:** `chunks_fts`, FTS5 for English/code chunks
- **Description:** The `chunks_ai` trigger uses `COALESCE(normalized_content, content)`.
  For English and code chunks, `normalized_content` is NULL. Verify FTS5 correctly falls
  back to `content` for indexing and querying in all SQLite versions used.
- **Recommended action:** Add an integration test asserting English chunk FTS search works
  when `normalized_content` is NULL.

---

### OQ-7: `_augment_http()` fallback trigger condition

- **Type:** OPEN_QUESTION
- **Impact scope:** `RagPipeline._augment_http()`
- **Description:** The method returns `None` to signal "fall back to in-process pipeline."
  The exact conditions that trigger this (`None` return) are not documented. Is it any exception,
  HTTP error, empty result, or only connection failure?
- **Recommended action:** Document the explicit conditions that cause `_augment_http()` to
  return `None`.

---

## Document Inconsistency (Additional Required Items)

### DOC-4: Markdown heading split condition — inconsistency between sources

- **Type:** Document inconsistency
- **Impact scope:** `scripts/rag/ingestion/chunk_splitter.py`, `md_index_enable` config behavior
- **Statement A:** `03_rag-ref-splitter.md §3.1` states that BOTH conditions — URL ending in `.md`/`.markdown`/`.mdx` AND body containing ≥2 heading lines — require `md_index_enable=true` to trigger heading-boundary split.
- **Statement B:** `03_spec_rag.md §8.1` states that `.md`/`.markdown`/`.mdx` URLs ALWAYS get heading split (regardless of `md_index_enable`); non-`.md` content with ≥2 heading lines requires `md_index_enable=true`.
- **Current safe interpretation:** Trust `03_spec_rag.md §8.1`. `.md`/`.markdown`/`.mdx` URLs always use heading split; non-`.md` content with ≥2 heading lines is only heading-split when `md_index_enable=true`.
- **Recommended action:** Verify behavior in `chunk_splitter.py` (`_is_markdown_source()`) and correct `03_rag-ref-splitter.md §3.1` accordingly.
- **Notes for AI reference:** When modifying `chunk_splitter.py`, apply the two-path model: always-on for `.md` extension, flag-gated for non-`.md` with headings.

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
- **Impact scope:** `chunks` table, `chunks_fts` virtual table, `rag/repository.py _build_fts_query()`, `rag/stages/augment.py`
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

- **Type:** Needs confirmation
- **Impact scope:** `crawler.py crawl_file()`, `ingester.py ingest_url_group()`
- **Description:** Both crawler and ingester support local file ingestion via the `file://` scheme. Crawler: `crawl_file(path, lang)` saves a JSON file to `rag-src/` with `url="file://{path}"`. Ingester: `ingest_url_group` accepts URL groups with `file://` URLs; these are processed identically to web URLs. Conditional GET does not apply to `file://` URLs (no ETag). When ingesting `.py` files, `crawl_file()` stores content as code blocks (not body text).
- **Current safe interpretation:** `file://` ingestion is supported and functional. The `--force` flag and idempotency behavior apply to `file://` URLs the same as web URLs.
- **Notes for AI reference:** Do not apply Conditional GET logic to `file://` URLs. The ETag/Last-Modified fields will be NULL for locally-ingested files. Source: `03_rag-ref-crawler.md §2.1`, `03_rag-ref-ingester.md §4.2`.

---

### DOC-01: `SemanticCache` import path incorrect in docs

- **Type:** Document inconsistency
- **Impact scope:** `docs/03_rag_03_query_pipeline.md §6`
- **Statement A:** Previous doc stated `from rag.repository import SemanticCache # re-exported`.
- **Statement B:** **Confirmed** (`rag/pipeline.py:30`): `from rag.cache import SemanticCache`. `rag/repository.py` does NOT re-export `SemanticCache`.
- **Current safe interpretation:** Import from `rag.cache` directly. `rag/cache.py:30` is the canonical definition.
- **Recommended action:** Fixed in doc (2026-06-16).
- **Notes for AI reference:** Use `from rag.cache import SemanticCache`.

---

### DOC-02: `PipelineContext.observers` and `add_observer()` do not exist

- **Type:** Document inconsistency
- **Impact scope:** `docs/03_rag_03_query_pipeline.md §4 PipelineContext`
- **Statement A:** Previous doc listed `observers: list[Any]` field and `add_observer(observer)` method.
- **Statement B:** **Confirmed** (`rag/stage.py:16-26`): `PipelineContext` has 7 fields only: `query`, `history_context`, `queries`, `search_results`, `merged`, `reranked`, `augment_result`. No `observers` field or `add_observer()` method.
- **Current safe interpretation:** `PipelineContext` has exactly 7 fields. Do not reference `observers` or `add_observer()`.
- **Recommended action:** Fixed in doc (2026-06-16).
- **Notes for AI reference:** Stage communication is via `ctx` field mutation only.

---

### DOC-03: Embedding dimension — dataclass default 768 vs configured production value 384

- **Type:** Document inconsistency
- **Impact scope:** `docs/03_rag_04_data_model_and_interfaces.md`, `docs/03_rag_02_ingestion_pipeline.md`
- **Statement A:** `models_config.py:53` — `IngesterConfig.embed_dimension: int = 768` (dataclass default).
- **Statement B:** **Confirmed** (`config/common.toml:43`): `embedding_dims = 384` with comment "all-MiniLM-L6-v2 = 384". `ingester.py:119` docstring also says "384-dim vector".
- **Current safe interpretation:** The production embedding dimension is **384** (set by `common.toml`). The dataclass default of 768 is overridden at runtime. `floats_to_blob` for 384-dim produces 1536 bytes (not 3072).
- **Recommended action:** Fixed in doc (2026-06-16). Old reference to `models.py:56` was also incorrect — correct location is `models_config.py:53`.
- **Notes for AI reference:** Use `common.toml::embedding_dims` (384) as the authoritative value, not the dataclass default (768).

---
