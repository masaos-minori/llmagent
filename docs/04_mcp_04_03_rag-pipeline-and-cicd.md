---
title: "MCP Server Catalog: rag-pipeline-mcp / cicd-mcp"
area: mcp
tags:
  - mcp
  - server-catalog
  - rag-pipeline
  - cicd
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_04_01_web-search-file-read-github.md
  - 04_mcp_04_02_file-write-file-delete-shell.md
  - 04_mcp_04_04_mdq.md
  - 04_mcp_04_05_git.md
---

# MCP Server Catalog: rag-pipeline-mcp / cicd-mcp

## rag-pipeline-mcp (Port 8010)

**Purpose:** RAG search pipeline (MQE → Search → RRF → Rerank → Deduplication → Expansion).
**Startup Mode:** persistent (HTTP)
**Configuration:** `config/rag_pipeline_mcp_server.toml`

**Tools:**

| Tool | Input | Output |
|---|---|---|
| `rag_run_pipeline` | `{query, history_context?, debug?}` | `augmented_text` + `selected_hits` |
| `rag_debug_pipeline` | `{query, history_context?}` | All intermediate stage outputs |
| `rag_list_documents` | `{lang?, limit?}` | List of indexed documents |
| `rag_delete_document` | `{url}` | Deletion confirmation |

**Configuration Parameters (RagPipelineConfig dataclass):**

| Key | Default | Description |
|---|---|---|
| `use_mqe` | `true` | Enable multi-query expansion |
| `use_rrf` | `true` | Enable RRF fusion |
| `rrf_k` | `60` | RRF constant |
| `use_rerank` | `true` | Enable reranking via cross-encoder |
| `use_refiner` | `false` | Enable context refinement/compression |
| `top_k_search` | `20` | Top k KNN/BM25 results per query |
| `top_k_rerank` | `15` | Top k cross-encoder results |
| `rag_top_k` | `5` | Number of final results |
| `rag_min_score` | `2.0` | Minimum threshold for rerank score |
| `max_chunks_per_doc` | `3` | Max chunks per document in final results |
| `semantic_cache_max_size` | `100` | Limit on semantic cache entries |
| `semantic_cache_threshold` | `0.92` | Cosine similarity threshold for semantic cache |
| `refiner_max_tokens` | `512` | Max tokens for context refinement |
| `refiner_max_chars_per_chunk` | `300` | Max characters per chunk for context refinement |
| `refiner_timeout` | `30.0` | Context refinement timeout (seconds) |

**Standalone Configuration Fields:** `llm_url`, `embed_url`, `rag_db_path`, `sqlite_vec_so`, `mqe_n_queries`, `mqe_prompt_template`, `rerank_prompt_template`, `use_mqe`, `use_rrf`, `use_rerank`, `use_refiner`, `rrf_k`, `top_k_search`, `top_k_rerank`, `rag_top_k`, `rag_min_score`, `max_chunks_per_doc`, `semantic_cache_max_size`, `semantic_cache_threshold`, `refiner_max_tokens`, `refiner_max_chars_per_chunk`, `refiner_timeout`

**Note (2026-07-13):** host/port/http_timeout were removed from `config/rag_pipeline_mcp_server.toml`. They were not loaded into `RagPipelineConfig` and were not referenced anywhere in the implementation. Actual values are hardcoded: `http_host="127.0.0.1"` (MCPServer base class), `http_port=8010` (`rag_pipeline/rag_pipeline_server.py`), `http_timeout=120.0` (`rag_pipeline/rag_pipeline_service.py`).

**Health:** If `embed_url` is configured: `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`; if not configured: `{"status":"degraded","ready":false,"dependencies":{"embed_url":"not configured"}}` or `{"dependencies":{"config":"check failed"}}` — returns HTTP 200 when ready, and 503 when degraded.
**Design Note:** To prevent HTTP loops, `rab_service_url = ""` is hardcoded in `build_rag_cfg_adapter()`.
**Logs:** `/opt/llm/logs/rag-mcp.log`
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): None / Layer3 (Dedicated): None — does not write audit logs
**Usage Scenarios:** All RAG searches; the `/rag search` command goes through this server.

**Tool Status:** All 4 tools are "production" (not stub/experimental).

---

## cicd-mcp (Port 8012)

See also: [00_security_02_high-risk-tool-common-policy.md](00_security_02_high-risk-tool-common-policy.md) for the cross-cutting canonical policy governing cicd-mcp as a high-risk tool.

**Purpose:** GitHub Actions workflow management.
**Startup Mode:** persistent (HTTP)
**Configuration:** `config/cicd_mcp_server.toml`
**Authentication:** `GITHUB_TOKEN` (via `conf.d/cicd-mcp`)

**Tools:**

| Tool | Tier | Input | config_dependent |
|---|---|---|---|
| `trigger_workflow` | WRITE_DANGEROUS | `{repo, workflow, ref?, inputs?}` | yes |
| `get_workflow_runs` | READ_ONLY | `{repo, workflow, limit?}` | yes |
| `get_workflow_status` | READ_ONLY | `{repo, run_id}` | yes |
| `get_workflow_logs` | READ_ONLY | `{repo, run_id}` | yes |

The git-mcp server's `enabled`/`disabled_reason` calculation logic ("workflow_allowlist is empty", etc.) is reserved for future use only. As planned in requirement 15, cicd/shell implementations are excluded. See [04_mcp_03_06_tool-runtime-availability-metadata.md](04_mcp_03_06_tool-runtime-availability-metadata.md) for details.

**Security:**
- `repo_allowlist`: fail-closed (empty = reject all; logs a warning at startup)
- `workflow_allowlist`: fail-closed (empty = reject all; logs a warning at startup)
- `trigger_workflow` supports the `dry_run` argument (exposed via tool schema)

**Configuration Fields:** `repo_allowlist`, `workflow_allowlist`, `max_log_size_kb` (default: 256 KB), `auth_token`, `github_token`

**Health:** When token is configured: `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`; if not configured: `{"status":"degraded","ready":false,"dependencies":{"github_token":"not_set"}}` or `{"dependencies":{"config":"check failed"}}` — returns HTTP 200 when ready, and 503 when degraded.
**Log Limit:** Up to 5 jobs, configurable with `max_log_size_kb` (default: total 256 KB)
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): `mcp_tool_exec` / Layer3 (Dedicated): None — recorded as JSON-lines to the shared audit log (`/opt/llm/logs/audit.log`) via `_audit_log()`
**Architecture:** `CiCdService` → `CiBackend` (Protocol) → `GitHubActionsBackend`
**Note:** The `CiBackend` Protocol allows for future support for GitLab CI / Jenkins backends.

---

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_04_01_web-search-file-read-github.md`
- `04_mcp_04_02_file-write-file-delete-shell.md`
- `04_mcp_04_04_mdq.md`
- `04_mcp_04_05_git.md`

## Keywords

mcp
server-catalog
rag-pipeline-mcp, cicd-mcp, port 8010, port 8012
