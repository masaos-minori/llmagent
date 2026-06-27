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

## Resolved Issues

### [Resolved] `status=success` with `fallback_reason="http_remote_empty"` is semantically confusing (SPEC-02, resolved 2026-06-27)

- **Was:** `status=success` with `fallback_reason="http_remote_empty"` is semantically confusing — `remote_empty` (HTTP 200 with no context) is a success case, not a fallback.
- **Now:** `remote_empty` returns `fallback_reason=None` and `http_result_kind="remote_empty"`, correctly indicating a successful empty remote response without any fallback.
- **See:** `scripts/rag/pipeline.py:436` (fallback_reason=None for empty result), `tests/test_pipeline_http_result_kind.py:test_remote_empty`

---

### [Resolved] RAG data model includes Agent-owned `sessions` and `messages` tables (SPEC-01, resolved 2026-06-27)

- **Was:** RAG data model documentation contained wording that could be read as Agent session tables residing in the same SQLite file for operational convenience.
- **Now:** Clarified in `03_rag_04_data_model_and_interfaces.md` that `sessions` and `messages` tables are owned by the Agent REPL layer, not the RAG layer. They reside in a separate SQLite file (`session.sqlite`) from the RAG database (`rag.sqlite`).
- **See:** `03_rag_04_data_model_and_interfaces.md §2.0`

### [Resolved] `.txt` / `.json` mixed references in RAG ingestion docs and code comments (DOC-01, resolved 2026-06-27)

- **Was:** RAG ingestion documentation and code comments referenced both `.txt` and `.json` artifact file extensions.
- **Now:** All stale `.txt` references in RAG ingestion code comments have been updated to `.json`. Runtime code already uses `.json`.
- **See:** `scripts/rag/ingestion/` — no `.txt` references remain

### [Resolved] `/db fts-rebuild` vs `/db rebuild-fts` command name mismatch (DOC-02, resolved 2026-06-27)

- **Was:** RAG operations docs referenced `/db fts-rebuild` instead of the canonical `/db rebuild-fts`.
- **Now:** Stale reference removed; all docs and implementation use `/db rebuild-fts`.
- **See:** `scripts/agent/commands/cmd_db.py`, `docs/03_rag_90_inconsistencies_and_known_issues.md` (entry removed)

### [Resolved] scripts/rag/llm.py backward-compat re-export (removed 2026-06-26)

- **Was**: `scripts/rag/llm.py` re-exported symbols from `rag.llm_client` and `rag.llm_prompts`
  for backward compatibility.
- **Now**: `rag.llm` module deleted. Use canonical imports directly:
  - `from rag.llm_client import RagLLM, get_embedding, summarize_tool_result`
  - `from rag.llm_prompts import RagExpansionError, RagRerankError`
- **See**: `docs/03_rag_00_document-guide.md` Archive Policy; `docs/03_rag_03_query_pipeline.md §7.3`

---

### [Resolved] PipelineStageResult legacy type (removed 2026-06-26)

- **Was**: `PipelineStageResult` in `scripts/rag/types.py` was an unused legacy type retained for
  backward compatibility.
- **Now**: Deleted. Use `StageResult` from `scripts/rag/stage.py`.
- **See**: `docs/03_rag_04_data_model_and_interfaces.md §5.3`

---
