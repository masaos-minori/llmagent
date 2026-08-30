# Implementation Procedure: Modify dispatch.py

## Goal

Update `DispatchResult` dataclass to include `RepositoryState` metadata; update `dispatch_tool()` to pass `RepositoryState` through pipeline stages; update `_to_call_tool_response()` serialization.

## Scope

- Update `DispatchResult` dataclass to include `RepositoryState` metadata
- Update `dispatch_tool()` to pass `RepositoryState` through pipeline stages
- Update `_to_call_tool_response()` serialization

## Assumptions

1. `RepositoryState` module exists and is importable
2. Existing `DispatchResult` dataclass can be extended without breaking other callers
3. `_to_call_tool_response()` serialization can be updated without breaking HTTP endpoint contract

## Design decisions

- `DispatchResult` gains a `repository_state` field for metadata
- `dispatch_tool()` passes `RepositoryState` instance through pipeline stages
- `_to_call_tool_response()` serializes `repository_state` metadata for observability

## Alternatives considered

- Keep `DispatchResult` unchanged: Would require importing `RepositoryState` elsewhere; cleaner to centralize
- Create separate `DispatchResultV2` class: Would duplicate code; updating existing class is simpler
- Pass both `RepositoryState` and `git.Repo`: Would defeat the purpose of eliminating duplicate instantiation

## Implementation

### Target file

`scripts/mcp_servers/dispatch.py`

### Procedure

1. Import `RepositoryState` from `repository_state` module
2. Update `DispatchResult` dataclass to include `RepositoryState` metadata
3. Update `dispatch_tool()` to pass `RepositoryState` through pipeline stages
4. Update `_to_call_tool_response()` serialization

### Method

#### Step 1: Add imports

```python
from mcp_servers.git.repository_state import RepositoryState
```

#### Step 2: Update `DispatchResult` dataclass

Current definition (line ~10):
```python
@dataclass(frozen=True)
class DispatchResult:
    status: Literal["success", "error"]
    output: str
    error: str | None = None
```

Update to:
```python
@dataclass(frozen=True)
class DispatchResult:
    status: Literal["success", "error"]
    output: str
    error: str | None = None
    repository_state: RepositoryState | None = None
```

#### Step 3: Update `dispatch_tool()`

Current body (lines 40-80):
```python
def dispatch_tool(
    tool_name: str,
    params: dict[str, Any],
    *,
    read_only: bool,
    allowed_repo_paths: list[str] | None = None,
    protected_branches: list[str] | None = None,
    allow_detached_head: bool = False,
) -> DispatchResult:
    ...
    repo = git.Repo(repo_path)
    ...
    if tool_name == "git_checkout":
        result = format_checkout(repo, req, allow_detached_head=allow_detached_head)
    elif tool_name == "git_pull":
        result = format_pull(repo, req)
    elif tool_name == "git_push":
        result = format_push(repo, req)
    else:
        return DispatchResult("error", "", f"Unknown tool: {tool_name}")
    ...
```

Replace with:
```python
def dispatch_tool(
    tool_name: str,
    params: dict[str, Any],
    *,
    read_only: bool,
    allowed_repo_paths: list[str] | None = None,
    protected_branches: list[str] | None = None,
    allow_detached_head: bool = False,
) -> DispatchResult:
    # Instantiate RepositoryState once per request
    repo_path = params.get("repo_path")
    if not repo_path:
        return DispatchResult("error", "", "Missing repo_path parameter")
    
    state = RepositoryState.snapshot(repo_path)
    
    # Determine operation based on tool name
    if tool_name == "git_checkout":
        req = GitCheckoutRequest(**params)
        op = lambda: format_checkout(state, req, allow_detached_head=allow_detached_head)
    elif tool_name == "git_pull":
        req = GitPullRequest(**params)
        op = lambda: format_pull(state, req)
    elif tool_name == "git_push":
        req = GitPushRequest(**params)
        op = lambda: format_push(state, req)
    else:
        return DispatchResult("error", "", f"Unknown tool: {tool_name}")
    
    # Execute through WriteProtectionPipeline
    pipeline = WriteProtectionPipeline(state)
    result = pipeline.run(tool_name, op)
    
    return DispatchResult(
        status="success",
        output=result.output,
        repository_state=state,
    )
```

#### Step 4: Update `_to_call_tool_response()` serialization

Current body (lines 80-100):
```python
def _to_call_tool_response(result: DispatchResult) -> JSONResponse:
    if result.status == "success":
        return JSONResponse(content={"status": "success", "output": result.output})
    return JSONResponse(status_code=400, content={"error": result.error})
```

Update to:
```python
def _to_call_tool_response(result: DispatchResult) -> JSONResponse:
    if result.status == "success":
        response: dict[str, Any] = {"status": "success", "output": result.output}
        if result.repository_state is not None:
            response["repository_state"] = {
                "path": result.repository_state.path,
                "is_dirty": result.repository_state.is_dirty,
                "head_type": result.repository_state.head_type,
                "active_branch": result.repository_state.active_branch,
                "untracked_file_count": result.repository_state.untracked_file_count,
                "protected_branch": result.repository_state.protected_branch,
                "ref_valid": result.repository_state.ref_valid,
            }
        return JSONResponse(content=response)
    return JSONResponse(status_code=400, content={"error": result.error})
```

### Details

- `RepositoryState.snapshot()` captures full state from a single `git.Repo` query
- `WriteProtectionPipeline.run()` orchestrates all 9 stages
- Response includes `repository_state` metadata for observability
- `DispatchResult` gains optional `repository_state` field for backward compatibility

## Compatibility considerations

- `DispatchResult` gains optional `repository_state` field — existing consumers are unaffected
- `_to_call_tool_response()` adds `repository_state` metadata to success responses
- Backward compatibility: existing callers of `dispatch_tool()` are unaffected

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
- **Related target files**: scripts/mcp_servers/dispatch.py
