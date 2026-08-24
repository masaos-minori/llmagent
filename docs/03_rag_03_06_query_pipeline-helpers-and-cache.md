---
title: "RAG Query Pipeline - Helpers and Cache"
area: rag
tags:
  - semantic-cache
  - rag-repository
  - rag-scorer
  - rag-llm
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_04_query_pipeline-search-stages.md
  - 03_rag_03_05_query_pipeline-augment-stages.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
  - 03_rag_03_06_query_pipeline-helpers-and-cache.md
source:
  - 03_rag_03_06_query_pipeline-helpers-and-cache.md
---

# RAG Query Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- Type Definitions → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

---

## 6. SemanticCache (`scripts/rag/cache.py`)

`SemanticCache` implements the `CacheService` protocol (also defined in `rag/cache.py`). This protocol declares only `lookup()` and `put()`; where substitutability is important, callers should type against `CacheService` rather than `SemanticCache` directly.

```python
from rag.cache import SemanticCache  # defined in SemanticCache class; imported by rag.pipeline

cache = SemanticCache(max_size=100, threshold=0.92)
```

"`SemanticCache` implements the `CacheService` protocol and provides `lookup()` and `put()` methods. It also features `prune()` using a FIFO policy for eviction, a `size` property, and an `invalidate()` method that atomically clears all entries and increments the `generation` counter. See `scripts/rag/cache.py` for detailed signatures."

**Behavior verified in tests (`tests/test_rag_quality_regression.py::test_semantic_cache_generation_invalidation`):** Calling `invalidate()` increments `generation` by 1, and all existing entries immediately stop hitting on `lookup()` (`size == 0`).

### RagPipeline.invalidate_cache()

```python
RagPipeline.invalidate_cache(self) -> None
```

Delegates to `self.semantic_cache.invalidate()`. Called only when the MCP `rag_pipeline` service's `fmt_delete_document()` succeeds.

**Implementation Intent:** To discard the cache known to this pipeline instance after corpus-changing operations (e.g., MCP `rag_delete_document`), ensuring subsequent queries do not return context for deleted documents. `SemanticCache.invalidate()` is implemented thread-safely using `threading.RLock` (see `scripts/rag/cache.py`).

### Cache Freshness After CLI Ingestion

The MCP `rag_delete_document` invalidates the `RagPipeline.semantic_cache` within the caller's MCP process via `invalidate_cache()` — this clears the cache **within a single process only**. CLI ingestion (`uv run python -m rag.ingestion.ingester`) runs in a **separate process** and cannot access the memory cache of the MCP service. **If immediate query freshness is required after CLI ingestion, you must restart the rag-pipeline-mcp service (or the agent process, or the MCP server in subprocess mode)** — this is an operational procedure and is not performed automatically by CLI ingestion. Without a restart, cached entries created before ingestion may return stale context for a limited window until they naturally expire through the cache's own Eviction/TTL ([see cache configuration]).

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_04_query_pipeline-search-stages.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache.md`

## Keywords

semantic-cache
rag-repository
rag-scorer
rag-llm
rag

---

# RAG Query Pipeline Implementation Details

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- Type Definitions → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

---

## 7a. Helper Classes

### 7.1 RagRepository (`scripts/rag/repository.py`)

Manages all SQL. For observability, logs `query` / `fts_query` / `top_k` / `elapsed_ms` for every call. See `scripts/rag/repository.py` for detailed implementation and signatures.

**Japanese FTS5 Tokenization:**

The FTS5 query token limit is 20, and Japanese tokens use Sudachi part-of-speech categories (`{"Noun", "Verb", "Adjective"}`). See `scripts/rag/repository.py` for details.

**Sudachi Lazy Loading:**

Sudachi is loaded upon first use. Dictionary: `core`, SplitMode: `C`. `tokenize_pos_filter(text, keep_pos)` returns `normalized_form()` for tokens whose `part_of_speech()[0]` is in `keep_pos`; raises `RuntimeError` if tokenization fails. See `scripts/rag/repository.py` for details.

**Public Methods:**

See `scripts/rag/repository.py` for details.

- `vector_search`: KNN implementation via `sqlite-vec`.
- `fts_search`: BM25 implementation via FTS5. Raises `sqlite3.OperationalError` on FTS syntax errors (handled by caller).
- `fetch_full_document(chunk_id, db, window=None)` $\rightarrow$ Fetches chunks for the same document in ascending order of `chunk_index`; `window=N` $\rightarrow$ $\pm N$.
- `deduplicate_chunks(hits, max_per_doc)` $\rightarrow$ Limits hits per unique URL; input must be sorted in descending order.
- `cosine_sim(a, b) -> float` $\rightarrow$ Cosine similarity; returns `0.0` for zero vectors.

**Module-level Standalone Wrappers:**
- `vector_search(embedding, top_k, db)` $\rightarrow$ Delegates to `RagRepository(db).vector_search()`
- `fts_search(query, top_k, db)` $\rightarrow$ Delegates to `RagRepository(db).fts_search()`
- `fetch_full_document(chunk_id, db, window=None)` $\rightarrow$ Fetches chunks for the same document in ascending order of `chunk_index`; `window=N` $\rightarrow$ $\pm N$
- `deduplicate_chunks(hits, max_per_doc)` $\rightarrow$ Limits hits per unique URL; input must be sorted in descending order.
- `cosine_sim(a, b) -> float` $\rightarrow$ Cosine similarity; returns `0.0` for zero vectors.

### 7.2 RagScorer (`scripts/rag/repository.py`)

Merges multiple search result lists using RRF (Reciprocal Rank Fusion) via `rrf_merge` (static method). See `scripts/rag/repository.py` for details.

### 7.3 RagLLM (`scripts/rag/llm_client.py`)

Implementation is located below:

- `scripts/rag/llm_client.py` — `RagLLM` class, `get_embedding()`, `summarize_tool_result()`
- `scripts/rag/llm_prompts.py` — Prompt templates, `RagExpansionError`, `RagRerankError`, `MqeParseError`

```python
from rag.llm_client import RagLLM
llm = RagLLM(client=http_client, llm_url="http://127.0.0.1:8080/v1/chat/completions")
```

**Correction (Explicit in code):** Duplicate `logger = logging.getLogger(__name__)` has been resolved. It now exists only once in `scripts/rag/llm_client.py`.

`RagLLM` provides MQE query expansion (`expand_queries`), Cross-Encoder reranking (`cross_encoder_rerank`), tool output summarization (`summarize_tool_result`), and context refining (`refine_context`). See `scripts/rag/llm_client.py` for detailed signatures.

Also provided are module-level functions like `get_embedding` and `summarize_tool_result`. See `scripts/rag/llm_client.py` for these as well.

### 7.4 PipelineRunResult (`scripts/rag/types.py`)

```python
@dataclass
class PipelineRunResult:
    queries: list[str]
    search_results: list[list[RawHit]]
    merged: list[RagHit]
    reranked: list[RagHit]
    stage_results: list[StageResult]
    diagnostics: SearchDiagnostics
```

Returned by `RagPipeline.run()`.

**Note on confusion:** There are two fields with the same name but different types.
- `SearchDiagnostics.result_source: ResultSource` (`rag/models_result.py`) — Takes `ResultSource.LOCAL` (default), `REMOTE`, or `FALLBACK`; updated via `dataclasses.replace()` during HTTP augment execution.
