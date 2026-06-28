# RAG Inconsistencies and Known Issues

This file catalogs known bugs, spec conflicts, document inconsistencies, and open questions
discovered during the restructuring of RAG documentation.

Each entry uses: Type / Impact / Description / Safe interpretation / Recommended action / Source.

---

## Design Notes (Required Explicit Items)

### DESIGN-2: FTS5 uses `normalized_content`; LLM receives `content`

- **Type:** Needs confirmation
- **Impact scope:** `chunks` table, `chunks_fts` virtual table, `scripts/rag/repository.py _build_fts_query()`, `scripts/rag/stages/augment.py`
- **Description:** Japanese chunks store two text representations. `chunks.content` (original text) is injected into the LLM context by `AugmentStage`. `chunks.normalized_content` (Sudachi `normalized_form()` space-joined) is indexed by the `chunks_ai` trigger via `COALESCE(normalized_content, content)` into `chunks_fts`. FTS5 query-side also normalizes Japanese terms in `_build_fts_tokens_ja()`. English and code chunks have `normalized_content=NULL`; FTS5 falls back to `content`. This separation ensures LLM receives readable original text while BM25 search uses morphologically normalized forms.
- **Current safe interpretation:** `normalized_content` is correctly read from chunk JSON. FTS5 indexing uses Sudachi-normalized forms for Japanese chunks when present.
- **Notes for AI reference:** Never replace `content` with `normalized_content` in the Augment stage output. The separation is intentional. Source: `03_rag_02_ingestion_pipeline.md §FTS5/LLM content separation`.

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

## Active Issues

---


