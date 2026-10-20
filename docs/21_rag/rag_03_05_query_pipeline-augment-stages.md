---
title: "RAG Query Pipeline - Augment Stages"
area: rag
tags:
  - rerank-stage
  - augment-stage
related:
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_03_01_query_pipeline-overview.md
  - rag_03_04_query_pipeline-search-stages.md
  - rag_03_03_query_pipeline-context-and-diagnostics.md
  - rag_04_dto-models-types.md
  - rag_05_01-configuration-reference.md
  - rag_03_06_query_pipeline-helpers-and-cache.md
  - adr_02_06_009_rag-fts5-text-separation.md
---


# RAG Query Pipeline - Augment Stages

## System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
## Configuration → [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md)
## Type Definitions → [rag_04_dto-models-types.md](rag_04_dto-models-types.md)

---

## 5. Stage Details

### 5.4 RerankStage

- `use_rerank=False`: Returns top `rag_top_k` in RRF order (sliced) + `deduplicate_chunks`
- `use_rerank=True`: `RagLLM.cross_encoder_rerank(query, candidates, top_k, rag_min_score)`; raises `RagRerankError` if the LLM fails
- Filters by `rag_min_score`; on `RagRerankError`, `RerankStage.run()` falls back to the RRF-ranked results (see below)
- Deduplication: `deduplicate_chunks(hits, max_chunks_per_doc)` limits the number of hits per URL. It requires input sorted by descending relevance and is applied after reranking (not before), so only the top chunks per document remain.

**Exception Catching Location:** `RerankStage.run()` catches `RagRerankError` (defined in `scripts/rag/exceptions.py`; it derives from `RagLayerError`, not from `RuntimeError`) and falls back to the RRF-ranked results, sliced to `rag_top_k` and deduplicated, recording the fallback reason `rerank_exception`; the stage is reported with status `fallback`. Any other exception propagates to `RagPipeline._run_stage()`, which catches `RuntimeError`, `sqlite3.OperationalError`, `httpx.HTTPStatusError`, `httpx.RequestError`, and `TimeoutError` and converts them into `StageResult(status="failure", fallback_reason=<exception_message>)`. The pipeline as a whole does not stop on such an exception, and subsequent stages (AugmentStage) continue with an empty `ctx.reranked`.

### 5.5 AugmentStage

AugmentStage formats `ctx.reranked` for the LLM. `_format_chunks` (`scripts/rag/stages/augment.py`) is the sole formatting implementation; both AugmentStage and the raw-chunk fallback in `RagPipeline.augment()` call it.

- Formats each chunk as `[Source: {title if title else url} | {url}]\n{sanitize_document(content)}` (the URL stands in when the title is empty)
- Concatenates with `\n\n---\n\n` and wraps with `[RAG_CONTEXT_START]` / `[RAG_CONTEXT_END]`
- Stores in `ctx.augment_result`
- Sanitizes content using `rag.utils.sanitize_document(c.content)` before formatting
- If `reranked` is empty, returns `[RAG_CONTEXT_START]\n\n[RAG_CONTEXT_END]`

**Content-only Invariance Rule:** AugmentStage only formats `content` and never uses `normalized_content`. Meaning: AugmentStage formats and outputs only the raw `content` field, never the search-normalized `normalized_content` field. Rationale: FTS5 indexes `COALESCE(normalized_content, content)`, so `content` alone is always a complete, valid representation, while `normalized_content` is a lossy, non-reconstructible derivative (per ADR-009). Scope: This rule applies specifically to AugmentStage's output formatting, not to the search/indexing layer, which does use `normalized_content` when present. Limitation: For Japanese content, the LLM-facing output does not benefit from Sudachi normalization (stopword removal, etc.) since only the raw `content` is shown. See [ADR-009](../10_adr/adr_02_06_009_rag-fts5-text-separation.md) for rationale, alternatives, and tradeoffs.

**sanitize_document() Contract:** Content sanitization applied before formatting. The function removes known prompt-injection patterns from retrieved chunk content. It covers five pattern categories: "ignore instructions" variants, a "system:" prefix, a "[SYSTEM OVERRIDE]" directive, "disregard instructions" variants, and a "new instructions:" directive. Each matched pattern is replaced with the literal string `[REMOVED]` (not deleted entirely). The function returns a plain `str` containing the sanitized text.

This differs from `sanitize_document_full()`, which also returns a `SanitizeResult` audit trail. `AugmentStage` uses `sanitize_document()` exclusively and does not consume the audit trail.

