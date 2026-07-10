---
title: "6.5 models_config.py (`scripts/rag/models_config.py`)"
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

# 6.5 models_config.py (`scripts/rag/models_config.py`)

### 6.5 models_config.py (`scripts/rag/models_config.py`)

**MqeConfig** — MQE query expansion configuration.

| Field | Type | Default | Description |
|---|---|---|---|
| `use_mqe` | `bool` | `True` | Enable MQE query expansion |
| `mqe_url` | `str` | `""` | MQE service URL |
| `mqe_timeout` | `float` | `5.0` | MQE request timeout (seconds) |

**FusionConfig** — RRF fusion configuration.

| Field | Type | Default | Description |
|---|---|---|---|
| `rrf_k` | `int` | `60` | RRF constant for rank aggregation |

**RerankConfig** — Cross-encoder rerank configuration.

| Field | Type | Default | Description |
|---|---|---|---|
| `use_rerank` | `bool` | `True` | Enable cross-encoder reranking |
| `rerank_url` | `str` | `""` | Rerank service URL |
| `rerank_timeout` | `float` | `10.0` | Rerank request timeout (seconds) |
| `rerank_max_tokens` | `int` | `512` | Max tokens for rerank LLM call |

**SearchConfig** — Search configuration.

| Field | Type | Default | Description |
|---|---|---|---|
| `use_search` | `bool` | `True` | Enable vector/FTS search |
| `embed_url` | `str` | `""` | Embedding service URL |
| `embed_timeout` | `float` | `5.0` | Embedding request timeout (seconds) |
| `top_k_search` | `int` | `10` | Number of results per query |
| `rag_min_score` | `float` | `0.0` | Minimum score threshold for filtering |
| `use_rrf` | `bool` | `True` | Enable RRF rank fusion |

**ChunkSplitterConfig** — Chunk splitting configuration.

| Field | Type | Default | Description |
|---|---|---|---|
| `chunk_size` | `int` | `500` | Target chunk size in characters |
| `chunk_overlap` | `int` | `50` | Overlap between chunks in characters |
| `lang` | `str` | `"en"` | Language for text splitting |
| `md_index_enable` | `bool` | `False` | Enable Markdown heading-based chunking |

**IngesterConfig** — Ingestion configuration.

| Field | Type | Default | Description |
|---|---|---|---|
| `embed_url` | `str` | `""` | Embedding service URL |
| `embed_timeout` | `float` | `5.0` | Embedding request timeout (seconds) |
| `batch_size` | `int` | `32` | Batch size for embedding requests |

**PipelineConfig** — Top-level pipeline configuration. Contains nested configs for each stage.

| Field | Type | Description |
|---|---|---|
| `mqe` | `MqeConfig` | MQE query expansion config |
| `fusion` | `FusionConfig` | RRF fusion config |
| `rerank` | `RerankConfig` | Cross-encoder rerank config |
| `search` | `SearchConfig` | Search config |


## Related Documents

- [03_rag_04_data_model_and_interfaces.md](03_rag_04_dto-models_data.md)

## Keywords

dto
data-model
