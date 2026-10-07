---
title: "MCP Server Catalog: web-search-mcp / file-read-mcp / github-mcp"
area: mcp
tags:
  - mcp
  - server-catalog
  - web-search
  - file-read
  - github
related:
  - mcp_00_document-guide.md
  - mcp_04_02_file-write-file-delete-shell.md
  - mcp_04_03_rag-pipeline-and-cicd.md
  - mcp_04_04_mdq.md
  - mcp_04_05_git.md
---

# MCP Server Catalog: web-search-mcp / file-read-mcp / github-mcp

## Purpose

Specifications for each MCP server: purpose, port, tools, I/O, configuration, startup, security, logs, operational notes, and known limitations.

> **Note:** This document is a formal server catalog. For a system-level list of servers including ports and transport types, refer to [mcp_01_system_overview.md Server Catalog](mcp_01_system_overview.md).

---

## web-search-mcp 

**Purpose:** Web search via DuckDuckGo (no API key required).
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/web_search_mcp_server.toml`

**Tools:**

| Tool | Input | Output |
|---|---|---|
| `search_web` | `{query: str (non-empty after trim, length-limited), max_results?: int (1 to configured `max_results_limit`, hard limit `HARD_MAX_RESULTS_LIMIT`)}` | Header + N result blocks (title/URL/snippet) |

**Configuration Parameters:**

| Key | Description |
|---|---|
| `default_max_results` | Default number of results |
| `max_results_limit` | Server-side limit (must be ≤ `HARD_MAX_RESULTS_LIMIT`) |
| `search_timeout_sec` | Timeout in seconds for provider calls (range: `(0, 60.0]`) |

Current default values are defined in `config/web_search_mcp_server.toml` and the owning config class.

**Note:** The above two keys are directly reflected in `SearchRequest.max_results` in `mcp_servers/web_search/web_search_github_models.py` (Pydantic `Field`'s `ge`/`le`/default value) via `WebSearchConfig.load()` which is loaded during module import (following the existing `_cfg: WebSearchConfig = WebSearchConfig.load()` pattern in `web_search_server.py`).

**Note:** `WebSearchConfig.from_dict()` validates the following invariants and raises `ValueError` on violation (evaluated at module import, so invalid configurations cause fail-fast process startup): `default_max_results >= 1`, `max_results_limit >= 1`, `default_max_results <= max_results_limit`, `max_results_limit <= HARD_MAX_RESULTS_LIMIT`, and `search_timeout_sec` within `(0, 60.0]`. Additionally, `SearchRequest.query` is normalized by field validators: leading/trailing whitespace is trimmed, and requests containing empty strings or control characters (Unicode category `Cc`, including NUL) after trimming are rejected. The `inputSchema` for the `search_web` tool (`TOOL_LIST` in `web_search_tools.py`) retrieves `minLength`/`maxLength`/`minimum`/`maximum` from the same `_cfg` singleton via `get_max_results_limit()`, ensuring TOML changes to `max_results_limit` are only reflected in `/v1/tools` after a server restart, consistent with `_cfg`.

**Note:** Calls to `health.record_success()`/`record_failure()`/`metrics.record_query()` are centralized in the orchestration layer `scripts/mcp_servers/web_search/web_search_service.py` (handles `SearchRequest` construction, `search_provider.search_duckduckgo` invocation, and latency measurement). `formatters.py::fdisp_search_web()` calls `service.search_web()` and formats the result. `web_search_server.py::call_tool()` does not call these update hooks directly; instead, it only handles `outcome`/`error_type` classification for `_audit_log(...)` to avoid double counting health/metrics—only `web_search_service.py` performs `health.record_*`/`metrics.record_query` within the package.

**Note:** The `browser_fetch` tool performs read-only page fetching and text extraction (no interactive operations; no JavaScript execution).

**Tools:**

| Tool | Input | Output |
|---|---|---|
| `browser_fetch` | `{url: str (http/https only), max_response_kb?: int}` | Extracted text (with `truncated` flag) |

**Configuration Parameters (Integrated into `config/web_search_mcp_server.toml`):**

| Key | Description |
|---|---|
| `browser_allowed_domains` | fail-closed; empty = all domains denied (exact host match) |
| `browser_max_response_kb` | Limit for extracted text size. If exceeded, text is truncated and `truncated=true` is set. |
| `browser_timeout_sec` | Timeout for fetch requests |
| `browser_auth_token` | Bearer token for `browser_fetch` calls only (independent of `search_web`) |

Current default values are defined in `config/web_search_mcp_server.toml` and the owning config class.

**Implementation Details (browser_fetch):**

- If the hostname is an IP literal, it is checked using `ipaddress.ip_address()`; if it falls under loopback / link-local / private / reserved / multicast, a `BrowserAuthorizationError` (HTTP 403) is raised regardless of `allowed_domains` content. This is a defense-in-depth mechanism independent of domain allowlists. (Explicit in code — `search_provider.py::_check_domain`)
- Only `http`/`https` schemes are allowed for `url`; others or missing hostnames trigger a `BrowserValidationError` (HTTP 422). (Explicit in code)
- While `max_response_kb` can be specified by the caller, it is always clamped to the server setting `browser_max_response_kb` using `min()`. (Explicit in code)
- Text truncation is performed by encoding to bytes before slicing (`_truncate`), preventing corruption of UTF-8 multibyte characters that might occur with naive character-based slicing. (Explicit in code)
- Since it does not execute JavaScript (fetches HTML and extracts visible text via `BeautifulSoup`), meaningful text may be minimal or absent on client-side rendered SPA/React pages. This is intended behavior. (Accepted current specification).
- `browser_fetch`'s health/metrics are managed by separate singletons from `search_web` (`_browser_*` in `health.py`/`metrics.py`) and are separately reflected in `/health`'s `details`.

### Availability metadata

The web-search server computes `enabled`/`disabled_reason` per tool in `/v1/tools` via `_web_search_tool_availability()`:

- `config_dependent`: `true` for `browser_fetch` — indicates the tool depends on configuration
- `enabled` / `disabled_reason`: `browser_fetch` is disabled with reason `"browser_allowed_domains is empty"` when no allowed domains are configured; `search_web` is always enabled

#### Enforcement mechanism

`/v1/call_tool` rejects a disabled tool with `Tool disabled: <reason>` (`is_error=True`) before dispatch. When `browser_fetch` is called with a domain not in the allowlist, the server raises `BrowserAuthorizationError`, returned via the `/v1/call_tool` response.

---

## file-read-mcp 

**Purpose:** Read-only access to the local filesystem within `allowed_dirs`.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/file_read_mcp_server.toml`

