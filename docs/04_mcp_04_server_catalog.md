# MCP Server Catalog

- System overview → [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md)
- Security model → [04_mcp_05_security_and_safety_model.md](04_mcp_05_security_and_safety_model.md)
- Configuration → [04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration_and_operations.md)

## Purpose

Per-server specification for all 11 MCP servers: purpose, port, tools, input/output,
config, startup, security, logs, operational notes, and known limitations.

---

## web-search-mcp (port 8004)

**Purpose:** Web search with multi-provider fallback (Brave → Bing → DuckDuckGo).
**Startup mode:** persistent (HTTP, OpenRC `web-search-mcp`)
**Config:** `config/web_search_mcp_server.toml`

**Tools:**

| Tool | Input | Output |
|---|---|---|
| `search_web` | `{query: str, max_results?: int}` | Header + N result blocks (title/URL/snippet) |

**Provider fallback:** Brave (requires `BRAVE_API_KEY`) → Bing (requires `BING_API_KEY`) → DuckDuckGo (no key).
All providers that fail or return 0 results are skipped automatically.
All providers failed → HTTP 502.

**Config parameters:**

| Key | Default | Description |
|---|---|---|
| `search_providers` | `["duckduckgo"]` | Provider priority list |
| `default_max_results` | `5` | Default result count |
| `max_results_limit` | `20` | Server-side cap |

**Health:** `{"status":"ok","providers":[...],"brave_key":"set","bing_key":"not_set"}`
**Log:** `/opt/llm/logs/web-search-mcp.log`
**When to use:** Real-time information not in RAG index; latest releases; news.

---

## file-read-mcp (port 8005)

**Purpose:** Read-only access to local filesystem within `allowed_dirs`.
**Startup mode:** persistent (HTTP, OpenRC `file-mcp`)
**Config:** `config/file_read_mcp_server.toml`

**Tools (9):** `read_text_file`, `list_directory`, `list_directory_with_sizes`, `directory_tree`,
`read_media_file`, `read_multiple_files`, `search_files`, `grep_files`, `get_file_info`

**Key tool inputs:**

| Tool | Input |
|---|---|
| `read_text_file` | `{path, head?, tail?}` |
| `grep_files` | `{path, pattern, file_pattern?, max_matches?}` |
| `directory_tree` | `{path, depth?}` |
| `read_multiple_files` | `{paths: list[str]}` |

**Config:**

| Key | Default |
|---|---|
| `allowed_dirs` | `["/opt/llm"]` |
| `max_read_bytes` | `1,000,000` (1 MB) |
| `max_tree_depth` | `5` |
| `max_search_results` | `100` |

**Error codes:** 400 (invalid path), 403 (outside allowed_dirs), 404 (not found), 413 (size limit), 415 (binary)
**Log:** `/opt/llm/logs/file-read-mcp.log`
**Additional endpoint:** `GET /list_allowed_directories` (not a MCP tool)

---

## github-mcp (port 8006)

**Purpose:** GitHub API via PyGithub. Reads and writes to GitHub repositories.
**Startup mode:** persistent (HTTP, OpenRC `github-mcp`)
**Config:** `config/github_mcp_server.toml`
**Auth:** `GITHUB_TOKEN` env var (PAT); without it: 60 req/hour anonymous

**Tools (21):** All prefixed `github_`: `search_repositories`, `get_file_contents`,
`push_files`, `delete_repo_file`, `list_branches`, `get_commit`, `list_issues`, `get_issue`,
`create_issue`, `search_issues`, `list_pull_requests`, `get_pull_request`,
`search_pull_requests`, `update_pull_request`, `merge_pull_request`, `list_commits`,
`search_code`, `create_pull_request`, `create_branch`, `create_or_update_file`, `add_issue_comment`

**Write operations (9) are subject to repo allowlist:**
`create_branch`, `create_or_update_file`, `push_files`, `delete_repo_file`,
`create_issue`, `add_issue_comment`, `create_pull_request`, `update_pull_request`, `merge_pull_request`

**Security controls:**
- `allowed_repos` / `allowed_repos_mode` (fail-closed by default)
- `protected_branches` (fnmatch patterns)
- `path_denylist` (fnmatch patterns)
- `max_file_size_kb` (0 = unlimited)
- `allow_force_push` (default `true`)
- `require_pr_review` (default `false`)

**Domain exceptions** (in `mcp/github/models.py`): `GitHubNotFoundError` (404), `GitHubAuthorizationError` (403),
`GitHubConflictError` (409), `GitHubValidationError` (400), `GitHubUpstreamError` (502), `GitHubAuditError` (500)

**Health:** `{"status":"ok","github_token":"set"}` or `"not_set"`
**Log:** `/opt/llm/logs/github-mcp.log`
**Audit log:** `config/github_mcp_server.toml::audit_log_path`

