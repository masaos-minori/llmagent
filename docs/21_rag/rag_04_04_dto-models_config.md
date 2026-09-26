---
title: "6.5 models_config.py (`scripts/rag/models_config.py`)"
area: rag
tags:
  - rag
  - dto
  - data-model
related:
  - rag_00_document-guide.md
  - rag_04_05_dto-types.md
source:
  - rag_04_05_dto-types.md
---


# 6.5 models_config.py (`scripts/rag/models_config.py`)

`RagConfigImpl` is the concrete implementation of the `RagConfig` Protocol, defining the flat configuration contract for the RAG pipeline. It contains 28 fields covering MQE query expansion, search, reranking, refiner, LLM/embedding service URLs, database paths, and retry/workers configuration. All fields are required (no defaults).

| Field | Type | Description |
|---|---|---|
| use_mqe | bool | Enable multi-query expansion |
| top_k_search | int | Number of results from search |
| use_rerank | bool | Enable cross-encoder reranking |
| rag_top_k | int | Number of results after reranking |
| max_chunks_per_doc | int | Maximum chunks per document |
| top_k_rerank | int | Number of results before reranking |
| rag_min_score | float | Minimum score threshold |
| use_rrf | bool | Enable reciprocal rank fusion |
| rrf_k | int | RRF parameter k |
| use_search | bool | Enable search functionality |
| rag_service_url | str | RAG service URL |
| rag_auth_token | str \| None | Authentication token |
| use_refiner | bool | Enable document refiner |
| refiner_max_tokens | int | Maximum tokens for refiner |
| refiner_max_chars_per_chunk | int | Maximum characters per chunk |
| refiner_timeout | float | Refiner timeout in seconds |
| llm_url | str | LLM service URL |
| embed_url | str | Embedding service URL |
| rag_db_path | str | Path to RAG database |
| sqlite_vec_so | str | Path to sqlite-vec extension |
| sqlite_timeout | int | SQLite timeout |
| sqlite_busy_timeout_ms | int | SQLite busy timeout in milliseconds |
| embed_retry | int | Embedding retry count |
| embed_workers | int | Embedding worker count |
| rag_pipeline_service_url | str \| None | Pipeline service URL |
| mqe_prompt_template | str | MQE prompt template |
| mqe_n_queries | int | Number of MQE queries |
| rerank_prompt_template | str | Rerank prompt template |

Note: All fields are required — no default values are specified in the dataclass.

## RagConfig Protocol

`RagConfigImpl` implements the `RagConfig` Protocol defined in `scripts/shared/types.py`. Any object satisfying these 28 fields can be passed to `RagPipeline` without importing agent-layer classes into the RAG layer. This is NOT a file-format DTO; config file DTOs live in `mcp_servers.rag_pipeline.models.RagPipelineConfig` (MCP TOML) and `rag.models_config.*` (ingestion TOML).

## Implementation Notes

CI-017 has been resolved — the legacy per-stage config dataclasses (`MqeConfig`, `FusionConfig`, `RerankConfig`, `SearchConfig`, `ChunkSplitterConfig`, `IngesterConfig`, `PipelineConfig`) have been replaced by `RagConfigImpl`.

## Related Documents

- [rag_04_05_dto-types.md](rag_04_05_dto-types.md)
- `shared/types.py`'s `RagConfig` Protocol — The configuration contract actually used at runtime.

## Keywords

dto
data-model
rag-config