**Tools:** `read_text_file`, `list_directory`, `list_directory_with_sizes`, `directory_tree`, `read_media_file`, `read_multiple_files`, `search_files`, `grep_files`, `get_file_info`

All tools do not require configuration (`config_dependent: false`).

Tool availability (`enabled`/`disabled_reason`) depends on `allowed_dirs` (empty → disabled, reason `"allowed_dirs is empty"`). See [mcp_03_06_tool-runtime-availability-metadata.md](mcp_03_06_tool-runtime-availability-metadata.md) for details.

**Primary Tool Inputs:**

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

**Configuration Fields:** `allowed_dirs`, `max_read_bytes`, `max_tree_depth`, `max_search_results`

**Health:** `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{"filesystem":"/workspace is not a directory"/"check failed: <error>"},"details":{}}` — HTTP 200 when ready, HTTP 503 when degraded.
**Error Codes:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**Logs:** `<log_dir>/file-read-mcp.log`
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): None / Layer3 (Dedicated): None — Does not write audit logs
**Additional Endpoints:** `GET /list_allowed_directories` (Not an MCP tool)

### Implementation Details (file-read-mcp)

- `FileReadConfig.from_dict` (`read_github_models.py`) interprets TOML's `max_read_bytes` as **KB** (`max_file_size_kb = max_read_bytes // 1024`). The effective limit is therefore `max_read_bytes // 1024 * 1024` bytes, which can differ from the TOML value when it is not a multiple of 1024. (Explicit in code)
- Read-only errors are `FileAuthorizationError`(403) / `FileNotFoundError`(404) / `FileValidationError`(400 or 422 as registered in `read_web_search_server.py`'s 422 handler) in addition to `read_text_file` rejecting simultaneous `head`/`tail` arguments via Pydantic model validation (ValueError → FastAPI standard 422). (Explicit in code)

---

## github-mcp 

See also: [security_02_high-risk-tool-common-policy.md](../91_security/security_02_high-risk-tool-common-policy.md) for the cross-cutting canonical policy governing github-mcp as a high-risk tool.

**Purpose:** GitHub API via PyGithub. Performs reads and writes to GitHub repositories.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/github_mcp_server.toml`
**Authentication:** `GITHUB_TOKEN` environment variable (PAT). If unset, every tool is reported disabled (`GITHUB_TOKEN is not set`) and `/v1/call_tool` rejects every call with `Tool disabled: GITHUB_TOKEN is not set`; there is no usable anonymous mode through the MCP tools. (Explicit in code — `scripts/mcp_servers/github/github_server.py`)

**Tools:** All prefixed with `github_`: `github_search_repositories`, `github_get_file_contents`, `github_push_files`, `github_delete_file`, `github_list_branches`, `github_get_commit`, `github_list_issues`, `github_get_issue`, `github_create_issue`, `github_search_issues`, `github_list_pull_requests`, `github_get_pull_request`, `github_search_pull_requests`, `github_update_pull_request`, `github_merge_pull_request`, `github_list_commits`, `github_search_code`, `github_create_pull_request`, `github_create_branch`, `github_create_or_update_file`, `github_add_issue_comment`

All tools require configuration (`config_dependent: true`).

The calculation logic for `enabled`/`disabled_reason` for the GitHub MCP server is computed by `_github_tool_availability()` (disabled with reason `"GITHUB_TOKEN is not set"` when the token is missing). Refer [mcp_03_06_tool-runtime-availability-metadata.md](mcp_03_06_tool-runtime-availability-metadata.md) for current contract.

**Write Operations (9 items) are subject to repository allowlist:**
`github_create_branch`, `github_create_or_update_file`, `github_push_files`, `github_delete_file`, `github_create_issue`, `github_add_issue_comment`, `github_create_pull_request`, `github_update_pull_request`, `github_merge_pull_request`

**Configuration Fields:** `max_per_page`, `allowed_repos`, `protected_branches` (fnmatch pattern), `path_denylist` (fnmatch pattern), `max_file_size_kb`, `allow_force_push`, `require_pr_review`, `audit_log_path`

**Note:** `default_per_page` is not a configuration key of `config/github_mcp_server.toml`. The default count for listing endpoints is module constant `DEFAULT_PER_PAGE` (`github_models_config.py`) which each request model references directly (not configurable). `max_per_page` is used as `self._max_per_page` for clamping `per_page` values and is a valid configuration.

**Security Control:**
- `allowed_repos` (fail-closed; empty list = all denied)
- `protected_branches` (fnmatch pattern)
- `path_denylist` (fnmatch pattern)
- `max_file_size_kb` (0 = unlimited)
- `allow_force_push` (disabled unless set to `true`, which allows force-push and rebase merges)
- `require_pr_review` (review required unless set to `false`, which allows merging without review)

**Domain Exceptions** (defined in `scripts/mcp_servers/github/github_models_config.py`, re-exported in `github_models.py`): `GitHubNotFoundError` (404), `GitHubAuthorizationError` (403), `GitHubConflictError` (409), `GitHubValidationError` (400), `GitHubUpstreamError` (502), `GitHubAuditError` (500)

**Health:** Token configured: `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`; Unset: `{"status":"degraded","ready":false,"dependencies":{"github_token":"not_set"}}` — HTTP 200 when ready, HTTP 503 when degraded.
**Logs:** `<log_dir>/github-mcp.log`
**Audit:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (Shared MCP): `mcp_tool_exec` / Layer3 (Dedicated): `github_audit.log`

### Implementation Details (github-mcp)

- Domain exception HTTP status mapping (`exception_handlers.py`): `GitHubAuthorizationError` → 403, `GitHubNotFoundError` → 404, `GitHubValidationError` → 400, `GitHubConflictError` → 409, `GitHubUpstreamError` → 502, `GitHubAuditError` → 500. (Explicit in code)
- PyGithub's `GithubException` is converted to domain exceptions in `service_security.py` based on status codes (404 → NotFound, 403 → Authorization, 409 → Conflict, 400/422 → Validation, others → Upstream). (Explicit in code)
- `allow_force_push=false` only applies by rejecting `merge_method="rebase"` in `merge_pull_request` (it does not directly block other force-push equivalent operations). (Explicit in code)
- `require_pr_review=true` ensures at least one `APPROVED` review exists when executing `merge_pull_request`. (Explicit in code)
- When `GITHUB_TOKEN` is unset, the process still starts and constructs an unauthenticated `Github()` client (with a startup warning about the unauthenticated API rate limit) and reports `degraded` health, but the disabled-tool gate in `/v1/call_tool` prevents any tool from using that client (`github_service_init.py`, `github_server.py`). (Explicit in code)

---

## Keywords

mcp
server-catalog
web-search-mcp, file-read-mcp, github-mcp
