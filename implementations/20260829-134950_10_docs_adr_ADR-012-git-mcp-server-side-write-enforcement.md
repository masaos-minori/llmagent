# Implementation Procedure: Modify ADR-012

## Goal

Update ADR-012 to reflect the new `RepositoryState`-based approach; add traceability section linking to implementation procedures; update consequences section.

## Scope

- Update ADR-012 to reflect the new `RepositoryState`-based approach
- Add traceability section linking to implementation procedures
- Update consequences section

## Assumptions

1. `RepositoryState` module exists and is importable
2. Existing ADR-012 can be updated without breaking other documents
3. Consequences section can be extended without breaking other ADRs

## Design decisions

- ADR-012 reflects the new `RepositoryState`-based approach
- Traceability section links to implementation procedures
- Consequences section is extended to include new risks and mitigations

## Alternatives considered

- Keep ADR-012 unchanged: Would require importing `RepositoryState` elsewhere; cleaner to centralize
- Create separate ADR-013: Would duplicate content; updating existing ADR is simpler
- Remove ADR-012 entirely: Would break traceability; migration is safer

## Implementation

### Target file

`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`

### Procedure

1. Update Decision Details section to reflect `RepositoryState`-based approach
2. Add traceability section linking to implementation procedures
3. Update consequences section

### Method

#### Step 1: Update Decision Details section

In the Decision Details section (after point 7), add:

```
8. `RepositoryState` frozen dataclass MUST capture full repository state from a single `git.Repo` query and provide immutable access to all fields.
9. `WriteProtectionPipeline` MUST enforce stage ordering: Stage 4 (state snapshot) → Stage 5 (preconditions) → Stage 6 (execution) → Stage 7 (postcondition verification).
10. Audit records for Git MCP write operations MUST include both pre-condition and post-condition snapshots captured by `RepositoryState`.
```

#### Step 2: Add traceability section

Add a new section after Consequences:

```
## Traceability

### Implementation Procedures
- `implementations/20260829-134950_01_scripts_mcp_servers_git_repository_state.py.md`: Create RepositoryState module
- `implementations/20260829-134950_02_scripts_mcp_servers_git_git_service.py.md`: Modify git_service.py
- `implementations/20260829-134950_03_scripts_mcp_servers_git_git_security.py.md`: Modify git_security.py
- `implementations/20260829-134950_04_scripts_mcp_servers_git_format_output.py.md`: Modify format_output.py
- `implementations/20260829-134950_05_scripts_mcp_servers_git_git_models.py.md`: Modify git_models.py
- `implementations/20260829-134950_06_scripts_mcp_servers_git_git_server.py.md`: Modify git_server.py
- `implementations/20260829-134950_07_scripts_mcp_servers_dispatch.py.md`: Modify dispatch.py
- `implementations/20260829-134950_08_scripts_mcp_servers_audit.py.md`: Modify audit.py
- `implementations/20260829-134950_09_tests_mcp_servers_git_test_repository_state.py.md`: Create tests

### Source Documents
- Source issue: issues/20260828-162303_mcp003_git_write_protection_pipeline.md
- Source plan: plans/20260829-134950_plan.md
```

#### Step 3: Update consequences section

In the Consequences section, add:

```
### New Risks
- Frozen dataclass immutability must hold under all code paths
- `RepositoryState._repo` weak reference must not prevent garbage collection
- Pipeline early-exit must not skip required audit entries
- Option-injection prevention via `_is_safe_ref()` must be enforced before any `git.Repo` query

### Mitigations
- Unit tests for `RepositoryState.snapshot()` capturing all fields
- Integration tests for pipeline ordering (Stage 4 → 5 → 6 → 7)
- Guard integration tests (dirty, detached, protected)
- Audit log verification tests
```

### Details

- ADR-012 reflects the new `RepositoryState`-based approach
- Traceability section links to implementation procedures
- Consequences section is extended to include new risks and mitigations

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20260828-162303_mcp003_git_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-134950_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-134950
- **Related target files**: docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md
