---
title: "6.5 models_config.py (`scripts/rag/models_config.py`)"
area: rag
tags:
  - rag
  - dto
  - data-model
related:
  - 03_rag_00_document-guide.md
  - 03_rag_04_05_dto-types.md
source:
  - 03_rag_04_05_dto-types.md
---


# 6.5 models_config.py (`scripts/rag/models_config.py`)

**MqeConfig** — MQE query expansion settings.

| Field | Type | Default | Description |
|---|---|---|---|
| `use_mqe` | `bool` | `True` | Enable MQE query expansion |
| `mqe_url` | `str` | `""` | URL for the MQE service |
| `mqe_timeout` | `float` | `5.0` | Timeout for MQE requests (seconds) |

**FusionConfig** — RRF fusion settings.

| Field | Type | Default | Description |
|---|---|---|---|
| `rrf_k` | `int` | `60` | RRF constant for rank aggregation |

**RerankConfig** — Cross-encoder reranking settings.

| Field | Type | Default | Description |
|---|---|---|---|
| `use_rerank` | `bool` | `True` | Enable cross-encoder reranking |
| `rerank_url` | `str` | `""` | URL for the reranking service |
| `rerank_timeout` | `float` | `10.0` | Timeout for reranking requests (seconds) |
| `rerank_max_tokens` | `int` | `512` | Maximum tokens for reranking LLM calls |

**SearchConfig** — Search settings.

| Field | Type | Default | Description |
|---|---|---|---|
| `use_search` | `bool` | `True` | Enable vector/FTS search |
| `embed_url` | `str` | `""` | URL for the embedding service |
| `embed_timeout` | `float` | `5.0` | Timeout for embedding requests (seconds) |
| `top_k_search` | `int` | `10` | Number of results per query |
| `rag_min_score` | `float` | `0.0` | Minimum score threshold for filtering |
| `use_rrf` | `bool` | `True` | Enable RRF rank fusion |

**ChunkSplitterConfig** — Chunk splitting settings.

| Field | Type | Default | Description |
|---|---|---|---|
| `chunk_size` | `int` | `500` | Target chunk size (character count) |
| `chunk_overlap` | `int` | `50` | Overlap between chunks (character count) |
| `lang` | `str` | `"en"` | Language targeted for text splitting |
| `md_index_enable` | `bool` | `False` | Enable chunk splitting based on Markdown headers |

**IngesterConfig** — Ingestion settings.

| Field | Type | Default | Description |
|---|---|---|---|
| `embed_url` | `str` | `""` | URL for the embedding service |
| `embed_timeout` | `float` | `5.0` | Timeout for embedding requests (seconds) |
| `batch_size` | `int` | `32` | Batch size for embedding requests |

**PipelineConfig** — Top-level pipeline configuration. Includes nested configurations for each stage.

| Field | Type | Description |
|---|---|---|
| `mqe` | `MqeConfig` | MQE query expansion settings |
| `fusion` | `FusionConfig` | RRF fusion settings |
| `rerank` | `RerankConfig` | Cross-encoder reranking settings |
| `search` | `SearchConfig` | Search settings |

## Implementation Notes

See Known Issue CI-017 in `docs/00_governance_03_issue-and-uncertainty-management.md`
for the documented-dataclasses-vs-actual-runtime-contract mismatch tracked for this file.

## Related Documents

- [03_rag_04_05_dto-types.md](03_rag_04_05_dto-types.md)
- `shared/types.py`'s `RagConfig` Protocol — The configuration contract actually used at runtime.

## Keywords

dto
data-model
unused-dto
