## Goal
- `list_tools()` should accept `include_disabled`/`disabled_code` query parameters
  and actually call the already-imported-but-unused `build_tools_response()`
  (REQ-005).

## Scope
- In scope: `web_search_server.py::list_tools()` only.
  `_web_search_tool_availability()`'s logic is unchanged.

## Assumptions
- `build_tools_response`'s import already exists.

## Design decisions
- Keep the existing per-tool list comprehension (`for t in TOOL_LIST for enabled, reason in [_web_search_tool_availability(_cfg, t["name"])]`) as the annotation
  step, and pass its result into `build_tools_response()`.

## Alternatives considered
- Writing a bespoke filter — rejected, same reasoning as the git/github documents.

## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_server.py`

### Procedure
1. Add `include_disabled`/`disabled_code` `Query` parameters to `list_tools()`'s
   signature.
2. Keep the existing list comprehension's result as a local variable.
3. Replace the return value with
   `build_tools_response(annotated, "web_search", include_disabled=include_disabled, disabled_code=disabled_code)`.

### Method
- Add `fastapi.Query` to the existing `from fastapi import FastAPI, Request` line.

### Details
- `_web_search_tool_availability(_cfg, t["name"])` is evaluated per-tool (unlike
  github's single shared value) and is unchanged.

## Compatibility considerations
- Existing `GET /v1/tools` (no parameters) response is unchanged.

## Security considerations
- No change.

## Rollback considerations
- Single-file change; reverting `web_search_server.py` restores prior behavior.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_server.py -v` to
  confirm `TestBrowserFetchToolsEndpoint` does not regress.
- Add a new case for `include_disabled`/`disabled_code` filtering.

## Out of scope
- `_web_search_tool_availability()`'s decision logic.
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
- **Related target files**: scripts/mcp_servers/web_search/web_search_server.py
