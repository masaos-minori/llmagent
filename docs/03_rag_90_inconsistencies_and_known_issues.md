---
title: "RAG Inconsistencies and Known Issues"
category: rag
tags:
  - rag
  - rag
  - inconsistencies
  - known-issues
  - bugs
  - open-questions
related:
  - 03_rag_00_document-guide.md
  - 03_rag_00_document-guide.md
  - 03_rag_91_design_notes-part1.md
  - 03_rag_91_design_notes-part2.md
---

# RAG Inconsistencies and Known Issues

This file catalogs known bugs, spec conflicts, document inconsistencies, and open questions
discovered during the restructuring of RAG documentation.

Each entry uses: Type / Impact / Description / Safe interpretation / Recommended action / Source.

---

## Confirmed Design Decisions

### DESIGN-2: FTS5 uses `normalized_content`; LLM receives `content`

- **Type:** Confirmed design decision
- **Impact scope:** `chunks` table, `chunks_fts` virtual table, `scripts/rag/repository.py`, `scripts/rag/stages/augment.py`
- **Invariants (non-negotiable):**
  - `chunks.content` is the original chunk text and the **only** text used for LLM context.
  - `chunks.normalized_content` is Sudachi-normalized Japanese text used **exclusively** for FTS5 search indexing; it must never appear in LLM context.
  - FTS5 indexes `COALESCE(normalized_content, content)` via the `chunks_ai` trigger.
  - Japanese chunks store Sudachi-normalized space-joined text in `normalized_content`. English/code chunks keep `normalized_content = NULL`; FTS5 falls back to `content`.
  - `AugmentStage` must always output `content`, never `normalized_content`.
- **Description:** Japanese chunks store two text representations. `chunks.content` (original text) is injected into the LLM context by `AugmentStage`. `chunks.normalized_content` (Sudachi-normalized) is indexed by the `chunks_ai` trigger into `chunks_fts`. FTS5 query-side also normalizes Japanese terms using Sudachi POS filtering. This separation ensures LLM receives readable original text while BM25 search uses morphologically normalized forms.
- **Notes for AI reference:** Never replace `content` with `normalized_content` in the Augment stage output. The separation is intentional and confirmed. Source: `03_rag_02_01_ingestion_pipeline-overview.md §FTS5/LLM content separation`, `03_rag_03_01_query_pipeline-overview.md §5.5 AugmentStage`.

---

### DESIGN-3: Separation of responsibilities among `documents`, `chunks`, `chunks_fts`, `chunks_vec`

- **Type:** Confirmed design decision
- **Impact scope:** DB schema, all ingestion and query code
- **Invariants (non-negotiable):**
  - `documents` and `chunks` are **canonical data stores**; all mutations go through them.
  - `chunks_fts` and `chunks_vec` are **derived indexes**; application code must treat them as read-only.
  - `chunks_fts` sync: trigger-based (`chunks_ai`/`chunks_au`/`chunks_ad`); never INSERT/UPDATE directly. Manual edits to `chunks_fts` are prohibited — use `/db rag rebuild-fts` instead.
  - `chunks_vec` sync: ingestion-time INSERT and explicit DELETE; no FK constraint (sqlite-vec limitation).
  - Deletion order for force-reinsertion: `chunks_vec` first → `chunks` → `documents` (mandatory to avoid orphaned vector records).
  - RAG consistency checks (`/db consistency`) validate synchronization between canonical `chunks` and derived indexes `chunks_fts` and `chunks_vec`.
- **Description:**
  - `documents`: canonical URL/document metadata (url, title, lang, fetched_at, etag, last_modified, chunking_strategy); one row per URL.
  - `chunks`: canonical chunk text and position data (content, normalized_content, chunk_index, chunk_type); FK to `documents` via `doc_id` (ON DELETE CASCADE).
  - `chunks_fts`: derived FTS5/BM25 full-text index; auto-synced by triggers using `COALESCE(normalized_content, content)`; BM25 search only. Must not be manually edited — use `/db rag rebuild-fts` to repair.
  - `chunks_vec`: derived sqlite-vec KNN vector index; float32 embedding BLOB; KNN search only.
- **RAG consistency checks:** validate synchronization between canonical data and derived indexes:
  - `fts_gap`: number of chunks missing from `chunks_fts` (repair: `/db rag rebuild-fts`)
  - `fts_orphan_count`: FTS entries without matching chunks (data loss risk; repair: `/db rag rebuild-fts`)
  - `orphan_vec_count`: vector rows without matching chunks (repair: `ingester.py --force`)
- **Notes for AI reference:** sqlite-vec virtual tables do not support standard FK constraints. RAG consistency checks (`/db consistency`) validate synchronization between canonical `chunks` and derived indexes `chunks_fts` and `chunks_vec`. Source: `03_rag_04_05_dto-types.md §DB Schema`, `03_rag_05_1-configuration-reference.md §RAG index consistency checks`.

---

---

## Cache Invalidation

### OPEN-01: CLI ingestion does not invalidate the semantic cache

**Status:** Open design question (verified against implementation 2026-07-09)
**Affected code:** `scripts/rag/ingestion/ingester.py` — `main()` calls
`ingester.ingest_all(args.force)` at line 620
**Impact:** After a CLI `rag-ingest` run, any running `RagPipeline` instance (e.g. inside
the MCP server) retains stale semantic cache entries. Subsequent queries may return cached
results that no longer reflect the updated document corpus.
**Root cause:** `main()` calls `ingester.ingest_all(args.force)` without passing an
`on_ingest_complete` callback. `RagIngester.ingest_all()` accepts
`on_ingest_complete: Callable[[], None] | None = None` (line 95) and forwards it (line 132);
this callback is the only mechanism for post-ingestion cache invalidation.
**Recommended action:** Pass `pipeline.semantic_cache.invalidate` as `on_ingest_complete`
in callers that require fresh results immediately after ingestion.

---

### OPEN-02: `delete_document()` does not invalidate the semantic cache

**Status:** Open design question (verified against implementation 2026-07-09 — affected
code path updated, root cause unchanged)
**Affected code:** The deletion logic moved out of `service.py` since this entry was
written. Actual chain: `scripts/mcp/rag_pipeline/service.py::RagPipelineMCPService.fmt_delete_document()`
(the `rag_delete_document` MCP tool handler, line 197) calls
`scripts/mcp/rag_pipeline/document_manager.py::DocumentManager.delete_document()` (line 72),
which deletes `chunks_vec` and `documents` rows directly via SQL.
**Impact:** After a document is deleted via `rag_delete_document` MCP tool, cached semantic
search results that referenced the deleted document remain in `SemanticCache` until the
next `invalidate()` call or process restart.
**Root cause:** Neither `fmt_delete_document()` nor `DocumentManager.delete_document()` calls
`semantic_cache.invalidate()`. `DocumentManager` holds no reference to the pipeline or its
cache, so it cannot invalidate directly; only `RagPipelineMCPService` (which holds
`self._pipeline: RagPipelineLike`, and `RagPipeline.semantic_cache` — see
`scripts/rag/pipeline.py:125`) can. No other invalidation path exists in the MCP service.
**Recommended action:** In `fmt_delete_document()`, after `self._doc_mgr.delete_document(url)`
returns `True`, call `self._pipeline.semantic_cache.invalidate()` (guard for
`self._pipeline is None`, matching `_pipeline_or_raise()`'s existing pattern), or document
that callers must trigger cache invalidation separately.

---

## Active Issues

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_91_design_notes-part1.md`
- `03_rag_91_design_notes-part2.md`

## Keywords

rag
inconsistencies
known-issues
bugs
open-questions
