---
title: "RAG Query Pipeline - Augment Stages"
category: rag
tags:
  - rerank-stage
  - augment-stage
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_03_04_query_pipeline-search-stages.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_03_01_query_pipeline-overview.md
---

# RAG Query Pipeline - Augment Stages

## System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
## Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
## Type Definitions → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

---

## 5. Stage Details

### 5.4 RerankStage

```python
RerankStage(cfg: RagConfig, llm: RagLLM)
```

- `use_rerank=False`: Returns top `rag_top_k` in RRF order (sliced) + `deduplicate_chunks`
- `use_rerank=True`: `RagLLM.cross_encoder_rerank(query, candidates, top_k, rag_min_score)`; raises `RagRerankError` if the LLM fails
- Filters by `rag_min_score`; there is no fallback on cross-encoder failure (the exception propagates)
- Deduplication: `deduplicate_chunks(hits, max_chunks_per_doc)` — Limits the number of hits per URL; while the function itself does not require sorted input, the caller passes descending results after reranking, so only top chunks remain; applied after reranking (not before)

**Exception Catching Location (Explicit in code):** `RerankStage.run()` itself does not catch exceptions. `RagPipeline` wraps the `run()` execution in a try/except block, catching `RuntimeError` (`RagRerankError` base), `sqlite3.OperationalError`, `httpx.HTTPStatusError`, `httpx.RequestError`, and `TimeoutError`, converting them into `StageResult(status="failure", fallback_reason=<exception_message>)`. Therefore, the pipeline as a whole does not stop on an exception, and subsequent stages (AugmentStage) continue execution by inheriting an empty `ctx.reranked`.

### 5.5 AugmentStage

No constructor (inherits from `PipelineStage`).

**Correction (Explicit in code):** Redundancy in chunk formatting functions has been resolved. The `_format_chunks` function is the sole implementation, and `scripts/rag/pipeline.py` imports it as `_augment_format_chunks` (`from rag.stages.augment import _format_chunks as _augment_format_chunks`). Both AugmentStage (in `augment.py`) and the raw chunk fallback in `RagPipeline.augment()` call this same function.

- Formats `ctx.reranked` as a block in the format `[Source: {title if title else url} | {url}]\n{sanitize_document(content)}`; uses the URL as a fallback if the title is empty
- Concatenates with `\n\n---\n\n` and wraps with `[RAG_CONTEXT_START]` / `[RAG_CONTEXT_END]`
- Stores in `ctx.augment_result`
- Sanitizes content using `rag.utils.sanitize_document(c.content)` before formatting
- If `reranked` is empty, returns `[RAG_CONTEXT_START]\n\n[RAG_CONTEXT_END]`

**Content-only Invariance Rule:** AugmentStage only formats `content` and never uses `normalized_content`. See [ADR-009](../adr/ADR-009-rag-ft5-text-separation.md) for rationale, alternatives, and tradeoffs.

#### RefineResult dataclass (`scripts/rag/pipeline_refiner.py`)

```python
from rag.pipeline_refiner import RefineResult
```

| Field | Type | Description |
|---|---|---|
| `text` | `str \| None` | Summarized context text; falls back to `None` (raw chunks) on failure |
| `reason` | `str \| None` | Failure reason; `None` on success; `"refiner_returned_empty"` or `"refiner_exception: ..."` on fallback |

#### Refiner Fallback Reasons

If summarization fails with `use_refiner=true`, `augment()` falls back to raw chunk formatting. The fallback reason is recorded in `last_stage_results` and `get_diagnostics()["fallback_reasons"]`.

| Reason | Condition |
|---|---|
| `refiner_returned_empty` | LLM response content is `""` or whitespace after `.strip()`. The `if refined:` guard evaluates to `False`. Common causes: rejection due to content policy, empty LLM generation, or prompt format without extractable key points. |
| `refiner_exception: {e}` | An `httpx.HTTPStatusError`, `httpx.RequestError`, or `ValueError` occurred during the LLM call. The exception message is included in the reason string. No retries are performed. |

**No-retry Policy**: Refiner failures are treated as non-critical quality degradations — allowing raw chunks as output. Retrying failed LLM calls offers low expected benefit while increasing latency (transient errors are rare, and content policy rejections will not succeed upon retry). If degraded output cannot be tolerated, completely disable the refiner by setting `use_refiner=false`.

Both reasons can be verified as follows:
- Displayed at INFO level in application logs (augment: refiner fallback (reason=...))
- Displayed as `[warn] refiner fallback: <reason>` in `/rag search` output
- Displayed as `~ Refiner: fallback — <reason>` and summary line `[refiner] fallback: N time(s)` in the stage results of `/rag search --debug`
- Available via `pipeline.get_diagnostics()["fallback_reasons"]`, `["refiner_fallback_count"]`, and `["refiner_exception_count"]`

**Related fields in get_diagnostics() (Explicit in code, scripts/rag/pipeline.py):**

| Key | Description |
|---|---|
| `refiner_fallback_count` | Number of times the Refiner stage reached `status="fallback"` |
| `refiner_returned_empty` | Count of the above where `fallback_reason == "refiner_returned_empty"` |
| `refiner_exception_count` | Count of the above where `fallback_reason` starts with `"refiner_exception:"` |
| `refiner_exception` | Boolean indicating if `refiner_exception_count > 0` |

---

### Related Documents

- [03_rag_00_document-guide.md](03_rag_00_document-guide.md)
- [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- [03_rag_03_01_query_pipeline-overview.md](03_rag_03_01_query_pipeline-overview.md)
- [03_rag_03_04_query_pipeline-search-stages.md](03_rag_03_04_query_pipeline-search-stages.md)
- [03_rag_03_03_query_pipeline-context-and-diagnostics.md](03_rag_03_03_query_pipeline-context-and-diagnostics.md)
- [03_rag_04_05_dto-types.md](03_rag_04_05_dto-types.md)
- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- [03_rag_03_06_query_pipeline-helpers-and-cache.md](03_rag_03_06_query_pipeline-helpers-and-cache.md)
- [03_rag_03_06_query_pipeline-helpers-and-cache.md](03_rag_03_06_query_pipeline-helpers-and-cache.md)
- System security architecture / Trust boundaries / Threat modeling / AuthN/AuthZ / Auditing / Local vs Production / Fail-open/Fail-closed / Prompt injection responsibility boundaries

### Keywords

rerank-stage
augment-stage
refiner-fallback
rag
