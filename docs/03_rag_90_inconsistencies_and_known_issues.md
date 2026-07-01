# RAG Inconsistencies and Known Issues

This file catalogs known bugs, spec conflicts, document inconsistencies, and open questions
discovered during the restructuring of RAG documentation.

Each entry uses: Type / Impact / Description / Safe interpretation / Recommended action / Source.

---

## Design Notes (Required Explicit Items)

### DESIGN-2: FTS5 uses `normalized_content`; LLM receives `content`

- **Type:** Confirmed design decision
- **Impact scope:** `chunks` table, `chunks_fts` virtual table, `scripts/rag/repository.py _build_fts_query()`, `scripts/rag/stages/augment.py`
- **Invariants (non-negotiable):**
  - `chunks.content` is the original chunk text and the **only** text used for LLM context.
  - `chunks.normalized_content` is Sudachi-normalized Japanese text used **exclusively** for FTS5 search indexing; it must never appear in LLM context.
  - FTS5 indexes `COALESCE(normalized_content, content)` via the `chunks_ai` trigger.
  - Japanese chunks store Sudachi `normalized_form()` space-joined text in `normalized_content`. English/code chunks keep `normalized_content = NULL`; FTS5 falls back to `content`.
  - `AugmentStage` must always output `content`, never `normalized_content`.
- **Description:** Japanese chunks store two text representations. `chunks.content` (original text) is injected into the LLM context by `AugmentStage`. `chunks.normalized_content` (Sudachi-normalized) is indexed by the `chunks_ai` trigger into `chunks_fts`. FTS5 query-side also normalizes Japanese terms in `_build_fts_tokens_ja()`. This separation ensures LLM receives readable original text while BM25 search uses morphologically normalized forms.
- **Notes for AI reference:** Never replace `content` with `normalized_content` in the Augment stage output. The separation is intentional and confirmed. Source: `03_rag_02_ingestion_pipeline.md §FTS5/LLM content separation`.

---

### DESIGN-3: Separation of responsibilities among `documents`, `chunks`, `chunks_fts`, `chunks_vec`

- **Type:** Confirmed design decision
- **Impact scope:** DB schema, all ingestion and query code
- **Invariants (non-negotiable):**
  - `documents` and `chunks` are **canonical data stores**; all mutations go through them.
  - `chunks_fts` and `chunks_vec` are **derived indexes**; application code must treat them as read-only.
  - `chunks_fts` sync: trigger-based (`chunks_ai`/`chunks_au`/`chunks_ad`); never INSERT/UPDATE directly.
  - `chunks_vec` sync: ingestion-time INSERT and explicit DELETE; no FK constraint (sqlite-vec limitation).
  - Deletion order for force-reinsertion: `chunks_vec` first → `chunks` → `documents` (mandatory to avoid orphaned vector records).
- **Description:**
  - `documents`: canonical URL/document metadata (url, title, lang, fetched_at, etag, last_modified, chunking_strategy); one row per URL.
  - `chunks`: canonical chunk text and position data (content, normalized_content, chunk_index, chunk_type); FK to `documents` via `doc_id` (ON DELETE CASCADE).
  - `chunks_fts`: derived FTS5/BM25 full-text index; auto-synced by triggers using `COALESCE(normalized_content, content)`; BM25 search only.
  - `chunks_vec`: derived sqlite-vec KNN vector index; float32 embedding BLOB; KNN search only.
- **Notes for AI reference:** sqlite-vec virtual tables do not support standard FK constraints. Source: `03_rag_04_data_model_and_interfaces.md §DB Schema`.

---

## Active Issues

---



