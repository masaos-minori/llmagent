## Goal
- Compute real per-tool `enabled`/`disabled_reason` for `shell-mcp`'s `shell_run`
  tool based on `command_allowlist` (REQ-004), and thread `include_disabled`/
  `disabled_code` through `list_tools()` into `build_tools_response()` (REQ-005).

## Scope
- In scope: `list_tools()` and a new `_shell_tool_availability()` helper in
  `scripts/mcp_servers/shell/shell_server.py`; a matching gate added to
  `call_tool()`.
- Out of scope: `ShellPolicy`/`shell_service.py`'s `allowed_commands` enforcement
  (already correct, fail-closed, and unchanged).

## Assumptions
- `shell_server.py` currently has no module-level `ShellConfig`/`_cfg` object — only
  `_service: ShellService = build_service(load_shell_policy())`. The new helper
  needs the raw `command_allowlist`, so a new module-level `_cfg: ShellConfig = ShellConfig.load()` is added, mirroring the git/cicd/web_search precedent of a
  dedicated `_cfg` singleton, without depending on `ShellPolicy`'s internal shape.

## Design decisions
- `_shell_tool_availability(cfg: ShellConfig, tool_name: str) -> tuple[bool, str]`:
  return `(False, "command_allowlist is empty")` when `cfg.command_allowlist` is
  empty, else `(True, "")`. Only one tool (`shell_run`) exists today, so `tool_name`
  is unused for now but kept for signature consistency with the other three servers.
- Add the same "Tool disabled: {reason}" gate to `call_tool()` as `git_server.py`/
  `github_server.py`, for consistency, even though `ShellService`'s dispatch path
  already rejects any command when the allowlist is empty.

## Alternatives considered
- Reading the allowlist off `_service`/`ShellPolicy` instead of adding a new
  `_cfg: ShellConfig` — rejected; `ShellPolicy` is the sandboxing runtime contract
  built once at import time, not a discovery-metadata source. A separate `_cfg` keeps
  the same clean separation the other three servers use.
- Skipping the `call_tool()` gate since `ShellService` already fails closed —
  rejected in favor of matching the established pattern for consistency.

## Implementation
### Target file
`scripts/mcp_servers/shell/shell_server.py`

### Procedure
1. Add `ShellConfig` to the existing `from mcp_servers.shell.shell_models import ...`
   line, and a module-level `_cfg: ShellConfig = ShellConfig.load()`.
2. Add `_shell_tool_availability(cfg, tool_name)` and `_annotate_tool(tool, cfg)`
   near `_dispatch_shell_tool()`.
3. Update `list_tools()` to accept `include_disabled: bool = False, disabled_code: str | None = None`, annotate `TOOL_LIST`, and call
   `build_tools_response(annotated, "shell", include_disabled=include_disabled, disabled_code=disabled_code)`.
4. In `call_tool()`, compute `_shell_tool_availability(_cfg, req.name)` and return
   `CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)` before
   `_dispatch_shell_tool()`, when not enabled.

### Method
- Mirror `git_server.py`'s pattern exactly, substituting `command_allowlist` for
  `allowed_repo_paths`/`read_only`.

### Details
- `load_shell_policy()` (used to build `_service`) and the new `ShellConfig.load()`
  both read `shell_mcp_server.toml`; loading twice at import is consistent with
  `web_search_server.py` also loading its own `_cfg` independently of service
  construction.

## Compatibility considerations
- Existing `test_lists_shell_run_with_server_key` continues to pass provided the
  test's config fixture sets a non-empty `command_allowlist`, or is extended to also
  assert `enabled`.
- Default query-parameter values preserve the current `/v1/tools` response shape.

## Security considerations
- Closes the metadata/enforcement gap: `/v1/tools` now reports `shell_run` as
  disabled whenever `command_allowlist` is empty, matching the already fail-closed
  dispatch behavior.

## Rollback considerations
- Fully revertible by reverting `shell_server.py`; no config/schema changes.

## Validation plan
| Target | Test | Expected |
|---|---|---|
| `list_tools()` | `tests/mcp_servers/shell/test_shell_server_endpoints.py::TestToolsListEndpoint` (extend) | `ShellConfig(command_allowlist=[])` → `shell_run` reports `enabled=False`, reason `"command_allowlist is empty"`; non-empty allowlist → `enabled=True`, reason `""` |
| `include_disabled`/`disabled_code` | same file, new case | `include_disabled=false` omits `shell_run` when disabled; `disabled_code="command_allowlist is empty"` matches it in that state |
| Regression | `uv run pytest tests/mcp_servers/shell/ -v` | All existing cases pass unmodified |

## Out of scope
- Changes to `ShellPolicy`/`shell_service.py`'s allowlist enforcement — already
  correct and unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260825-122500 | 20260825-122900 | Added module-level `_cfg: ShellConfig = ShellConfig.load()` (did not exist before); matches doc04/05's `cast("list[McpTool]", ...)` pattern |
| 2 | Add or update tests per Validation plan | Completed | 20260825-122900 | 20260825-123500 | Added 4 new cases; fixed 3 existing tests (`test_lists_shell_run_with_server_key`, `test_dispatches_known_tool_and_audit_logs`, `test_unknown_tool_returns_error_result`) that implicitly depended on the real, empty `_cfg.command_allowlist` — same root cause as docs 04/05 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260825-123500 | 20260825-123900 | ruff/mypy/lint-imports/bandit clean; `shell_server.py` is in the coverage `omit` list (confirmed: diff-cover reports "No lines with coverage information"); 66/66 tests pass in `tests/mcp_servers/shell/` |
| 4 | Update documentation — MCP-002 fully resolved | Completed | 20260825-123900 | 20260825-124100 | This is the last of the 4 REQ-004 servers (rag_pipeline, cicd, mdq, shell) — updated `docs/04_mcp_90_inconsistencies_and_known_issues.md` MCP-002 to `Status: resolved` with a resolution note naming all 4 servers' availability functions |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `scripts/mcp_servers/shell/shell_server.py` change | 1 | Code Change | Completed | — | — |
| `tests/mcp_servers/shell/test_shell_server_endpoints.py` cases | 2 | Test | Completed | — | — |
| `docs/04_mcp_90_inconsistencies_and_known_issues.md` MCP-002 resolution | 4 | Doc Change | Completed | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/mcp_servers/shell/shell_server.py
