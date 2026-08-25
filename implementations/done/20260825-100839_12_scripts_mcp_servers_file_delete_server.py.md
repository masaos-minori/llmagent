## Goal
- `list_tools()` should accept `include_disabled`/`disabled_code` query parameters
  and pass them through to `build_tools_response()` (REQ-005).

## Scope
- In scope: `delete_server.py::list_tools()` only. `availability_flags()`'s logic is
  unchanged.

## Assumptions
- `build_tools_response`'s import is not yet present in this file and must be added.

## Design decisions
- Same pattern as `write_server.py`/`read_server.py`: keep the existing
  `_annotate_tool(t, enabled, disabled_reason)` list and pass it into
  `build_tools_response()`.

## Alternatives considered
- Writing a bespoke filter — rejected, same reasoning as the other five documents in
  this set.

## Implementation
### Target file
`scripts/mcp_servers/file/delete_server.py`

### Procedure
1. Add `build_tools_response` to the `from mcp_servers.server import ...` line.
2. Add `include_disabled`/`disabled_code` `Query` parameters to `list_tools()`'s
   signature.
3. Replace the return value with the `_annotate_tool()`-built list passed into
   `build_tools_response(annotated, "file_delete", include_disabled=include_disabled, disabled_code=disabled_code)`.

### Method
- Add `fastapi.Query` to imports.

### Details
- The existing `availability_flags(_cfg.allowed_dirs)` call and `_annotate_tool()`
  loop are unchanged.

## Compatibility considerations
- Existing `GET /v1/tools` (no parameters) response is unchanged.

## Security considerations
- No change to `delete_file`/`delete_directory`'s own execution path.

## Rollback considerations
- Single-file change; reverting `delete_server.py` restores prior behavior.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260825-140800 | 20260825-141100 | Matches docs 04-11's pattern; last of the 10 REQ-005 servers |
| 2 | Add or update tests per Validation plan | Completed | 20260825-141100 | 20260825-141500 | Extended `_FILE_SERVERS_REQ_005` in `test_tools_endpoint.py` to cover all 3 file servers (now equal to `_FILE_SERVERS`) since `delete_server.py` is the last one migrated |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260825-141500 | 20260825-141800 | ruff/mypy/lint-imports/bandit clean; `delete_server.py` is in the coverage `omit` list; 294/296 pass in `tests/mcp_servers/file/` + `test_tools_endpoint.py` (18/18) — the 2 failures confirmed pre-existing across all prior docs |
| 4 | Update documentation — MCP-001 fully resolved | Completed | 20260825-141800 | 20260825-142000 | This is the last of the 10 REQ-005 servers — updated `docs/04_mcp_90_inconsistencies_and_known_issues.md` MCP-001 to `Status: resolved` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `scripts/mcp_servers/file/delete_server.py` change | 1 | Code Change | Completed | — | — |
| `tests/mcp_servers/git/test_tools_endpoint.py` update | 2 | Test | Completed | — | — |
| `docs/04_mcp_90_inconsistencies_and_known_issues.md` MCP-001 resolution | 4 | Doc Change | Completed | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/mcp_servers/file/delete_server.py