**Limitations:** Pattern-based matching only catches the five specific phrasings above. Matching is case-insensitive but not semantic — it cannot detect novel or paraphrased injection attempts outside its pattern list.

### 5.6 AugmentRefiner Class (`scripts/rag/augment.py`)

**Purpose:** Owns all HTTP augment and context refinement related state and behavior extracted from `RagPipeline`. Dependencies (HTTP client, `RagConfig`, optional callbacks, diagnostics object, optional `RagLLM`) are injected through the constructor.

The optional constructor parameters fall into three categories by consequence of omission:

- **Observational callbacks** (`on_status`, `set_fetch_result`, `set_fallback_reason`): purely informational — each forwards data to an external caller and has no effect on `AugmentRefiner`'s own HTTP-augment or refiner behavior if omitted. Leaving them as their no-op defaults means the caller loses visibility into those events but nothing else changes.
- **Functionally required** (`llm`): omitting `llm` while `run_refiner()` is invoked with `use_refiner=true` raises `ValueError` at call time; there is no silent degradation.
- **Functionally inert default** (`search_diagnostics`): its default value (a fresh `SearchDiagnostics()`) only determines the diagnostics object's starting state before the first update; omitting it has no other functional consequence.

#### Methods

##### `run_http_augment(query, history_context, rag_url)` — HTTP augment execution

Returns `str | None`:

- `str` (non-empty): HTTP call successful; non-empty context returned
- `""` (empty string): HTTP 200 but `context` field is `""` — valid empty result, not a fallback
- `None`: HTTP error; triggers fallback to in-process pipeline

Side effects: updates `search_diagnostics` (`result_source`, `http_result_kind`, `remote_status_code`, `remote_latency_ms`) and appends a `StageResult` to `last_stage_results`.

##### `run_refiner(reranked, query)` — Context refinement

Returns `RefineResult` (`scripts/rag/pipeline_refiner.py`): `text` is the summarized context, or `None` on failure (raw chunks are then used); `reason` is the failure reason, `None` on success.

Raises `ValueError` if `llm` dependency not injected.

Side effects: appends a `StageResult` with `"success"` or `"fallback"` status to `last_stage_results`, and logs at INFO level when refiner fallback occurs.

##### `map_http_result_kind(kind)` — Static method

Maps the internal HTTP result literal to the `HttpResultKind` enum (see [rag_03_03_query_pipeline-context-and-diagnostics.md](rag_03_03_query_pipeline-context-and-diagnostics.md) section 4.2); `None` maps to `NOT_USED`.

#### Integration with RagPipeline

`RagPipeline` instantiates `AugmentRefiner` via constructor injection and delegates HTTP augment and refiner operations to it. The class maintains its own `SearchDiagnostics` and `StageResult` tracking separate from `RagPipeline`'s own diagnostics.

#### Refiner Fallback Reasons

If summarization fails with `use_refiner=true`, `augment()` falls back to raw chunk formatting. The fallback reason is recorded in `last_stage_results` and `get_diagnostics()["fallback_reasons"]`.

| Reason | Condition |
|---|---|
| `refiner_returned_empty` | LLM response content is `""` or whitespace after `.strip()`. The `if refined:` guard evaluates to `False`. Common causes: rejection due to content policy, empty LLM generation, or prompt format without extractable key points. |
| `refiner_exception: {e}` | An `httpx.HTTPStatusError`, `httpx.RequestError`, or `ValueError` occurred during the LLM call. The exception message is included in the reason string. No retries are performed. |

**No-retry Policy**: Refiner failures are treated as non-critical quality degradations — allowing raw chunks as output. The refiner call is not retried (`scripts/rag/pipeline_refiner.py`). If degraded output cannot be tolerated, completely disable the refiner by setting `use_refiner=false`.

Both reasons can be verified as follows:

- Displayed at INFO level in application logs (augment: refiner fallback (reason=...))
- Available via `pipeline.get_diagnostics()["fallback_reasons"]`, `["refiner_fallback_count"]`, and `["refiner_exception_count"]`

**Refiner counters in `get_diagnostics()` (`scripts/rag/pipeline.py`):**

| Key | Description |
|---|---|
| `refiner_fallback_count` | Number of times the Refiner stage reached `status="fallback"` |
| `refiner_returned_empty` | Count of the above where `fallback_reason == "refiner_returned_empty"` |
| `refiner_exception_count` | Count of the above where `fallback_reason` starts with `"refiner_exception:"` |
| `refiner_exception` | Boolean indicating if `refiner_exception_count > 0` |

## Keywords

- rerank-stage
- augment-stage
- refiner-fallback
- rag
