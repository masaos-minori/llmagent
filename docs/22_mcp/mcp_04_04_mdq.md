---
title: "MCP Server Catalog: mdq-mcp"
area: mcp
tags:
  - mcp
  - server-catalog
  - mdq
related:
  - mcp_00_document-guide.md
  - mcp_04_01_web-search-file-read-github.md
  - mcp_04_02_file-write-file-delete-shell.md
  - mcp_04_03_rag-pipeline-and-cicd.md
  - mcp_04_05_git.md
  - security_02_high-risk-tool-common-policy.md
  - mcp_06_04_verification-methods.md
---

# MCP Server Catalog: mdq-mcp

Tool membership and risk tiers: [mcp_01_tool_ownership_matrix.md](mcp_01_tool_ownership_matrix.md). Health response semantics common to all servers: [mcp_02_02](mcp_02_02_startup-modes-and-health.md). Cross-cutting policy: [security_02_high-risk-tool-common-policy.md](../91_security/security_02_high-risk-tool-common-policy.md) (Layered protection model). Agent-side approval confirms user intent only; it is not a bypass for any check below.

## mdq-mcp

**Purpose:** Indexing Markdown documentation and context compression. For production RAG search, use `rag-pipeline-mcp`. All tools are production.
**Startup Mode:** `subprocess` (HTTP)
**Configuration:** `config/mdq_mcp_server.toml` (`allowed_dirs`, `db_path`, glob filters, size and result limits, `search_timeout_sec`, grep and outline limits)
**Scope:** FTS5 (BM25) structural Markdown search only. mdq-mcp has no hybrid or semantic search and no embedding-related configuration; the `mode` parameter of `search_docs` accepts `bm25` only.

**Authentication:** every endpoint requires the Bearer token (`auth_token` in `config/mdq_mcp_server.toml`, the `MCP_MDQ_AUTH_TOKEN` variable); the server refuses to start with an empty value. `allowed_dirs` path authorization applies after authentication (see `mcp_05_05_mdq-enforcement-and-lockdown.md`).

**Enforced limits:**

- `include_globs` / `exclude_globs` apply to all four indexing scans.
- `max_file_chars`: a larger file is skipped with a warning and is not indexed.
- `max_chunk_chars`: content is truncated before `content_hash` is calculated, so the hash matches the stored content.
- `max_snippet_chars` truncates search snippets.
- `search_timeout_sec`: a timed-out `search_docs` call stops its worker through the progress-handler stop event and waits for it inside the bounded drain interval (`DRAIN_INTERVAL_SEC`, module constant); the call is reported with the code `timeout` and the worker's connection is closed by the worker before the caller returns. A worker that does not stop inside the drain interval is left to release its own connection, and the connection an interrupted search holds is never reused by another search. See `mcp_05_05_mdq-enforcement-and-lockdown.md` for the enforcement boundary.

**Stored data:** `chunks.tags_json` holds the YAML frontmatter `tags:` values (list or comma-separated) and is the data `search_docs` `tag_filter` matches against. `token_count` is an approximation (`max(1, len(content) // 4)`, so an empty or very short section still reports at least 1), not an accurate tokenizer.

**Operations:**

