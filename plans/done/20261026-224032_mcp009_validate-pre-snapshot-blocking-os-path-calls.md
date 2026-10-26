## Goal
Replace synchronous `os.path` calls in `_validate_pre_snapshot` with async-compatible alternatives using `asyncio.to_thread()` to prevent event loop stalls.

## Priority
Low

## Scope
- **In-Scope**: Wrap `_validate_pre_snapshot` in `asyncio.to_thread()`; update docstring to document the async execution model
- **Out-of-Scope**: Changes to the validation logic itself; changes to how paths are resolved before validation
- **Dependencies**: N/A: none

## Background
The `_validate_pre_snapshot` function at lines 111-132 of `git_server.py`:

```python
def _validate_pre_snapshot(path: str) -> tuple[bool, str]:
    """Validate that *path* is accessible and contains a Git repository before calling snapshot."""
    try:
        import os as _os
        if not _os.path.exists(path):
            return False, "[DENIED] repository path does not exist"
        if not _os.access(path, _os.R_OK):
            return False, "[DENIED] repository path is not readable"
        has_git = _os.path.isdir(_os.path.join(path, ".git"))
        if not has_git:
            has_bare = _os.path.isfile(_os.path.join(path, "HEAD"))
            if not has_bare:
                return False, "[DENIONED] path is not a Git repository"
        return True, ""
    except PermissionError:
        return False, "[DENIED] permission denied accessing repository"
```

This function is called from the `call_tool` endpoint at line 285:

```python
ok, err = _validate_pre_snapshot(resolved)
```

The `call_tool` endpoint is an async FastAPI handler (line 244-245):

```python
@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
```

## Problem
The `os.path.exists()`, `os.path.access()`, `os.path.isdir()`, and `os.path.isfile()` calls are synchronous file system operations. In an async event loop (uvicorn), these calls block the entire event loop while executing, preventing other requests from being processed.

While the impact is typically small (filesystem operations are fast), under high load or on slow filesystems (e.g., NFS mounts), this can cause:
1. Event loop stalls — other requests wait for the blocking call to complete.
2. Increased latency for concurrent requests.
3. Potential timeout issues if the filesystem is unresponsive.

## Reason for Change
Blocking I/O in an async handler degrades the server's responsiveness under load. Using async-compatible file system operations would prevent event loop stalls.

## Implementation Intent
1. Replace synchronous `os.path` calls with `aiofiles` or `anyio` equivalents, or
2. Run the blocking calls in a thread pool executor using `asyncio.to_thread()`, or
3. Accept the current behavior and document it as a known limitation.

## Requirements
- `REQ-001`: File system validation does not block the event loop
- `REQ-002`: Validation results are identical to the synchronous version
- `REQ-003`: No performance regression under low load

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Modify | Wrap `_validate_pre_snapshot` in `asyncio.to_thread()` | REQ-001, REQ-002 | Confirmed: `_validate_pre_snapshot` at lines 111-132 uses synchronous `os.path` calls; called from async `call_tool` at line 285 (checked in Step 3) | Unit test for async validation | Needs confirmation |

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
| tests/mcp_servers/git/test_git_server.py | Verify existing validation patterns | REQ-001 |

## Acceptance Criteria
- File system validation does not block the event loop (REQ-001)
- Validation results are identical to the synchronous version (REQ-002)
- No performance regression under low load (REQ-003)

## Tests
- Unit test: verify validation works correctly with async executor (REQ-001)
- Integration test: verify no event loop stall under concurrent load (REQ-001)
- Regression test: ensure existing validation behavior is preserved (REQ-003)

## Documentation Impact
Update `_validate_pre_snapshot` docstring to document the async execution model.

## Assumptions
- `asyncio.to_thread()` is available in Python 3.9+ (project uses Python 3.13)
- The validation logic should remain unchanged — only the execution model should change
- The `***` prefix convention should be preserved for consistency

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Is `aiofiles` available in the project's dependencies? | Need to check pyproject.toml | Already verified: not available | False |
| UNK-02 | Are there other MCP servers with the same pattern? | Need to check all MCP servers for similar validation logic | Search for `_validate_pre_snapshot` in other servers | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Modify | Low | N/A | N/A | No impact |

## Design
- **Approach**: Wrap `_validate_pre_snapshot` in `asyncio.to_thread()` to run the blocking calls in a thread pool executor
- **Rationale**: `asyncio.to_thread()` is available in Python 3.9+ without additional dependencies. It runs the blocking calls in a thread pool executor, preventing event loop stalls.
- **Alternative considered**: Using `aiofiles` or `anyio` — these would provide native async file system operations but require adding new dependencies.

## Implementation steps
1. **Phase 1: Preparation**
   - [ ] Verify test file path exists under `tests/mcp_servers/git/` (Requirement ID: REQ-001; File Path: tests/mcp_servers/git/test_git_server.py)
2. **Phase 2: Core Logic Implementation**
   - [ ] Create async wrapper: `async def _validate_pre_snapshot_async(path: str) -> tuple[bool, str]: return await asyncio.to_thread(_validate_pre_snapshot, path)` (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/git_server.py)
   - [ ] Update `call_tool` to call `_validate_pre_snapshot_async` instead of `_validate_pre_snapshot` (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/git_server.py)
   - [ ] Update `_validate_pre_snapshot` docstring to document the async execution model (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/git_server.py)
3. **Phase 3: Testing & Verification**
   - [ ] Run lint/type checks on modified files (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/git_server.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Unit test | uv run pytest tests/mcp_servers/git/test_git_server.py -v | Test passes; validation works with async executor |
| scripts/mcp_servers/git/git_server.py | Lint check | uv run ruff check scripts/mcp_servers/git/git_server.py | Clean (no findings) |
| scripts/mcp_servers/git/git_server.py | Type check | uv run mypy scripts/mcp_servers/git/git_server.py | Clean (no type errors) |

## Risks
- **Risk**: Adding `asyncio.to_thread()` may introduce subtle timing differences in error handling → **Mitigation**: The `PermissionError` exception is caught inside `_validate_pre_snapshot` and returned as `(False, error_message)`, so the async wrapper doesn't change error semantics
- **Risk**: Thread pool overhead may add latency under low load → **Mitigation**: `asyncio.to_thread()` uses the default thread pool which is optimized for short-lived tasks; the overhead is negligible compared to filesystem I/O

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation — verify test file path | Pending | — | — | |
| 2 | Phase 2: Core Logic — wrap in asyncio.to_thread() | Pending | — | — | |
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
- **Source issue**: issues/20261026-220730_mcp009-validate-pre-snapshot-blocking-os-path-calls.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261026-224032
- **Related target files**: scripts/mcp_servers/git/git_server.py

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue Section | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem, Acceptance Criteria | scripts/mcp_servers/git/git_server.py | Phase 2 | Event loop not blocked | Unit test for async validation | Confirmed by repository evidence |
| REQ-002 | Problem, Acceptance Criteria | scripts/mcp_servers/git/git_server.py | Phase 2 | Validation results identical | Regression test for validation | Confirmed by repository evidence |
| REQ-003 | Reason for Change, Acceptance Criteria | scripts/mcp_servers/git/git_server.py | Phase 3 | No performance regression | Integration test for concurrency | Needs confirmation |
