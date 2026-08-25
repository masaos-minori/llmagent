## Goal
- `list_tools()` should accept `include_disabled`/`disabled_code` query parameters
  and actually call the already-imported-but-unused `build_tools_response()`
  (REQ-005).

## Scope
- In scope: `github_server.py::list_tools()` only. `_github_tool_availability()`'s
  logic is unchanged.

## Assumptions
- `build_tools_response`'s import (from `mcp_servers.server`) already exists, so no
  new import line is needed for it.

## Design decisions
- The current `list_tools()` calls `_github_tool_availability("")` once and applies
  the same `enabled`/`disabled_reason` to every tool via a list comprehension; keep
  that annotation step as-is and pass its result into `build_tools_response()`.

## Alternatives considered
- Removing the `build_tools_response` import and writing a bespoke filter — rejected;
  it would both leave the "unused import" oddity unresolved in spirit and duplicate
  logic the Plan's Design section says to reuse.

## Implementation
### Target file
`scripts/mcp_servers/github/github_server.py`

### Procedure
1. Add `include_disabled`/`disabled_code` `Query` parameters to `list_tools()`'s
   signature.
2. Keep the existing annotation step (`enabled, reason = _github_tool_availability("")`, then the per-tool dict comprehension) as a local variable.
3. Replace the return value with
   `build_tools_response(annotated, "github", include_disabled=include_disabled, disabled_code=disabled_code)`.

### Method
- Add `fastapi.Query` to imports.
- The existing `{**t, "server_key": "github", "enabled": enabled, "disabled_reason": reason} for t in TOOL_LIST` list comprehension is kept as the annotation step, whose
  result becomes `build_tools_response()`'s `tools` argument.

### Details
- The `_github_tool_availability("")` call's argument (empty string) is unchanged.

## Compatibility considerations
- Existing `GET /v1/tools` (no parameters) response shape/content is unchanged.

## Security considerations
- No change; `disabled_code` filtering is delegated to `build_tools_response()`'s
  existing implementation.

## Rollback considerations
- Single-file change; reverting `github_server.py` restores prior behavior.
  `build_tools_response`'s import predates this change, so reverting does not affect
  anything else.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_server_endpoints.py -v` to
  confirm `TestToolsListEndpoint`'s existing `server_key == "github"` assertion does
  not regress.
- Add a new case for `include_disabled`/`disabled_code` query-parameter filtering.

## Out of scope
- `_github_tool_availability()`'s decision logic.
- The equivalent change to the other five servers — each has its own document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no doc update required by this item |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/mcp_servers/github/github_server.py
