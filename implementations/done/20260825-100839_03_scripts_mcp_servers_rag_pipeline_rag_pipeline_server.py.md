## Goal
- Make `rag_pipeline`'s `/v1/tools` response compute real per-tool `enabled`/
  `disabled_reason` (REQ-004) and accept `include_disabled`/`disabled_code` query
  parameters passed through to `build_tools_response()` (REQ-005), bringing this
  server in line with `git`/`file_read`/`file_write`/`file_delete`/`github`/
  `web_search`.

## Scope
- In scope: `list_tools()` and its helpers in
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`; a new module-level
  `_cfg: RagPipelineConfig` singleton; a new `_rag_pipeline_tool_availability()`
  helper; a matching disabled-tool gate in `call_tool()`.
- Out of scope: `build_tools_response()` itself (`scripts/mcp_servers/server.py`,
  unchanged signature); the pipeline's internal embed/search/rerank logic; the
  separate HTTP endpoints `/rag_run_pipeline`/`/rag_debug_pipeline`, which are
  distinct from the MCP `/v1/call_tool` path.

## Assumptions
- Loading `RagPipelineConfig.load()` a second time at module import is safe (it is
  already loaded per-request inside `_check_health_deps()`); a module-level singleton
  follows the same pattern already used by `web_search_server.py`'s `_cfg`.
- `rag_list_documents`/`rag_delete_document` operate against `rag_db_path`, not
  `embed_url` (per `RagPipelineMCPService.get_dispatch_table()`), so they are not
  gated by the embedding-service condition.

## Design decisions
- Add `_rag_pipeline_tool_availability(cfg: RagPipelineConfig, tool_name: str) -> tuple[bool, str]`, mirroring `_git_tool_availability`/`_web_search_tool_availability`.
- Gate only `rag_run_pipeline` and `rag_debug_pipeline` on `cfg.embed_url` being
  empty (reason: `"embed_url is not configured"`) — reusing the exact signal
  `_check_health_deps()` already treats as the degraded condition.
  `rag_list_documents`/`rag_delete_document` remain unconditionally enabled.
- Add the same "Tool disabled: {reason}" pre-dispatch gate to `call_tool()` already
  used by `git_server.py`/`web_search_server.py`/`github_server.py`, since
  `rag_pipeline`'s service does not currently fail closed when `embed_url` is empty.

## Alternatives considered
- Gating all 4 tools uniformly on `embed_url` — rejected; `rag_list_documents`/
  `rag_delete_document` do not call the embedding endpoint and would be disabled
  without cause.
- Skipping the `call_tool()` gate and relying on `list_tools()` metadata alone —
  rejected; unlike the other three target servers, `rag_pipeline`'s dispatch path has
  no existing fail-closed check for `embed_url`, so a caller could still invoke a
  "disabled" tool and get an unclear downstream failure.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`

### Procedure
1. Add `from mcp_servers.rag_pipeline.rag_pipeline_models import RagPipelineConfig`
   and a module-level `_cfg: RagPipelineConfig = RagPipelineConfig.load()`.
2. Add `_rag_pipeline_tool_availability(cfg, tool_name)` and an
   `_annotate_tool(tool, cfg)` helper near `_dispatch_rag_tool()`.
3. Update `list_tools()` to accept `include_disabled: bool = False, disabled_code: str | None = None`, annotate `TOOL_LIST`, and call
   `build_tools_response(annotated, "rag_pipeline", include_disabled=include_disabled, disabled_code=disabled_code)` instead of the current bare call.
4. Add the disabled-tool gate to `call_tool()`: compute
   `_rag_pipeline_tool_availability(_cfg, req.name)` first and return
   `CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)` when not
   enabled, before dispatching.

### Method
- Follow `web_search_server.py`'s exact pattern (module-level `_cfg`, per-tool
  availability function, gate in both `list_tools()` and `call_tool()`).

### Details
- FastAPI wiring: `include_disabled`/`disabled_code` as plain function parameters
  with defaults are auto-bound from the query string; no `Request` object needed,
  matching this codebase's existing convention.

## Compatibility considerations
- Default parameter values preserve today's response shape for callers not passing
  the new parameters.
- Existing tests asserting `rag_run_pipeline`/`rag_debug_pipeline` appear in
  `/v1/tools` continue to pass as long as the test's `RagPipelineConfig` sets a
  non-empty `embed_url`.

## Security considerations
- Closes a fail-open gap: previously a caller could invoke `rag_run_pipeline`/
  `rag_debug_pipeline` via `/v1/call_tool` even when `embed_url` was unset, resulting
  in an unclear downstream failure instead of an explicit rejection.

## Rollback considerations
- Fully revertible by reverting `rag_pipeline_server.py`; no schema/data migration,
  no config file changes required.

## Validation plan
| Target | Test | Expected |
|---|---|---|
| `list_tools()` | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py::TestToolsListEndpoint` (extend) | `RagPipelineConfig(embed_url="")` → `rag_run_pipeline`/`rag_debug_pipeline` report `enabled=False` with a non-empty `disabled_reason`; `rag_list_documents`/`rag_delete_document` remain `enabled=True` |
| `include_disabled`/`disabled_code` | same file, new case | `include_disabled=false` omits the disabled tool; `disabled_code="embed_url is not configured"` filters to matching tools |
| Regression | `uv run pytest tests/mcp_servers/rag_pipeline/ -v` | All existing cases pass unmodified |

## Out of scope
- Adding an equivalent fail-closed check inside `RagPipelineMCPService`/
  `rag_pipeline_service.py` itself — the HTTP-layer gate added here does not change
  in-process calls (e.g. from `augment()`).
- Any `rag_db_path`-based gating for `rag_list_documents`/`rag_delete_document` — no
  existing precedent or acceptance criterion calls for it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260825-113000 | 20260825-113500 | Added `cast("list[McpTool]", annotated)` at the `build_tools_response()` call site — `McpTool` TypedDict has no `enabled`/`disabled_reason` fields but the function reads them at runtime via `.get()`; this mismatch will recur for every server in this REQ-004/REQ-005 batch |
| 2 | Add or update tests per Validation plan | Completed | 20260825-113500 | 20260825-114000 | Added 4 new cases to `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260825-114000 | 20260825-114300 | ruff/mypy/lint-imports/bandit clean; `rag_pipeline_server.py` is in `pyproject.toml`'s coverage `omit` list (FastAPI entry point, not unit-coverage-tracked) so diff-cover does not apply to it; 15/15 tests in the file pass, 78/78 in the directory |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Deferred | — | — | `docs/04_mcp_90_inconsistencies_and_known_issues.md` MCP-001/MCP-002 both name this file as part of a multi-server gap (MCP-002: 4 servers; MCP-001: 10 servers). Updating the entry now would only be accurate for 1/4 or 1/10 servers and require re-editing on every subsequent document in this batch. Deferred to the last document that closes each issue (MCP-002 at doc 06/shell, MCP-001 at doc 12/delete_server) — tracked in Blocker Log below so it isn't silently dropped. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | `docs/04_mcp_90_inconsistencies_and_known_issues.md` MCP-002 update deferred until all 4 REQ-004 servers (rag_pipeline, cicd, mdq, shell) are done | N/A: intentionally deferred, see doc for `shell_server.py` (seq 06) | — |
| 4 | `docs/04_mcp_90_inconsistencies_and_known_issues.md` MCP-001 update deferred until all 10 REQ-005 servers are done | N/A: intentionally deferred, see doc for `delete_server.py` (seq 12) | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` change | 1 | Code Change | Completed | — | — |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` cases | 2 | Test | Completed | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py