---

## file-write-mcp (port 8007)

**Purpose:** Local filesystem write operations. All tools support `dry_run=True`.
**Startup mode:** persistent (HTTP, OpenRC `file-mcp`)
**Config:** `config/file_write_mcp_server.toml`

**Tools (4):** `write_file`, `edit_file`, `create_directory`, `move_file`

| Tool | Input | dry_run behavior |
|---|---|---|
| `write_file` | `{path, content, dry_run?}` | Returns diff only; no write |
| `edit_file` | `{path, edits: [{old_text, new_text}], dry_run?}` | Returns diff; no write |
| `create_directory` | `{path, dry_run?}` | Returns existence check |
| `move_file` | `{source, destination, dry_run?}` | Returns move feasibility |

**Config:** `max_write_bytes` (default 1 MB; enforced as UTF-8 byte count via Pydantic)
**Error codes:** 400, 403 (outside allowed_dirs), 404, 413/422 (size limit)
**Log:** `/opt/llm/logs/file-write-mcp.log`

---

## file-delete-mcp (port 8008)

**Purpose:** Local filesystem deletion. All tools support `dry_run=True`.
**Startup mode:** persistent (HTTP, OpenRC `file-mcp`)
**Config:** `config/file_delete_mcp_server.toml`

**Tools (2):** `delete_file`, `delete_directory`

| Tool | Input | dry_run behavior |
|---|---|---|
| `delete_file` | `{path, dry_run?}` | Returns file info; no delete |
| `delete_directory` | `{path, recursive?, dry_run?}` | Scans contents (up to 1000 files); no delete |

**Delete audit log:** `/opt/llm/logs/delete_audit.log` (ISO8601 UTC + op + path + user)
**Log:** `/opt/llm/logs/file-delete-mcp.log`

---

## shell-mcp (port 8009)

**Purpose:** Sandboxed shell command execution within `command_allowlist`.
**Startup mode:** persistent (HTTP, OpenRC `shell-mcp`)
**Config:** `config/shell_mcp_server.toml`

**Tools (1):** `shell_run`

| Input field | Default | Description |
|---|---|---|
| `command` | required | Shell command string |
| `argv` | `null` | Direct argv (skips shlex; preferred for injection prevention) |
| `cwd` | `null` | Working directory (must be in `shell_cwd_allowed_dirs`) |
| `timeout_sec` | `30` | Timeout (capped at `max_timeout_sec`) |
| `max_output_kb` | `256` | Output limit KB (capped at config `max_output_kb`) |
| `env` | `{}` | Additional env vars (filtered by allowlist/denylist) |

**Output:** `{stdout, stderr, exit_code, timed_out, truncated, elapsed_sec}`

**Config:**

| Key | Default | Description |
|---|---|---|
| `command_allowlist` | `[]` | Allowed command names (`argv[0]` basename) |
| `shell_cwd_allowed_dirs` | `[]` | Allowed CWD paths (empty = deny all) |
| `max_timeout_sec` | `300` | Max timeout cap |
| `max_output_kb` | `4096` | Output cap |
| `max_memory_mb` | `512` | Memory limit (`RLIMIT_AS`) |
| `shell_sandbox_backend` | `"none"` | `"firejail"` or `"none"` |
| `audit_log_path` | `"/opt/llm/logs/shell_audit.log"` | Audit log |

**Known limitation:** `shell_run_bg` is listed in tool constants but NOT implemented.
**Log:** `/opt/llm/logs/shell-mcp.log`

---

## rag-pipeline-mcp (port 8010)

**Purpose:** RAG retrieval pipeline (MQE → Search → RRF → Rerank → Dedup → Augment).
**Startup mode:** persistent (HTTP, OpenRC `rag-pipeline-mcp`)
**Config:** `config/rag_pipeline_mcp_server.toml`

**Tools (2):**

| Tool | Input | Output |
|---|---|---|
| `rag_run_pipeline` | `{query, history_context?, debug?}` | `augmented_text` + `selected_hits` |
| `rag_debug_pipeline` | `{query, history_context?}` | All intermediate stage outputs |

**Additional endpoint:** `POST /v1/search` (backward compat for `RagPipeline._augment_http()`)

**Key config:** `llm_url`, `embed_url`, `rag_db_path`, `sqlite_vec_so`, `use_mqe`, `use_rrf`,
`use_rerank`, `top_k_search`, `top_k_rerank`, `rag_top_k`, `rag_min_score`

**Design note:** `rag_service_url = ""` is hardcoded in `build_rag_cfg_adapter()` to prevent HTTP loops.
**Log:** (uses structlog; check `agent.log` or configure separate log)
**When to use:** All RAG retrieval; `/rag search` command goes through this server.

---

## sqlite-mcp (port 8011)

