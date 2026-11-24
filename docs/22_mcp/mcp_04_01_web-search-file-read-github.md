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
  - mcp_01_system_overview.md
  - mcp_03_06_tool-runtime-availability-metadata.md
  - security_02_high-risk-tool-common-policy.md
---

# MCP Server Catalog: web-search-mcp / file-read-mcp / github-mcp

## Purpose

Per-server design specification: purpose, security boundary, failure behavior, audit, and operational notes. Tool-to-server membership and risk tiers are owned by [mcp_01_tool_ownership_matrix.md](mcp_01_tool_ownership_matrix.md); ports and tool counts are in its auto-generated table. Health response semantics are common to all servers: [mcp_02_02](mcp_02_02_startup-modes-and-health.md). Availability metadata (`enabled`/`disabled_reason`): [mcp_03_06](mcp_03_06_tool-runtime-availability-metadata.md).

> **Note:** For a system-level list of servers, refer to [mcp_01_system_overview.md Server Catalog](mcp_01_system_overview.md).

---

## web-search-mcp

**Purpose:** Web search via DuckDuckGo (no API key required, `search_web`) and read-only page fetch with text extraction (`browser_fetch`; no interactive operations, no JavaScript execution).
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/web_search_mcp_server.toml` (defaults are owned by this file and `WebSearchConfig`)

**Configuration invariants:**

- `WebSearchConfig.from_dict()` raises `ValueError` on violation at module import, so an invalid configuration fails process startup: `default_max_results >= 1`, `max_results_limit >= 1`, `default_max_results <= max_results_limit <= HARD_MAX_RESULTS_LIMIT`, and `search_timeout_sec` within `(0, 60.0]`.
- `search_web` input is normalized: surrounding whitespace is trimmed, and a query that is empty or contains control characters (Unicode category `Cc`, including NUL) after trimming is rejected.
- The `search_web` `inputSchema` limits come from the same config singleton as the request validation, so a TOML change to `max_results_limit` is reflected in `/v1/tools` only after a server restart.
- `auth_token` is required on every request to the server (both tools), supplied by the same environment variable as the agent's web-search entry so both sides share one secret.

**`browser_fetch` security boundary:**

- `browser_allowed_domains` is fail-closed: empty means all domains are denied (exact host match). The tool is then reported disabled with reason `"browser_allowed_domains is empty"`; `search_web` is always enabled. `config_dependent` is `true` for `browser_fetch`.
- A hostname that is an IP literal in a loopback / link-local / private / reserved / multicast range raises `BrowserAuthorizationError` (HTTP 403) regardless of the allowlist. This is defense-in-depth independent of domain allowlists (`_check_domain` in `search_provider.py`).
- Only `http`/`https` URLs with a hostname are accepted; otherwise `BrowserValidationError` (HTTP 422).
- A caller-supplied `max_response_kb` is always clamped to the server setting `browser_max_response_kb`. Truncation is byte-based (encode, then slice) so UTF-8 multibyte characters are not corrupted, and the result carries `truncated=true`.
- Client-side rendered pages (SPA/React) may yield little or no text. This is accepted current specification.

**Operational notes:**

- Health and metrics recording is centralized in `web_search_service.py`; the server's `call_tool()` only classifies `outcome`/`error_type` for the audit log, to avoid double counting.
- `browser_fetch` health/metrics use separate singletons from `search_web` and are reported separately in `/health` `details`.
- `/v1/call_tool` rejects a disabled tool with `Tool disabled: <reason>` (`is_error=True`) before dispatch.

---

## file-read-mcp

**Purpose:** Read-only access to the local filesystem within `allowed_dirs`.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/file_read_mcp_server.toml` (`allowed_dirs`, size and result limits)

