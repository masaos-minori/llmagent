## Goal
- `list_tools()` should accept `include_disabled`/`disabled_code` query parameters
  and pass them through to `build_tools_response()` (REQ-005).

## Scope
- In scope: `read_server.py::list_tools()` only. `availability_flags()`'s logic is
  unchanged.

## Assumptions
- `build_tools_response`'s import is not yet present in this file and must be added.

## Design decisions
- Same pattern as `write_server.py`/`delete_server.py`: keep the existing
  `_annotate_tool(t, enabled, disabled_reason)` list and pass it into
  `build_tools_response()`.

## Alternatives considered
- Writing a bespoke filter — rejected, same reasoning as the other five documents in
  this set.

## Implementation
### Target file
`scripts/mcp_servers/file/read_server.py`

### Procedure
1. Add `build_tools_response` to the `from mcp_servers.server import ...` line.
2. Add `include_disabled`/`disabled_code` `Query` parameters to `list_tools()`'s
   signature.
3. Replace the return value with the `_annotate_tool()`-built list passed into
   `build_tools_response(annotated, "file_read", include_disabled=include_disabled, disabled_code=disabled_code)`.

### Method
- Add `fastapi.Query` to imports.

### Details
- The existing `availability_flags(_cfg.allowed_dirs)` call and `_annotate_tool()`
  loop are unchanged.

## Compatibility considerations
- Existing `GET /v1/tools` (no parameters) response is unchanged.

## Security considerations
- No change.

## Rollback considerations
- Single-file change; reverting `read_server.py` restores prior behavior.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_tools_endpoint.py -v` (cross-file-server
  parametrized test) to confirm no regression.
- Add a new case for `include_disabled`/`disabled_code` filtering.

## Out of scope
- `availability_flags()`'s decision logic.
- The equivalent change to the other five servers — each has its own document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260825-135300 | 20260825-135600 | Matches docs 04-10's pattern |
| 2 | Add or update tests per Validation plan | Completed | 20260825-135600 | 20260825-140200 | Added a new `_FILE_SERVERS_REQ_005` subset list in `test_tools_endpoint.py` plus 2 new parametrized tests (`include_disabled=false` omission, `disabled_code` filtering) covering `read_server.py`+`write_server.py` — deliberately excludes `delete_server.py` until doc 12 lands, to avoid failing against a handler that doesn't accept those query params yet |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260825-140200 | 20260825-140500 | ruff/mypy/lint-imports/bandit clean; `read_server.py` is in the coverage `omit` list; 292/294 pass (16/16 in `test_tools_endpoint.py`) — the 2 failures confirmed pre-existing |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Deferred | — | — | Same MCP-001 batching decision as doc 03 — see that document's Blocker Log |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | `docs/04_mcp_90_inconsistencies_and_known_issues.md` MCP-001 update deferred — see doc 03 Blocker Log | N/A: intentionally deferred | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `scripts/mcp_servers/file/read_server.py` change | 1 | Code Change | Completed | — | — |
| `tests/mcp_servers/git/test_tools_endpoint.py` new cases | 2 | Test | Completed | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/mcp_servers/file/read_server.py