- `/health` returns more fields than the basic response (refer to [mcp_06 Health probes](mcp_06_04_verification-methods.md#health-probes)).
- Logs: `<log_dir>/mdq-mcp.log`. Audit: Layer1 `tool_exec`, Layer2 `mcp_tool_exec` (JSON-lines records in `<log_dir>/mdq-mcp.log` via `_audit_log()`, `server_key="mdq"`), Layer3 none. There is no dedicated audit log and no `audit_log_path` key.

### Path Control

All tools receiving paths enforce fail-closed authorization via `allowed_dirs`. Configure `allowed_dirs` in `config/mdq_mcp_server.toml` before using indexing tools.

| Tool | Path Input | Authorization |
|---|---|---|
| `index_paths` | Directory/File to index | `authorize_path()` raises `MdqAuthorizationError` if outside `allowed_dirs` |
| `refresh_index` | Path to refresh | Path authorization; raises `MdqAuthorizationError` if any path is denied |
| `outline` | File to outline | `authorize_path()` raises `MdqAuthorizationError` if outside `allowed_dirs` |
| `search_docs` | `source_path` of indexed chunks (authorized in SQL before `COUNT`, ranking, and `LIMIT`) | Chunks outside the canonicalized `allowed_dirs` roots are excluded by the query predicate — they are not counted and cannot fill a result slot; `matched_count` is the authorized count. Empty `allowed_dirs` matches no row (fail-closed) |
| `get_chunk` | `source_path` of chunk to retrieve (re-checked upon reading) | Raises `MdqAuthorizationError` if outside `allowed_dirs` |
| `grep_docs` | Explicitly specified path, or the authorized set of all indexed `source_path`s (re-checked upon reading) | An unauthorized explicit path rejects the entire call with `MdqAuthorizationError`; with no filter, unauthorized paths are silently excluded |

- `..` traversal and symbolic-link escapes are blocked by `Path.resolve()` within `authorize_path()` (`scripts/mcp_servers/mdq/auth.py`).
- Empty `allowed_dirs = []` (default) denies all path access (fail-closed). `canonicalized_roots()` gives the SQL query boundary the same canonical form `authorize_path()` resolves to, so the predicate and the authorization never disagree.

### Query boundary contract

`search_docs` applies the authorized-source predicate in SQL before `COUNT`, ranking, and `LIMIT`, so an unauthorized row can neither change a visible count nor fill a result slot. Filter semantics are exact, not pattern-based:

- `path_prefix` compares the literal prefix with a path-separator boundary (`%` and `_` in the prefix are data, not wildcards), and the filter is authorized before the query is built.
- `tag_filter` matches whole JSON array values, so a similar tag does not match.
- `matched_count` is the authorized count reported by the predicate before any `LIMIT`; the response reports matched and shown counts separately when limiting hides rows.
- Each search owns one connection through `db.helper.SQLiteHelper`, cancelled through the progress-handler stop event within the bounded drain; active searches are capped at `MAX_ACTIVE_SEARCHES`, the existing per-server concurrency convention (`DEFAULT_PER_SERVER_CONCURRENCY`).
- The raw query text never reaches the response, the metadata, or the persistent log line: the hashed identifier from `hash_query_value()` is used instead.

### Availability and execution contract

One availability function answers both discovery and dispatch, and it is evaluated per tool name at call time inside the dispatch boundary before the handler runs, so `GET /v1/tools` and `POST /v1/call_tool` never report different states for the same call. `config_dependent` is `true` for every mdq tool entry (see `mcp_03_06_tool-runtime-availability-metadata.md`).

- A tool is disabled when no authorized root is configured, because every tool serves content under `allowed_dirs`.
- `grep_docs` is additionally disabled when `enable_grep` is `false`.
- A disabled tool is refused before the handler runs with the code `tool_disabled`, and the refusal is recorded as `outcome="rejected"`.

### Health surface

The health body carries only non-sensitive state: the service name, the size of the authorized-root list, the deny-all flag, and the read-only dedup metrics. Dependency values are reason codes from the closed health-reason vocabulary, so no absolute database path, no database-wide count, no database-wide timestamp, and no configuration path appears in the response. Readiness is reported through the `mdq.corpus` capability block, the capability name the tool catalog declares for mdq: the state is `unavailable` with the availability reason code when a dependency fails and `ok` otherwise. A missing production configuration is a pre-bind failure, so no configuration dependency remains for a health request to report.

### Stats surface

`stats` reports counts scoped to the currently authorized roots. With no authorized root configured the call is refused rather than returning database-wide zero counts, so "no access" and "nothing indexed" stay distinguishable. The raw `index_state` metadata dictionary is not part of the response.

### Administrator diagnostics

Administrator diagnostics stay on the existing runtime-availability diagnostics surface — the declared `config_dependent`, `enabled`, and `disabled_reason` metadata plus the Security Posture checks — rather than a new surface. mdq publishes the posture built at startup; its checks cover the configured allowlist, allowlist entries that exist, the database path, schema and FTS health, and index availability.

### Error codes

The error vocabulary is one closed set of lowercase-snake codes, recorded in `mcp_02_03_audit-logging-and-errors.md`: `validation_error`, `authorization_error`, `tool_disabled`, `not_found`, `database_unavailable`, `consistency_error`, `timeout`, and `unexpected_error`. `timeout` is reserved for the search path and is resolved from the cause of the exception it raises (a `TimeoutError` cause maps to `timeout` in `scripts/mcp_servers/mdq/mdq_error_codes.py`); `tool_disabled` has no exception class and is produced by the dispatch boundary. `unexpected_error` covers a failure with no mdq exception class. A code never carries exception text, SQLite detail, or a path, and `error_type` in an audit record is one of these codes rather than an exception class name.

Search-path classification is by cause, not by swallowing: a rejected FTS5 query syntax resolves to `validation_error`, an index-consistency failure (missing table, corruption) resolves to `consistency_error` and is not retryable, a busy or locked database resolves to `consistency_error` and is retryable, and an interrupted statement resolves to `timeout`. A malformed FTS5 query is no longer reported as a successful zero-result response.

Tool-domain failures return HTTP 200 with `is_error=true` and the code, per `mcp_02_01_endpoints-and-transport.md`, so they count as transport successes in the health registry and are not retried; retry classification applies only to transport failures (see `mcp_03_03_transport-and-health.md`). The exception handlers render the transport response only.

### Guard and postcondition coverage

- **Agent approval:** not applicable server-side; mdq enforces only its own technical constraints (Bearer token, `allowed_dirs`).
- **Common guard:** the Path Control table is the common guard and the traversal- and symlink-containment reference implementation the cross-cutting policy measures the other high-risk servers against.
- **Command-specific guard:** per-tool `authorize_path()` on every path-bearing tool. Read tools re-check the stored `source_path` of each chunk at read time, so a chunk that left `allowed_dirs` is excluded or rejected at read time rather than at index time. The stale-document check (`is_stale()`, `mtime_ns > int(indexed_at * 1e9)` in `scripts/mcp_servers/mdq/mdq_models.py`) is a reporting guard only: `outline` returns a `stale_warning`, and the stale count is input to the Security Posture index check rather than a field of the health body; neither rejects the call. `stats()` reports a stale count scoped to the authorized roots. Proven by `tests/mcp_servers/mdq/test_mdq_stale_detection.py` (`test_stale_one_nanosecond_past_boundary`, `test_sql_condition_agrees_with_python_predicate`).
- **Postcondition verification:** not applicable per operation, and no resulting-state verification exists. Two reporting mechanisms exist: `refresh_paths()` records per-path failures, continues the batch, and returns indexed, skipped, deleted, and failed counts; the Security Posture check `server.index_available` warns when documents exist while the FTS index holds no rows. Neither compares a resulting state with an expected state or gates the refresh.
- **Audit:** Exactly one `mcp_tool_exec` record per authenticated call, emitted from the single audit boundary in `call_tool()` rather than from an exception handler. `target` is the redacted target from `extract_audit_target()`: a query or pattern hash, a root-relative path identifier, or a hash when the path is outside the authorized roots; no raw query text, regex, chunk identifier, or absolute path is stored. `outcome` is `ok`, `error`, or `rejected` (a call refused before the tool's work is `rejected`, a failure during it is `error`), `error_type` is a code from the closed vocabulary above, and `server_key` is `mdq`. No dedicated audit log; before/after state snapshots are not applicable.

### Markdown Compatibility Scope

| Markdown Feature | Support | Fallback Behavior |
|---|---|---|
| ATX Headings (H1–H6) | Yes | — |
| Fenced Code Blocks | Yes | `#` inside fences are not treated as headings. Fence content itself is also excluded from section indexing text and is not searched in `search_docs`/`grep_docs` (because `parser.py` uses `continue` to skip fence lines before adding them to the section body) |
| YAML Frontmatter | Yes | Parsed and removed from the beginning of the file |
| Content before H1 | Yes | Stored in the `<root>` section |
| Duplicate Headings | Yes | Individual chunk IDs are assigned via ordinality |
| Setext Headings (===,---) | No | Treated as plain text |
| HTML Blocks | No | Treated as plain text |
| MDX | No | Excluded from indexing (.mdx files are excluded via glob) |
| GFM Tables | No | Stored as plain text within the parent section |
| Inline HTML Tags | No | Treated as plain text |

> Frontmatter `tags` real-data storage and `search_docs` `tag_filter` support are described under "Stored data" above; this table covers heading/structural features only.

### Search Result Limits

- **Effective SQL limit:** `effective_limit = min(request limit, server max_results_limit)` is applied directly to the SQL `LIMIT` clause, so a large requested `limit` never fetches more rows than the server setting.
- **Count display:** the response header shows a definitive count ("N found") only when no filtering occurs (match count equals shown count). When filtering occurs it distinguishes "matched" from "shown" and does not claim the limited count is the total.

### Audit `detail` Metadata

The audit `detail` field is built from structured metadata (a `(text, metadata)` tuple) returned by each `MdqService` method, not by parsing output text, so audit values stay consistent when output wording changes. It carries result, shown, indexed, skipped, deleted, and failed counts and a `truncated=true` flag where applicable; for `get_chunk`, `truncated=true` is derived from the `"[Truncated"` marker in the output text. For the indexing tools it also carries the request's own path count and the authorized root as a hash, because the metadata carries counts only and the root path itself must not reach the record.

`detail` carries no exception-class names and `error_type` carries a code from the closed error-code vocabulary above, not an exception class name. The record is emitted from the single audit boundary in `call_tool()`, not from an exception handler.

---

## Layered protection coverage

mdq-mcp is a high-risk category (path-authorized document access) and serves as the
traversal- and symlink-containment reference implementation for the common guard. The five
Layered protection layers stand as follows.

- **Agent approval** — Not applicable server-side. Approval is an Agent-side gate; mdq enforces only its own technical constraints (Bearer token, `allowed_dirs`).
- **Common guard** — Implemented. `allowed_dirs` fail-closed authorization with `..`-traversal and symbolic-link escape blocked by `Path.resolve()` inside `authorize_path()`; an empty `allowed_dirs` denies every path (see Path Control). (Explicit in code — `scripts/mcp_servers/mdq/auth.py`, `scripts/mcp_servers/mdq/mdq_security_validation.py`)
- **Command-specific guard** — Implemented. Per-tool `authorize_path()` on every path-bearing tool, plus a stale-index check on the read path. (Explicit in code — `scripts/mcp_servers/mdq/auth.py`, `scripts/mcp_servers/mdq/mdq_service.py`)
- **Postcondition verification** — Not applicable. `refresh_index()` reports operation counts (indexed/skipped/deleted/failed) but performs no before/after comparison of the resulting index state against an expected state; the `_index_check` posture entry surfaces a "documents exist while the FTS index holds no rows" warning rather than gating the refresh. No resulting-state verification exists to implement. (Code review — `scripts/mcp_servers/mdq/mdq_service.py::refresh_index`, `scripts/mcp_servers/mdq/mdq_security_validation.py::_index_check`)
- **Audit** — Implemented. Every call is recorded through the shared `_audit_log()` with `server_key="mdq"`; the target is resolved via `extract_audit_target()`. (Explicit in code — `scripts/mcp_servers/mdq/audit_target.py`, `scripts/mcp_servers/audit.py`)

## Keywords

- mcp
- server-catalog
- mdq-mcp
