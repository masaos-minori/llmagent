# Implementation Procedure: Modify git_service.py

## Goal

Replace scattered `git.Repo` queries in `git_service.py` with `RepositoryState` property access; update dispatch table factory to instantiate `RepositoryState` once per request; deprecate `RepoValidationResult` in favor of `RepositoryState`.

## Scope

- Replace `_check_dirty_worktree()` / `_check_detached_head()` with `RepositoryState` property access
- Update dispatch table factory to instantiate `RepositoryState` once
- Deprecate `RepoValidationResult` in favor of `RepositoryState`

## Assumptions

1. `RepositoryState` module exists and is importable
2. Existing `RepoValidationResult` can be deprecated but not removed until all callers are migrated
3. Pipeline ordering conflicts with current check ordering must respect existing guard precedence

## Design decisions

- `RepositoryState` instance is created once per request in the dispatch table factory
- Existing guard methods delegate to `RepositoryState` properties rather than being replaced wholesale
- `RepoValidationResult` is deprecated with a warning, not removed immediately

## Alternatives considered

- Remove `RepoValidationResult` entirely: Would break existing callers; deprecation provides migration window
- Inline `RepositoryState` creation in each handler: Would duplicate instantiation; factory pattern centralizes it
- Replace all guard methods wholesale: Would break backward compatibility; delegation preserves existing API

## Implementation

### Target file

`scripts/mcp_servers/git/git_service.py`

### Procedure

1. Import `RepositoryState` from `repository_state` module
2. Replace `_check_dirty_worktree()` with `RepositoryState.is_dirty` property access
3. Replace `_check_detached_head()` with `RepositoryState.head_type` property access
4. Update dispatch table factory to instantiate `RepositoryState` once per request
5. Deprecate `RepoValidationResult` with a warning
6. Update `_run_tool()` to pass `RepositoryState` through pipeline stages

### Method

#### Step 1: Add imports

```python
from mcp_servers.git.repository_state import RepositoryState, WriteProtectionPipeline
```

#### Step 2: Replace `_check_dirty_worktree()`

Current implementation (line ~248 in git_service.py):
```python
ok, err = self._check_dirty_worktree(repo)
if not ok:
    return err
```

Replace with:
```python
state = RepositoryState.snapshot(req.repo_path)
if state.is_dirty:
    return "[DENIED] worktree has uncommitted changes (dirty worktree)"
```

#### Step 3: Replace `_check_detached_head()`

Current implementation (line ~251 in git_service.py):
```python
ok, err = self._check_detached_head(repo)
if not ok:
    return err
```

Replace with:
```python
if state.head_type == "detached" and not self._allow_detached_head:
    return "[DENIED] repository is in a detached HEAD state"
```

#### Step 4: Update dispatch table factory

In `_run_tool()`, replace:
```python
repo = self._open_repo(repo_path)
return self._wrap_git_op(tool_name, lambda: op(repo))
```

With:
```python
state = RepositoryState.snapshot(repo_path)
pipeline = WriteProtectionPipeline(state)
result = pipeline.run(tool_name, lambda: op(state._repo))
return result.output
```

#### Step 5: Deprecate `RepoValidationResult`

Add deprecation warning:
```python
import warnings

warnings.warn(
    "RepoValidationResult is deprecated; use RepositoryState instead",
    DeprecationWarning,
    stacklevel=2,
)
```

### Details

- In `git_checkout` handler (lines 231-258), replace the two guard calls with `RepositoryState` property access
- In `git_pull` handler (lines 260-288), same replacement pattern
- In `git_push` handler (lines 290-310), same replacement pattern
- `_validate_protected()` delegates to `RepositoryState.protected_branch` property
- `_validate_ref()` delegates to `RepositoryState.ref_valid` property

## Compatibility considerations

- `RepoValidationResult` is deprecated but still functional during migration period
- `format_checkout/pull/push` signatures change to accept `RepositoryState` instead of `git.Repo`
- Existing callers of `_check_dirty_worktree()` and `_check_detached_head()` will receive deprecation warnings

## Security considerations

- Pipeline order conflicts with current check ordering in at least one place — Stage 5 precondition must respect existing guard precedence
- Frozen dataclass immutability must hold under all code paths
- `RepositoryState._repo` weak reference must not prevent garbage collection
- Pipeline early-exit must not skip required audit entries

## Rollback considerations

- If `RepositoryState` causes behavioral regression, revert callers to direct `git.Repo` queries
- If `RepoValidationResult` deprecation breaks existing callers, remove deprecation warning temporarily

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Complete | 2026-08-30 | 2026-08-30 | Pipeline already partially migrated; fixed `_run_tool` to return `pipeline_result.rejection_message` on failure |
| 2 | Add or update tests per Validation plan | Complete | 2026-08-30 | 2026-08-30 | Fixed `test_git_service_dispatch.py`: `snap.repo` → `snap._repo` in `test_dry_run_fetch` and `test_pull_result` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Complete | 2026-08-30 | 2026-08-30 | ruff check ✓, mypy ✓, compileall ✓, pytest 155 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Complete | 2026-08-30 | 2026-08-30 | N/A — no docs changed |

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
- **Requirement ID**: REQ-001, REQ-003, REQ-006
- **Source issue**: issues/20260828-162303_mcp003_git_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-134950_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-134950
- **Related target files**: scripts/mcp_servers/git/git_service.py
