## Goal
- `list_tools()` should accept `include_disabled`/`disabled_code` query parameters
  and pass them through to `build_tools_response()` (REQ-005).

## Scope
- In scope: `git_server.py::list_tools()` only. `_git_tool_availability()`/
  `_annotate_tool()`'s enabled/disabled-reason logic is unchanged.

## Assumptions
- `build_tools_response()`'s signature (`include_disabled: bool = False`,
  `disabled_code: str | None = None`) is unchanged from its current shape.
- The existing `_annotate_tool(t, cfg)` output already includes `enabled`/
  `disabled_reason`, satisfying `build_tools_response()`'s filter condition.

## Design decisions
- Annotate each tool with the existing `_annotate_tool()` as today, then pass the
  resulting list into `build_tools_response()` (separating annotation from delivery
  filtering).
- Declare the query parameters via FastAPI's `Query()`, typed to match
  `build_tools_response()`'s parameters.

## Alternatives considered
- Re-implementing the filter inside `list_tools()` — rejected; duplicates
  `build_tools_response()`'s logic, against the Plan's Design section (reuse the
  existing function).

## Implementation
### Target file
`scripts/mcp_servers/git/git_server.py`

### Procedure
1. Add `build_tools_response` to the existing `from mcp_servers.server import ...`
   line.
2. Add `include_disabled`/`disabled_code` `Query` parameters to `list_tools()`'s
   signature.
3. Replace `list_tools()`'s return value: build the `_annotate_tool()`-annotated list
   as today, then return `build_tools_response(annotated, "git", include_disabled=include_disabled, disabled_code=disabled_code)` instead of the current hand-built
   `{"schema_version": ..., "tools": [...]}` dict literal.

### Method
- Add `fastapi.Query` to imports.

### Details
- The existing `_annotate_tool(t, _cfg)` loop over `TOOL_LIST` is unchanged.
- `build_tools_response()` re-sets `server_key` on the response, to the same `"git"`
  value already used, so this has no side effect.

## Compatibility considerations
- The new parameters have defaults, so an existing `GET /v1/tools` call with no
  parameters is unaffected.

## Security considerations
- `disabled_code` is only used for string-equality filtering inside the existing
  `build_tools_response()` implementation, unchanged by this document. The exposure
  of disabled-reason text is unchanged unless a caller explicitly passes
  `include_disabled=True`.

## Rollback considerations
- Single-file change; revert the `git_server.py` diff to restore prior behavior. No
  dependency on other files.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_tools_endpoint.py -v` to confirm the
  existing enabled/disabled_reason assertions do not regress.
- Add a new case asserting `include_disabled=false` omits a disabled tool from the
  response, and that `disabled_code` filters correctly.

## Out of scope
- `_git_tool_availability()`'s enabled/disabled decision logic (REQ-004, not
  applicable to this already-compliant server).
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
- **Related target files**: scripts/mcp_servers/git/git_server.py
