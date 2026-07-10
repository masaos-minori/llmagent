---
title: "4. Error Handling Reference"
category: rag
tags:
  - rag
  - configuration
related:
  - 03_rag_00_document-guide.md
  - 03_rag_05_configuration_and_operations.md
source:
  - 03_rag_05_configuration_and_operations.md
---

# 4. Error Handling Reference

## 4. Error Handling Reference

### Crawler

| Error | Action |
|---|---|
| HTTP failure | Retry up to `fetch_retry` with exponential backoff (`min(2**i, 10)` sec) |
| URL-level exception | `WARNING` + continue |
| Language not `ja`/`en` | Skip URL |

### ChunkSplitter

| Error | Action |
|---|---|
| Sudachi tokenize error | Return `""`; skip chunk; `WARNING` |
| File-level failure | `ERROR` (traceback); continue to next file |
| Existing chunks | Skip unless `--force` |

### RagIngester

| Error | Action |
|---|---|
| Embed API failure | Retry up to `embed_retry` with exponential backoff |
| Retry exhausted (single chunk) | `WARNING`; skip chunk; continue |
| Invalid `lang` value | `ValueError`; skip URL group; `ERROR` (traceback) |

### RagPipeline

| Error | Action |
|---|---|
| DB open error | Raise `RagPipelineError` (not return `""`) |
| `use_search=False` | Return `""` immediately |
| `rag_service_url` set + failure | Fall back to in-process pipeline |
| Cross-encoder failure | `RagRerankError` is caught as `RuntimeError`, records `StageResult.status="failure"`, and logs a warning. The pipeline continues with `ctx.reranked=[]` (no RRF fallback). `use_rerank=False` uses RRF order + dedup instead. |

---


## Related Documents

- [03_rag_05_configuration_and_operations.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
