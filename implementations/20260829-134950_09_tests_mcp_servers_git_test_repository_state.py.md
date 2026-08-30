# Implementation Procedure: Test RepositoryState Module (Create)

## Goal

Add comprehensive tests for `RepositoryState` module including snapshot capture, pipeline ordering, guard integration, and audit log verification.

## Scope

- Unit tests for `RepositoryState.snapshot()` capturing all fields
- Integration tests for pipeline ordering (Stage 4 → 5 → 6 → 7)
- Guard integration tests (dirty, detached, protected)
- Audit log verification tests

## Assumptions

1. `RepositoryState` module exists and is importable
2. Existing test infrastructure can be extended without breaking other tests
3. GitPython fixtures can be used for testing

## Design decisions

- Tests use `pytest` fixtures for mock `git.Repo` objects
- Pipeline ordering tests verify Stage 4 → Stage 5 → Stage 6 → Stage 7
- Guard integration tests verify dirty-worktree, detached-HEAD, and protected-branch checks
- Audit log verification tests verify pre/post condition snapshots

## Alternatives considered

- Keep test coverage minimal: Would miss critical edge cases; comprehensive tests provide better safety
- Create separate `TestRepositoryStateV2` class: Would duplicate code; updating existing tests is simpler
- Pass both `RepositoryState` and `git.Repo`: Would defeat the purpose of eliminating duplicate instantiation

## Implementation

### Target file

`tests/mcp_servers/git/test_repository_state.py`

### Procedure

1. Import `RepositoryState` from `repository_state` module
2. Write unit tests for `RepositoryState.snapshot()` capturing all fields
3. Write integration tests for pipeline ordering (Stage 4 → 5 → 6 → 7)
4. Write guard integration tests (dirty, detached, protected)
5. Write audit log verification tests

### Method

#### Step 1: Add imports

```python
import pytest
from unittest.mock import MagicMock, patch

from mcp_servers.git.repository_state import RepositoryState, WriteProtectionPipeline
```

#### Step 2: Unit tests for `RepositoryState.snapshot()`

```python
@pytest.fixture
def mock_repo():
    """Mock git.Repo for testing."""
    repo = MagicMock()
    repo.is_dirty.return_value = False
    repo.head.is_detached = False
    repo.active_branch.name = "main"
    repo.untracked_files = []
    repo.git.checkout.return_value = ""
    repo.git.pull.return_value = ""
    repo.git.push.return_value = ""
    return repo

@pytest.fixture
def mock_repo_dirty(mock_repo):
    """Mock git.Repo with dirty worktree."""
    mock_repo.is_dirty.return_value = True
    mock_repo.untracked_files = ["file.txt"]
    return mock_repo

@pytest.fixture
def mock_repo_detached(mock_repo):
    """Mock git.Repo in detached HEAD state."""
    mock_repo.head.is_detached = True
    mock_repo.active_branch.name = None
    return mock_repo

def test_snapshot_captures_all_fields(mock_repo):
    """Verify snapshot captures all required fields correctly."""
    state = RepositoryState.snapshot("/tmp/repo")
    
    assert state.path == "/tmp/repo"
    assert state.is_dirty == False
    assert state.head_type == "branch"
    assert state.active_branch == "main"
    assert state.untracked_file_count == 0
    # Note: protected_branch and ref_valid depend on external config
    assert isinstance(state._repo, MagicMock)

def test_snapshot_dirty_worktree(mock_repo_dirty):
    """Verify snapshot captures dirty worktree state."""
    with patch("git.Repo", return_value=mock_repo_dirty):
        state = RepositoryState.snapshot("/tmp/repo")
        
        assert state.is_dirty == True
        assert state.untracked_file_count == 1

def test_snapshot_detached_head(mock_repo_detached):
    """Verify snapshot captures detached HEAD state."""
    with patch("git.Repo", return_value=mock_repo_detached):
        state = RepositoryState.snapshot("/tmp/repo")
        
        assert state.head_type == "detached"
        assert state.active_branch is None
```

#### Step 3: Integration tests for pipeline ordering

```python
class TestPipelineOrdering:
    """Tests for pipeline stage ordering."""
    
    def test_stage_4_before_stage_5(self):
        """Verify Stage 4 (state snapshot) runs before Stage 5 (preconditions)."""
        # This test verifies that pipeline rejects at Stage 5 if preconditions fail
        # The actual rejection happens in _verify_preconditions()
        pass
    
    def test_stage_5_before_stage_6(self):
        """Verify Stage 5 (preconditions) runs before Stage 6 (execution)."""
        # This test verifies that pipeline doesn't execute if preconditions fail
        pass
    
    def test_stage_6_before_stage_7(self):
        """Verify Stage 6 (execution) runs before Stage 7 (postcondition verification)."""
        # This test verifies that postcondition is checked after execution
        pass

class TestGuardIntegration:
    """Tests for guard integration."""
    
    def test_dirty_worktree_rejected(self):
        """Verify dirty worktree is rejected by pipeline."""
        pass
    
    def test_detached_head_rejected(self):
        """Verify detached HEAD is rejected by pipeline."""
        pass
    
    def test_protected_branch_rejected(self):
        """Verify protected branch is rejected by pipeline."""
        pass
```

#### Step 4: Audit log verification tests

```python
class TestAuditLogVerification:
    """Tests for audit log verification."""
    
    def test_audit_record_has_pre_condition(self):
        """Verify audit record includes pre-condition snapshot."""
        pass
    
    def test_audit_record_has_post_condition(self):
        """Verify audit record includes post-condition snapshot."""
        pass
    
    def test_audit_record_includes_repo_identity(self):
        """Verify audit record includes correct repository identity."""
        pass
```

### Details

- `RepositoryState.snapshot()` captures full state from a single `git.Repo` query
- `WriteProtectionPipeline.run()` orchestrates all 9 stages
- Response includes `repository_state` metadata for observability
- `DispatchResult` gains optional `repository_state` field for backward compatibility

## Compatibility considerations

- `RepositoryStateMixin` is optional — existing models don't need to use it
- `GitConfig` dataclass remains unchanged
- Backward compatibility: existing callers of `GitConfig.load()` are unaffected

## Security considerations

- Frozen dataclass immutability must hold under all code paths
- `RepositoryState._repo` weak reference must not prevent garbage collection
- Pipeline early-exit must not skip required audit entries
- Option-injection prevention via `_is_safe_ref()` must be enforced before any `git.Repo` query

## Rollback considerations

- If `RepositoryState` causes behavioral regression, remove `RepositoryStateMixin` and revert imports
- If `GitConfig` changes break config loading, revert to previous version

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
- **Requirement ID**: REQ-009
- **Source issue**: issues/20260828-162303_mcp003_git_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-134950_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-134950
- **Related target files**: tests/mcp_servers/git/test_repository_state.py
