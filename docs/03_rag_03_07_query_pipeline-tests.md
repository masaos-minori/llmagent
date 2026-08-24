---
title: "RAG Query Pipeline - Tests"
area: rag
tags:
  - rag-tests
  - quality-regression
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_04_query_pipeline-search-stages.md
  - 03_rag_03_05_query_pipeline-augment-stages.md
  - 03_rag_03_06_query_pipeline-helpers-and-cache.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_03_01_query_pipeline-overview.md
---


# RAG Query Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- Type Definitions → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

---

## 8. Tests

### 8.1 Deterministic Regression Tests (`tests/test_rag_quality_regression.py`)

This test suite verifies that the key operational characteristics of the RAG query pipeline are maintained deterministically. For detailed test cases and assertions, see [tests/test_rag_quality_regression.py](tests/test_rag_quality_regression.py).

#### Key Characteristics Verified:
- **RRF and Fusion Mode Behavior**:
  - Hit deduplication and descending sorting by `rrf_score` in RRF mode.
  - Handling of `rrf_score == 0.0` in non-RRF (deduplication only) mode.
  - Fallback behavior when no embedding server is configured (returns empty results).
- **Semantic Cache Behavior**:
  - Context retrieval on cache hits, misses below threshold, and entry eviction via `invalidate()`.
- **Accuracy of Diagnostics**:
  - Accurate counting of fusion modes (`rrf` vs `dedup_only`), FTS errors, and embedding failures.
  - Tracking of fallback occurrences and exceptions in the Refiner stage.
- **Search Result Constraints**:
  - Slicing of the `reranked` list based on `rag_top_k`, and retention of all hits in the `merged` list.

**Execution Command:**
`uv run pytest tests/test_rag_quality_regression.py -v`

### 8.2 References

This section is limited to the scope of `tests/test_rag_quality_regression.py`. Other tests covering individual stages or service layers are included in the following files:
- `test_rag_pipeline.py`
- `test_rag_pipeline_stage.py`
- `test_rag_pipeline_service.py`
- `test_rag_pipeline_mcp_service.py`
- `test_mcp_rag_pipeline.py`

These tests cover individual stages (`MqeStage`/`SearchStage`/`FusionStage`/`RerankStage`/`AugmentStage`) and the `pipeline_service`/MCP service layer separately. This section focuses specifically on deterministic quality regression (`test_rag_quality_regression.py`).

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_04_query_pipeline-search-stages.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

rag-tests
quality-regression
semantic-cache-generation
refiner-diagnostics
rag
