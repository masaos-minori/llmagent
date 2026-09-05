# Implementation Procedure: Wire Config into Live Path

## Goal

Thread `GitConfig.protected_branches` from module-level `_cfg` into each of the 3 `RepositoryState.snapshot()` call sites in `scripts/mcp_servers/git/git_server.py`, following the same pattern already established for `_cfg.allow_detached_head`.

## Scope

Only changes required for Requirement REQ-003 in `scripts/mcp_servers/git/git_server.py`. Specifically: adding `protected_branches=_cfg.protected_branches` to each of the 3 `snapshot()` calls at lines 169, 173, and 184.

## Assumptions

- `GitConfig.protected_branches`'s existing values (`main`, `master`, `release`) are correct policy; this Plan does not change what is configured.
- The 3 `RepositoryState.snapshot()` call sites (lines 169, 173, 184) are the complete set requiring the new parameter — confirmed by repository-wide `rg "RepositoryState.snapshot"` across `git_server.py`.
- Adding `protected_branches=[]` default to `snapshot()` preserves every existing direct-`snapshot()` call site that does not pass it.
- `_cfg` is already loaded at module level (line 60), so no additional config loading is needed here.

## Design decisions

- Follow the exact same threading pattern as `_cfg.allow_detached_head` (line 243): pass `_cfg.protected_branches` as a keyword argument directly at each call site, rather than extracting it to a local variable first.
- Default `protected_branches=[]` on `snapshot()` means partial deployment (some call sites wired, others not) leaves protection silently disabled for unwired sites — but this is acceptable because all 3 sites must be wired together for the fix to take effect.

## Alternatives considered

- Extracting `protected_branches = _cfg.protected_branches` to a local variable before the handler dict: rejected because it adds unnecessary indirection; the `_cfg.allow_detached_head` pattern passes the value inline at each call site.
- Reading `_cfg` inside `snapshot()` itself: rejected because it would introduce a hidden dependency and break test isolation; explicit threading makes the data flow visible.

## Implementation

### Target file

`scripts/mcp_servers/git/git_server.py`

### Procedure

##### Method: Thread protected_branches at each snapshot() call site

**REQ-003**: Add `protected_branches=_cfg.protected_branches` keyword argument to each of the 3 `RepositoryState.snapshot()` calls.

Current call sites (confirmed by `rg "RepositoryState\.snapshot"`):

1. **Line 169** — validation error path (before resolved repo check):
   ```python
   # Before:
   pre_condition=_serialize_state(RepositoryState.snapshot(repo_path))
   
   # After:
   pre_condition=_serialize_state(RepositoryState.snapshot(repo_path, protected_branches=_cfg.protected_branches))
   ```

2. **Line 173** — pre-state capture after resolved repo path:
   ```python
   # Before:
   pre_state = RepositoryState.snapshot(resolved)
   
   # After:
   pre_state = RepositoryState.snapshot(resolved, protected_branches=_cfg.protected_branches)
   ```

3. **Line 184** — post-state capture after pipeline execution:
   ```python
   # Before:
   post_state = RepositoryState.snapshot(resolved)
   
   # After:
   post_state = RepositoryState.snapshot(resolved, protected_branches=_cfg.protected_branches)
   ```

### Details

Key code locations to modify:

1. **Line 169**: Add `protected_branches=_cfg.protected_branches` to the `RepositoryState.snapshot(repo_path)` call within the `_on_git_service_error` exception handler path (inside the `call_tool` route).

2. **Line 173**: Add `protected_branches=_cfg.protected_branches` to the `RepositoryState.snapshot(resolved)` call that captures pre-pipeline state.

3. **Line 184**: Add `protected_branches=_cfg.protected_branches` to the `RepositoryState.snapshot(resolved)` call that captures post-pipeline state.

No other files in this row require modification. The `protected_branches` parameter is purely additive to `snapshot()`'s signature with a default value, so no other callers need updating.

## Compatibility considerations

- **Backward compatibility**: `protected_branches=[]` default on `snapshot()` means existing direct-`snapshot()` calls outside this file (e.g., in tests) continue working without passing the parameter.
- **Partial deployment risk**: If only some of the 3 call sites are wired during deployment, protection is silently disabled for unwired sites. However, since all 3 must be deployed together (they're in the same file), this risk is eliminated in practice.
- **No change to `_serialize_state`**: The serialization function reads `state.protected_branch` and `state.ref_valid` from the instance — no modification needed.

## Security considerations

- **Fail-closed prerequisite**: This change alone does not add protection; it wires the config value into the live path. Protection takes effect only when combined with the fixes in `repository_state.py` (Rows 1). Deploying this file without the other rows leaves the system unchanged (no regression, but also no improvement).
- **Config value integrity**: `_cfg.protected_branches` is read once per request via `_cfg` module-level reference. If `GitConfig` supports hot-reload, the value could change mid-request — but this is consistent with how `_cfg.allow_detached_head` works today.

## Rollback considerations

- **Simple revert**: Reverting this file removes the `protected_branches` argument from all 3 call sites. Since the default is `[]`, the system falls back to no-protection behavior (same as current state).
- **No cross-file dependency**: This change has no dependency on other files beyond `_cfg` being available at import time (already true).

## Validation plan

| Step | Action | Command | Expected Outcome |
|------|--------|---------|------------------|
| 1 | Verify no syntax errors | `uv run python -c "import mcp_servers.git.git_server"` | Module imports successfully |
| 2 | Run git-mcp unit tests | `uv run pytest tests/mcp_servers/git/test_mcp_git.py -v` | All pass |
| 3 | Run full git-mcp suite | `uv run pytest tests/mcp_servers/git/ -v` | 184+ tests pass, no new failures |
| 4 | Static analysis | `uv run ruff check scripts/mcp_servers/git/`; `uv run mypy scripts/mcp_servers/git/` | All pass with no new findings |

## Completion criteria

- [ ] Line 169: `RepositoryState.snapshot(repo_path, protected_branches=_cfg.protected_branches)` — parameter added.
- [ ] Line 173: `RepositoryState.snapshot(resolved, protected_branches=_cfg.protected_branches)` — parameter added.
- [ ] Line 184: `RepositoryState.snapshot(resolved, protected_branches=_cfg.protected_branches)` — parameter added.
- [ ] No other `snapshot()` call sites exist in this file (confirmed by `rg`).
- [ ] Module imports without syntax errors.
- [ ] All existing tests pass with no new failures.
- [ ] All static analysis tools pass with no new findings.

## Out of scope

- Fixing `_is_protected_branch()` placeholder — Row 1 responsibility.
- Adding Stage 3 call to `WriteProtectionPipeline.run()` — Row 1 responsibility.
- Replacing `ref_valid=True` — Row 1 responsibility.
- Operation-target resolution — Row 1 responsibility.
- Adding HTTP-level regression tests — Row 3 responsibility.
- Adding unit tests for the fixed logic — Row 4 responsibility.
- Modifying `GitConfig` class — no change needed; `protected_branches` field already exists.
- Documentation updates — deferred per issue's Constraint.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260902-144907_gitauth_complete_protected_branch_and_ref_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-162951_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-131142
- **Related target files**: scripts/mcp_servers/git/git_server.py
