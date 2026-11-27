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

- `browser_allowed_domains` is fail-closed: empty means all domains are denied. Entries are bare hostnames, normalized when the configuration loads (lowercase, IDNA ASCII, one trailing dot removed), and the URL host is normalized the same way before an exact match. A non-string, blank, malformed, or duplicate entry, or an entry with a scheme, path, query, fragment, user information, or port, stops startup (the error names the setting and the entry index, never the value). A URL returned by `search_web` is not authorized for `browser_fetch`: only an allowlisted host is fetched. The tool is then reported disabled with reason `"browser_allowed_domains is empty"`; `search_web` is always enabled. `config_dependent` is `true` for `browser_fetch`.
- A hostname that is an IP literal in a loopback / link-local / private / reserved / multicast range raises `BrowserAuthorizationError` (HTTP 403) regardless of the allowlist. This is defense-in-depth independent of domain allowlists (`_check_domain` in `search_provider.py`).
- Only `http`/`https` URLs with a hostname are accepted; otherwise `BrowserValidationError` (HTTP 422).
- DNS and connection: before connecting, the server resolves every A and AAAA answer of the host (`scripts/mcp_servers/address_policy.py`). If any answer is loopback, private, link-local, reserved, multicast, unspecified, or an IPv4-mapped form of such an address, the request is rejected as a whole with `BrowserAuthorizationError` (HTTP 403); a mixed answer is not filtered to its public addresses. An empty answer or a failed lookup is a `WebSearchNetworkError`. The connection is made to the validated address while the original host stays the `Host` header and the TLS server name, so certificate checks use the requested host. Environment proxies are not used, because a proxy resolves names itself and would defeat the pinning.
- Redirects: the server follows at most 5 redirects itself (`scripts/mcp_servers/bounded_fetch.py`). Each hop repeats the scheme, allowlist, DNS, and address checks. A redirect without a usable `Location`, to a non-http(s) scheme, or beyond the bound is a `BrowserHttpStatusError` with category `redirect`.
- Status: only a 2xx response is a result. 4xx (`client_error`), 429 (`rate_limited`), 5xx (`server_error`), and any other status (`other`) raise `BrowserHttpStatusError`, mapped to HTTP 502, and the upstream body is never returned as page content.
- Content types: only `text/html` (parsed for visible text) and `text/plain` (returned as text) are accepted, decided from the response headers before the body is read; any other or missing type, and any content encoding other than identity, gzip, or deflate, raises `BrowserUnsupportedContentError`.
- Limits: four independent limits apply. The raw network bytes (2 MiB), the bytes after content decoding (8 MiB), and the bytes handed to the HTML parser (2 MiB) are enforced while the body is streamed, so a declared or missing `Content-Length`, chunked transfer, or a compressed body cannot exceed them. The returned text is limited by `browser_max_response_kb`. The extracted-text limit alone is not a resource control: it applies only after the download and the parse.
- A caller-supplied `max_response_kb` is always clamped to the server setting `browser_max_response_kb`. Truncation of the extracted text is byte-based (encode, then slice) so UTF-8 multibyte characters are not corrupted, and the result carries `truncated=true`. A download that stopped at a network, decoding, or parser-input limit is reported separately as `download_truncated=true`, and the result carries the `content_type`.
- Client-side rendered pages (SPA/React) may yield little or no text. This is accepted current specification.

**Operational notes:**

- Health and metrics recording is centralized in `web_search_service.py`; the server's `call_tool()` only classifies `outcome`/`error_type` for the audit log, to avoid double counting.
- `browser_fetch` health/metrics use separate singletons from `search_web` and are reported separately in `/health` `details`. `/health` reports the current state of each provider (degraded after repeated failures, healthy again after a success); the `last_error_type` and last failure time in `details` are historical metadata and do not mean the provider is failing now.
- `browser_fetch` records one metrics `error_type` per outcome: `authorization_error`, `validation_error`, `http_redirect`, `http_client_error`, `http_rate_limited`, `http_server_error`, `http_other`, `unsupported_content`, `network_error`, or `fetch_error` (an httpx timeout or connection error). The audit record carries the same type. Only `http_rate_limited`, `http_server_error`, `http_other`, `network_error`, and `fetch_error` count as browser health failures; a redirect, a 4xx answer, unsupported content, and authorization and validation errors describe the target or the request and leave the health state unchanged.
- `/v1/call_tool` rejects a disabled tool with `Tool disabled: <reason>` (`is_error=True`) before dispatch. The rejection is audited once (`outcome` `"rejected"`, `error_type` `"tool_disabled"`) and changes no health count.
- Audit records carry a query hash (`search_web`) or a redacted URL (`browser_fetch`), never raw queries or URLs; see [mcp_02_03_audit-logging-and-errors.md](mcp_02_03_audit-logging-and-errors.md).
- Both tool `inputSchema` values are generated from the request models, so unknown arguments are rejected, `url` must be non-empty, and `max_response_kb` is bounded by the server ceiling (4096 KB) and clamped to the configured maximum. Example: `curl -H "Authorization: Bearer $MCP_WEB_SEARCH_AUTH_TOKEN" http://localhost:8004/v1/tools`.

