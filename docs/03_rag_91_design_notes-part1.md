---
title: "DESIGN-2 FTS5 Content Separation"
category: rag
tags:
  - rag
  - design-decision
  - fts5
related:
  - 03_rag_00_document-guide.md
  - 03_rag_91_design_notes.md
source:
  - 03_rag_91_design_notes.md
---

# DESIGN-2 FTS5 Content Separation


## DESIGN-2: FTS5 uses `normalized_content`; LLM receives `content`

- **Type:** Confirmed design decision
- **Impact scope:** `chunks` table, `chunks_fts` virtual table, `scripts/rag/repository.py`, `scripts/rag/stages/augment.py`
- **Invariants (non-negotiable):**
  - `chunks.content` is the original chunk text and the **only** text used for LLM context.
  - `chunks.normalized_content` is Sudachi-normalized Japanese text used **exclusively** for FTS5 search indexing; it must never appear in LLM context.
  - FTS5 indexes `COALESCE(normalized_content, content)` via the `chunks_ai` trigger.
  - Japanese chunks store Sudachi-normalized space-joined text in `normalized_content`. English/code chunks keep `normalized_content = NULL`; FTS5 falls back to `content`.
  - `AugmentStage` must always output `content`, never `normalized_content`.
- **Description:** Japanese chunks store two text representations. `chunks.content` (original text) is injected into the LLM context by `AugmentStage`. `chunks.normalized_content` (Sudachi-normalized) is indexed by the `chunks_ai` trigger into `chunks_fts`. FTS5 query-side also normalizes Japanese terms using Sudachi POS filtering. This separation ensures LLM receives readable original text while BM25 search uses morphologically normalized forms.
- **Notes for AI reference:** Never replace `content` with `normalized_content` in the Augment stage output. The separation is intentional and confirmed. Source: `03_rag_02_ingestion_pipeline-overview.md §FTS5/LLM content separation`, `03_rag_03_query_pipeline.md §5.5 AugmentStage`.

---



## DESIGN-3: Separation of responsibilities among `documents`, `chunks`, `chunks_fts`, `chunks_vec`

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
- **Notes for AI reference:** sqlite-vec virtual tables do not support standard FK constraints. RAG consistency checks (`/db consistency`) validate synchronization between canonical `chunks` and derived indexes `chunks_fts` and `chunks_vec`. Source: `03_rag_04_dto-types.md §DB Schema`, `03_rag_05_1-configuration-reference.md §RAG index consistency checks`.

---



## DESIGN-2 Regression Test Expectations

**Existing tests:**

| Test | File | Coverage |
|------|------|----------|
| COALESCE fallback for NULL `normalized_content` | `tests/test_fts_fallback.py` | ✓ English/code chunks indexed on `content` when `normalized_content` is NULL |
| Mixed-language document indexing | `tests/test_fts_fallback.py` | ✓ Japanese chunk uses `normalized_content`; English chunk uses `content` |
| Empty string vs NULL `normalized_content` | `tests/test_fts_fallback.py` | ✓ `""` ≠ NULL (COALESCE semantics) |
| TEST-DESIGN2-01: Chunks output contains only `content` field | `tests/test_rag_pipeline.py::TestFormatChunksDesign2` | ✓ `test_content_appears_in_output`, `test_normalized_content_does_not_appear` |
| TEST-DESIGN2-02: Japanese FTS search returns original `content` | `tests/test_fts_fallback.py` | ✓ Covered by `test_code_search_returns_original_content` and `test_mixed_japanese_english_document` |
| TEST-DESIGN2-03: LLM context does not contain `normalized_content` when it differs from `content` | `tests/test_rag_pipeline.py::TestFormatChunksDesign2`, `tests/test_rag_pipeline_stage.py::TestAugmentStage` | ✓ `test_normalized_differs_from_content_not_in_output`, `test_augment_stage_normalized_does_not_leak` |
| TEST-DESIGN2-01 (AugmentStage path): AugmentStage outputs `content` only | `tests/test_rag_pipeline_stage.py::TestAugmentStage` | ✓ `test_augment_stage_content_only_invariant`, `test_augment_stage_normalized_does_not_leak` |

**Missing tests:**

| Test ID | Description | Priority |
|---------|-------------|----------|
| _(none — all DESIGN-2 tests are now implemented)_ | | |

---


## Related Documents

- [03_rag_91_design_notes.md](03_rag_91_design_notes-part1.md)

## Keywords

design-decision
fts5
content-separation
