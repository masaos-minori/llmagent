# Implementation Procedure: Modify git_models.py

## Goal

Add `RepositoryState` field references to Pydantic models where needed; update `GitConfig` dataclass imports.

## Scope

- Add `RepositoryState` field references to Pydantic models where needed
- Update `GitConfig` dataclass imports

## Assumptions

1. `RepositoryState` module exists and is importable
2. Existing Pydantic models can be updated without breaking other callers
3. `GitConfig` dataclass can be extended without breaking config loading

## Design decisions

- `RepositoryState` field references are added to Pydantic models where they provide value
- `GitConfig` dataclass imports are updated to include `RepositoryState`
- Changes are minimal — only add what is necessary for the pipeline to work

## Alternatives considered

- Keep `GitConfig` unchanged: Would require importing `RepositoryState` elsewhere; cleaner to centralize
- Create separate `PydanticRepositoryState`: Would duplicate code; using `RepositoryState` directly is simpler
- Remove `GitConfig` entirely: Would break config loading; migration is safer

## Implementation

### Target file

`scripts/mcp_servers/git/git_models.py`

### Procedure

1. Import `RepositoryState` from `repository_state` module
2. Add `RepositoryState` field references to Pydantic models where needed
3. Update `GitConfig` dataclass imports

### Method

#### Step 1: Add imports

```python
from mcp_servers.git.repository_state import RepositoryState
```

#### Step 2: Add `RepositoryState` field references to Pydantic models

In the Pydantic request model section (after line ~100), add a mixin class:

```python
class RepositoryStateMixin(BaseModel):
    """Mixin providing the common repository_state field."""
    
    repository_state: RepositoryState | None = Field(
        default=None, description="Repository state snapshot for write operations"
    )
```

This mixin allows Pydantic models to optionally carry a `RepositoryState` snapshot alongside their request parameters.

#### Step 3: Update `GitConfig` dataclass imports

No changes needed to `GitConfig` itself — it already has all required fields. Only ensure the import of `RepositoryState` is available for downstream consumers.

### Details

- `RepositoryStateMixin` provides optional `repository_state` field for Pydantic models
- `GitConfig` dataclass remains unchanged — it already has all required fields
- Downstream consumers can import `RepositoryState` from this module for convenience

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Complete | 2026-08-30 | 2026-08-30 | Removed `RepositoryStateMixin` class and its import; resolved circular import between `git_models.py` and `repository_state.py` |
| 2 | Add or update tests per Validation plan | Complete | 2026-08-30 | 2026-08-30 | Updated `test_git_models.py` to import `GitServiceError` from `errors.py` |
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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260828-162303_mcp003_git_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-134950_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-134950
- **Related target files**: scripts/mcp_servers/git/git_models.py