---

## file-read-mcp

**Purpose:** Read-only access to the local filesystem within `allowed_dirs`.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/file_read_mcp_server.toml` (`allowed_dirs`, size and result limits)

- No tool requires configuration (`config_dependent: false`), but availability depends on `allowed_dirs`: empty means disabled with reason `"allowed_dirs is empty"`.
- `max_read_bytes` is a byte count applied unchanged; `max_file_size_kb` belongs to github-mcp only.
- Symlink entries are excluded from traversal results (`directory_tree`, `search_files`, `grep_files`): symlinks are skipped before any filesystem inspection, so entries outside `allowed_dirs` cannot be reached through a symlink and broken links never raise. There is no opt-in to follow symlinks. Proven by `tests/mcp_servers/file/test_read_service.py::test_resolve_safe_rejects_symlink_outside_allowed`.
- Traversal limits report a structured truncation reason in the response's `truncation_reason` field: `max_tree_nodes` (2000) reports `node_limit`, `max_scanned_files` (5000) reports `scanned_file_limit`, `max_total_scan_bytes` (10485760) reports `byte_limit`, and `traversal_deadline_sec` (10.0) reports `deadline`. Proven by `tests/mcp_servers/file/test_read_service.py::test_search_scanned_file_limit` and `test_search_byte_limit`; path traversal outside `allowed_dirs` is refused by `test_resolve_safe_rejects_traversal_etc_shadow`.
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

**Input contract:** every tool's `inputSchema` is generated from its request model, so the schema a client discovers on `/v1/tools` and the validation `/v1/call_tool` performs are one source rather than two descriptions that can drift. Request models are strict: unknown fields are rejected instead of ignored, declared bounds and patterns are published in the schema, write tools expose `dry_run`, and `github_push_files` declares its file entries as a nested definition. A call whose arguments fail validation returns an error result naming the request model and the offending fields; arguments are never silently dropped.

- Newly rejected argument shapes: unknown fields, empty text where an identifier or query is required, numbers outside the published range, oversized file content, empty or oversized file lists, and a `github_update_pull_request` call that changes nothing.
- Newly accepted arguments: `dry_run` on the write tools, and `per_page` on the repository listing and code-search tools, which the models accept but the previous published schemas did not advertise.

**Authentication:** `GITHUB_TOKEN` environment variable (PAT). If unset, every tool is reported disabled (`GITHUB_TOKEN is not set`) and `/v1/call_tool` rejects every call with `Tool disabled: GITHUB_TOKEN is not set`; there is no usable anonymous mode through the MCP tools. The process still starts with an unauthenticated client (startup warning about the API rate limit) and reports `degraded` health, but the disabled-tool gate prevents any tool from using that client. All tools are `config_dependent: true`.

**Security controls (`config/github_mcp_server.toml`):**

- `allowed_repos`: fail-closed; an empty list denies every repository. Every operation naming a repository — reads included — is checked inside `_get_repo()` (`github_service_security.py`) before the first API call, and `Owner/Repo` and `owner/repo` are the same canonical lowercase key for the guard, the API slug, the error text, and the audit record. Proven by `tests/mcp_servers/github/test_github_security_compliance.py::test_read_outside_allowlist_is_refused_and_calls_no_api`.
- `allow_global_search` (`false` by default): each search is scoped to `allowed_repos` at query-construction time, and a caller `repo:`/`org:`/`user:` qualifier naming something outside the boundary is rejected before the call. `true` opts in to global search and the posture reports it. Proven by `tests/mcp_servers/github/test_github_security_compliance.py::test_search_query_is_scoped_to_the_allowlisted_repository` and `test_search_qualifier_outside_the_allowlist_is_refused`.
- `max_file_read_size_kb` (`0` = unlimited): the content metadata size is checked before decoding, and content that does not decode as strict UTF-8 is rejected with `GitHubValidationError`; no U+FFFD substitution occurs. Proven by `tests/mcp_servers/github/test_github_security_compliance.py::test_oversized_read_is_refused_before_decoding` and `test_non_utf8_content_is_refused`.
- `protected_branches` and `path_denylist` (fnmatch patterns) reject matching branches and paths. `path_denylist` applies to reads as well as writes. Proven by `tests/mcp_servers/github/test_github_security_compliance.py::test_denied_path_is_refused_before_the_api_call`.
- `max_file_size_kb` (0 = unlimited) rejects larger content.
- `allow_force_push` is disabled unless `true`; it only gates `merge_pull_request` by rejecting `merge_method="rebase"` and does not block other force-push equivalents.
- `require_pr_review` is on unless `false`; `merge_pull_request` then requires at least one `APPROVED` review.
- `max_per_page` clamps requested `per_page` below the bound the request models declare. The models validate `per_page` against their own published range, so a value above that range is rejected as an argument error rather than silently clamped; the config value only lowers the effective cap further, and the model default decides the listing size when `per_page` is omitted.
- `connect_timeout_sec` (`5`) and `read_timeout_sec` (`30`) must be strictly positive; a timeout can never disable itself. A timeout never proves that a write did not apply, so a timed-out write is reported as `outcome_unknown` and is never retried.

**Guard coverage (layered protection):**

- **Agent approval:** not applicable server-side; github enforces only its own technical constraints.
- **Common guard:** `call_tool` rejects a disabled tool first; every operation naming a repository — reads included — resolves through `_get_repo()`, which asserts the canonical key against `allowed_repos` (`_assert_allowed_repo`, `github_service_security.py`) and raises `GitHubAuthorizationError` outside the allowlist before the first API call.
- **Command-specific guard:** per-operation asserts run before the call they guard: the path denylist and read-size check with strict UTF-8 decoding on the read path (`_assert_allowed_path`, `_assert_max_read_file_size`), and the path, branch, write file size, and `per_page` clamping asserts on the write path (`github_service_security.py`). Search tools scope their query at construction time (`_resolve_search_query`).
- **Postcondition verification:** not applicable in the current plan, because the GitHub API response carries the resulting state and no local before/after comparison is performed. `push_files` returns the new commit SHA without inspecting the ref update result, so it does not confirm that the ref moved; confirming ref movement without an extra API call is a follow-up (Plan UNK-02).
- **Audit:** `call_tool` writes one `mcp_tool_exec` record (to `github-mcp.log`) per dispatched call (`server_key="github"`, `target` = `repo={owner}/{repo}` with the canonical lowercase key); a disabled-tool rejection returns before the audit call and writes no record. The service also writes the dedicated `github_audit.log` in two phases for every write: an intent record before the API call and a completion record after the applied write. Each record carries the session id, request id, and logical call id (the idempotency key) alongside the existing identifiers, and never payload text. A failed audit write is no longer one outcome but three: a pre-write (intent) failure raises `GitHubAuditError` (HTTP 500) before anything is applied, a completion failure after the write landed is reported as `applied_audit_failed` (the write is named as applied and must not be retried), and an ambiguous transport failure during a write is `outcome_unknown` (HTTP 504). Before/after state snapshots are not applicable.

**Write retry policy:** every GitHub write declares `retry_policy = never`, so the dedup layer never re-dispatches a logical call and the Agent transport never retries a write. The PyGithub client is built with `retry=None`, so the library re-sends nothing either: a write is sent at most once per call. Reads rely on the transport's safe read retry.

**Error mapping:** PyGithub `GithubException` is converted to domain exceptions by status (404 NotFound, 403 Authorization, 409 Conflict, 400/422 Validation, others Upstream 502); `GitHubAuditError` is 500 with `outcome: audit_failed` in the body, and `GitHubOutcomeUnknownError` is 504 with `outcome: outcome_unknown`. Mapping is registered in `exception_handlers.py`. Local argument rejection is a separate outcome from that upstream mapping: `/v1/call_tool` answers it with an error result (`is_error: true`, HTTP 200) whose text names the request model and the offending fields without echoing the values, and the domain routers answer the same domain error type with HTTP 400.

**Health:** `dependencies.github_token="not_set"` when the token is missing (`degraded`, HTTP 503); otherwise `ok`. The details report `audit_failure_count`, the number of audit-write failures since startup.
**Logs:** `<log_dir>/github-mcp.log`
**Audit layers:** Layer1 (Agent/MCP shared): `tool_exec` / Layer2 (per-server application log): `mcp_tool_exec` / Layer3 (Dedicated): `github_audit.log`

---

## Keywords

- mcp
- server-catalog
- web-search-mcp
- file-read-mcp
- github-mcp
