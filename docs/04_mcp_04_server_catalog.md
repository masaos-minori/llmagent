# MCP Server Catalog

- System overview → [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md)
- Security model → [04_mcp_05_security_and_safety_model.md](04_mcp_05_security_and_safety_model.md)
- Configuration → [04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration_and_operations.md)

## Purpose

Per-server specification for all 11 MCP servers: purpose, port, tools, input/output,
config, startup, security, logs, operational notes, and known limitations.

> **Note:** This document is the authoritative server catalog. For the system-level server list with ports and transport types, see [04_mcp_01_system_overview.md §Server Catalog](04_mcp_01_system_overview.md).

---

## web-search-mcp (port 8004)

**Purpose:** Web search via DuckDuckGo (no API key required).
**Startup mode:** persistent (HTTP)
**Config:** `config/web_search_mcp_server.toml`

**Tools:**

| Tool | Input | Output |
|---|---|---|
| `search_web` | `{query: str, max_results?: int}` | Header + N result blocks (title/URL/snippet) |

**Config parameters:**

| Key | Default | Description |
|---|---|---|
| `default_max_results` | `5` | Default result count |
| `max_results_limit` | `20` | Server-side cap |

**Health:** `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}` — HTTP 200 when ready, 503 when degraded.
**Log:** `/opt/llm/logs/web-search-mcp.log`
**When to use:** Real-time information not in RAG index; latest releases; news.

---

## file-read-mcp (port 8005)

**Purpose:** Read-only access to local filesystem within `allowed_dirs`.
**Startup mode:** persistent (HTTP)
**Config:** `config/file_read_mcp_server.toml`

**Tools (9):** `read_text_file`, `list_directory`, `list_directory_with_sizes`, `directory_tree`,
`read_media_file`, `read_multiple_files`, `search_files`, `grep_files`, `get_file_info`

All tools do not require config (`requires_config: false`).

**Key tool inputs:**

| Tool | Input |
|---|---|
| `read_text_file` | `{path, head?, tail?}` |
| `read_media_file` | `{path, mime_type?}` |
| `read_multiple_files` | `{paths: list[str]}` |
| `list_directory` | `{path}` |
| `list_directory_with_sizes` | `{path}` |
| `directory_tree` | `{path, depth?}` |
| `search_files` | `{path, pattern}` |
| `grep_files` | `{path, pattern, file_pattern?, max_matches?}` |
| `get_file_info` | `{path}` |

**Config fields:** `allowed_dirs`, `max_read_bytes` (default: 1,000,000), `max_tree_depth` (default: 5), `max_search_results` (default: 200)

**Health:** `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{"filesystem":"/workspace is not a directory"/"check failed: <error>"},"details":{}}` — HTTP 200 when ready, 503 when degraded.
**Error codes:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**Log:** `/opt/llm/logs/file-read-mcp.log`
**Additional endpoint:** `GET /list_allowed_directories` (not a MCP tool)

---

## github-mcp (port 8006)

**Purpose:** GitHub API via PyGithub. Reads and writes to GitHub repositories.
**Startup mode:** persistent (HTTP)
**Config:** `config/github_mcp_server.toml`
**Auth:** `GITHUB_TOKEN` env var (PAT); without it: 60 req/hour anonymous

**Tools (21):** All prefixed `github_`: `github_search_repositories`, `github_get_file_contents`,
`github_push_files`, `github_delete_file`, `github_list_branches`, `github_get_commit`, `github_list_issues`, `github_get_issue`,
`github_create_issue`, `github_search_issues`, `github_list_pull_requests`, `github_get_pull_request`,
`github_search_pull_requests`, `github_update_pull_request`, `github_merge_pull_request`, `github_list_commits`,
`github_search_code`, `github_create_pull_request`, `github_create_branch`, `github_create_or_update_file`, `github_add_issue_comment`

All tools require config (`requires_config: true`).

**Write operations (9) are subject to repo allowlist:**
`github_create_branch`, `github_create_or_update_file`, `github_push_files`, `github_delete_file`,
`github_create_issue`, `github_add_issue_comment`, `github_create_pull_request`, `github_update_pull_request`, `github_merge_pull_request`

**Config fields:** `default_per_page` (20), `max_per_page` (100), `allowed_repos`, `allowed_repos_mode`, `protected_branches`, `path_denylist`, `max_file_size_kb` (1024 KB), `allow_force_push` (false), `require_pr_review` (true), `audit_log_path`