- No tool requires configuration (`config_dependent: false`), but availability depends on `allowed_dirs`: empty means disabled with reason `"allowed_dirs is empty"`.
- `max_read_bytes` is a byte count applied unchanged; `max_file_size_kb` belongs to github-mcp only.
- `read_text_file` rejects simultaneous `head` and `tail` through model validation (422).
- Error mapping: `FileAuthorizationError` 403, `FileNotFoundError` 404, `FileValidationError` 400 or 422 (as registered by the server's validation-error handler).
- `/health`: `dependencies.filesystem` reports a workspace root that is not a directory; HTTP 200 when ready, 503 when degraded.
- `GET /list_allowed_directories` is an auxiliary endpoint, not an MCP tool.
- Logs: `<log_dir>/file-read-mcp.log`. Audit: file-read-mcp writes no audit log (no shared or dedicated layer).

---

## github-mcp

See also: [security_02_high-risk-tool-common-policy.md](../91_security/security_02_high-risk-tool-common-policy.md) for the cross-cutting canonical policy governing github-mcp as a high-risk tool. Agent-side approval confirms user intent only; it is not a bypass for any guard below.

**Purpose:** GitHub API via PyGithub. Performs reads and writes to GitHub repositories.
**Startup Mode:** `subprocess` (HTTP) in the default configuration. `startup_mode = "none"` in `config/agent.toml` disables the server: the Agent performs no subprocess startup or lifecycle operations for it.
**Configuration:** `config/github_mcp_server.toml`
**Authentication:** `GITHUB_TOKEN` environment variable (PAT). If unset, every tool is reported disabled (`GITHUB_TOKEN is not set`) and `/v1/call_tool` rejects every call with `Tool disabled: GITHUB_TOKEN is not set`; there is no usable anonymous mode through the MCP tools. The process still starts with an unauthenticated client (startup warning about the API rate limit) and reports `degraded` health, but the disabled-tool gate prevents any tool from using that client. All tools are `config_dependent: true`.

**Security controls (`config/github_mcp_server.toml`):**

- `allowed_repos`: fail-closed; an empty list denies every repository. Every operation naming a repository — reads included — is checked inside `_get_repo()` (`github_service_security.py`) before the first API call, and `Owner/Repo` and `owner/repo` are the same canonical lowercase key for the guard, the API slug, the error text, and the audit record.
- `allow_global_search` (`false` by default): each search is scoped to `allowed_repos` at query-construction time, and a caller `repo:`/`org:`/`user:` qualifier naming something outside the boundary is rejected before the call. `true` opts in to global search and the posture reports it.
- `max_file_read_size_kb` (`0` = unlimited): the content metadata size is checked before decoding, and content that does not decode as strict UTF-8 is rejected with `GitHubValidationError`; no U+FFFD substitution occurs.
- `protected_branches` and `path_denylist` (fnmatch patterns) reject matching branches and paths. `path_denylist` applies to reads as well as writes.
- `max_file_size_kb` (0 = unlimited) rejects larger content.
- `allow_force_push` is disabled unless `true`; it only gates `merge_pull_request` by rejecting `merge_method="rebase"` and does not block other force-push equivalents.
- `require_pr_review` is on unless `false`; `merge_pull_request` then requires at least one `APPROVED` review.
- `max_per_page` clamps requested `per_page`; the default listing size is a module constant, not a configuration key.

**Guard coverage (layered protection):**

- **Agent approval:** not applicable server-side; github enforces only its own technical constraints.
- **Common guard:** `call_tool` rejects a disabled tool first; every operation naming a repository — reads included — resolves through `_get_repo()`, which asserts the canonical key against `allowed_repos` (`_assert_allowed_repo`, `github_service_security.py`) and raises `GitHubAuthorizationError` outside the allowlist before the first API call.
- **Command-specific guard:** per-operation asserts run before the call they guard: the path denylist and read-size check with strict UTF-8 decoding on the read path (`_assert_allowed_path`, `_assert_max_read_file_size`), and the path, branch, write file size, and `per_page` clamping asserts on the write path (`github_service_security.py`). Search tools scope their query at construction time (`_resolve_search_query`).
- **Postcondition verification:** not applicable in the current plan, because the GitHub API response carries the resulting state and no local before/after comparison is performed. `push_files` returns the new commit SHA without inspecting the ref update result, so it does not confirm that the ref moved; confirming ref movement without an extra API call is a follow-up (Plan UNK-02).
- **Audit:** `call_tool` writes one `mcp_tool_exec` record (to `github-mcp.log`) per dispatched call (`server_key="github"`, `target` = `repo={owner}/{repo}` with the canonical lowercase key); a disabled-tool rejection returns before the audit call and writes no record. The service also writes the dedicated `github_audit.log`, and a failure to write it raises `GitHubAuditError` (HTTP 500) instead of being ignored. Before/after state snapshots are not applicable.

**Error mapping:** PyGithub `GithubException` is converted to domain exceptions by status (404 NotFound, 403 Authorization, 409 Conflict, 400/422 Validation, others Upstream 502); `GitHubAuditError` is 500. Mapping is registered in `exception_handlers.py`.

**Health:** `dependencies.github_token="not_set"` when the token is missing (`degraded`, HTTP 503); otherwise `ok`.
**Logs:** `<log_dir>/github-mcp.log`
**Audit layers:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (per-server application log): `mcp_tool_exec` / Layer3 (Dedicated): `github_audit.log`

---

## Keywords

- mcp
- server-catalog
- web-search-mcp
- file-read-mcp
- github-mcp
