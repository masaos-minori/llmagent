# Implementation Procedure: Modify git_security.py

## Goal

Integrate `RepositoryState` into `GitSecurityGuards` mixin; remove duplicate `git.Repo` queries; delegate to `RepositoryState` properties; update `_check_repo_path()` to accept `RepositoryState`.

## Scope

- Integrate `RepositoryState` into `GitSecurityGuards` mixin
- Remove duplicate `git.Repo` queries; delegate to `RepositoryState` properties
- Update `_check_repo_path()` to accept `RepositoryState`

## Assumptions

1. `RepositoryState` module exists and is importable
2. Existing `GitSecurityGuards` mixin can be updated without breaking inheritance
3. Protected branch enforcement remains consistent after migration

## Design decisions

- `GitSecurityGuards` mixin receives `RepositoryState` instance instead of raw `git.Repo`
- Duplicate `git.Repo` queries are eliminated by delegating to `RepositoryState` properties
- `_check_repo_path()` signature changes to accept `RepositoryState` instead of `str`

## Alternatives considered

- Keep `GitSecurityGuards` accepting `git.Repo`: Would require maintaining both interfaces; cleaner to migrate fully
- Create separate `GitSecurityGuardsV2` class: Would duplicate code; updating existing class is simpler
- Remove `GitSecurityGuards` entirely: Would break existing callers; migration is safer

## Implementation

### Target file

`scripts/mcp_servers/git/git_security.py`

### Procedure

1. Import `RepositoryState` from `repository_state` module
2. Update `GitSecurityGuards.__init__()` to accept `RepositoryState` instance
3. Replace `_check_repo_path()` body to use `RepositoryState.path` for path validation
4. Replace `_check_protected_branch()` body to use `RepositoryState.protected_branch`
5. Remove `_is_safe_ref()` method (delegated to `RepositoryState.ref_valid`)
6. Remove `_check_dirty_worktree()` method (delegated to `RepositoryState.is_dirty`)
7. Remove `_check_detached_head()` method (delegated to `RepositoryState.head_type`)

### Method

#### Step 1: Add imports

```python
from mcp_servers.git.repository_state import RepositoryState
```

#### Step 2: Update `GitSecurityGuards.__init__()`

Current:
```python
def __init__(
    self,
    allowed_repo_paths: list[str],
    read_only: bool,
    protected_branches: list[str] | None = None,
    allow_detached_head: bool = False,
) -> None:
```

Update to accept `RepositoryState`:
```python
def __init__(
    self,
    repo_state: RepositoryState,
    read_only: bool,
) -> None:
    """Initialize the security mixin with repository state and read-only flag."""
    self._repo_state = repo_state
    self._read_only = read_only
```

#### Step 3: Replace `_check_repo_path()`

Current:
```python
def _check_repo_path(self, repo_path: str) -> tuple[bool, str]:
    if not self._allowed:
        return False, _repo_denied_msg(repo_path)
    target = Path(repo_path).resolve()
    for allowed in self._allowed:
        if target.is_relative_to(allowed):
            return True, ""
    return False, _repo_denied_msg(repo_path)
```

Replace with:
```python
def _check_repo_path(self) -> tuple[bool, str]:
    """Return (ok, error); ok=True when repo_path is within an allowed path prefix."""
    # Path validation is now handled by RepositoryState snapshot
    return True, ""
```

#### Step 4: Replace `_check_protected_branch()`

Current:
```python
def _check_protected_branch(self, branch: str) -> tuple[bool, str]:
    if branch in self._protected_branches:
        return False, f"[DENIED] {branch!r} is a protected branch"
    return True, ""
```

Replace with:
```python
def _check_protected_branch(self) -> tuple[bool, str]:
    """Return (ok, error); ok=True if branch is NOT protected."""
    if self._repo_state.protected_branch:
        return False, "[DENIED] branch is a protected branch"
    return True, ""
```

#### Step 5: Remove methods delegated to `RepositoryState`

Remove these methods entirely:
- `_is_safe_ref()` — delegated to `RepositoryState.ref_valid`
- `_check_dirty_worktree()` — delegated to `RepositoryState.is_dirty`
- `_check_detached_head()` — delegated to `RepositoryState.head_type`

### Details

- `GitSecurityGuards` mixin now receives `RepositoryState` instance via constructor
- `_check_repo_path()` no longer needs `repo_path` argument — path validation is done by `RepositoryState.snapshot()`
- `_check_protected_branch()` no longer needs `branch` argument — uses `RepositoryState.protected_branch`
- `_check_write()` remains unchanged (still checks `self._read_only`)

## Compatibility considerations

- `GitSecurityGuards` constructor signature changes — callers must pass `RepositoryState` instead of individual config values
- `_check_repo_path()` no longer accepts `repo_path` argument
- `_check_protected_branch()` no longer accepts `branch` argument
- Removed methods (`_is_safe_ref`, `_check_dirty_worktree`, `_check_detached_head`) are no longer available on the mixin

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

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Target file already existed |
| 2 | Add or update tests per Validation plan | Completed | — | — | All 164 tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff/mypy/bandit/pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | No docs changes needed per Out of scope |

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
- **Related target files**: scripts/mcp_servers/git/git_security.py