**Purpose:** Read-only SELECT queries against registered SQLite databases.
**Startup mode:** `subprocess` (agent-managed subprocess; NOT OpenRC)
**Config:** `config/sqlite_mcp_server.toml`

**Tools (1):** `query_sqlite`

**Input:** `{db: str, sql: str}` — `db` must be in `db_allowlist`; `sql` must be a single SELECT

**Security (4 layers):**
1. `db_allowlist` — fail-closed; empty list → deny all
2. SQL comment stripping (`--`, `/* */`)
3. Multi-statement rejection (`;` count check)
4. First keyword must be `SELECT`
5. `PRAGMA query_only=ON` on every connection

**Config:**

| Key | Default |
|---|---|
| `db_allowlist` | `[]` |
| `[db_paths]` | `{}` |
| `max_rows` | `100` |
| `auth_token` | `""` |

**Important:** `query_sqlite` is NOT in the static routing table. Must set `tool_names = ["query_sqlite"]` in `mcp_servers.sqlite` config.
**Databases:** `rag` → `/opt/llm/db/rag.sqlite`; `session` → `/opt/llm/db/session.sqlite`

---

## cicd-mcp (port 8012)

**Purpose:** GitHub Actions workflow management.
**Startup mode:** persistent (HTTP, OpenRC `cicd-mcp`)
**Config:** `config/cicd_mcp_server.toml`
**Auth:** `GITHUB_TOKEN` (via `conf.d/cicd-mcp`)

**Tools (4):**

| Tool | Tier | Input |
|---|---|---|
| `trigger_workflow` | WRITE_DANGEROUS | `{repo, workflow, ref?, inputs?}` |
| `get_workflow_runs` | READ_ONLY | `{repo, workflow, limit?}` |
| `get_workflow_status` | READ_ONLY | `{repo, run_id}` |
| `get_workflow_logs` | READ_ONLY | `{repo, run_id}` |

**Security:**
- `repo_allowlist`: fail-closed (empty = deny all)
- `workflow_allowlist`: fail-open (empty = allow all)
- `trigger_workflow` supports `dry_run` argument

**Log limits:** max 5 jobs, 256 KB total (default)
**Architecture:** `CiCdService → CiBackend (Protocol) → GitHubActionsBackend`
**Note:** `CiBackend` Protocol allows future GitLab CI / Jenkins backends.

---

## mdq-mcp (port 8013)

**Purpose:** Markdown document indexing and context compression.
**Startup mode:** persistent (HTTP, OpenRC `mdq-mcp`)
**Config:** `config/mdq_mcp_server.toml`

**Tools (7):** `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`

> **IMPORTANT — Placeholder Implementation:** The server schema, HTTP endpoints, and MCPServer
> base class are complete. The service layer (`MdqService`) and search/index logic are PLACEHOLDERS.
> All tools return stub strings (e.g., `"Search results for: {query}"`). No actual data operations occur.
> See [04_mcp_90_inconsistencies_and_known_issues.md](04_mcp_90_inconsistencies_and_known_issues.md).

**DB path:** `/opt/llm/db/mdq.db` (hardcoded in `MdqService.__init__()`)
**Log:** `/opt/llm/logs/mdq-mcp.log`
**When to use:** Currently stub only. Use `rag-pipeline-mcp` for actual search.

---

## git-mcp (port 8014)

**Purpose:** Local git repository operations with 2-tier safety guards.
**Startup mode:** persistent (HTTP, OpenRC `git-mcp`)
**Config:** `config/git_mcp_server.toml`
**Auth:** `GITHUB_TOKEN` not needed; uses local git credentials

**Tools (10):**

| Tool | Tier | `read_only` guard | `dry_run` |
|---|---|---|---|
| `git_status` | READ_ONLY | — | — |
| `git_log` | READ_ONLY | — | — |
| `git_diff` | READ_ONLY | — | — |
| `git_branch` | READ_ONLY | — | — |
| `git_show` | READ_ONLY | — | — |
| `git_add` | WRITE_SAFE | blocked if `read_only=true` | yes |
| `git_commit` | WRITE_SAFE | blocked | yes |
| `git_checkout` | WRITE_DANGEROUS | blocked | yes |
| `git_pull` | WRITE_DANGEROUS | blocked | yes |
| `git_push` | WRITE_DANGEROUS | blocked | yes |

**Config:**

| Key | Default | Note |
|---|---|---|
| `allowed_repo_paths` | `[]` | fail-closed; empty = deny all; paths resolved via `Path.resolve()` |
| `read_only` | `true` | All write tools return `[DENIED]` unless explicitly `false` |
| `max_log_entries` | `50` | `git_log` entry cap |
| `audit_log_path` | `"/opt/llm/logs/git-mcp.log"` | Operations log |

**Note:** `git_show` truncates at 8000 chars. `git_log max_entries` is capped by config.
