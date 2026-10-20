---
title: "Configuration Reference"
area: rag
tags:
  - rag
  - configuration
related:
  - rag_00_document-guide.md
  - rag_02_02_ingestion_pipeline-crawler.md
  - rag_02_03_ingestion_pipeline-chunksplitter.md
  - rag_02_04_ingestion_pipeline-ingester.md
  - rag_02_06_ingestion_pipeline-supporting-components.md
  - adr_02_01_002_platform-config-isolation.md
  - deployment_01_deployment.md
  - shared_03_01_runtime_and_execution-config-and-logging.md
  - adr_02_06_010_rag-fallback.md
  - governance_03_issue-and-uncertainty-management.md
---


# Configuration Reference

Crawler / chunk_splitter / ingester / rag-pipeline-mcp are each independent processes, reading only their respective configuration files. There are no shared configuration files. If multiple processes require the same DB path or external service URL, they must specify them individually in their respective configuration files.

→ For details on the Process Separation Policy: [ADR-002](../10_adr/adr_02_01_002_platform-config-isolation.md) / [Process Separation Policy](../40_shared/shared_03_01_runtime_and_execution-config-and-logging.md#2a-process-separation-policy-config-isolation-policy)

The `config/*.toml` files below own the current operational values, and the corresponding config dataclasses own the key set and code defaults. Per-key inventories are intentionally not duplicated here; this reference records only ownership, semantics that are not obvious from a key name, and constraints.

## `config/crawler.toml`

Used by: `crawler.py` only.

- Keys cover the crawl output directory (`rag_src_dir`), the SQLite path used only to read ETag/Last-Modified for Conditional GET (`rag_db_path`), SQLite timeouts, request delay/retry/timeout/concurrency, and the BFS bounds (`max_depth`, `max_pages`).
- `max_pages`: reaching it stops BFS for the site. `skip_nofollow` / `skip_external` exclude `rel="nofollow"` links and cross-origin links from the BFS queue.
- `target_urls` is a list of `[url, lang]` pairs, used when `--url` is not specified.
- `min_chunk` is present here as well as in `chunk_splitter.toml`; chunks smaller than it are discarded as noise.

## `config/chunk_splitter.toml`

Used by: `chunk_splitter.py` only.

- Keys cover the chunk input/output base directory, chunk size bounds (`min_chunk`, `max_chunk`), and `chunk_overlap` (characters carried from the previous chunk; zero disables overlap).
- `md_index_enable` enables heading splitting for non-`.md` content with two or more heading lines; `.md`/`.markdown`/`.mdx` URLs always use heading splits. `md_snippet_max_chars` is the per-section limit above which a section falls back to text splitting.
- `en_stopwords` and `ja_stop_pos` are the stopwords excluded from FTS5 indexing and chunking; `ja_stop_pos` is a list of Japanese Sudachi part-of-speech names (not English labels).

## `config/ingester.toml`

Used by: `ingester.py` only.

- Keys cover the chunk input directory (`{rag_src_dir}/chunk/*.json`), the SQLite path (`rag_db_path`), the `sqlite-vec` shared library (`sqlite_vec_so`), SQLite timeouts, the embedding endpoint (`embed_url`), embedding retry (exponential backoff), and the embedding thread count (`embed_workers`).
- The embedding dimension is not a config key: it is the code-level constant from `get_embedding_dims()` (`scripts/db/store_protocols.py`) and must match the actual deployed embedding model. For model provisioning see [deployment_01_deployment.md section 1.4](../90_deployment/deployment_01_deployment.md#14-obtaining-llm-models); concrete model names are operator choices recorded in each LLM service configuration.

**Note:** `strict_artifact_validation` is not a setting (`RagIngester.__init__` does not read it, and artifact validation function calls do not specify `strict`). Rejection of chunks with missing required fields is always enabled via Python defaults in the artifact validation function.

## `config/rag_pipeline_mcp_server.toml`

Used by: `rag-pipeline-mcp` only (the rag-pipeline MCP server process). Loaded via `RagPipelineConfig.from_dict()` in `mcp_servers/rag_pipeline/rag_pipeline_models.py`. Does NOT use `agent.toml` (as stated in the header comment).

- Keys cover the SQLite path and `sqlite-vec` library, the LLM and embedding endpoints, the stage switches (`use_mqe`, `use_rrf`, `use_rerank`, `use_refiner`), search sizing (`top_k_search`, `top_k_rerank`, `rag_top_k`, `rag_min_score`, `max_chunks_per_doc`), `rrf_k`, `mqe_n_queries`, refiner limits, and the MQE/rerank prompt templates (placeholders `{n_queries}`, `{query}` and `{query}`, `{items_text}`).
- `rag_auth_token` is the outbound Bearer token sent to a remote RAG service; empty means no header.
- `auth_token` is the inbound Bearer token required by the rag-pipeline MCP server itself; it is an `${ENV:...}` reference and must match the Agent's `[mcp_servers.rag_pipeline].auth_token` in `config/agent.toml`.

**Precedence rule:** When a key exists in `config/rag_pipeline_mcp_server.toml`, its value overrides the corresponding code default in `RagPipelineConfig`; code defaults apply only when a key is absent from the `.toml` file.

`rag_pipeline_mcp_server.toml` is completely independent of `agent.toml`, and both files can have different values for same-named keys like `use_mqe`. Its header comment states the purpose: to override module-level caches for `agent_rag`, `rag_llm`, and `sqlite_helper`, and run the RAG pipeline independently from the main agent process.

## Hardcoded Values

The following values are **hardcoded** and cannot be changed via
`config/rag_pipeline_mcp_server.toml`; modifying them requires a source code change.
`host`/`port` are not configuration keys because `RagPipelineConfig` does not load them.

| Value | Source File |
|---|---|
| `http_host` | `MCPServer` base class (`server.py`) |
| `http_port` | `rag_pipeline_server.py` |
| `http_timeout` | `rag_pipeline_service.py` |
| Fallback `timeout` | `scripts/rag/pipeline_service.py::call_rag_service()` |

`http_timeout` is the HTTP client timeout of the MCP server itself, while a separate, shorter fixed per-attempt timeout is used for fallback calls to external RAG services (`call_rag_service()`); neither is loaded from configuration or `RagPipelineConfig`.

> **Warning:** Hardcoded values listed above cannot be changed by editing
> `config/rag_pipeline_mcp_server.toml`. Any modification must be made in the
> corresponding source file.

## `config/agent.toml`

Used by: Agent process only. Loaded via `ConfigLoader().load_all()` to build `AgentConfig`.

`AgentConfig.rag` (`RAGConfig`) carries only `embed_url`. The refiner is configured in `config/rag_pipeline_mcp_server.toml`; refiner keys in `config/agent.toml` are rejected at startup. It does not carry the search-stage parameters (`use_search`, `use_mqe`, `use_rrf`, `use_rerank`, `top_k_search`, `top_k_rerank`, `rag_top_k`, `rag_min_score`, `max_chunks_per_doc`) or `rag_service_url`. Those are owned by `config/rag_pipeline_mcp_server.toml` (see the `config/rag_pipeline_mcp_server.toml` section above).

- The Agent process consumes `embed_url` (memory embedding client and the `embed-llm` health check).
- `rag_service_url` is not a key of `config/agent.toml`, and no production process sets it to a non-empty value (see `adr_02_06_010_rag-fallback.md` Scope).

(Explicit in code — `scripts/agent/config_builders.py`)

---


## Keywords

- configuration
