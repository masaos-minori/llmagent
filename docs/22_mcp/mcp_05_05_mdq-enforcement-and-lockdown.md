---
title: "MCP Security and Safety Model: MDQ/RAG Boundary Enforcement, Fail-Open/Fail-Closed Defaults and Deny-All Lockdown"
area: mcp
tags:
  - mcp
  - security
  - mdq-boundary
related:
  - mcp_05_04_mdq-rag-boundary.md
  - mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
---
# MCP Security and Safety Model: MDQ/RAG Boundary Enforcement, Fail-Open/Fail-Closed Defaults and Deny-All Lockdown

## Boundary Enforcement

Automated pytest checks (`tests/test_mdq_rag_boundary.py`) verify the MDQ/RAG boundary during every CI run. They scan source files for prohibited cross-DB references and unauthorized direct SQLite access within the agent layer.

### Allowed Access Paths

| Layer | DB | Mechanism | Context |
|---|---|---|---|
| `scripts/mcp_servers/mdq/` | `mdq.sqlite` | Its own service | Normal operation |
| `scripts/mcp_servers/rag_pipeline/` | `rag.sqlite` | Its own service | Normal operation |
| Agent Layer | `session.sqlite` | `SQLiteHelper("session")` | Normal operation |
| Agent Layer | `workflow.sqlite` | `SQLiteHelper("workflow")` | Normal operation |
| Agent Layer | `rag.sqlite` | via `RagMaintenanceService` using `SQLiteHelper("rag")` | `/session rag-consistency`, `/session rag-rebuild-fts`, `/session rag-rebuild-vec` commands |

#### Prohibited Access Paths

| Layer | DB | Reason |
|---|---|---|
| `scripts/mcp_servers/mdq/` | `rag.sqlite` | Cross-DB dependency |
| `scripts/mcp_servers/rag_pipeline/` | `mdq.sqlite` | Cross-DB dependency |
| Agent Layer (Normal) | `mdq.sqlite` or `rag.sqlite` | Must use MCP tools instead of direct DB access |

#### Handling False Positives

If a new administrative maintenance file requires direct access to `rag.sqlite`, add that filename to the `ALLOWED` set in `tests/test_mdq_rag_boundary.py` and document the exception in the Allowed Access Paths table above. Changes to `ALLOWED` require a design review comment in a PR.

---

### mdq-mcp `allowed_dirs` Authorization (fail-closed)

Separately from the DB boundaries with other servers, mdq-mcp has a fail-closed allowlist based on file paths. The `allowed_dirs` in `config/mdq_mcp_server.toml` (default `[]`) restricts target directories for reading, and `authorize_path()` in `scripts/mcp_servers/mdq/auth.py` performs the actual authorization (Explicit in code).

- If `allowed_dirs` is empty, `authorize_path()` always returns `False` — implementing fail-closed behavior where all path access is denied (Explicit in code).
- Before evaluation, both the target path and the allowed root are normalized using `Path.resolve()` to prevent directory traversal via `../` or escaping the allowlist via symbolic links (Explicit in code).
- Authorization checks are applied to five tools: `MdqService.outline()` (`outline` tool), path validation functions (used by `index_paths`/`refresh_index` tools), and `search_docs`, `get_chunk`, and `grep_docs` (**additional re-check upon reading added on 2026-07-20**, see below). Violations raise `MdqAuthorizationError`, which is converted to HTTP 403 by the error handler in `scripts/mcp_servers/mdq/mdq_server.py` (Explicit in code).
- For `search_docs`, `get_chunk`, and `grep_docs`, the `source_path` of indexed chunks is re-checked against current `allowed_dirs` using `authorize_path()` before returning results. `search_docs` and `grep_docs` (when `paths` is not specified) silently exclude unauthorized lines and do not count them in totals (fail-closed, ensuring existence of unauthorized results is not leaked). `get_chunk` and `grep_docs` (when `paths` is explicitly specified) reject the entire call with `MdqAuthorizationError` if unauthorized targets are included (Explicit in code).
- Since `stats` only returns counts and does not include path-level content, it continues to bypass `authorize_path()` (Explicit in code).

#### HTTP Level Authentication (`auth_token`) is Intentionally Disabled

mdq-mcp starts with an empty Bearer token via `attach_auth_middleware(app, "")`, so authentication is not performed at the HTTP layer (per `scripts/mcp_servers/server.py` `attach_auth_middleware()` docstring: "When token is empty, auth is skipped..." (Explicit in code)).

This is not an oversight. The `MdqMCPServer` class docstring in `scripts/mcp_servers/mdq/mdq_server.py` explicitly states: `"auth_token: empty string (no auth required — mdq has its own authorization via allowed_dirs)"` (Explicit in code). The actual call is a module-level call in `scripts/mcp_servers/mdq/mdq_server.py`: `attach_auth_middleware(cast(_FastAPIApp, app), "")` (immediately after the `# Attach auth middleware` comment).

Instead, the path authorization based on `allowed_dirs` (default `[]`) serves as the actual security boundary. Setting `allowed_dirs = []` is fail-closed (denies all path access) (Explicit in code — see section above).

> **Important:** The empty token passed to `attach_auth_middleware()` is enforced and intended: it skips HTTP auth for mdq-mcp and is part of the **current specification**.
>
> If the MDQ HTTP authentication model changes in the future (e.g., adding actual Bearer tokens), it should be treated as an independent security design task and not as part of a compatibility cleanup.

---

### Implementation Notes

- **Search mode:** `search_docs` supports `mode=bm25` only. There is no hybrid or vector search in mdq-mcp; use the RAG pipeline when semantic search is required (Explicit in code).
- **Tools:** the tools exposed by mdq-mcp are exactly those in its `TOOL_LIST`; no FTS administration tool is exposed (Explicit in code).
- **Serialization:** `index_paths` and `refresh_index` acquire `MdqService._index_lock` (a lazily initialized `asyncio.Lock`) before execution to prevent concurrent operations, independent of any config value (Explicit in code). This is separate from `requires_serial: True` in `scripts/agent/tool_scheduler.py` (a global barrier for simultaneous tool calls within an agent turn); the two mechanisms are complementary. The serialization is verified by `tests/test_mdq_index_serialization.py`.
- **Config gates:** `enable_grep` is enforced in `grep_docs()` (raises `MdqValidationError` if `not self.enable_grep`) and tested in `tests/mcp_servers/mdq/test_mdq_service.py::TestGrepDocsConfigGate`. There is no equivalent gate for `refresh_index()` (Explicit in code).
- **Chunk metadata:** `tags_json` in the `chunks` table stores a JSON array extracted from the YAML frontmatter `tags:` field (list or comma-separated) by `scripts/mcp_servers/mdq/parser.py::parse_markdown()`. `token_count` is an approximation (`len(content) // 4`), not a tokenizer value. `search_docs`'s `tag_filter` matches against `tags_json` via the `LIKE` condition in `scripts/mcp_servers/mdq/search.py` (Explicit in code).

---

### Fail-Open vs Fail-Closed Configuration Review

| Setting | Default | Behavior when Fail-Open | Recommended for Production |
|---|---|---|---|
| `allowed_dirs` (mdq-mcp) | `[]` | `[]` = All path access denied (fail-closed); however, not subject to startup audit (Explicit in code) | Explicitly enumerate directories allowed for reading |

## Keywords

mcp
security
safety-model
mdq-rag-boundary-enforcement
deny-all
lockdown
fail-open
fail-closed
security-audit
mdq-allowed-dirs
authorize-path
mdq-authorization-error
fts-consistency-check
fts-rebuild
