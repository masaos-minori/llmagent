---
title: "MCP Security and Safety Model: MDQ/RAG Boundary Enforcement, Fail-Open/Fail-Closed Defaults and Deny-All Lockdown"
area: mcp
tags:
  - mcp
  - security
  - mdq-boundary
related:
  - 04_mcp_05_04_mdq-rag-boundary.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
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
| Agent Layer | `rag.sqlite` | via `RagMaintenanceService` using `SQLiteHelper("rag")` | Admin-only `/db` command |

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

Instead, the path authorization based on `allowed_dirs` (default `[]`) serves as the actual security boundary. Setting `allowed_dirs = []` is fail-closed (denies all path access) (Explicit in code, see section above).

> **Important:** An empty `auth_token` is the exact opposite of the configuration keys removed during the 2026-07-16 MDQ compatibility cleanup (which included `audit_log_path`, `concurrency_limit`, `enable_refresh`, embedding/hybrid related keys, and summary-cache related keys). While those were removed because they were loaded but not enforced, `auth_token=""` is loaded and its effect (skipping HTTP auth) is fully enforced and intended—it is part of the **current specification** and is not subject to removal/correction.
>
> If the MDQ HTTP authentication model changes in the future (e.g., adding actual Bearer tokens), it should be treated as an independent security design task and not as part of a compatibility cleanup.

---

### Known Issues

- **MDQ-02 (Resolved):** Hybrid search embedding integration (`mode=hybrid`) was implemented as a permanent placeholder that never worked (`_search_vector()` always returned an empty list); therefore, **on 2026-07-16, the `mode` parameter was restricted to `bm25` only, and related code (`_search_vector()`, `_merge_hybrid()`, `_RRF_K`) and config items (`use_embedding`, `embedding_dims`, `vector_table`, `embedding_model`) were completely removed** (Explicit in code; can be restored from git history prior to `db_fts.py` deletion). Use the RAG pipeline if semantic search is required.
- The `fts_consistency_check` and `fts_rebuild` tools were defined in `scripts/mcp_servers/mdq/mdq_tools.py` with `status: "admin"`, but no handler was registered in the `_DISPATCH_TABLE` of `scripts/mcp_servers/mdq/mdq_server.py`, causing "Unknown tool" errors when called. Due to lack of operational requirement for these two tools (no clients calling them, no active need for formal safety tier/serialization/audit/testing setup), **they were completely removed on 2026-07-16 from the schema (`TOOL_LIST`), model (`mdq_models.py`), service layer (`mdq_service.py`), `db_fts.py`, registry (`tool_constants.py`), and config (`config/agent.toml`)** (Explicit in code; can be restored from git history prior to `db_fts.py` deletion).
- It was confirmed that `concurrency_limit` in `mdq_mcp_server.toml` is not referenced anywhere in `scripts/mcp_servers/mdq/` or the repository (confirmed via `grep -rn '"concurrency_limit"'` with no hits), so **it was removed from the config file on 2026-07-13**. Actual serialization is achieved via `asyncio.Lock` (`_index_lock`) within `MdqService` specifically for `index_paths`/`refresh_index` and does not depend on a config value (Explicit in code).
- **Serialization Model Details:** Both `index_paths` and `refresh_index` acquire `MdqService._index_lock` (a lazily initialized `asyncio.Lock`) before execution to prevent concurrent operations (Explicit in code). This is a separate serialization mechanism from `requires_serial: True` in `scripts/agent/tool_scheduler.py` (which applies a global barrier to simultaneous tool calls within an agent turn); both are complementary and neither is targeted for removal/consolidation. This serialization is verified by `tests/test_mdq_index_serialization.py`.
- The `enable_refresh` key in `mdq_mcp_server.toml` was removed on **2026-07-16** because a gate check was never implemented in `refresh_index()` (it was loaded but always ignored). In contrast, `enable_grep` is actively enforced in `grep_docs()` (raises `MdqValidationError` if `not self.enable_grep`), and is tested in `tests/mcp_servers/mdq/test_mdq_service.py::TestGrepDocsConfigGate` — while they appear similar in config, one is actually connected to behavior and the other is not (Explicit in code).
- The `tags_json` and `token_count` fields in the `chunks` table were previously hardcoded placeholders (`""` / `None`) in `scripts/mcp_servers/mdq/indexer.py::_index_single_file()`; **on 2026-07-19, they were updated to store real data**. `tags_json` stores a JSON array extracted from the YAML frontmatter `tags:` field (supporting both list and comma-separated formats) by `scripts/mcp_servers/mdq/parser.py::parse_markdown()`. `token_count` is an approximation (via local heuristic `len(content) // 4`) rather than an accurate tokenizer value. `search_docs`'s `tag_filter` now matches against this real data via the existing `LIKE` condition in `scripts/mcp_servers/mdq/search.py` (Explicit in code).

---

### Fail-Open vs Fail-Closed Configuration Review

| Setting | Default | Behavior when Fail-Open | Recommended for Production |
|---|---|---|---|
| `allowed_dirs` (mdq-mcp) | `[]` | `[]` = All path access denied (fail-closed); however, not subject to startup audit (Explicit in code) | Explicitly enumerate directories allowed for reading |

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_05_01_access-control-and-allowlists.md`
- `04_mcp_05_02_auth-profiles-and-sandboxing.md`
- `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
- `04_mcp_05_04_mdq-rag-boundary.md`
- `04_mcp_04_04_mdq.md`
- `00_security_02_high-risk-tool-common-policy.md` — High-risk MCP tool common policy (path/repo allowlists, traversal prevention, approval-risk tier mapping)

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