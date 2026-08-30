# Implementation Procedure: RepositoryState Module (Create)

## Goal

Create `scripts/mcp_servers/git/repository_state.py` with a frozen `RepositoryState` dataclass and a 9-stage `WriteProtectionPipeline` orchestrator to unify scattered `git.Repo` queries across write-protection guards.

## Scope

- Create new module `scripts/mcp_servers/git/repository_state.py`
- Define `RepositoryState` frozen dataclass with `snapshot()` classmethod
- Implement `_is_protected_branch()` and `_is_safe_ref()` helpers
- Define `WriteProtectionPipeline` orchestrator class
- Export `__all__ = ["RepositoryState", "WriteProtectionPipeline"]`

## Assumptions

1. The `gitpython` library version supports all required attributes (`is_dirty`, `active_branch`, `untracked_files`)
2. No concurrent write operations to the same repository during a single request
3. Existing `RepoValidationResult` can be deprecated in favor of `RepositoryState`
4. Performance impact of additional `RepositoryState` instantiation is acceptable (one-time cost per request)

## Design decisions

- Frozen dataclass: `RepositoryState` is immutable after snapshot — prevents accidental mutation between stages
- Single source of truth: One `git.Repo` query per request — eliminates duplicate instantiation
- Early exit: Pipeline rejects at Stage 5 if preconditions fail — execution never runs
- Backward compatibility: Existing guard methods delegate to `RepositoryState` properties rather than being replaced wholesale

## Alternatives considered

- Mutable dataclass: Would require explicit synchronization between stages; frozen provides stronger guarantees with zero runtime overhead
- Function-based state capture: Would lose type safety and IDE support; dataclass provides structured access to all fields
- Pipeline as standalone functions: Would lack shared state context; class encapsulates pipeline logic and state together

## Implementation

### Target file

`scripts/mcp_servers/git/repository_state.py`

### Procedure

1. Define `RepositoryState` frozen dataclass with all required fields
2. Implement `snapshot()` classmethod that captures full state from a single `git.Repo` query
3. Implement `_is_protected_branch()` helper function
4. Implement `_is_safe_ref()` helper function
5. Define `WriteProtectionPipeline` orchestrator class with stage methods
6. Add `__all__` export list

### Method

#### Step 1: Define `RepositoryState` dataclass

```python
@dataclass(frozen=True)
class RepositoryState:
    path: str
    is_dirty: bool
    head_type: Literal["detached", "branch"]
    active_branch: str | None
    untracked_file_count: int
    protected_branch: bool
    ref_valid: bool
    _repo: git.Repo | None = field(default=None, repr=False, compare=False)
```

- `path`: repository path used for snapshot
- `is_dirty`: result of `repo.is_dirty(indexed_working_tree=True)`
- `head_type`: `"detached"` or `"branch"` based on `repo.head.is_detached`
- `active_branch`: branch name or `None` if detached
- `untracked_file_count`: `len(repo.untracked_files)`
- `protected_branch`: result of `_is_protected_branch(repo)`
- `ref_valid`: result of `_is_safe_ref(repo)`
- `_repo`: weak reference to avoid preventing garbage collection

#### Step 2: Implement `snapshot()` classmethod

```python
@classmethod
def snapshot(cls, repo_path: str) -> "RepositoryState":
    """Capture full state from a single git.Repo query."""
    repo = git.Repo(repo_path)
    return cls(
        path=repo_path,
        is_dirty=repo.is_dirty(indexed_working_tree=True),
        head_type="detached" if repo.head.is_detached else "branch",
        active_branch=repo.active_branch.name if not repo.head.is_detached else None,
        untracked_file_count=len(repo.untracked_files),
        protected_branch=_is_protected_branch(repo),
        ref_valid=_is_safe_ref(repo),
        _repo=repo,
    )
```

#### Step 3: Implement helper functions

```python
def _is_protected_branch(repo: git.Repo) -> bool:
    """Check if HEAD points to a protected branch."""
    # Read protected branches from GitConfig or environment
    ...

def _is_safe_ref(ref: str) -> bool:
    """Return True if ref does not look like a CLI option."""
    return not ref.startswith("-")
```

#### Step 4: Define `WriteProtectionPipeline` orchestrator

```python
class WriteProtectionPipeline:
    def __init__(self, state: RepositoryState):
        self.state = state

    def run(self, command: str, operation: Callable[[], GitOperationResult]) -> DispatchResult:
        # Stage 1: Schema validation (already done by caller)
        # Stage 2: Repository resolution (already done — state captured)
        # Stage 3: Common authorization
        self._verify_authorization()

        # Stage 4: State snapshot (already done — passed as constructor arg)
        # Stage 5: Command-specific precondition
        self._verify_preconditions(command)

        # Stage 6: Execution
        result = operation()

        # Stage 7: Postcondition verification
        self._verify_postcondition(result)

        # Stage 8: Audit
        self._audit(result)

        # Stage 9: Structured result
        return self._structured_result(result)
```

### Details

- `_verify_authorization()`: checks `state.protected_branch` and `state.ref_valid`
- `_verify_preconditions(command)`: checks `state.is_dirty`, `state.head_type` based on command type
- `_verify_postcondition(result)`: compares postcondition against `state` captured at Stage 4
- `_audit(result)`: logs both pre-condition (`state`) and postcondition snapshots
- `_structured_result(result)`: wraps result with `RepositoryState` metadata for `DispatchResult`

## Compatibility considerations

- `RepositoryState` replaces `RepoValidationResult` — callers must migrate to the new type
- `format_checkout/pull/push` signatures change to accept `RepositoryState` instead of `git.Repo`
- `GitSecurityGuards` mixin methods must accept `RepositoryState` instead of raw `git.Repo`
- `DispatchResult` gains a `RepositoryState` metadata field — existing consumers may need updates
- `AuditRecord` TypedDict gains pre/post condition snapshot fields

## Security considerations

- Frozen dataclass immutability must hold under all code paths
- `RepositoryState._repo` weak reference must not prevent garbage collection
- Pipeline early-exit must not skip required audit entries
- Option-injection prevention via `_is_safe_ref()` must be enforced before any `git.Repo` query

## Rollback considerations

- If `RepositoryState` causes behavioral regression, revert callers to direct `git.Repo` queries
- If performance degrades, add caching layer to `RepositoryState.snapshot()`
- If `AuditRecord` schema drift occurs, version the TypedDict and add migration tests

## Validation plan

- Unit tests for `RepositoryState.snapshot()` capturing all fields
- Integration tests for pipeline ordering (Stage 4 → 5 → 6 → 7)
- Guard integration tests (dirty, detached, protected)
- Audit log verification tests
- Behavioral equivalence: compare output of old vs new guards on identical inputs

## Completion criteria

- [ ] `RepositoryState` captures all required fields correctly
- [ ] Pipeline enforces Stage 4 before Stage 5, Stage 5 before Stage 6, Stage 6 before Stage 7
- [ ] All write-protection guards use `RepositoryState` exclusively — zero direct `git.Repo` queries in guard logic
- [ ] New test suite passes without modification
- [ ] Lint/type check passes: `ruff check scripts/mcp_servers/git/` and `mypy scripts/mcp_servers/git/`

## Out of scope

- GitHub MCP's existing `protected_branches`/force-push handling (already implemented separately)
- Redesign of Agent-side approval risk-tier mapping (tracked separately as Known Issue MCP-004)
- Any capability to allow Force Push, even as an administrative feature

## Execution Status

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260828-162303_mcp003_git_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-134950_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-134950
- **Related target files**: scripts/mcp_servers/git/repository_state.py
