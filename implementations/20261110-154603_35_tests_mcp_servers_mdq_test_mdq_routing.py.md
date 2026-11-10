## Goal
Delete the tests of `list_tools()`, `list_tools_with_server_key()` and the base `health()` from `tests/mcp_servers/mdq/test_mdq_routing.py` (`REQ-006`: the helpers have no production caller).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- `scripts/mcp_servers/server.py` (row 11) removes the three methods; `MdqMCPServer` inherits no replacement, so these tests would raise `AttributeError`.
- The `/health` and `/v1/tools` HTTP behavior stays covered by `tests/mcp_servers/mdq/test_mdq_health.py`, `test_mdq_metadata_consistency.py` and `TestMdqV1ToolsEndpoint` in this file, which use the module-level handlers.

## Design decisions
- Delete, do not rewrite: the deleted tests assert the removed methods' shapes, not production behavior.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_routing.py`

### Procedure
- Delete `test_list_tools_with_server_key` (lines 140-148).
- Delete `test_health_method_returns_standard_shape` (lines 157-170, calls `server.health()` at line 161).
- Delete `test_list_tools_returns_tool_names` (lines 172-179).
- Keep `test_dispatch_method_exists` (lines 150-155) and the rest of the class.

### Method
- Remove each method in full including its blank-line separator; drop any import left unused (check with `uv run ruff check`).

### Details
- After the deletions, `rg -n "list_tools|\.health\(" tests/mcp_servers/mdq/test_mdq_routing.py` returns nothing.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_routing.py -v`
- `uv run pytest tests/mcp_servers/mdq/test_mdq_rag_boundary.py -v`

## Completion criteria
- No reference to `list_tools`, `list_tools_with_server_key` or `health()` remains in the file.
- Remaining tests pass.

## Out of Scope
- Changing the mdq `/health` handler or its tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/mcp_servers/mdq/test_mdq_routing.py` per Procedure/Method/Details | Pending | — | — | |
| 2 | Run `uv run pytest tests/mcp_servers/mdq/test_mdq_routing.py -v` and fix remaining fixtures in this file only | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (unused `MCPServer` helpers removed)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_routing.py`
