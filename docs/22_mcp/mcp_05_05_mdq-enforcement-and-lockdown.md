---
title: "MCP Security and Safety Model: MDQ/RAG Boundary Enforcement and mdq-mcp Path Authorization"
area: mcp
tags:
  - mcp
  - security
  - mdq-boundary
related:
  - mcp_05_04_mdq-rag-boundary.md
  - mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
---
# MCP Security and Safety Model: MDQ/RAG Boundary Enforcement and mdq-mcp Path Authorization

## Boundary Enforcement

Automated pytest checks (`tests/mcp_servers/mdq/test_mdq_rag_boundary.py`) verify the MDQ/RAG boundary during every CI run. They scan source files for prohibited cross-DB references and unauthorized direct SQLite access within the agent layer.

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

If a new administrative maintenance file requires direct access to `rag.sqlite`, add that filename to the `ALLOWED` set in `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` and document the exception in the Allowed Access Paths table above. Changes to `ALLOWED` require a design review comment in a PR.

---

### mdq-mcp `allowed_dirs` Authorization (fail-closed)

Separately from the DB boundaries with other servers, mdq-mcp has a fail-closed allowlist based on file paths. The `allowed_dirs` in `config/mdq_mcp_server.toml` (default `[]`) restricts target directories for reading, and `authorize_path()` (`scripts/mcp_servers/mdq/auth.py`) performs the actual authorization.

- If `allowed_dirs` is empty, `authorize_path()` always returns `False` — implementing fail-closed behavior where all path access is denied.
- Before evaluation, both the target path and the allowed root are normalized using `Path.resolve()` to prevent directory traversal via `../` or escaping the allowlist via symbolic links.
- Authorization checks are applied to the following tools: `MdqService.outline()` (`outline` tool), path validation functions (used by `index_paths`/`refresh_index` tools), and `search_docs`, `get_chunk`, and `grep_docs` (these three re-check authorization upon reading, see below). Violations raise `MdqAuthorizationError`, which is converted to HTTP 403 by the error handler in `scripts/mcp_servers/mdq/mdq_server.py`.
- For `search_docs`, `get_chunk`, and `grep_docs`, the `source_path` of indexed chunks is re-checked against current `allowed_dirs` using `authorize_path()` before returning results. `search_docs` and `grep_docs` (when `paths` is not specified) silently exclude unauthorized lines and do not count them in totals (fail-closed, ensuring existence of unauthorized results is not leaked). `get_chunk` and `grep_docs` (when `paths` is explicitly specified) reject the entire call with `MdqAuthorizationError` if unauthorized targets are included.
- Since `stats` only returns counts and does not include path-level content, it continues to bypass `authorize_path()`.

#### HTTP Bearer Authentication Precedes `allowed_dirs` Authorization

mdq-mcp verifies the Bearer token on every endpoint (`/health`, `/v1/tools`, `/v1/call_tool`) through the common `attach_auth_middleware()`. The token is read from `auth_token` in `config/mdq_mcp_server.toml` (the `MCP_MDQ_AUTH_TOKEN` environment variable, the same value as the Agent's `[mcp_servers.mdq].auth_token`); an empty or unset value makes the server refuse to start. The Agent and mdq-mcp each read their own configuration file and never read the other's (ADR-002).

Request order: loopback-only network boundary, then Bearer authentication, then `allowed_dirs` path authorization, then input and resource-limit validation, then the MDQ operation.

- A missing, malformed, or non-matching `Authorization` header is rejected with HTTP 401 before any path decision is made, so an unauthenticated caller learns nothing about path existence, authorization state, or MDQ data.
- After authentication, a path outside `allowed_dirs` (or an empty `allowed_dirs`) is denied fail-closed as `MdqAuthorizationError`. On `/v1/call_tool` this is a tool-level error result (HTTP 200 with `is_error`, per the MCP tool-error contract).
- Authentication does not replace path authorization, and path authorization does not replace authentication. An authentication or authorization failure is a Safety/Integrity failure; it never triggers a fallback, an unauthenticated retry, or partial operation (ADR-004, ADR-007).
- The token is never written to logs, error responses, or health responses.


---

### Implementation Notes

- **Serialization:** `index_paths` and `refresh_index` acquire `MdqService._index_lock` (an `asyncio.Lock`) before execution to prevent concurrent index operations, independent of any config value. This is separate from `requires_serial: True` (a global barrier for simultaneous tool calls within an agent turn); the two mechanisms are complementary. Verified by `tests/mcp_servers/mdq/test_mdq_index_serialization.py`.
- **Config gate:** `enable_grep` is enforced in `grep_docs()` (raises `MdqValidationError` when false); there is no equivalent gate for `refresh_index()`.
- Search mode (`bm25` only), the tool surface, and chunk metadata are specified in [mcp_04_04_mdq.md](mcp_04_04_mdq.md).

## Keywords

- mcp
- security
- safety-model
- mdq-rag-boundary-enforcement
- fail-closed
- security-audit
- mdq-allowed-dirs
- authorize-path
- mdq-authorization-error
