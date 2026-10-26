## Goal
Add explicit `http_host = "127.0.0.1"` to `GitMCPServer` to maintain consistency with other MCP server subclasses and prevent future regressions.

## Priority
Low

## Scope
- **In-Scope**: Add `http_host = "127.0.0.1"` to `GitMCPServer`; update class docstring
- **Out-of-Scope**: Changes to the `MCPServer` base class's default `http_host` behavior; changes to how the server binds to network interfaces
- **Dependencies**: N/A: none

## Background
The `MCPServer` base class in `server.py` uses `http_host` to determine which network interface to bind to. The `MdqMCPServer` subclass explicitly sets `http_host = "127.0.0.1"` (mdq_server.py, line 451).

However, `GitMCPServer` (git_server.py, lines 376-384) does not define `http_host`:

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
Without an explicit `http_host` attribute, the server relies on the `MCPServer` base class's default value (`"127.0.0.1"`). While this is currently safe (the default is loopback-only), the lack of explicit declaration creates:
1. An inconsistency with other MCP server subclasses that explicitly set `http_host`.
2. A potential regression risk if the base class default changes in the future.
3. Reduced code clarity — readers cannot immediately see the intended binding address.

## Reason for Change
The missing `http_host` attribute creates an inconsistency with other MCP server subclasses and reduces code clarity. While the current default is safe, explicit declaration prevents future regressions.

## Implementation Intent
Add `http_host = "127.0.0.1"` to `GitMCPServer` to match the pattern used by other MCP server subclasses.

## Requirements
- `REQ-001`: `GitMCPServer` explicitly declares `http_host = "127.0.0.1"`
- `REQ-002`: Consistent with other MCP server subclasses
- `REQ-003`: No security regression from binding to all interfaces

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Modify | Add `http_host = "127.0.0.1"` to `GitMCPServer` | REQ-001, REQ-002 | Confirmed: `GitMCPServer` at lines 376-384 does not define `http_host`; `MCPServer` default is `"127.0.0.1"` (checked in Step 3) | Integration test for binding address | Needs confirmation |

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
| tests/mcp_servers/git/test_git_server.py | Verify existing binding patterns | REQ-001 |

## Acceptance Criteria
- `GitMCPServer` explicitly declares `http_host = "127.0.0.1"` (REQ-001)
- Consistent with other MCP server subclasses (REQ-002)
- No security regression from binding to all interfaces (REQ-003)

## Tests
- Integration test: verify server binds to `127.0.0.1` only (REQ-001)
- Regression test: ensure existing port binding behavior is unchanged (REQ-003)

## Documentation Impact
Update `GitMCPServer` docstring to document the `http_host` attribute.

## Assumptions
- The `http_host` value should be `"127.0.0.1"` to match other MCP server subclasses
- The existing port binding behavior should not change
- The `MCPServer` base class default of `"127.0.0.1"` is correct and should not be changed

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | What is the default `http_host` value in `MCPServer` if not specified? | Already verified: `"127.0.0.1"` | N/A | False |
| UNK-02 | Are there any deployment configurations that rely on the current behavior? | Need to check deployment configs | Review deployment configurations | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Modify | Low | N/A | N/A | No impact |

## Design
- **Approach**: Add `http_host = "127.0.0.1"` to `GitMCPServer` to match the pattern used by other MCP server subclasses
- **Rationale**: Explicit declaration prevents future regressions if the base class default changes, and improves code clarity by making the intended binding address visible.
- **Alternative considered**: Adding a comment to clarify the reliance on the base class default — this would document the current behavior but doesn't fix the inconsistency.

## Implementation steps
1. **Phase 1: Preparation**
   - [ ] Verify test file path exists under `tests/mcp_servers/git/` (Requirement ID: REQ-001; File Path: tests/mcp_servers/git/test_git_server.py)
2. **Phase 2: Core Logic Implementation**
   - [ ] Add `http_host = "127.0.0.1"` to `GitMCPServer` class attributes (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/git_server.py)
   - [ ] Update `GitMCPServer` docstring to document the `http_host` attribute (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/git_server.py)
3. **Phase 3: Testing & Verification**
   - [ ] Run lint/type checks on modified files (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/git_server.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Integration test | uv run pytest tests/mcp_servers/git/test_git_server.py -v | Test passes; server binds to 127.0.0.1 |
| scripts/mcp_servers/git/git_server.py | Lint check | uv run ruff check scripts/mcp_servers/git/git_server.py | Clean (no findings) |
| scripts/mcp_servers/git/git_server.py | Type check | uv run mypy scripts/mcp_servers/git/git_server.py | Clean (no type errors) |

## Risks
- **Risk**: Adding `http_host` may conflict with existing deployment configurations that rely on the current behavior → **Mitigation**: The current default is `"127.0.0.1"`, so adding the explicit value should not change behavior
- **Risk**: The `http_host` attribute may be overridden by environment variables or config files → **Mitigation**: Verify that the attribute is not overridden elsewhere in the deployment pipeline

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation — verify test file path | Pending | — | — | |
| 2 | Phase 2: Core Logic — add http_host attribute | Pending | — | — | |
| 3 | Phase 3: Testing & Verification — add integration test and run checks | Pending | — | — | |

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
- **Source issue**: issues/20261026-220730_mcp011-git-mcp-server-missing-http-host-attribute.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261026-224412
- **Related target files**: scripts/mcp_servers/git/git_server.py

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue Section | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem, Acceptance Criteria | scripts/mcp_servers/git/git_server.py | Phase 2 | http_host explicitly declared | Integration test for binding address | Confirmed by repository evidence |
| REQ-002 | Problem, Acceptance Criteria | scripts/mcp_servers/git/git_server.py | Phase 2 | Consistent with other subclasses | Code review for consistency | Confirmed by repository evidence |
| REQ-003 | Reason for Change, Acceptance Criteria | scripts/mcp_servers/git/git_server.py | Phase 3 | No security regression | Regression test for binding | Needs confirmation |