**Security controls:**
- `allowed_repos` / `allowed_repos_mode` (fail-closed by default; empty list = deny all when mode is "fail_closed")
- `protected_branches` (fnmatch patterns)
- `path_denylist` (fnmatch patterns)
- `max_file_size_kb` (0 = unlimited)
- `allow_force_push` (default `false`; set `true` to permit force-push and rebase merge)
- `require_pr_review` (default `true`; set `false` to allow merge without review)

**Domain exceptions** (in `mcp/github/models.py`): `GitHubNotFoundError` (404), `GitHubAuthorizationError` (403),
`GitHubConflictError` (409), `GitHubValidationError` (400), `GitHubUpstreamError` (502), `GitHubAuditError` (500)

**Health:** `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}` when token is set; `"status":"degraded","ready":false,"dependencies":{"github_token":"not_set"}` when not set — HTTP 200 when ready, 503 when degraded.
**Log:** `/opt/llm/logs/github-mcp.log`
**Audit log:** `config/github_mcp_server.toml::audit_log_path`

---

## file-write-mcp (port 8007)

**Purpose:** Local filesystem write operations. All tools support `dry_run=True`.
**Startup mode:** persistent (HTTP)
**Config:** `config/file_write_mcp_server.toml`

**Tools (4):** `write_file`, `edit_file`, `create_directory`, `move_file`

All tools do not require config (`requires_config: false`).

**Config fields:** `allowed_dirs`, `max_write_bytes` (default: 1,000,000)

| Tool | Input | dry_run behavior |
|---|---|---|
| `write_file` | `{path, content, dry_run?}` | Returns diff only; no write |
| `edit_file` | `{path, edits: [{old_text, new_text}], dry_run?}` | Returns diff; no write |
| `create_directory` | `{path, dry_run?}` | Returns directory info (exists/would create); no create |
| `move_file` | `{source, destination, dry_run?}` | Returns move feasibility |

**Health:** `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{"filesystem":"/workspace is not a directory"/"check failed: <error>"},"details":{}}` — HTTP 200 when ready, 503 when degraded.
**Config:** `max_write_bytes` (default 1 MB; enforced as UTF-8 byte count via Pydantic)
**Error codes:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**Log:** `/opt/llm/logs/file-write-mcp.log`

---

## file-delete-mcp (port 8008)

**Purpose:** Local filesystem deletion. All tools support `dry_run=True`.
**Startup mode:** persistent (HTTP)
**Config:** `config/file_delete_mcp_server.toml`

**Tools (2):** `delete_file`, `delete_directory`

All tools do not require config (`requires_config: false`).

**Config fields:** `allowed_dirs`, `audit_log_path`

| Tool | Input | dry_run behavior |
|---|---|---|
| `delete_file` | `{path, dry_run?}` | Returns file info; no delete |
| `delete_directory` | `{path, recursive?, dry_run?}` | Scans contents (up to 1000 files); no delete |

**Health:** `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{"filesystem":"/workspace is not a directory"/"check failed: <error>"},"details":{}}` — HTTP 200 when ready, 503 when degraded.
**Delete audit log:** `/opt/llm/logs/delete_audit.log` (ISO8601 UTC + op + path + user)
**Error codes:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**Log:** `/opt/llm/logs/file-delete-mcp.log`

---

## shell-mcp (port 8009)

**Purpose:** Sandboxed shell command execution within `command_allowlist`.
**Startup mode:** persistent (HTTP)
**Config:** `config/shell_mcp_server.toml`

**Tools (1):** `shell_run`

| Tool | Input | `requires_config` |
|---|---|---|
| `shell_run` | `{command, argv?, cwd?, timeout_sec?, max_output_kb?, env?, dry_run?}` | yes |

**Output:** `{stdout, stderr, exit_code, timed_out, truncated, elapsed_sec}`

**Config:**

| Key | Default | Description |
|---|---|---|
| `command_allowlist` | `[]` | Allowed command names (`argv[0]` basename) |
| `shell_cwd_allowed_dirs` | `[]` | Allowed CWD paths (empty = deny all) |
| `max_timeout_sec` | `300` | Max timeout cap |
| `max_output_kb` | `4096` | Output cap |
| `max_memory_mb` | `512` | Memory limit (`RLIMIT_AS`) |
| `shell_sandbox_backend` | `"none"` | `"firejail"` or `"none"` (see sandbox table below) |
| `audit_log_path` | `"/opt/llm/logs/shell_audit.log"` | Audit log |
| `default_cwd` | `"/opt/llm/storage"` | Working directory when cwd not specified in request |
| `shell_path` | `"/opt/llm/venv/bin:/usr/bin:/bin"` | PATH environment variable for child processes |
| `env_allowlist` | `[]` | Permitted env var keys in req.env (empty = use env_denylist) |
| `env_denylist` | `["LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH"]` | Glob patterns for env keys removed from req.env |
| `execution_user` | `""` | OS user to run commands as via setuid (requires CAP_SETUID) |
| `kill_policy` | `"sigterm_then_sigkill"` | SIGTERM+SIGKILL or `"sigkill_only"` for timed-out processes |
| `kill_grace_sec` | `2.0` | Seconds to wait after SIGTERM before escalating to SIGKILL |

