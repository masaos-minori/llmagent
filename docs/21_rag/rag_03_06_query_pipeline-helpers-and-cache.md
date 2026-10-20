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
  - rag_05_04-error-handling-reference.md
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

Owns all SQL for retrieval. For observability, logs `query` / `fts_query` / `top_k` / `elapsed_ms` for every call. KNN search runs via `sqlite-vec` (`vector_search`) and BM25 search via FTS5 (`fts_search`); `fts_search` raises `sqlite3.OperationalError` on FTS syntax errors, which the caller handles. `fetch_full_document(chunk_id, db, window=None)` returns surrounding chunks of the same document in reading order (`window=None` returns the whole document); an unknown `chunk_id` yields `[]`, a valid not-found result rather than an error. See `scripts/rag/repository.py` for signatures.

**Japanese FTS5 Tokenization:**

The FTS5 query token limit is defined by `_MAX_FTS_TOKENS`, and Japanese tokens use Sudachi part-of-speech categories (`{"Noun", "Verb", "Adjective"}`, excluding particles and auxiliary verbs). English queries use regex tokenization (`[a-zA-Z0-9]+`). Tokens beyond the limit are silently truncated to prevent query explosion; FTS5 metacharacters (double quotes) and whitespace are removed from each token, and empty tokens are discarded. If no valid token remains, an empty FTS5 query (`'""'`) is returned. There is no recorded rationale or load-test data for the limit; it is a heuristic.

**Sudachi Lazy Loading:**

Sudachi is loaded upon first use (dictionary `core`, SplitMode `C`). `tokenize_pos_filter(text, keep_pos)` keeps only tokens whose part of speech is in `keep_pos`; it raises `RuntimeError` if tokenization fails.

**Deduplication:** `deduplicate_chunks(hits, max_per_doc)` limits hits per unique URL; its input must already be sorted in descending relevance.

`cosine_sim` is not a repository method; it is a shared helper in `rag.utils` — see [rag_02_09_ingestion_pipeline-shared-utilities.md](rag_02_09_ingestion_pipeline-shared-utilities.md).

### 7.2 RagScorer (`scripts/rag/repository.py`)

Merges multiple search result lists using RRF (Reciprocal Rank Fusion) via `rrf_merge` (static method).

### 7.3 RagLLM (`scripts/rag/llm_client.py`)

`RagLLM` provides MQE query expansion (`expand_queries`), Cross-Encoder reranking (`cross_encoder_rerank`), tool output summarization (`summarize_tool_result`), and context refining (`refine_context`); the module also provides `get_embedding`. Prompt templates and `MqeParseError` live in `scripts/rag/llm_prompts.py`; `RagExpansionError` and `RagRerankError` live in `scripts/rag/exceptions.py` (see [rag_05_04-error-handling-reference.md](rag_05_04-error-handling-reference.md)).

### 7.4 PipelineRunResult (`scripts/rag/types.py`)

Returned by `RagPipeline.run()`. Its fields are defined by the dataclass in `scripts/rag/types.py` (summary in [rag_04_dto-models-types.md](rag_04_dto-models-types.md)); the result origin (`result_source`) is carried by `SearchDiagnostics`, described in [rag_03_03_query_pipeline-context-and-diagnostics.md](rag_03_03_query_pipeline-context-and-diagnostics.md).

## Keywords

- rag-repository
- rag-scorer
- rag-llm
- rag
