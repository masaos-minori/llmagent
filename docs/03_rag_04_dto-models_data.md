---
title: "6.1 models_data.py (`scripts/rag/models_data.py`)"
category: rag
tags:
  - rag
  - dto
  - data-model
related:
  - 03_rag_00_document-guide.md
  - 03_rag_04_data_model_and_interfaces.md
source:
  - 03_rag_04_data_model_and_interfaces.md
---

# 6.1 models_data.py (`scripts/rag/models_data.py`)

### 6.1 models_data.py (`scripts/rag/models_data.py`)

**EmbeddingResponse** — Response from embedding API.

| Field | Type | Description |
|---|---|---|
| `embedding` | `list[float]` | Embedding vector |
| `model` | `str \| None` | Model name (optional) |

**CrawlTarget** — Target for WebCrawler crawl operation.

| Field | Type | Description |
|---|---|---|
| `url` | `str` | URL to crawl |
| `lang` | `LanguageCode` | Language hint (`"en"` / `"ja"`) |

**ChunkDocument** — Chunk data passed between pipeline stages.

| Field | Type | Default | Description |
|---|---|---|---|
| `url` | `str` | (required) | Source document URL |
| `title` | `str` | (required) | Source document title |
| `lang` | `str` | (required) | Language code (`"ja"` / `"en"`) |
| `content` | `str` | (required) | Chunk text |
| `code_blocks` | `list[str]` | `[]` | Code block contents |
| `etag` | `str \| None` | `None` | ETag for freshness detection |
| `last_modified` | `str \| None` | `None` | Last-Modified timestamp |
| `chunking_strategy` | `str` | `"text"` | Chunk split strategy |
| `normalized_content` | `str \| None` | `None` | Sudachi normalized text (JA only) |
| `chunk_index` | `int` | `0` | Position in document |
| `source_file` | `str` | `""` | Original crawler output filename |
| `chunk_type` | `str` | `""` | `"text"` or `"code"` |

**ChunkRecord** — Chunk data with embedding vector (used by query pipeline).

| Field | Type | Default | Description |
|---|---|---|---|
| `chunk_id` | `str` | (required) | Chunk identifier |
| `url` | `str` | (required) | Source document URL |
| `title` | `str` | (required) | Source document title |
| `lang` | `str` | (required) | Language code |
| `content` | `str` | (required) | Chunk text |
| `embedding` | `list[float]` | `[]` | Embedding vector |

**RegisteredDocument** — Document registration record.

| Field | Type | Description |
|---|---|---|
| `url` | `str` | Source URL |
| `lang` | `str` | Language code |
| `chunk_count` | `int` | Number of chunks |

**CacheEntry** — Semantic cache entry.

| Field | Type | Default | Description |
|---|---|---|---|
| `embedding` | `list[float]` | (required) | Cached embedding vector |
| `context_str` | `str` | (required) | Cached context string |
| `history_context` | `str` | `""` | Associated conversation history |
| `generation` | `int` | `0` | Generation counter for cache invalidation |

**TwoStageFetchResult** — Result from HTTP RAG service call.

| Field | Type | Description |
|---|---|---|
| `hits` | `list[Any]` | Hits (RagHit in-process, dict in HTTP mode) |
| `min_score_applied` | `float` | rag_min_score used for filtering |
| `max_chunks_per_doc` | `int` | Per-doc dedup limit applied |


## Related Documents

- [03_rag_04_data_model_and_interfaces.md](03_rag_04_dto-models_data.md)

## Keywords

dto
data-model
