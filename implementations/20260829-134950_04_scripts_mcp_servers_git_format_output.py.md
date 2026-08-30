# Implementation Procedure: Modify format_output.py

## Goal

Change `format_checkout/pull/push` signatures to accept `RepositoryState` instead of `git.Repo`; use `state.is_dirty`, `state.active_branch`, `state.untracked_file_count` instead of `repo.*` calls.

## Scope

- Change `format_checkout/pull/push` signatures to accept `RepositoryState` instead of `git.Repo`
- Use `state.is_dirty`, `state.active_branch`, `state.untracked_file_count` instead of `repo.*` calls

## Assumptions

1. `RepositoryState` module exists and is importable
2. Existing `format_*` functions can be updated without breaking other callers
3. Postcondition verification in `format_checkout` remains consistent after migration

## Design decisions

- `format_*` functions receive `RepositoryState` instance instead of raw `git.Repo`
- Direct `repo.*` calls are replaced with `state.*` property access
- Postcondition verification in `format_checkout` uses `state.active_branch` instead of `repo.active_branch.name`

## Alternatives considered

- Keep `format_*` accepting `git.Repo`: Would require maintaining both interfaces; cleaner to migrate fully
- Create separate `format_*V2` functions: Would duplicate code; updating existing functions is simpler
- Pass both `RepositoryState` and `git.Repo`: Would defeat the purpose of eliminating duplicate instantiation

## Implementation

### Target file

`scripts/mcp_servers/git/format_output.py`

### Procedure

1. Import `RepositoryState` from `repository_state` module
2. Update `format_checkout()` signature to accept `RepositoryState` instead of `git.Repo`
3. Update `format_pull()` signature to accept `RepositoryState` instead of `git.Repo`
4. Update `format_push()` signature to accept `RepositoryState` instead of `git.Repo`
5. Replace `repo.*` calls with `state.*` property access in each function

### Method

#### Step 1: Add imports

```python
from mcp_servers.git.repository_state import RepositoryState
```

#### Step 2: Update `format_checkout()`

Current signature:
```python
def format_checkout(
    repo: git.Repo, req: GitCheckoutRequest, *, allow_detached_head: bool = False
) -> str:
```

Update to:
```python
def format_checkout(
    state: RepositoryState, req: GitCheckoutRequest, *, allow_detached_head: bool = False
) -> str:
```

Current body (lines 122-142):
```python
if req.dry_run:
    action = (
        f"create and checkout '{req.branch}'"
        if req.create
        else f"checkout '{req.branch}'"
    )
    return f"[DRY RUN] Would {action}"
if req.create:
    new_branch = repo.create_head(req.branch)
    new_branch.checkout()
else:
    repo.git.checkout("--", req.branch)
if repo.active_branch.name != req.branch or (
    not allow_detached_head and repo.head.is_detached
):
    raise GitServiceError(...)
return f"Switched to branch '{req.branch}'"
```

Replace with:
```python
if req.dry_run:
    action = (
        f"create and checkout '{req.branch}'"
        if req.create
        else f"checkout '{req.branch}'"
    )
    return f"[DRY RUN] Would {action}"
if req.create:
    new_branch = state._repo.create_head(req.branch)
    new_branch.checkout()
else:
    state._repo.git.checkout("--", req.branch)
if state.active_branch != req.branch or (
    not allow_detached_head and state.head_type == "detached"
):
    raise GitServiceError(
        f"checkout postcondition failed: expected branch {req.branch!r}, "
        f"got {'<detached HEAD>' if state.head_type == 'detached' else state.active_branch!r}"
    )
return f"Switched to branch '{req.branch}'"
```

#### Step 3: Update `format_pull()`

Current signature:
```python
def format_pull(repo: git.Repo, req: GitPullRequest) -> str:
```

Update to:
```python
def format_pull(state: RepositoryState, req: GitPullRequest) -> str:
```

Current body (lines 145-160):
```python
if req.dry_run:
    fetch_info = repo.git.fetch("--dry-run", req.remote)
    return f"[DRY RUN] fetch --dry-run result:\n{fetch_info or '(nothing to commit)'}"
pull_args = [req.remote]
if req.branch:
    pull_args.extend(["--", req.branch])
result = repo.git.pull(*pull_args)
if repo.index.unmerged_blobs():
    raise GitServiceError("pull postcondition failed: unresolved merge conflicts remain")
return result or "Already up to date."
```

Replace with:
```python
if req.dry_run:
    fetch_info = state._repo.git.fetch("--dry-run", req.remote)
    return f"[DRY RUN] fetch --dry-run result:\n{fetch_info or '(nothing to commit)'}"
pull_args = [req.remote]
if req.branch:
    pull_args.extend(["--", req.branch])
result = state._repo.git.pull(*pull_args)
if state._repo.index.unmerged_blobs():
    raise GitServiceError("pull postcondition failed: unresolved merge conflicts remain")
return result or "Already up to date."
```

#### Step 4: Update `format_push()`

Current signature:
```python
def format_push(repo: git.Repo, req: GitPushRequest) -> str:
```

Update to:
```python
def format_push(state: RepositoryState, req: GitPushRequest) -> str:
```

Current body (lines 163-174):
```python
branch = req.branch or repo.active_branch.name
if req.dry_run:
    return f"[DRY RUN] Would push branch '{branch}' to '{req.remote}'"
result = repo.git.push(req.remote, "--", branch)
_rejection_markers = ("[rejected]", "non-fast-forward", "failed to push")
if result and any(m in result for m in _rejection_markers):
    raise GitServiceError(...)
return result or f"Pushed '{branch}' to '{req.remote}'"
```

Replace with:
```python
branch = req.branch or state.active_branch
if req.dry_run:
    return f"[DRY RUN] Would push branch '{branch}' to '{req.remote}'"
result = state._repo.git.push(req.remote, "--", branch)
_rejection_markers = ("[rejected]", "non-fast-forward", "failed to push")
if result and any(m in result for m in _rejection_markers):
    raise GitServiceError(...)
return result or f"Pushed '{branch}' to '{req.remote}'"
```

### Details

- `state._repo` provides access to the underlying `git.Repo` for operations that need it
- `state.active_branch` replaces `repo.active_branch.name`
- `state.head_type` replaces `repo.head.is_detached` checks
- `state.untracked_file_count` replaces `len(repo.untracked_files)` where applicable

## Compatibility considerations

- `format_checkout/pull/push` signatures change to accept `RepositoryState` instead of `git.Repo`
- Callers must pass `RepositoryState` instance instead of `git.Repo`
- `state._repo` provides access to underlying `git.Repo` for operations that need it

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260828-162303_mcp003_git_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-134950_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-134950
- **Related target files**: scripts/mcp_servers/git/format_output.py
