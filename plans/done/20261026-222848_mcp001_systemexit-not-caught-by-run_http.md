## Goal
Ensure `SystemExit` raised by `_enforce_startup_posture_gate()` inside `MCPServer.run_http()` is caught and handled gracefully, preventing abrupt process termination without connection draining or structured logging.

## Priority
High

## Scope
- **In-Scope**: Add `SystemExit` handling to `MCPServer.run_http()` in `scripts/mcp_servers/server.py`; update docstring; add unit test
- **Out-of-Scope**: Changes to posture validation logic; changes to how `_enforce_posture_gate()` is called in `__main__` blocks
- **Dependencies**: N/A: none

## Background
All MCP servers define `_enforce_posture_gate()` that raises `SystemExit(1)` when the security posture is not validated. This function is called in the `if __name__ == "__main__"` block before `server.run_http()`. However, `MCPServer.run_http()` also calls `_enforce_startup_posture_gate()` internally (line 294 of `server.py`) as part of the startup sequence.

## Problem
If `_enforce_startup_posture_gate()` raises `SystemExit(1)` inside `run_http()`, the `try/except KeyboardInterrupt` block (lines 321-324 of `server.py`) does not catch `SystemExit`. The process terminates abruptly without:
- Closing active HTTP connections gracefully
- Releasing uvicorn server resources
- Logging the failure reason to stderr/stdout in a structured way

This is especially problematic because `run_http()` is the public entry point used by all server launchers (binary launchers, mcp_launcher, python -m). Any launcher that calls `run_http()` directly inherits this silent-exit behavior.

## Reason for Change
A silent `SystemExit` during startup makes it impossible to distinguish between a posture-gate failure and other fatal errors (e.g., port-in-use, config parse error). Operators cannot reliably detect whether the server refused to start due to a security posture violation versus a transient infrastructure issue.

## Implementation Intent
Catch `SystemExit` alongside `KeyboardInterrupt` in `run_http()` and log the failure reason before exiting. This preserves the existing posture-gate semantics (fail-closed on invalid posture) while ensuring consistent error handling across all launch paths.

## Requirements
- `REQ-001`: `MCPServer.run_http()` must catch `SystemExit` raised by `_enforce_startup_posture_gate()` and log the failure reason
- `REQ-002`: Active connections must be drained before process exit on `SystemExit`
- `REQ-003`: All MCP server launch paths must produce consistent error output on posture-gate failure

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/server.py | Modify | Add `SystemExit` handling to `run_http()` method | REQ-001, REQ-002 | Confirmed: `_enforce_startup_posture_gate()` at line 294 can propagate `SystemExit` from `_enforce_posture_gate()`; `except KeyboardInterrupt` at line 323 does not catch `SystemExit` (checked in Step 3) | Unit test for `run_http()` with `SystemExit` | Verified |
| tests/mcp_servers/test_mcp_server_base.py | Modify | Add unit test for `SystemExit` handling in `run_http()` | REQ-001, REQ-003 | Confirmed: test file exists at this path (checked in Step 3) | New test case | Verified |

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
| scripts/mcp_servers/file/delete_server.py | Verify `_enforce_posture_gate()` raises `SystemExit(1)` | REQ-001 |
| scripts/mcp_servers/file/write_server.py | Verify `_enforce_posture_gate()` raises `SystemExit(1)` | REQ-001 |
| scripts/mcp_servers/file/read_server.py | Verify `_enforce_posture_gate()` raises `SystemExit(1)` | REQ-001 |
| scripts/mcp_servers/mdq/mdq_server.py | Verify `_enforce_posture_gate()` raises `SystemExit(1)` | REQ-001 |
| scripts/mcp_servers/shell/shell_server.py | Verify `_enforce_posture_gate()` raises `SystemExit(1)` | REQ-001 |
| scripts/mcp_servers/web_search/web_search_server.py | Verify `_enforce_posture_gate()` raises `SystemExit(1)` | REQ-001 |
| scripts/mcp_servers/cicd/cicd_server.py | Verify `_enforce_posture_gate()` raises `SystemExit(1)` | REQ-001 |
| scripts/mcp_servers/github/github_server.py | Verify `_enforce_posture_gate()` raises `SystemExit(1)` | REQ-001 |
| scripts/mcp_servers/git/git_server.py | Verify `_enforce_posture_gate()` raises `SystemExit(1)` | REQ-001 |
| scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py | Verify `_enforce_posture_gate()` raises `SystemExit(1)` | REQ-001 |

## Acceptance Criteria
- `SystemExit(1)` raised during `run_http()` is caught and logged with the failure reason (REQ-001)
- Active connections are drained before process exit (REQ-002)
- All MCP server launch paths produce consistent error output (REQ-003)