**Health:** `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{"sandbox_backend":"firejail"/"none"}}` when sh is found; `"status":"degraded","ready":false,"dependencies":{"shell":"sh not found in PATH"/"check failed"}}` when not — HTTP 200 when ready, 503 when degraded.
**Log:** `/opt/llm/logs/shell-mcp.log`

| sandbox_backend | Meaning | Use case |
|---|---|---|
| `"none"` | No process isolation; only `RLIMIT_*` limits applied | Local development only |
| `"firejail"` | firejail process isolation (`--private --net=none --noroot`) | Production recommended |

> **Security note — Sandbox is disabled by default:** `sandbox_backend` defaults to `"none"`.
> Shell commands run with the agent process's OS user and permissions — no container, no namespace isolation.
> To enable sandboxing, install firejail and set `sandbox_backend = "firejail"` in
> `config/shell_mcp_server.toml`. The active backend is visible in the `/health` response under
> `details.sandbox_backend` (`"none"` or `"firejail"`).
> **Production enforcement:** In production mode (`security_profile = "production"` in `agent.toml`),
> `sandbox_backend = "none"` is not permitted. The agent raises `RuntimeError` at startup if this
> combination is detected. Set `sandbox_backend = "firejail"` or disable shell-mcp in production.

---

## rag-pipeline-mcp (port 8010)

**Purpose:** RAG retrieval pipeline (MQE → Search → RRF → Rerank → Dedup → Augment).
**Startup mode:** persistent (HTTP)
**Config:** `config/rag_pipeline_mcp_server.toml`

**Tools (4):**

| Tool | Input | Output |
|---|---|---|
| `rag_run_pipeline` | `{query, history_context?, debug?}` | `augmented_text` + `selected_hits` |
| `rag_debug_pipeline` | `{query, history_context?}` | All intermediate stage outputs |
| `rag_list_documents` | `{lang?, limit?}` | List of indexed documents |
| `rag_delete_document` | `{url}` | Deletion confirmation |

**Config parameters (`RagPipelineConfig` dataclass):**

| Key | Default | Description |
|---|---|---|
| `use_mqe` | `true` | Enable multi-query expansion |
| `use_rrf` | `true` | Enable RRF fusion |
| `rrf_k` | `60` | RRF constant |
| `use_rerank` | `true` | Enable cross-encoder rerank |
| `use_refiner` | `false` | Enable context refinement/compression |
| `top_k_search` | `20` | KNN/BM25 top-k per query |
| `top_k_rerank` | `15` | Cross-encoder top-k |
| `rag_top_k` | `5` | Final result count |
| `rag_min_score` | `2.0` | Minimum rerank score threshold |
| `max_chunks_per_doc` | `3` | Max chunks per document in final result |
| `semantic_cache_max_size` | `100` | Semantic cache entry limit |
| `semantic_cache_threshold` | `0.92` | Semantic cache cosine similarity threshold |
| `refiner_max_tokens` | `512` | Context refinement max tokens |
| `refiner_max_chars_per_chunk` | `300` | Context refinement chars per chunk |
| `refiner_timeout` | `30.0` | Context refinement timeout (seconds) |

**Config fields (standalone):** `llm_url`, `embed_url`, `rag_db_path`, `sqlite_vec_so`, `host`, `port`, `http_timeout`, `mqe_n_queries`, `mqe_prompt_template`, `rerank_prompt_template`, `use_mqe`, `use_rrf`, `use_rerank`, `use_refiner`, `rrf_k`, `top_k_search`, `top_k_rerank`, `rag_top_k`, `rag_min_score`, `max_chunks_per_doc`, `semantic_cache_max_size`, `semantic_cache_threshold`, `refiner_max_tokens`, `refiner_max_chars_per_chunk`, `refiner_timeout`

