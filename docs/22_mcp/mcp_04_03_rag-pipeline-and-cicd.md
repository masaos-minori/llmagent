---
title: "MCP Server Catalog: rag-pipeline-mcp / cicd-mcp"
area: mcp
tags:
  - mcp
  - server-catalog
  - rag-pipeline
  - cicd
related:
  - mcp_00_document-guide.md
  - mcp_04_01_web-search-file-read-github.md
  - mcp_04_02_file-write-file-delete-shell.md
  - mcp_04_04_mdq.md
  - mcp_04_05_git.md
---

# MCP Server Catalog: rag-pipeline-mcp / cicd-mcp

## rag-pipeline-mcp 

**Purpose:** RAG search pipeline (MQE → Search → RRF → Rerank → Deduplication → Expansion).
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/rag_pipeline_mcp_server.toml`

**Tools:**

| Tool | Input | Output |
|---|---|---|
| `rag_run_pipeline` | `{query, history_context?, debug?}` | `augmented_text` + `selected_hits` |
| `rag_debug_pipeline` | `{query, history_context?}` | All intermediate stage outputs |
| `rag_list_documents` | `{lang?, limit?}` | List of indexed documents |
| `rag_delete_document` | `{url}` | Deletion confirmation |

**Configuration Parameters (RagPipelineConfig dataclass):**

| Key | Description |
|---|---|
| `use_mqe` | Enable multi-query expansion |
| `use_rrf` | Enable RRF fusion |
| `rrf_k` | RRF constant |
| `use_rerank` | Enable reranking via cross-encoder |
| `use_refiner` | Enable context refinement/compression |
| `top_k_search` | Top k KNN/BM25 results per query |
| `top_k_rerank` | Top k cross-encoder results |
| `rag_top_k` | Number of final results |
| `rag_min_score` | Minimum threshold for rerank score |
| `max_chunks_per_doc` | Max chunks per document in final results |
| `semantic_cache_max_size` | Limit on semantic cache entries |
| `semantic_cache_threshold` | Cosine similarity threshold for semantic cache |
| `refiner_max_tokens` | Max tokens for context refinement |
| `refiner_max_chars_per_chunk` | Max characters per chunk for context refinement |
| `refiner_timeout` | Context refinement timeout (seconds) |

Current default values are defined in `config/rag_pipeline_mcp_server.toml` and `RagPipelineConfig`.

**Standalone Configuration Fields:** `llm_url`, `embed_url`, `rag_db_path`, `sqlite_vec_so`, `mqe_n_queries`, `mqe_prompt_template`, `rerank_prompt_template`, `use_mqe`, `use_rrf`, `use_rerank`, `use_refiner`, `rrf_k`, `top_k_search`, `top_k_rerank`, `rag_top_k`, `rag_min_score`, `max_chunks_per_doc`, `semantic_cache_max_size`, `semantic_cache_threshold`, `refiner_max_tokens`, `refiner_max_chars_per_chunk`, `refiner_timeout`

**Note:** host/port/http_timeout are not configuration keys of `config/rag_pipeline_mcp_server.toml`, because `RagPipelineConfig` does not load them. The values are hardcoded: `http_host` (MCPServer base class), `http_port` (`rag_pipeline/rag_pipeline_server.py`), `http_timeout` (`rag_pipeline/rag_pipeline_service.py`).

**Health:** If `embed_url` is configured: `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`; if not configured: `{"status":"degraded","ready":false,"dependencies":{"embed_url":"not configured"}}` or `{"dependencies":{"config":"check failed"}}` — returns HTTP 200 when ready, and 503 when degraded.
**Design Note:** To prevent HTTP loops, `rag_service_url = ""` is hardcoded in `build_rag_cfg_adapter()`.
**Logs:** `rag-mcp.log` (in the log directory)
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): None / Layer3 (Dedicated): None — does not write audit logs
**Usage Scenarios:** All RAG searches; the `/rag search` command goes through this server.

**Tool Status:** All tools are "production" (not stub/experimental).

---

## cicd-mcp 

See also: [security_02_high-risk-tool-common-policy.md](../91_security/security_02_high-risk-tool-common-policy.md) for the cross-cutting canonical policy governing cicd-mcp as a high-risk tool.

**Purpose:** GitHub Actions workflow management.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/cicd_mcp_server.toml`
**Authentication:** `GITHUB_TOKEN` (via `conf.d/cicd-mcp`)

**Tools:**

| Tool | Tier | Input | config_dependent |
|---|---|---|---|
| `trigger_workflow` | WRITE_DANGEROUS | `{repo, workflow, ref?, inputs?}` | yes |
| `get_workflow_runs` | READ_ONLY | `{repo, workflow, limit?}` | yes |
| `get_workflow_status` | READ_ONLY | `{repo, run_id}` | yes |
| `get_workflow_logs` | READ_ONLY | `{repo, run_id}` | yes |

The cicd server computes `enabled`/`disabled_reason` via `_cicd_tool_availability()` (`"repo_allowlist is empty"` for all tools; `"workflow_allowlist is empty"` for `trigger_workflow`), and the rag_pipeline server via `_rag_pipeline_tool_availability()` (`"embed_url is not configured"` for `rag_run_pipeline`/`rag_debug_pipeline`). Both gate `/v1/call_tool` with `Tool disabled: <reason>`. See [mcp_03_06_tool-runtime-availability-metadata.md](mcp_03_06_tool-runtime-availability-metadata.md) for details.

**Security:**
- `repo_allowlist`: fail-closed (empty = reject all; logs a warning at startup)
- `workflow_allowlist`: fail-closed (empty = reject all; logs a warning at startup)
- `trigger_workflow` supports the `dry_run` argument (exposed via tool schema)

**Configuration Fields:** `repo_allowlist`, `workflow_allowlist`, `max_log_size_kb`, `auth_token`, `github_token`

**Health:** When token is configured: `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`; if not configured: `{"status":"degraded","ready":false,"dependencies":{"github_token":"not_set"}}` or `{"dependencies":{"config":"check failed"}}` — returns HTTP 200 when ready, and 503 when degraded.
**Log Limit:** Limited number of jobs, with total log size configurable via `max_log_size_kb`
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): `mcp_tool_exec` / Layer3 (Dedicated): None — recorded as JSON-lines to the shared audit log (`<log_dir>/audit.log`) via `_audit_log()`
**Architecture:** `CiCdService` → `CiBackend` (Protocol) → `GitHubActionsBackend`
**Note:** The `CiBackend` Protocol allows for future support for GitLab CI / Jenkins backends.

---

## Keywords

mcp
server-catalog
rag-pipeline-mcp, cicd-mcp
