---
title: "RAG Query Pipeline - Helpers and Retrieval Freshness"
area: rag
tags:
  - rag-repository
  - rag-scorer
  - rag-llm
related:
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_03_01_query_pipeline-overview.md
  - rag_03_03_query_pipeline-context-and-diagnostics.md
  - rag_03_04_query_pipeline-search-stages.md
  - rag_03_05_query_pipeline-augment-stages.md
  - rag_04_dto-models-types.md
  - rag_02_09_ingestion_pipeline-shared-utilities.md
  - rag_05_01-configuration-reference.md
---

# RAG Query Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md)
- Type Definitions → [rag_04_dto-models-types.md](rag_04_dto-models-types.md)

---

## 6. Retrieval Freshness

Every query executes the full retrieval pipeline (`SearchStage`, via `RagPipeline.augment()`) — including repeated identical queries. No query-result cache exists. Committed document additions, updates, and deletions are reflected in the very next query with no cache-invalidation action or service/process restart required. This guarantee is verified by `tests/rag/test_rag_pipeline_no_cache_freshness.py`.

For the status of the semantic cache feature, see the Semantic Cache section of [rag_01_system_overview.md](rag_01_system_overview.md).

---

## 7. Helper Classes

### 7.1 RagRepository (`scripts/rag/repository.py`)

Manages all SQL. For observability, logs `query` / `fts_query` / `top_k` / `elapsed_ms` for every call. See `scripts/rag/repository.py` for detailed implementation and signatures.

**Japanese FTS5 Tokenization:**

The FTS5 query token limit is defined by `_MAX_FTS_TOKENS`, and Japanese tokens use Sudachi part-of-speech categories (`{"Noun", "Verb", "Adjective"}`, excluding particles and auxiliary verbs). English queries use regex tokenization (`[a-zA-Z0-9]+`). Tokens beyond the limit are silently truncated to prevent query explosion; FTS5 metacharacters (double quotes) and whitespace are removed from each token, and empty tokens are discarded. If no valid token remains, an empty FTS5 query (`'""'`) is returned. There is no recorded rationale or load-test data for the limit; it is a heuristic. See `scripts/rag/repository.py` for details.

**Sudachi Lazy Loading:**

Sudachi is loaded upon first use. Dictionary: `core`, SplitMode: `C`. `tokenize_pos_filter(text, keep_pos)` returns `normalized_form()` for tokens whose `part_of_speech()[0]` is in `keep_pos`; raises `RuntimeError` if tokenization fails. See `scripts/rag/repository.py` for details.

**Public Methods:**

See `scripts/rag/repository.py` for details.

- `vector_search`: KNN implementation via `sqlite-vec`.
- `fts_search`: BM25 implementation via FTS5. Raises `sqlite3.OperationalError` on FTS syntax errors (handled by caller).
- `deduplicate_chunks(hits, max_per_doc)` → Limits hits per unique URL; input must be sorted in descending order.

**Module-level Standalone Wrappers:**
- `vector_search(embedding, top_k, db)` → Delegates to `RagRepository(db).vector_search()`
- `fts_search(query, top_k, db)` → Delegates to `RagRepository(db).fts_search()`
- `fetch_full_document(chunk_id, db, window=None)` → Retrieve surrounding chunks for a given chunk_id from the same document. Parameters: `chunk_id` (int, required), `db` (SQLiteHelper, required), `window` (int or None, optional). When `window=None`, returns all chunks from the same document (full expansion); when `window=N`, returns chunks within N positions of chunk_id (±N window range). Results are ordered by `chunk_index` ascending (document reading order). Returns an empty list `[]` when `chunk_id` is not found (valid not-found result, not an error).
- `deduplicate_chunks(hits, max_per_doc)` → Limits hits per unique URL; input must be sorted in descending order.

`cosine_sim` is not a repository method; it is a shared helper in `rag.utils` — see [rag_02_09_ingestion_pipeline-shared-utilities.md](rag_02_09_ingestion_pipeline-shared-utilities.md).

### 7.2 RagScorer (`scripts/rag/repository.py`)

Merges multiple search result lists using RRF (Reciprocal Rank Fusion) via `rrf_merge` (static method). See `scripts/rag/repository.py` for details.

### 7.3 RagLLM (`scripts/rag/llm_client.py`)

Implementation is located below:

- `scripts/rag/llm_client.py` — `RagLLM` class, `get_embedding()`, `summarize_tool_result()`
- `scripts/rag/llm_prompts.py` — Prompt templates, `RagExpansionError`, `RagRerankError`, `MqeParseError`

```python
from rag.llm_client import RagLLM
llm = RagLLM(client=http_client, llm_url="<LLM_URL>")
```

`RagLLM` provides MQE query expansion (`expand_queries`), Cross-Encoder reranking (`cross_encoder_rerank`), tool output summarization (`summarize_tool_result`), and context refining (`refine_context`). See `scripts/rag/llm_client.py` for detailed signatures.

Also provided are module-level functions like `get_embedding` and `summarize_tool_result`. See `scripts/rag/llm_client.py` for these as well.

### 7.4 PipelineRunResult (`scripts/rag/types.py`)

Returned by `RagPipeline.run()`. Its fields are defined in [rag_04_dto-models-types.md](rag_04_dto-models-types.md); the result origin (`result_source`) is carried by `SearchDiagnostics`, described in [rag_03_03_query_pipeline-context-and-diagnostics.md](rag_03_03_query_pipeline-context-and-diagnostics.md).

---

## Keywords

- rag-repository
- rag-scorer
- rag-llm
- rag
