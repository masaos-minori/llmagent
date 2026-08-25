## Goal
- Compute real per-tool `enabled`/`disabled_reason` for `cicd-mcp`'s tools based on
  `repo_allowlist`/`workflow_allowlist` (REQ-004), and thread `include_disabled`/
  `disabled_code` query parameters through `list_tools()` into
  `build_tools_response()` (REQ-005).

## Scope
- In scope: `list_tools()`, a new `_cicd_tool_availability()` helper, and a new
  disabled-tool gate in `call_tool()`, all in
  `scripts/mcp_servers/cicd/cicd_server.py`.
- Out of scope: `CiCdGuards`/`cicd_service_guards.py` (already fail-closed and
  unchanged); `build_tools_response()` signature (unchanged).

## Assumptions
- The existing module-level `_cfg = CicdConfig.load()` in `cicd_server.py` is the
  correct config source for the new helper.
- `trigger_workflow` is the only tool that touches `workflow_allowlist`;
  `get_workflow_runs`/`get_workflow_status`/`get_workflow_logs` only require a repo
  to be allowlisted, per `CiCdGuards._assert_allowed_repo`/`_assert_allowed_workflow`
  call sites in `cicd_service_business.py`.

## Design decisions
- `_cicd_tool_availability(cfg: CicdConfig, tool_name: str) -> tuple[bool, str]`:
  return `(False, "repo_allowlist is empty")` when `cfg.repo_allowlist` is empty
  (applies to all tools); else for `tool_name == "trigger_workflow"`, return
  `(False, "workflow_allowlist is empty")` when `cfg.workflow_allowlist` is empty;
  else `(True, "")`.
- Check repo before workflow, mirroring `CiCdGuards._assert_allowed_repo()` running
  before `_assert_allowed_workflow()` in the actual guard mixin, so the surfaced
  `disabled_reason` matches the order the underlying service would actually reject
  in.
- Add the same "Tool disabled: {reason}" gate to `call_tool()` as `git_server.py`/
  `github_server.py`, for consistency, even though `CiCdGuards` already fails closed
  (harmless double-gating, and short-circuits before dispatch/audit-log overhead).

## Alternatives considered
- Skipping the `call_tool()` gate since `CiCdGuards` already raises
  `CicdAuthorizationError` — rejected in favor of matching the established pattern
  used by the other target servers; the existing exception-handler path remains as a
  second layer of defense.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_server.py`

### Procedure
1. Add `_cicd_tool_availability(cfg, tool_name)` near `_dispatch_cicd_tool()`.
2. Add `_annotate_tool(tool, cfg)` returning `{**tool, "enabled": ..., "disabled_reason": ...}`.
3. Update `list_tools()` to accept `include_disabled: bool = False, disabled_code: str | None = None`, annotate `TOOL_LIST`, and call
   `build_tools_response(annotated, "cicd", include_disabled=include_disabled, disabled_code=disabled_code)`.
4. In `call_tool()`, compute `_cicd_tool_availability(_cfg, req.name)` and return
   `CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)` before the
   existing `_dispatch_cicd_tool()` call, when not enabled.

### Method
- Mirror `git_server.py`'s `_git_tool_availability`/`_annotate_tool`/gate-in-both-
  endpoints pattern, substituting the repo/workflow allowlist conditions for git's
  `read_only`/`GIT_WRITE_TOOLS` condition.

### Details
- No new imports beyond what's already present (`CicdConfig`/`_cfg` already exist at
  module scope).
- FastAPI query-parameter wiring identical to the `rag_pipeline` change.

## Compatibility considerations
- Existing `test_lists_cicd_tools_with_server_key` continues to pass provided the
  test's fixtures configure a non-empty `repo_allowlist`/`workflow_allowlist`, or is
  extended to also assert `enabled`.
- Default parameter values preserve current `/v1/tools` response shape.

## Security considerations
- Closes the metadata/enforcement gap: previously `/v1/tools` always reported all
  tools as available regardless of allowlist state; the discovery response now
  accurately reflects service-layer enforcement.

## Rollback considerations
- Fully revertible by reverting `cicd_server.py`; no config or schema changes.

## Validation plan
| Target | Test | Expected |
|---|---|---|
| `list_tools()` | `tests/mcp_servers/cicd/test_cicd_server_endpoints.py::TestToolsListEndpoint` (extend) | `CicdConfig(repo_allowlist=[])` → all tools `enabled=False`, reason `"repo_allowlist is empty"`; `CicdConfig(repo_allowlist=["o/r"], workflow_allowlist=[])` → only `trigger_workflow` `enabled=False`, reason `"workflow_allowlist is empty"`, others `enabled=True` |
| `include_disabled`/`disabled_code` | same file, new case | `include_disabled=false` omits `trigger_workflow` when disabled; `disabled_code="workflow_allowlist is empty"` filters to matching tools |
| Regression | `uv run pytest tests/mcp_servers/cicd/ -v` | All existing cases pass unmodified |

## Out of scope
- Changes to `CiCdGuards`/`cicd_service_guards.py` enforcement logic — already
  correct and unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260825-114500 | 20260825-115000 | Adversarially checked the audit log's `req.args.get("repo", "")` (looked like the same schema-key-mismatch shape as Git MCP's M-4) — confirmed CI/CD's actual schema key IS `"repo"`, so no bug there; also added `cast("list[McpTool]", annotated)` per the recurring McpTool/build_tools_response mismatch noted in doc03 |
| 2 | Add or update tests per Validation plan | Completed | 20260825-115000 | 20260825-115600 | Added 5 new cases; discovered and fixed 3 existing tests (`test_lists_cicd_tools_with_server_key`, `test_dispatches_known_tool_and_audit_logs`, `test_unknown_tool_returns_error_result`) that implicitly depended on the real, empty `_cfg.repo_allowlist` from the test environment's `cicd_mcp_server.toml` — with the new gate, they now need an explicit non-empty `_cfg` to exercise the behavior they were actually meant to test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260825-115600 | 20260825-120000 | ruff/mypy/lint-imports clean; bandit's 1 finding (B105 on `"not_set"` in `health()`) confirmed pre-existing via `git show HEAD` — unrelated to this change; diff-cover 100%; 174/174 tests pass in `tests/mcp_servers/cicd/` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Deferred | — | — | Same MCP-001/MCP-002 batching decision as doc 03 (rag_pipeline) — see that document's Blocker Log |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | `docs/04_mcp_90_inconsistencies_and_known_issues.md` MCP-001/MCP-002 update deferred — see doc 03 (rag_pipeline) Blocker Log for the batching rationale | N/A: intentionally deferred | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `scripts/mcp_servers/cicd/cicd_server.py` change | 1 | Code Change | Completed | — | — |
| `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` cases | 2 | Test | Completed | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/mcp_servers/cicd/cicd_server.py