**Health:** `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}` when embed_url is configured; `"status":"degraded","ready":false,"dependencies":{"embed_url":"not configured"}}` or `"dependencies":{"config":"check failed"}}` when not — HTTP 200 when ready, 503 when degraded.
**Design note:** `rag_service_url = ""` is hardcoded in `build_rag_cfg_adapter()` to prevent HTTP loops.
**Log:** `/opt/llm/logs/rag-mcp.log`
**When to use:** All RAG retrieval; `/rag search` command goes through this server.

**Tool status:** All 4 tools are `"production"` (not stub/experimental).

---

## cicd-mcp (port 8012)

**Purpose:** GitHub Actions workflow management.
**Startup mode:** persistent (HTTP)
**Config:** `config/cicd_mcp_server.toml`
**Auth:** `GITHUB_TOKEN` (via `conf.d/cicd-mcp`)

**Tools (4):**

| Tool | Tier | Input | `requires_config` |
|---|---|---|---|
| `trigger_workflow` | WRITE_DANGEROUS | `{repo, workflow, ref?, inputs?}` | yes |
| `get_workflow_runs` | READ_ONLY | `{repo, workflow, limit?}` | yes |
| `get_workflow_status` | READ_ONLY | `{repo, run_id}` | yes |
| `get_workflow_logs` | READ_ONLY | `{repo, run_id}` | yes |

**Security:**
- `repo_allowlist`: fail-closed (empty = deny all; warning logged at startup)
- `workflow_allowlist`: fail-closed (empty = deny all; warning logged at startup)
- `trigger_workflow` supports `dry_run` argument (exposed via tool schema)

**Config fields:** `repo_allowlist`, `workflow_allowlist`, `max_log_size_kb` (default: 256 KB), `auth_token`, `github_token`

**Health:** `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}` when token is set; `"status":"degraded","ready":false,"dependencies":{"github_token":"not_set"}}` or `"dependencies":{"config":"check failed"}}` when not — HTTP 200 when ready, 503 when degraded.
**Log limits:** max 5 jobs, configurable via `max_log_size_kb` (default: 256 KB total)
**Architecture:** `CiCdService → CiBackend (Protocol) → GitHubActionsBackend`
**Note:** `CiBackend` Protocol allows future GitLab CI / Jenkins backends.

---

## mdq-mcp (port 8013)

**Purpose:** Markdown document indexing and context compression.
**Startup mode:** persistent (HTTP)
**Config:** `config/mdq_mcp_server.toml`

**Tools (9):** `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`, `fts_consistency_check`, `fts_rebuild`
**Tool status:** 7 tools are `production` (`search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`), 2 tools (`fts_consistency_check`, `fts_rebuild`) are `admin`.

**Config fields:** `status`, `allowed_dirs`, `db_path`, `include_globs`, `exclude_globs`, `max_search_results`, `max_snippet_chars`, `max_chunk_chars`, `max_file_chars`, `max_results_limit`, `max_chars_per_chunk`, `max_total_result_chars`, `max_outline_items`, `max_grep_matches`, `search_timeout_sec`, `enable_refresh`, `enable_grep`, `audit_log_path`, `concurrency_limit`, `summary_cache_enabled`, `summary_threshold`, `summary_model`, `use_embedding`, `embedding_dims` (default 384), `vector_table`, `embedding_model`, `max_chars_per_match` (default 500), `context_before` (default 2), `context_after` (default 2), `max_outline_depth` (default 6), `sqlite_busy_timeout` (default 5000)

