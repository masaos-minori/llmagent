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
  - security_02_high-risk-tool-common-policy.md
  - mcp_03_06_tool-runtime-availability-metadata.md
---

# MCP Server Catalog: rag-pipeline-mcp / cicd-mcp

## rag-pipeline-mcp 

**Purpose:** RAG search pipeline (MQE → Search → Fusion → Rerank → Augment, followed by the optional Refiner).
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/rag_pipeline_mcp_server.toml`

**Tools:**

| Tool | Input | Output |
|---|---|---|
| `rag_run_pipeline` | `{query, history_context?, debug?}` | Plain text: the `augmented_text` context block, or a fixed no-results message when it is empty |
| `rag_debug_pipeline` | `{query, history_context?, debug?}` | JSON summary: `query`, `queries`, hit counts per stage (`merged_count`, `reranked_count`, `selected_count`), `elapsed`, `augmented_text` |
| `rag_list_documents` | `{lang?, limit?}` | List of indexed documents |
| `rag_delete_document` | `{url}` | Deletion confirmation |

The tools return text through `POST /v1/call_tool` (`CallToolResponse`: `result`, `is_error`). The direct endpoints `POST /rag_run_pipeline` and `POST /rag_debug_pipeline` return the structured models, where `selected_hits` (the final selected chunks) is a field of the response body; `selected_hits` is not part of the `/v1/call_tool` result.

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
| `refiner_max_tokens` | Max tokens for context refinement |
| `refiner_max_chars_per_chunk` | Max characters per chunk for context refinement |
| `refiner_timeout` | Context refinement timeout (seconds) |
| `auth_token` | Inbound Bearer token required by this server (resolved from `MCP_RAG_PIPELINE_AUTH_TOKEN`) |
| `rag_auth_token` | Outbound Bearer token sent to a remote RAG service; empty means no header |

Current default values are defined in `config/rag_pipeline_mcp_server.toml` and `RagPipelineConfig`.

**Standalone Configuration Fields:** `llm_url`, `embed_url`, `rag_db_path`, `sqlite_vec_so`, `mqe_n_queries`, `mqe_prompt_template`, `rerank_prompt_template`, `use_mqe`, `use_rrf`, `use_rerank`, `use_refiner`, `rrf_k`, `top_k_search`, `top_k_rerank`, `rag_top_k`, `rag_min_score`, `max_chunks_per_doc`, `refiner_max_tokens`, `refiner_max_chars_per_chunk`, `refiner_timeout`, `auth_token`, `rag_auth_token`

**Note:** host/port/http_timeout are not configuration keys of `config/rag_pipeline_mcp_server.toml`, because `RagPipelineConfig` does not load them. The values are hardcoded: `http_host` (MCPServer base class), `http_port` (`rag_pipeline/rag_pipeline_server.py`), `http_timeout` (`rag_pipeline/rag_pipeline_service.py`).

**Health:** If `embed_url` is configured: `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`; if not configured: `{"status":"degraded","ready":false,"dependencies":{"embed_url":"not configured"}}` or `{"dependencies":{"config":"check failed"}}` — returns HTTP 200 when ready, and 503 when degraded.
**Design Note:** To prevent HTTP loops, `rag_service_url = ""` is hardcoded in `build_rag_cfg_adapter()`.
**Logs:** `rag-mcp.log` (in the log directory)
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): None / Layer3 (Dedicated): None — does not write audit logs
**Usage Scenarios:** All RAG searches; RAG tool calls from the agent go through this server.

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
**Note:** The `CiBackend` Protocol abstracts the CI backend implementation.

### Guard and postcondition coverage

See also: [security_02_high-risk-tool-common-policy.md](../91_security/security_02_high-risk-tool-common-policy.md) Layered protection model for the general framework this section instantiates. Agent-side approval confirms user intent only; it is not a bypass for any check below.

#### Common guard

`cicd_server.py::call_tool` rejects a disabled tool (reason `repo_allowlist is empty`, or `workflow_allowlist is empty` for `trigger_workflow`) before anything else. Every operation asserts its `repo` argument against `repo_allowlist` — `trigger_workflow` through `_assert_allowed_repo()`, the read tools through `_validate_and_parse_repo()` — and an empty allowlist denies all calls. (Explicit in code — `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/cicd/cicd_service_guards.py`, `scripts/mcp_servers/cicd/cicd_service_business.py`)

#### Command-specific guard status

`trigger_workflow` runs `_assert_allowed_workflow()`: it denies all triggers when `workflow_allowlist` is empty, rejects a `workflow` value that contains `/` or `\`, and rejects a value that is not in `workflow_allowlist`. The same path-separator rule is checked at startup by the Security Posture check `server.workflow_pattern_valid`, so a configured workflow pattern that contains a separator fails posture validation. The read tools are gated by the repository allowlist only. (Explicit in code — `scripts/mcp_servers/cicd/cicd_service_guards.py`)

#### Postcondition verification

Not applicable: triggering a workflow is asynchronous, and the server returns the identity of the created run rather than a resulting local state to compare against. Run state is read afterwards through `get_workflow_status` and `get_workflow_runs`. (Explicit in code — `scripts/mcp_servers/cicd/cicd_service_business.py`)

#### Audit

`cicd_server.py::call_tool` writes one shared `mcp_tool_exec` record per dispatched call, with `target` set to the requested `repo` and `outcome` taken from the dispatch result; a disabled-tool rejection returns before the audit call and writes no record. cicd-mcp has no dedicated audit log, and before/after state snapshots are not applicable. (Explicit in code — `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/audit.py`)

---

## Keywords

- mcp
- server-catalog
- rag-pipeline-mcp
- cicd-mcp
