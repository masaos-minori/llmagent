# Implementation Procedure: Modify git_server.py

## Goal

Update `call_tool` endpoint handler to instantiate `RepositoryState` once per request; pass `RepositoryState` through pipeline stages; update tool response serialization.

## Scope

- Update `call_tool` endpoint handler to instantiate `RepositoryState` once per request
- Pass `RepositoryState` through pipeline stages
- Update tool response serialization

## Assumptions

1. `RepositoryState` module exists and is importable
2. Existing `call_tool` handler can be updated without breaking HTTP endpoint contract
3. Tool response serialization remains consistent after migration

## Design decisions

- `call_tool` handler instantiates `RepositoryState` once per request
- `RepositoryState` instance is passed through pipeline stages
- Tool response serialization uses `RepositoryState` metadata for structured output

## Alternatives considered

- Keep `call_tool` accepting `git.Repo`: Would require maintaining both interfaces; cleaner to migrate fully
- Create separate `call_toolV2` handler: Would duplicate code; updating existing handler is simpler
- Pass both `RepositoryState` and `git.Repo`: Would defeat the purpose of eliminating duplicate instantiation

## Implementation

### Target file

`scripts/mcp_servers/git/git_server.py`

### Procedure

1. Import `RepositoryState` from `repository_state` module
2. Update `call_tool` endpoint handler to instantiate `RepositoryState` once per request
3. Pass `RepositoryState` through pipeline stages
4. Update tool response serialization

### Method

#### Step 1: Add imports

```python
from mcp_servers.git.repository_state import RepositoryState, WriteProtectionPipeline
```

#### Step 2: Update `call_tool` endpoint handler

Current body (lines 120-146):
```python
tool_name = req.tool_name
if tool_name == "git_checkout":
    ...
elif tool_name == "git_pull":
    ...
elif tool_name == "git_push":
    ...
else:
    return JSONResponse(status_code=400, content={"error": f"Unknown tool: {tool_name}"})
```

Replace with:
```python
tool_name = req.tool_name
try:
    # Instantiate RepositoryState once per request
    repo_path = req.repo_path
    state = RepositoryState.snapshot(repo_path)
    
    # Determine operation based on tool name
    if tool_name == "git_checkout":
        op = lambda: self._format_checkout(state, req)
    elif tool_name == "git_pull":
        op = lambda: self._format_pull(state, req)
    elif tool_name == "git_push":
        op = lambda: self._format_push(state, req)
    else:
        return JSONResponse(status_code=400, content={"error": f"Unknown tool: {tool_name}"})
    
    # Execute through WriteProtectionPipeline
    pipeline = WriteProtectionPipeline(state)
    result = pipeline.run(tool_name, op)
    
    # Serialize response with RepositoryState metadata
    return JSONResponse(content={
        "status": "success",
        "output": result.output,
        "repository_state": {
            "path": state.path,
            "is_dirty": state.is_dirty,
            "head_type": state.head_type,
            "active_branch": state.active_branch,
            "untracked_file_count": state.untracked_file_count,
            "protected_branch": state.protected_branch,
            "ref_valid": state.ref_valid,
        },
    })
except GitServiceError as e:
    return JSONResponse(status_code=400, content={"error": str(e)})
```

#### Step 3: Add helper methods for formatting

In `GitMCPHandler`, add private methods that delegate to `format_*` functions:

```python
def _format_checkout(self, state: RepositoryState, req: GitCheckoutRequest) -> str:
    """Delegate to format_checkout with RepositoryState."""
    return format_checkout(state, req, allow_detached_head=self.allow_detached_head)

def _format_pull(self, state: RepositoryState, req: GitPullRequest) -> str:
    """Delegate to format_pull with RepositoryState."""
    return format_pull(state, req)

def _format_push(self, state: RepositoryState, req: GitPushRequest) -> str:
    """Delegate to format_push with RepositoryState."""
    return format_push(state, req)
```

### Details

- `RepositoryState.snapshot()` captures full state from a single `git.Repo` query
- `WriteProtectionPipeline.run()` orchestrates all 9 stages
- Response includes `repository_state` metadata for observability
- `GitServiceError` exceptions are caught and returned as 400 responses

## Compatibility considerations

- `call_tool` handler now requires `repo_path` field in request
- Response includes additional `repository_state` metadata field
- `allow_detached_head` configuration must be set on `GitMCPHandler` instance

## Security considerations

- Frozen dataclass immutability must hold under all code paths
- `RepositoryState._repo` weak reference must not prevent garbage collection
- Pipeline early-exit must not skip required audit entries
- Option-injection prevention via `_is_safe_ref()` must be enforced before any `git.Repo` query

## Rollback considerations

- If `RepositoryState` causes behavioral regression, revert callers to direct `git.Repo` queries
- If removed methods are still needed temporarily, restore them as delegation wrappers

## Validation plan

- Verify existing test suite passes without modification (behavioral equivalence)
- Compare output of old vs new guards on identical inputs
- Verify pipeline ordering: Stage 4 → Stage 5 → Stage 6 → Stage 7
- Verify no behavioral regression in dirty-worktree, detached-HEAD, or protected-branch checks

## Completion criteria

- [ ] All write-protection guards use `RepositoryState` exclusively — zero direct `git.Repo` queries in guard logic
- [ ] Pipeline ordering verified via test: Stage 4 → Stage 5 → Stage 6 → Stage 7
- [ ] Existing test suite passes without modification (behavioral equivalence)
- [ ] No behavioral regression in dirty-worktree, detached-HEAD, or protected-branch checks
- [ ] Lint/type check passes: `ruff check scripts/mcp_servers/git/` and `mypy scripts/mcp_servers/git/`

## Out of scope

- GitHub MCP's existing `protected_branches`/force-push handling (already implemented separately)
- Redesign of Agent-side approval risk-tier mapping (tracked separately as Known Issue MCP-004)
- Any capability to allow Force Push, even as an administrative feature

## execution_status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-006
- **Source issue**: issues/20260828-162303_mcp003_git_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-134950_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-134950
- **Related target files**: scripts/mcp_servers/git/git_server.py