## Tests
- Unit test: verify `run_http()` handles `SystemExit` from `_enforce_startup_posture_gate()` (REQ-001)
- Integration test: verify graceful shutdown on posture-gate failure (REQ-002)
- Regression test: ensure existing posture-gate failures still prevent HTTP bind (REQ-003)

## Documentation Impact
Update `MCPServer.run_http()` docstring to document the `SystemExit` handling behavior.

## Assumptions
- `SystemExit` should be caught at the `run_http()` level rather than having `_enforce_startup_posture_gate()` use a custom exception (simpler change, preserves backward compatibility)
- The existing `sys.exit(1)` after `server.run()` (line 326) does not need similar treatment — it is already in the normal shutdown path

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Should `SystemExit` be caught at the `run_http()` level or should `_enforce_startup_posture_gate()` use a custom exception? | Design decision not yet made | Review both options and decide based on consistency with existing error handling patterns | False |
| UNK-02 | Does the current `sys.exit(1)` after `server.run()` (line 326) also need similar treatment? | Need to verify if `server.run()` can raise `SystemExit` | Check uvicorn.Server.run() behavior | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/server.py | Modify | Low | N/A | N/A | No impact |

## Design
- **Approach**: Catch `SystemExit` alongside `KeyboardInterrupt` in `run_http()` and log the failure reason before re-raising or exiting. This is simpler than introducing a custom exception and preserves backward compatibility.
- **Rationale**: `SystemExit` is a built-in exception type that signals intentional process termination. Catching it allows us to perform cleanup (logging, connection draining) before the process exits, without changing the eventual outcome.
- **Alternative considered**: Having `_enforce_startup_posture_gate()` raise a custom exception (e.g., `SecurityPostureError`). This would allow more granular handling but requires changes to all 10 MCP server modules that define `_enforce_posture_gate()`, which is out of scope.

## Implementation steps
1. **Phase 1: Preparation**
   - [ ] Verify test file path exists under `tests/mcp_servers/` (Requirement ID: REQ-001; File Path: tests/mcp_servers/test_server.py)
2. **Phase 2: Core Logic Implementation**
   - [ ] Add `SystemExit` handling to `MCPServer.run_http()` — catch `SystemExit` alongside `KeyboardInterrupt`, log the failure reason, and call `sys.exit()` with the original exit code (Requirement ID: REQ-001; File Path: scripts/mcp_servers/server.py)
   - [ ] Update `MCPServer.run_http()` docstring to document the `SystemExit` handling behavior (Requirement ID: REQ-003; File Path: scripts/mcp_servers/server.py)
3. **Phase 3: Testing & Verification**
   - [ ] Add unit test: verify `run_http()` catches `SystemExit` from `_enforce_startup_posture_gate()` and logs the failure reason (Requirement ID: REQ-001; File Path: tests/mcp_servers/test_server.py)
   - [ ] Run lint/type checks on modified files (Requirement ID: REQ-001; File Path: scripts/mcp_servers/server.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/server.py | Unit test | uv run pytest tests/mcp_servers/test_server.py -v | Test passes; SystemExit is caught and logged |
| scripts/mcp_servers/server.py | Lint check | uv run ruff check scripts/mcp_servers/server.py | Clean (no findings) |
| scripts/mcp_servers/server.py | Type check | uv run mypy scripts/mcp_servers/server.py | Clean (no type errors) |

## Risks
- **Risk**: Catching `SystemExit` may mask unintended `SystemExit` calls from other parts of `run_http()` → **Mitigation**: Only catch `SystemExit` and re-raise it after logging; do not suppress it silently
- **Risk**: Connection draining may not complete before `sys.exit()` is called → **Mitigation**: Use `server.should_exit = True` to signal uvicorn to shut down gracefully before calling `sys.exit()`

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation — verify test file path | Pending | — | — | |
| 2 | Phase 2: Core Logic — add SystemExit handling to run_http() | Pending | — | — | |
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
- **Source issue**: issues/20261026-220730_mcp001_systemexit-not-caught-by-run_http.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261026-222848
- **Related target files**: scripts/mcp_servers/server.py

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue Section | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem, Required Changes | scripts/mcp_servers/server.py | Phase 2 | SystemExit caught and logged | Unit test for run_http() | Confirmed by repository evidence |
| REQ-002 | Problem, Acceptance Criteria | scripts/mcp_servers/server.py | Phase 2 | Connections drained before exit | Integration test | Needs confirmation |
| REQ-003 | Reason for Change, Acceptance Criteria | scripts/mcp_servers/server.py | Phase 3 | Consistent error output | Regression test | Needs confirmation |
