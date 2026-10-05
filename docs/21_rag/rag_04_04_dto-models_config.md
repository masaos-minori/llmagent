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

`RagConfigImpl` is the concrete implementation of the `RagConfig` Protocol, defining the flat configuration contract for the RAG pipeline. It contains fields covering MQE query expansion, search, reranking, refiner, LLM/embedding service URLs, database paths, and retry/workers configuration. All fields are required (no defaults).

The field set is defined by the dataclass in `scripts/rag/models_config.py` and the `RagConfig` Protocol in `scripts/shared/types.py`; current operational values live in `config/*.toml` (see [Configuration Reference](rag_05_1-configuration-reference.md)).

Note: All fields are required — no default values are specified in the dataclass.

## RagConfig Protocol

`RagConfigImpl` implements the `RagConfig` Protocol defined in `scripts/shared/types.py`. Any object satisfying these fields can be passed to `RagPipeline` without importing agent-layer classes into the RAG layer. This is NOT a file-format DTO; config file DTOs live in `mcp_servers.rag_pipeline.models.RagPipelineConfig` (MCP TOML) and `rag.models_config.*` (ingestion TOML).

## Implementation Notes

RAG configuration is provided by `RagConfigImpl`.

## Code References

- `shared/types.py`'s `RagConfig` Protocol — The configuration contract actually used at runtime.

## Keywords

dto
data-model
rag-config