**Health:** `{"status":"ok"/"degraded","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{...},"details":{"service":"mdq-mcp",...}}` — returns richer fields than base response (see [04_mcp_06 §Health probes](04_mcp_06_configuration_and_operations.md#health-probes))

**DB path:** `/opt/llm/db/mdq.sqlite` (`config/mdq_mcp_server.toml`: `db_path`)
**Log:** `/opt/llm/logs/mdq-mcp.log`
**When to use:** Markdown document indexing and context compression. Use `rag-pipeline-mcp` for production RAG search.

### Path Control

All path-accepting tools enforce fail-closed authorization via `allowed_dirs`:

| Tool | Path Input | Authorization |
|------|------------|---------------|
| `index_paths` | Directories/files to index | `authorize_path()` — raises `MdqAuthorizationError` if outside `allowed_dirs` |
| `refresh_index` | Paths to refresh | Path authorization — raises `MdqAuthorizationError` if any path is denied |
| `outline` | File to outline | `authorize_path()` — raises `MdqAuthorizationError` if outside `allowed_dirs` |

- `..` traversal: blocked by `Path.resolve()` inside `authorize_path()`
- Symlink escapes: blocked by `Path.resolve()` inside `authorize_path()`
- Empty `allowed_dirs = []` (default): denies all paths (fail-closed)

Configure `allowed_dirs` in `config/mdq_mcp_server.toml` before using indexing tools.

### Markdown Compatibility Scope

| Markdown Feature          | Support | Fallback Behavior                          |
|---------------------------|---------|---------------------------------------------|
| ATX headings (H1–H6)      | Yes     | —                                           |
| Fenced code blocks        | Yes     | `#` inside fences not treated as headings   |
| YAML frontmatter          | Yes     | Parsed and stripped at file start           |
| Content before H1         | Yes     | Stored as `<root>` section                  |
| Duplicate headings        | Yes     | Distinct chunk IDs via ordinal              |
| Setext headings (===,---) | No      | Treated as plain text                       |
| HTML blocks               | No      | Treated as plain text                       |
| MDX                       | No      | Not indexed (.mdx excluded by glob)         |
| GFM tables                | No      | Stored as plain text in parent section      |
| Inline HTML tags          | No      | Treated as plain text                       |

### Search Modes

| Mode | Description | Config |
|---|---|---|
| FTS5-only (Phase 1) | Full-text search via FTS5; production baseline | `use_embedding = false` (default) |
| Hybrid (Phase 2) | FTS5 + semantic vector search merged via RRF | `use_embedding = true` |

**Hybrid Search (Phase 2):**

When `use_embedding = true`, MDQ performs hybrid search:
1. FTS5 keyword search on `chunks_fts`
2. Semantic vector search (stub — returns empty list in Phase 1)
3. Results merged via Reciprocal Rank Fusion (RRF)

**MDQ Hybrid vs RAG Decision Criteria:**

| Use Case | Recommended | Rationale |
|---|---|---|
| Markdown structural queries (headings, sections, outlines) | MDQ hybrid | MDQ understands Markdown document structure; FTS5 is precise for keyword matching within documents |
| General semantic search across all indexed content | RAG pipeline | RAG has broader corpus coverage and mature embedding model integration |
| Cross-document structural comparison | MDQ hybrid | MDQ chunk_id includes heading hierarchy (level, parent_path, ordinal) |

> **Note:** For detailed MDQ vs RAG boundary definition, see [04_mcp_05 §MDQ vs RAG Boundary](04_mcp_05_security_and_safety_model.md#mdq-vs-rag-boundary).

---

## git-mcp (port 8014)

**Purpose:** Local git repository operations with 2-tier safety guards.
**Startup mode:** persistent (HTTP)
**Config:** `config/git_mcp_server.toml`
**Auth:** `GITHUB_TOKEN` not needed; uses local git credentials

**Tools (10):**

All tools require config (`requires_config: true`).

| Tool | Tier | `read_only` guard | `dry_run` | `requires_config` |
|---|---|---|---|---|
| `git_status` | READ_ONLY | — | — | yes |
| `git_log` | READ_ONLY | — | — | yes |
| `git_diff` | READ_ONLY | — | — | yes |
| `git_branch` | READ_ONLY | — | — | yes |
| `git_show` | READ_ONLY | — | — | yes |
| `git_add` | WRITE_SAFE | blocked if `read_only=true` | yes | yes |
| `git_commit` | WRITE_SAFE | blocked | yes | yes |
| `git_checkout` | WRITE_DANGEROUS | blocked | yes | yes |
| `git_pull` | WRITE_DANGEROUS | blocked | yes | yes |
| `git_push` | WRITE_DANGEROUS | blocked | yes | yes |

**Health:** `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}` when git is found; `"status":"degraded","ready":false,"dependencies":{"git":"git not found in PATH"/"check failed"}}` when not — HTTP 200 when ready, 503 when degraded.
**Config:**

| Key | Default | Note |
|---|---|---|
| `allowed_repo_paths` | `[]` | fail-closed; empty = deny all; paths resolved via `Path.resolve()` |
| `read_only` | `true` | All write tools return `[DENIED]` unless explicitly `false` |
| `max_log_entries` | `50` | `git_log` entry cap |
| `audit_log_path` | `"/opt/llm/logs/git-mcp.log"` | Operations log |
| `auth_token` | `""` | Bearer token for MCP server call authentication |

**Note:** `git_show` truncates at 8000 chars. `git_log` inputSchema defaults to `max_entries=20`; config cap `max_log_entries` defaults to `50`.
