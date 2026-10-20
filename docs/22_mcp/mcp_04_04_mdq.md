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
- `search_timeout_sec`: `search_docs()` raises `MdqConsistencyError` on timeout; the background thread is not forcibly interrupted.

**Stored data:** `chunks.tags_json` holds the YAML frontmatter `tags:` values (list or comma-separated) and is the data `search_docs` `tag_filter` matches against. `token_count` is an approximation (`len(content) // 4`), not an accurate tokenizer.

**Operations:**

- `/health` returns more fields than the basic response (refer to [mcp_06 Health probes](mcp_06_04_verification-methods.md#health-probes)).
- Logs: `<log_dir>/mdq-mcp.log`. Audit: Layer1 `tool_exec`, Layer2 `mcp_tool_exec` (shared JSON-lines audit log `<log_dir>/audit.log` via `_audit_log()`, `server_key="mdq"`), Layer3 none. There is no dedicated audit log and no `audit_log_path` key.

### Path Control

All tools receiving paths enforce fail-closed authorization via `allowed_dirs`. Configure `allowed_dirs` in `config/mdq_mcp_server.toml` before using indexing tools.

| Tool | Path Input | Authorization |
|---|---|---|
| `index_paths` | Directory/File to index | `authorize_path()` raises `MdqAuthorizationError` if outside `allowed_dirs` |
| `refresh_index` | Path to refresh | Path authorization; raises `MdqAuthorizationError` if any path is denied |
| `outline` | File to outline | `authorize_path()` raises `MdqAuthorizationError` if outside `allowed_dirs` |
| `search_docs` | `source_path` of indexed chunks (re-checked upon reading) | Chunks outside `allowed_dirs` are silently excluded from results (not counted) |
| `get_chunk` | `source_path` of chunk to retrieve (re-checked upon reading) | Raises `MdqAuthorizationError` if outside `allowed_dirs` |
| `grep_docs` | Explicitly specified path, or the authorized set of all indexed `source_path`s (re-checked upon reading) | An unauthorized explicit path rejects the entire call with `MdqAuthorizationError`; with no filter, unauthorized paths are silently excluded |

- `..` traversal and symbolic-link escapes are blocked by `Path.resolve()` within `authorize_path()` (`scripts/mcp_servers/mdq/auth.py`).
- Empty `allowed_dirs = []` (default) denies all path access (fail-closed).

### Guard and postcondition coverage

- **Agent approval:** not applicable server-side; mdq enforces only its own technical constraints (Bearer token, `allowed_dirs`).
- **Common guard:** the Path Control table is the common guard and the traversal- and symlink-containment reference implementation the cross-cutting policy measures the other high-risk servers against.
- **Command-specific guard:** per-tool `authorize_path()` on every path-bearing tool. Read tools re-check the stored `source_path` of each chunk at read time, so a chunk that left `allowed_dirs` is excluded or rejected at read time rather than at index time. The stale-document check (`is_stale()`, `mtime_ns > indexed_at`) is a reporting guard only: `outline` returns a `stale_warning` and `/health` reports `stale_document_count`; neither rejects the call.
- **Postcondition verification:** not applicable per operation, and no resulting-state verification exists. Two reporting mechanisms exist: `refresh_paths()` records per-path failures, continues the batch, and returns indexed, skipped, deleted, and failed counts; the Security Posture check `server.index_available` warns when documents exist while the FTS index holds no rows. Neither compares a resulting state with an expected state or gates the refresh.
- **Audit:** `call_tool` writes one shared `mcp_tool_exec` record per call (a tool-level exception records `outcome="error"` with `error_type`; a dispatched call records the dispatch outcome), with `target` from `extract_audit_target()` truncated to 80 characters and `server_key="mdq"`. No dedicated audit log; before/after state snapshots are not applicable.

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

The audit `detail` field is built from structured metadata (a `(text, metadata)` tuple) returned by each `MdqService` method, not by parsing output text, so audit values stay consistent when output wording changes. It carries result, shown, indexed, skipped, deleted, and failed counts and a `truncated=true` flag where applicable; for `get_chunk`, `truncated=true` is derived from the `"[Truncated"` marker in the output text.

Tool-level exceptions (`MdqValidationError` / `MdqAuthorizationError` / `MdqNotFoundError` / `MdqIndexNotReadyError`) and FastAPI exception handlers (`MdqDatabaseError` / `MdqConsistencyError` / `MdqServiceError`) are not embedded in `detail`; the error type is passed as `error_type=` to `_audit_log()`.

---

## Keywords

- mcp
- server-catalog
- mdq-mcp
