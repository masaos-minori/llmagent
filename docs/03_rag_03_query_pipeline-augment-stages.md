---
title: "RAG Query Pipeline - Augment Stages"
category: rag
tags:
  - rerank-stage
  - augment-stage
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_query_pipeline.md
  - 03_rag_03_query_pipeline-search-stages.md
  - 03_rag_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_04_data_model_and_interfaces.md
  - 03_rag_05_configuration_and_operations.md
source:
  - 03_rag_03_query_pipeline.md
---

# RAG Query Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_configuration_and_operations.md](03_rag_05_1-configuration-reference.md)
- Type definitions → [03_rag_04_data_model_and_interfaces.md](03_rag_04_dto-models_data.md)

---

## 5. Stage Details

### 5.4 RerankStage

```python
RerankStage(cfg: RagConfig, llm: RagLLM)
```

- `use_rerank=False`: return top `rag_top_k` by RRF order (slice) + `deduplicate_chunks`
- `use_rerank=True`: `RagLLM.cross_encoder_rerank(query, candidates, top_k, rag_min_score)`; raises `RagRerankError` on LLM failure
- Filters by `rag_min_score`; no fallback on cross-encoder failure (exception propagates)
- Deduplication: `deduplicate_chunks(hits, max_chunks_per_doc)` — caps same-URL hits; input must be descending-sorted; applied after reranking (not before)

### 5.5 AugmentStage

No constructor (inherits from `PipelineStage`).

**Note:** Chunk formatting function is duplicated between `scripts/rag/pipeline.py:368` (static method) and `scripts/rag/stages/augment.py:11` (module function). They produce identical output but are separate copies. AugmentStage uses the augment.py version; `RagPipeline.augment()` uses the pipeline.py version for raw-chunk fallback (line 474).

- Formats `ctx.reranked` as `[Source: {title if title else url} | {url}]\n{sanitize_document(content)}` blocks; when title is empty, uses URL as fallback
- Joined by `\n\n---\n\n`; wrapped in `[RAG_CONTEXT_START]` / `[RAG_CONTEXT_END]`
- Stored in `ctx.augment_result`
- Uses `sanitize_document(c.content)` from `rag.utils` to sanitize content before formatting
- Empty reranked returns `[RAG_CONTEXT_START]\n\n[RAG_CONTEXT_END]`

**Content-only invariant (DESIGN-2):** AugmentStage formats `content` only — never `normalized_content`.

- `chunks.content` is the original chunk text and the **only** text used for LLM context
- `chunks.normalized_content` is Sudachi-normalized Japanese text used **exclusively** for FTS5 search indexing; it must never appear in LLM context
- Replacing `content` with `normalized_content` would degrade LLM context quality (Sudachi-normalized text loses original readability)
- RAG context blocks must always contain original readable chunk text

#### RefineResult dataclass (`scripts/rag/pipeline_refiner.py`)

```python
from rag.pipeline_refiner import RefineResult
```

| Field | Type | Description |
|---|---|---|
| `text` | `str \| None` | Refined context text; `None` on failure (fallback to raw chunks) |
| `reason` | `str \| None` | Reason for failure; `None` on success; `"refiner_returned_empty"` or `"refiner_exception: ..."` on fallback |

#### Refiner fallback reasons

When `use_refiner=true` and refinement fails, `augment()` falls back to raw-chunk
formatting. The fallback reason is recorded in `last_stage_results` and
`get_diagnostics()["fallback_reasons"]`.

| Reason | Condition |
|---|---|
| `refiner_returned_empty` | LLM response content is `""` or whitespace-only after `.strip()`. The `if refined:` guard is falsy. Common causes: content-policy refusal, empty LLM generation, prompt format producing no extractable key points. |
| `refiner_exception: {e}` | `httpx.HTTPStatusError`, `httpx.RequestError`, or `ValueError` raised during the LLM call. The exception message is included in the reason string. Not retried. |

**No retry policy**: Refiner failure is treated as a non-critical degradation — raw chunks are acceptable output. Retrying a failed LLM call adds latency with low expected benefit (transient errors are rare; content-policy refusals will not succeed on retry). Use `use_refiner=false` to disable the refiner entirely when degraded output is not acceptable.

Both reasons are:
- Visible at INFO level in application logs (`augment: refiner fallback (reason=...)`)
- Visible in `/rag search` output as `[warn] refiner fallback: <reason>`
- Visible in `/rag search --debug` stage results as `~ Refiner: fallback — <reason>` and summary line `[refiner] fallback: N time(s)`
- Available via `pipeline.get_diagnostics()["fallback_reasons"]`, `["refiner_fallback_count"]`, `["refiner_exception_count"]`

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_query_pipeline.md`
- `03_rag_03_query_pipeline-search-stages.md`
- `03_rag_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_04_data_model_and_interfaces.md`
- `03_rag_05_configuration_and_operations.md`

## Keywords

rerank-stage
augment-stage
rag
