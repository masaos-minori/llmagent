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

Tool membership and risk tiers: [mcp_01_tool_ownership_matrix.md](mcp_01_tool_ownership_matrix.md). Health response semantics common to all servers: [mcp_02_02](mcp_02_02_startup-modes-and-health.md). Availability metadata: [mcp_03_06_tool-runtime-availability-metadata.md](mcp_03_06_tool-runtime-availability-metadata.md).

## rag-pipeline-mcp

**Purpose:** RAG search pipeline (MQE -> Search -> Fusion -> Rerank -> Augment, followed by the optional Refiner). All RAG tool calls from the agent go through this server. All tools are production (not stub/experimental).
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/rag_pipeline_mcp_server.toml` (`RagPipelineConfig`; defaults are owned by these two)

Tool output contract:

- `rag_run_pipeline` returns plain text: the `augmented_text` context block, or a fixed no-results message when it is empty.
- `rag_debug_pipeline` returns a JSON summary (query, expanded queries, per-stage hit counts, elapsed time, `augmented_text`).
- `rag_list_documents` and `rag_delete_document` (by `url`) operate over the RAG database; no ingestion or indexing tool is exposed.
- Tools return text through `POST /v1/call_tool`. The direct endpoints `POST /rag_run_pipeline` and `POST /rag_debug_pipeline` return structured models in which `selected_hits` (the final selected chunks) is a response field; `selected_hits` is not part of the `/v1/call_tool` result.

Configuration notes:

- Pipeline stages are switched by `use_mqe`, `use_rrf`, `use_rerank`, `use_refiner`; result limits by `top_k_search`, `top_k_rerank`, `rag_top_k`, `rag_min_score`, `max_chunks_per_doc`; refiner limits by `refiner_*`. `llm_url`, `embed_url`, `rag_db_path`, and `sqlite_vec_so` locate the backing services.
- `auth_token` is the inbound Bearer token required by this server (resolved from `MCP_RAG_PIPELINE_AUTH_TOKEN`). `rag_auth_token` is the outbound Bearer token sent to a remote RAG service; empty means no header.
- host, port, and http_timeout are not configuration keys: `RagPipelineConfig` does not load them and they are fixed in code.
- To prevent HTTP loops, `rag_service_url = ""` is fixed in `build_rag_cfg_adapter()`.

Operations:

- Availability: `rag_run_pipeline` and `rag_debug_pipeline` are disabled with reason `"embed_url is not configured"` when `embed_url` is empty; `/v1/call_tool` rejects them with `Tool disabled: <reason>`.
- `/health`: `dependencies.embed_url` is `"not configured"` (embedding URL unset), `"unreachable"` (embedding URL configured but the reachability probe fails), or `dependencies.config` is `"check failed"` (degraded, HTTP 503); otherwise `ok`.
- Logs: `rag-mcp.log` in the log directory. Audit: Layer1 `tool_exec` only; no shared or dedicated audit log.

---

## cicd-mcp

See also: [security_02_high-risk-tool-common-policy.md](../91_security/security_02_high-risk-tool-common-policy.md) for the cross-cutting canonical policy governing cicd-mcp as a high-risk tool. Agent-side approval confirms user intent only; it is not a bypass for any check below.

**Purpose:** GitHub Actions workflow management (`trigger_workflow` is `WRITE_DANGEROUS`; the others are read-only run, status, and log tools). All tools are `config_dependent: true`.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/cicd_mcp_server.toml` (`repo_allowlist`, `workflow_allowlist`, `max_log_size_kb`, `auth_token`, `github_token`)
**Authentication:** `GITHUB_TOKEN` (via `conf.d/cicd-mcp`)

Security and availability:

- `repo_allowlist` and `workflow_allowlist` are fail-closed: empty rejects everything and logs a warning at startup. Tools are disabled with reason `"repo_allowlist is empty"` (all tools) or `"workflow_allowlist is empty"` (`trigger_workflow`); `/v1/call_tool` rejects with `Tool disabled: <reason>`.
- `trigger_workflow` supports `dry_run` (exposed via the tool schema).
- Log retrieval is bounded by a job count limit and a total size limit (`max_log_size_kb`).
- `/health`: `dependencies.github_token="not_set"` or `dependencies.config="check failed"` (degraded, HTTP 503); otherwise `ok`.
- Architecture: `CiCdService` delegates to a `CiBackend` Protocol (`GitHubActionsBackend`), which abstracts the CI backend.
- Audit: Layer1 `tool_exec`, Layer2 `mcp_tool_exec` (JSON-lines records in the server's application log `<log_dir>/cicd-mcp.log` via `_audit_log()`, `server_key="cicd"`), Layer3 none.

### Guard and postcondition coverage

- **Agent approval:** not applicable server-side; cicd enforces only its own technical constraints (`GITHUB_TOKEN`, repository and workflow allowlists).
- **Common guard:** `call_tool` rejects a disabled tool first. Every operation asserts its `repo` argument against `repo_allowlist` (`_assert_allowed_repo()` for `trigger_workflow`, `_validate_and_parse_repo()` for the read tools); an empty allowlist denies all calls. Enforcement: `scripts/mcp_servers/cicd/cicd_service_guards.py`.
- **Command-specific guard:** `trigger_workflow` runs `_assert_allowed_workflow()`: it denies all triggers when `workflow_allowlist` is empty, rejects a `workflow` value containing `/` or `\`, and rejects a value not in `workflow_allowlist`. The same path-separator rule is checked at startup by the Security Posture check `server.workflow_pattern_valid`, so a configured pattern containing a separator fails posture validation. The read tools are gated by the repository allowlist only.
- **Postcondition verification:** not applicable. Triggering a workflow is asynchronous: the server POSTs a dispatch event and returns a confirmation rather than a resulting state to compare. Run state is read afterwards through `get_workflow_status` and `get_workflow_runs`.
- **Audit:** one shared `mcp_tool_exec` record per dispatched call (`target` is the requested `repo`; `outcome` from the dispatch result); a disabled-tool rejection returns before the audit call and writes no record. No dedicated audit log; before/after state snapshots are not applicable.

---

## Keywords

- mcp
- server-catalog
- rag-pipeline-mcp
- cicd-mcp
