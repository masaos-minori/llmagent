---
title: "RAG Query Pipeline - Helpers and Cache"
category: rag
tags:
  - semantic-cache
  - rag-repository
  - rag-scorer
  - rag-llm
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_query_pipeline.md
  - 03_rag_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_query_pipeline-stages.md
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

## 6. SemanticCache (`scripts/rag/cache.py`)

```python
from rag.cache import SemanticCache  # defined in rag/cache.py:30; imported by rag/pipeline.py:30

cache = SemanticCache(max_size=100, threshold=0.92)
```

| Method / Property | Signature | Description |
|---|---|---|
| `lookup` | `(embedding, history_context="") -> str \| None` | Return cached result if cosine similarity ≥ threshold among matching `history_context` entries; raises `ValueError` on embedding dimension mismatch; else `None` |
| `put` | `(embedding, history_context, context_str) -> None` | Store entry; `history_context` is part of cache key; raises `ValueError` on embedding dimension mismatch; calls `prune()` after |
| `prune` | `() -> None` | Remove oldest entries (FIFO) until `len ≤ max_size` |
| `size` | property `int` | Current entry count |
| `invalidate` | `() -> None` | Bump generation counter and clear all cached entries atomically |
| `generation` | property `int` | Current cache invalidation generation count |

Cache is initialized in `RagPipeline.__init__` using `cfg.semantic_cache_max_size` and
`cfg.semantic_cache_threshold`.

---

## 7. Helper Classes

### 7.1 RagRepository (`scripts/rag/repository.py`)

Owns all SQL. Used internally by stages. Logs query / fts_query / top_k / elapsed_ms on every call for observability.

**SQL queries:**

| Method | SQL |
|---|---|
| `vector_search` | `SELECT c.chunk_id, c.content, d.url, d.title, cv.distance FROM chunks_vec cv JOIN chunks c ON c.chunk_id = cv.chunk_id JOIN documents d ON d.doc_id = c.doc_id WHERE cv.embedding MATCH ? ORDER BY cv.distance LIMIT ?` |
| `fts_search` | `SELECT c.chunk_id, c.content, d.url, d.title, bm25(chunks_fts) AS bm25_score FROM chunks_fts JOIN chunks c ON c.chunk_id = chunks_fts.rowid JOIN documents d ON d.doc_id = c.doc_id WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts) LIMIT ?` |

**Japanese FTS5 tokenization:**

| Constant | Value | Description |
|---|---|---|
| Maximum tokens in an FTS5 query | 20 | |
| Sudachi POS categories retained for Japanese tokens | `{"名詞", "動詞", "形容詞"}` | |

**Lazy Sudachi loading:**

Sudachi is loaded on first use. Dictionary: `core`, SplitMode: `C`.

| Method | Signature | Description |
|---|---|---|
| `tokenize_pos_filter` | `(text: str, keep_pos: frozenset[str]) -> list[str]` | Return normalized_form() for tokens whose part_of_speech()[0] is in keep_pos; raises RuntimeError on tokenization failure |

**Public methods:**

| Method | Signature | Description |
|---|---|---|
| `vector_search` | `(embedding: list[float], top_k: int) -> list[RagHit]` | KNN via sqlite-vec; returns RawHit with `distance` field; logs `top_k`/`hits`/`elapsed_ms` |
| `fts_search` | `(query: str, top_k: int) -> list[RagHit]` | BM25 via FTS5; returns RawHit with `bm25_score` field; raises `sqlite3.OperationalError` on FTS syntax errors (caller handles); logs `query`/`fts_query`/`top_k`/`hits`/`elapsed_ms` |

**Module-level standalone wrappers:**
- `vector_search(embedding, top_k, db)` → delegates to `RagRepository(db).vector_search()`
- `fts_search(query, top_k, db)` → delegates to `RagRepository(db).fts_search()`
- `fetch_full_document(chunk_id, db, window=None)` → same-doc chunks by `chunk_index` asc; `window=N` → ±N
- `deduplicate_chunks(hits, max_per_doc)` → cap same-URL hits; input must be descending-sorted
- `cosine_sim(a, b) -> float` → cosine similarity; returns `0.0` for zero vectors

### 7.2 RagScorer (`scripts/rag/repository.py`)

| Method | Signature | Description |
|---|---|---|
| `rrf_merge` (static) | `(results_list: list[list[RawHit]] \| list[list[RagHit]], rrf_k: int = 60) -> list[RagHit]` | RRF score Σ 1/(rrf_k+rank); descending order; assigns `rrf_score`; accepts RawHit or RagHit result lists |

### 7.3 RagLLM (`scripts/rag/llm_client.py`)

Implementations live in:

- `scripts/rag/llm_client.py` — `RagLLM` class, `get_embedding()`, `summarize_tool_result()`
- `scripts/rag/llm_prompts.py` — prompt templates, `RagExpansionError`, `RagRerankError`, `MqeParseError`

```python
from rag.llm_client import RagLLM
llm = RagLLM(client=http_client, llm_url="http://127.0.0.1:8001/v1/chat/completions")
```

**Note:** `scripts/rag/llm_client.py:48-50` has a duplicate `logger = logging.getLogger(__name__)` line — the second assignment overwrites the first. Only one is needed.

| Method | Signature | Description |
|---|---|---|
| `expand_queries` | `async (query: str, context: str = "") -> list[str]` | MQE; raises `RagExpansionError` on HTTP failure, connection error, or parse failure |
| `cross_encoder_rerank` | `async (query: str, candidates: list[RagHit], top_k: int, rag_min_score=0.0) -> list[RagHit]` | Cross-encoder; raises `RagRerankError` on HTTP failure, connection error, or parse failure; filters by `rag_min_score` |
| `summarize_tool_result` | `async (text: str, tool_name: str, args: dict[str, object]) -> str` | Summarize tool output via LLM; raises on any HTTP or parse failure — callers decide how to handle |
| `refine_context` | `async (chunks: list[RagHit], query: str, max_tokens: int, per_chunk_chars: int, timeout: float) -> str` | Compress chunks to query-relevant key points via single LLM call; raises on error so callers can fall back |

**Module-level functions:**

| Function | Signature | Description |
|---|---|---|
| `get_embedding` | `async (text, client, embed_url) -> list[float]` | Convert text to embedding vector; uses `"query: "` prefix (E5 convention); raises on HTTP failure or missing/empty embedding field |
| `summarize_tool_result` | `async (text, tool_name, args, client, llm_url=None) -> str` | Standalone summarization; loads `llm_url` from cached config when `None`; raises on LLM call failure |

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
    result_source: str | None = None
```

Returned by `RagPipeline.run()`. **`result_source` is always `None`** — `run()` never sets it. The field exists only for HTTP mode where HTTP augment handler may set it via `dataclasses.replace()`.

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_query_pipeline.md`
- `03_rag_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_query_pipeline-stages.md`
- `03_rag_04_data_model_and_interfaces.md`
- `03_rag_05_configuration_and_operations.md`

## Keywords

semantic-cache
rag-repository
rag-scorer
rag-llm
rag
