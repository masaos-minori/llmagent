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

See `MqeConfig` in `scripts/rag/models_config.py` for exact fields, types, and
defaults.

**FusionConfig** — RRF fusion settings.

See `FusionConfig` in `scripts/rag/models_config.py` for exact fields, types, and
defaults.

**RerankConfig** — Cross-encoder reranking settings.

See `RerankConfig` in `scripts/rag/models_config.py` for exact fields, types, and
defaults.

**SearchConfig** — Search settings.

See `SearchConfig` in `scripts/rag/models_config.py` for exact fields, types, and
defaults.

**ChunkSplitterConfig** — Chunk splitting settings.

See `ChunkSplitterConfig` in `scripts/rag/models_config.py` for exact fields, types,
and defaults.

**IngesterConfig** — Ingestion settings.

See `IngesterConfig` in `scripts/rag/models_config.py` for exact fields, types, and
defaults.

**PipelineConfig** — Top-level pipeline configuration. Includes nested configurations for each stage.

See `PipelineConfig` in `scripts/rag/models_config.py` for exact fields — its 4
fields are the `MqeConfig`/`FusionConfig`/`RerankConfig`/`SearchConfig` DTOs
described above, not independent primitive fields.

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
