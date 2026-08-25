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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260825-131200 | 20260825-131500 | Matches docs 04-08's pattern; `build_tools_response` import predates this change |
| 2 | Add or update tests per Validation plan | Completed | 20260825-131500 | 20260825-132000 | Added 2 new REQ-005 cases; fixed `test_tools_endpoint_lists_both_tools_under_web_search_server_key` (same "vacuous/failing on empty filtered list" issue as docs 07/08 — `browser_allowed_domains` is empty in this test environment) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260825-132000 | 20260825-132300 | ruff/mypy/lint-imports/bandit clean; `web_search_server.py` is in the coverage `omit` list; 151/156 tests pass in `tests/mcp_servers/web_search/` — the 5 failures (2 in `test_web_search_server.py`, 3 in `test_web_search_audit.py`) confirmed pre-existing via `git stash`, unrelated to `/v1/tools` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Deferred | — | — | Same MCP-001 batching decision as doc 03 — see that document's Blocker Log |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | `docs/04_mcp_90_inconsistencies_and_known_issues.md` MCP-001 update deferred — see doc 03 Blocker Log | N/A: intentionally deferred | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `scripts/mcp_servers/web_search/web_search_server.py` change | 1 | Code Change | Completed | — | — |
| `tests/mcp_servers/web_search/test_web_search_server.py` cases | 2 | Test | Completed | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/mcp_servers/web_search/web_search_server.py
