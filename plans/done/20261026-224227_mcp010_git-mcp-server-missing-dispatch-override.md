## Goal
Add `dispatch()` method override to `GitMCPServer` to maintain consistency with other MCP server subclasses and prevent `NotImplementedError` when called programmatically.

## Priority
Medium

## Scope
- **In-Scope**: Add `dispatch()` method to `GitMCPServer`; update class docstring
- **Out-of-Scope**: Changes to the git service's dispatch table; changes to the HTTP-based dispatch flow
- **Dependencies**: N/A: none

## Background
The `MCPServer` base class in `server.py` defines a `dispatch()` method that raises `NotImplementedError`:

```python
async def dispatch(self, name: str, args: dict[str, Any]) -> DispatchResult:
    raise NotImplementedError("Subclasses must implement dispatch")
```

Other MCP server subclasses override this method:
- `MdqMCPServer` (mdq_server.py, line 458): overrides `dispatch()`
- `WebSearchMCPServer` (web_search_server.py, line 326): overrides `dispatch()`
- `FileDeleteMCPServer` (delete_server.py, line 268): overrides `dispatch()`

But `GitMCPServer` (git_server.py, line 376) does NOT override `dispatch()`:

```python
class GitMCPServer(MCPServer):
    """MCPServer subclass for git-mcp."""
    server_name = "git-mcp"
    server_version = "1.0.0"
    http_port = 8014
    own_config_file = "git_mcp_server.toml"
    app_module = "mcp_servers.git.git_server:app"
    mcp_tools = TOOL_LIST
```

## Problem
If any code path calls `server.dispatch()` programmatically (e.g., via the MCPServer base class interface), it will raise `NotImplementedError`. This is a latent bug that only manifests when:
1. The server is instantiated programmatically (not via `__main__`).
2. The `dispatch()` method is called directly on the instance.

The risk is that:
1. Future refactoring could add a programmatic dispatch path.
2. Test code might instantiate `GitMCPServer` and call `dispatch()`.
3. The inconsistency with other MCP server subclasses makes the codebase harder to reason about.

## Reason for Change
The missing `dispatch()` override creates an inconsistency with other MCP server subclasses and introduces a latent bug that could surface during testing or future development.

## Implementation Intent
Add a `dispatch()` method to `GitMCPServer` that delegates to the git service's dispatch table, similar to how other MCP servers implement it.

## Requirements
- `REQ-001`: `GitMCPServer.dispatch()` returns a `DispatchResult` without raising `NotImplementedError`
- `REQ-002`: The method delegates to the git service's dispatch table
- `REQ-003`: Other MCP server subclasses have consistent `dispatch()` implementations

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Modify | Add `dispatch()` method to `GitMCPServer` | REQ-001, REQ-002 | Confirmed: `GitMCPServer` at lines 376-384 does not override `dispatch()`; other 9 MCP servers do (checked in Step 3) | Unit test for programmatic dispatch | Needs confirmation |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| tests/mcp_servers/git/test_git_server.py | Verify existing dispatch patterns | REQ-001 |

## Acceptance Criteria
- `GitMCPServer.dispatch()` returns a `DispatchResult` without raising `NotImplementedError` (REQ-001)
- The method delegates to the git service's dispatch table (REQ-002)
- Other MCP server subclasses have consistent `dispatch()` implementations (REQ-003)

## Tests
- Unit test: verify `GitMCPServer.dispatch()` does not raise `NotImplementedError` (REQ-001)
- Integration test: verify programmatic dispatch works correctly (REQ-002)
- Regression test: ensure existing HTTP dispatch behavior is unchanged (REQ-003)

## Documentation Impact
Update `GitMCPServer` docstring to document the `dispatch()` method.

## Assumptions
- The `dispatch()` method should delegate to `_service.get_dispatch_table()` similar to other MCP servers
- The method signature should match the `MCPServer.dispatch()` contract
- The existing HTTP-based dispatch flow should not be changed

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Are there any existing code paths that call `GitMCPServer.dispatch()` programmatically? | Need to check git-mcp server for programmatic dispatch usage | Review git-mcp server code | False |
| UNK-02 | Should the `dispatch()` method include idempotency key support? | Need to check if other MCP servers include idempotency key support | Review other MCP server dispatch implementations | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Modify | Low | N/A | N/A | No impact |

## Design
- **Approach**: Add `dispatch()` method to `GitMCPServer` that delegates to `_service.get_dispatch_table()`
- **Rationale**: Consistency with other MCP server subclasses prevents latent bugs and makes the codebase easier to reason about.
- **Alternative considered**: Adding a `NotImplementedError` comment to clarify the intentional omission — this would document the current behavior but doesn't fix the inconsistency.

## Implementation steps
1. **Phase 1: Preparation**
   - [ ] Verify test file path exists under `tests/mcp_servers/git/` (Requirement ID: REQ-001; File Path: tests/mcp_servers/git/test_git_server.py)
2. **Phase 2: Core Logic Implementation**
   - [ ] Add `dispatch()` method to `GitMCPServer` that delegates to `_service.get_dispatch_table()` (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/git_server.py)
   - [ ] Update `GitMCPServer` docstring to document the `dispatch()` method (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/git_server.py)
3. **Phase 3: Testing & Verification**
   - [ ] Run lint/type checks on modified files (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/git_server.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Unit test | uv run pytest tests/mcp_servers/git/test_git_server.py -v | Test passes; dispatch() works without NotImplementedError |
| scripts/mcp_servers/git/git_server.py | Lint check | uv run ruff check scripts/mcp_servers/git/git_server.py | Clean (no findings) |
| scripts/mcp_servers/git/git_server.py | Type check | uv run mypy scripts/mcp_servers/git/git_server.py | Clean (no type errors) |

## Risks
- **Risk**: Adding `dispatch()` may introduce subtle differences in error handling compared to HTTP-based dispatch → **Mitigation**: Delegate to the same git service dispatch table used by HTTP-based dispatch
- **Risk**: The `dispatch()` method may not handle all edge cases that the HTTP-based dispatch handles → **Mitigation**: Ensure the method signature matches the `MCPServer.dispatch()` contract exactly

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation — verify test file path | Pending | — | — | |
| 2 | Phase 2: Core Logic — add dispatch() method | Pending | — | — | |
| 3 | Phase 3: Testing & Verification — add unit test and run checks | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261026-220730_mcp010-git-mcp-server-missing-dispatch-override.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261026-224227
- **Related target files**: scripts/mcp_servers/git/git_server.py

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue Section | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem, Acceptance Criteria | scripts/mcp_servers/git/git_server.py | Phase 2 | dispatch() doesn't raise NotImplementedError | Unit test for programmatic dispatch | Confirmed by repository evidence |
| REQ-002 | Problem, Acceptance Criteria | scripts/mcp_servers/git/git_server.py | Phase 2 | Method delegates to dispatch table | Integration test for programmatic dispatch | Confirmed by repository evidence |
| REQ-003 | Reason for Change, Acceptance Criteria | scripts/mcp_servers/git/git_server.py | Phase 3 | Consistent dispatch implementations | Regression test for HTTP dispatch | Needs confirmation |
