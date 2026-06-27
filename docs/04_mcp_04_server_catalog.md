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

**Health:** `{"status":"ok","ready":true}`
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

**Config:**

| Key | Default |
|---|---|
| `allowed_dirs` | `["/opt/llm"]` |
| `max_read_bytes` | `1,000,000` (1 MB) |
| `max_tree_depth` | `5` |
| `max_search_results` | `100` |

**Health:** `{"status":"ok","ready":bool,"dependencies":{"filesystem":"/workspace not found"/"check failed"},"details":{}}`
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

**Security controls:**
- `allowed_repos` / `allowed_repos_mode` (fail-closed by default)
- `protected_branches` (fnmatch patterns)
- `path_denylist` (fnmatch patterns)
- `max_file_size_kb` (0 = unlimited)
- `allow_force_push` (default `false`; set `true` to permit force-push and rebase merge)
- `require_pr_review` (default `true`; set `false` to allow merge without review)

**Domain exceptions** (in `mcp/github/models.py`): `GitHubNotFoundError` (404), `GitHubAuthorizationError` (403),
`GitHubConflictError` (409), `GitHubValidationError` (400), `GitHubUpstreamError` (502), `GitHubAuditError` (500)

**Health:** `{"status":"ok","ready":bool,"dependencies":{"github_token":"set"/"not_set"},"details":{}}`
**Log:** `/opt/llm/logs/github-mcp.log`
**Audit log:** `config/github_mcp_server.toml::audit_log_path`

---

## file-write-mcp (port 8007)

**Purpose:** Local filesystem write operations. All tools support `dry_run=True`.
**Startup mode:** persistent (HTTP)
**Config:** `config/file_write_mcp_server.toml`

**Tools (4):** `write_file`, `edit_file`, `create_directory`, `move_file`

All tools do not require config (`requires_config: false`).

| Tool | Input | dry_run behavior |
|---|---|---|
| `write_file` | `{path, content, dry_run?}` | Returns diff only; no write |
| `edit_file` | `{path, edits: [{old_text, new_text}], dry_run?}` | Returns diff; no write |
| `create_directory` | `{path, dry_run?}` | Returns directory info (exists/would create); no create |
| `move_file` | `{source, destination, dry_run?}` | Returns move feasibility |

**Health:** `{"status":"ok","ready":bool,"dependencies":{"filesystem":"/workspace not found"/"check failed"},"details":{}}`
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

| Tool | Input | dry_run behavior |
|---|---|---|
| `delete_file` | `{path, dry_run?}` | Returns file info; no delete |
| `delete_directory` | `{path, recursive?, dry_run?}` | Scans contents (up to 1000 files); no delete |

**Health:** `{"status":"ok","ready":bool,"dependencies":{"filesystem":"/workspace not found"/"check failed"},"details":{}}`
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
| `audit_log_path` | `""` | Audit log (set in config for production) |

**Health:** `{"status":"ok","ready":bool,"dependencies":{"shell":"sh not found in PATH"/"check failed"},"details":{"sandbox_backend":"firejail"/"none"}}`
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
| `use_mqe` | `True` | Enable multi-query expansion |
| `use_rrf` | `True` | Enable RRF fusion |
| `rrf_k` | `60` | RRF constant |
| `use_rerank` | `True` | Enable cross-encoder rerank |
| `use_refiner` | `False` | Enable context refinement/compression |
| `top_k_search` | `5` | KNN/BM25 top-k per query |
| `top_k_rerank` | `10` | Cross-encoder top-k |
| `rag_top_k` | `5` | Final result count |
| `rag_min_score` | `0.0` | Minimum rerank score threshold |
| `max_chunks_per_doc` | `3` | Max chunks per document in final result |
| `semantic_cache_max_size` | `128` | Semantic cache entry limit |
| `semantic_cache_threshold` | `0.92` | Semantic cache cosine similarity threshold |
| `use_semantic_cache` | `False` | Enable semantic cache |
| `refiner_max_tokens` | `512` | Context refinement max tokens |
| `refiner_max_chars_per_chunk` | `800` | Context refinement chars per chunk |
| `refiner_timeout` | `30.0` | Context refinement timeout (seconds) |
| `rag_auth_token` | `""` | Authentication token for RAG service |

**Health:** `{"status":"ok","ready":bool,"dependencies":{"embed_url":"not configured"/"check failed"},"details":{}}`
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
- `repo_allowlist`: fail-closed (empty = deny all)
- `workflow_allowlist`: fail-open (empty = allow all); in production mode (`security_profile = "production"`), empty list raises `RuntimeError` at agent startup
- `trigger_workflow` supports `dry_run` argument (exposed via tool schema)

**Health:** `{"status":"ok","ready":bool,"dependencies":{} / {"github_token":"not_set"},"details":{}}` — empty deps when token is set, `"github_token":"not_set"` when not set
**Log limits:** max 5 jobs, 256 KB total (default)
**Architecture:** `CiCdService → CiBackend (Protocol) → GitHubActionsBackend`
**Note:** `CiBackend` Protocol allows future GitLab CI / Jenkins backends.

---

## mdq-mcp (port 8013)

**Purpose:** Markdown document indexing and context compression.
**Startup mode:** persistent (HTTP)
**Config:** `config/mdq_mcp_server.toml`

**Tools (9):** `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`, `fts_consistency_check`, `fts_rebuild`

**Health:** `{"status":"ok","ready":bool,"dependencies":{},"details":{"service":"mdq-mcp"}}`

**DB path:** `/opt/llm/db/mdq.sqlite` (`config/mdq_mcp_server.toml`: `db_path`)
**Log:** `/opt/llm/logs/mdq-mcp.log`
**When to use:** Markdown document indexing and context compression. Use `rag-pipeline-mcp` for production RAG search.

### Markdown Compatibility Scope

**Supported features:**
- ATX headings (## Heading) — all levels 1-6
- Fenced code blocks (```, ~~~) — # inside fences are not headings
- Content before first heading (as <root> section)
- Repeated heading names (distinct chunk identities via ordinal)
- Nested heading hierarchy (heading_path includes ancestors)
- Optional YAML frontmatter (parsed and stripped)
- Malformed headings (ignored)

**Unsupported features:**
- Setext-style headings (===, --- underlines)
- Inline tags (<del>, <ins>, etc.) — not parsed
- HTML blocks — not parsed, treated as plain text
- MDX — not supported
- GFM tables — not parsed (but not required for section extraction)

**Fallback behavior:** Unsupported syntax may cause heading misclassification. For example, Setext-style headings are treated as plain text with no heading level, and their content is included in the preceding section rather than creating a new one.

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

**Health:** `{"status":"ok","ready":bool,"dependencies":{"git":"git not found in PATH"/"check failed"},"details":{}}`
**Config:**

| Key | Default | Note |
|---|---|---|
| `allowed_repo_paths` | `[]` | fail-closed; empty = deny all; paths resolved via `Path.resolve()` |
| `read_only` | `true` | All write tools return `[DENIED]` unless explicitly `false` |
| `max_log_entries` | `50` | `git_log` entry cap |
| `audit_log_path` | `""` | Operations log (unused in current implementation) |

**Note:** `git_show` truncates at 8000 chars. `git_log` inputSchema defaults to `max_entries=20`; config cap `max_log_entries` defaults to `50`.
