---
title: "RAG Query Pipeline - Tests"
category: rag
tags:
  - rag-tests
  - quality-regression
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_query_pipeline.md
  - 03_rag_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_query_pipeline-stages.md
  - 03_rag_03_query_pipeline-helpers-and-cache.md
  - 03_rag_04_data_model_and_interfaces.md
  - 03_rag_05_configuration_and_operations.md
source:
  - 03_rag_03_query_pipeline.md
---

# RAG Query Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_configuration_and_operations.md](03_rag_05_configuration_and_operations.md)
- Type definitions → [03_rag_04_data_model_and_interfaces.md](03_rag_04_data_model_and_interfaces.md)

---

## 8. Tests

### 8.1 Deterministic regression tests (`tests/test_rag_quality_regression.py`)

Fixtures: in-memory SQLite DB with 3 known documents, fixed-vector mock embedder.

| Test | Mode | Assertion |
|---|---|---|
| `test_rrf_returns_result_for_known_query` | RRF (default) | `len(result.reranked) >= 0` — must not raise |
| `test_no_rrf_returns_result` | No-RRF | `len(result.reranked) >= 0` — must not raise |
| `test_semantic_cache_hit` | RRF + cache | Second identical query returns cached context or reranked results |
| `test_fallback_no_embed_server` | RRF, embed failure | `result.reranked == []` — fallback yields empty result, not exception |
| `test_rrf_score_values_with_known_hits` | `use_rrf=True, rrf_k=60` | Hit in both lists has strictly higher `rrf_score` |
| `test_top_n_retrieval_count` | `use_rrf=True, use_rerank=False, rag_top_k=3` | `len(reranked)==3`, `len(merged)==5` |
| `test_semantic_cache_hit_returns_cached_result` | Direct `SemanticCache` unit | `lookup()` returns stored context |
| `test_semantic_cache_miss_below_threshold` | Direct `SemanticCache` unit | `lookup()` returns `None` when cosine sim < threshold |
| `test_rrf_merged_order_is_descending` | `use_rrf=True` | `merged` is sorted descending by `rrf_score` |

Run: `uv run pytest tests/test_rag_quality_regression.py -v`

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_query_pipeline.md`
- `03_rag_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_query_pipeline-stages.md`
- `03_rag_03_query_pipeline-helpers-and-cache.md`
- `03_rag_04_data_model_and_interfaces.md`
- `03_rag_05_configuration_and_operations.md`

## Keywords

rag-tests
quality-regression
rag
