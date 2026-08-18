## Title

RagPipelineConfig Defaults vs TOML Settings Alignment

### Context

Whether defaults in `RagPipelineConfig` should align with operational TOML values.

### Decision

**Align defaults with TOML.** TOML represents actual production configuration; defaults are stale.

### Rationale

Five values differ between defaults and TOML. Defaults should reflect production values to avoid confusion during development and testing.

### Evidence

| Field | Default | TOML | Impact |
|---|---|---|---|
| `top_k_search` | 5 | 20 | Search result count |
| `top_k_rerank` | 10 | 15 | Rerank candidate count |
| `rag_min_score` | 0.0 | 2.0 | Score threshold filtering |
| `semantic_cache_max_size` | 128 | 100 | Cache capacity |
| `refiner_max_chars_per_chunk` | 800 | 300 | Chunk size limit |

Sources:
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py:37-65` — defaults
- `config/rag_pipeline_mcp_server.toml:42-63` — TOML values

### Follow-up Actions

Create issue to update defaults in `rag_pipeline_models.py` to match TOML values.
