## Goal

Thread `GitConfig.protected_branches` from the module-level `_cfg` into each of the 3 `RepositoryState.snapshot()` call sites in the live `POST /v1/call_tool` route.

## Scope

- Modify `git_server.py`'s 3 `RepositoryState.snapshot()` calls to pass `_cfg.protected_branches` as the new parameter (REQ-003).

## Assumptions

- The 3 `RepositoryState.snapshot()` call sites in `git_server.py` (lines 169, 173, 184) are the complete set requiring the new `protected_branches` parameter — confirmed by repository-wide search.
- `GitConfig.load()` already provides `_cfg.protected_branches` with default value `[]`.
- The existing pattern of threading `_cfg.allow_detached_head` through `snapshot()` establishes precedent for this approach.

## Design decisions

- Follow the same pattern already used for `_cfg.allow_detached_head`: supply the real value from the module-level `_cfg` at each call site.
- Default parameter value (`[]`) for `protected_branches` preserves every existing direct-`snapshot()` call that does not pass it.

## Alternatives considered

- **Using a global config accessor instead of threading**: Would reduce boilerplate but introduces hidden coupling; threading follows the established pattern already used for `_cfg.allow_detached_head`.
- **Adding a factory function that wraps `snapshot()`**: Adds abstraction overhead for minimal benefit given the narrow scope (3 call sites).

## Implementation
### Target file

`scripts/mcp_servers/git/git_server.py`

### Procedure

1. Add `protected_branches=_cfg.protected_branches` argument to each of the 3 `RepositoryState.snapshot()` calls.

### Method

Modify existing `snapshot()` call expressions in-place.

### Details

- Line 169: `RepositoryState.snapshot(repo_path)` → `RepositoryState.snapshot(repo_path, protected_branches=_cfg.protected_branches)`
- Line 173: `RepositoryState.snapshot(resolved)` → `RepositoryState.snapshot(resolved, protected_branches=_cfg.protected_branches)`
- Line 184: `RepositoryState.snapshot(resolved)` → `RepositoryState.snapshot(resolved, protected_branches=_cfg.protected_branches)`

## Compatibility considerations

- Default parameter value (`[]`) for `protected_branches` preserves every existing direct-`snapshot()` call that does not pass it.
- No change to public API surface.

## Security considerations

- Threading `protected_branches` ensures the configured policy takes effect on the live path — without this wiring, the parameter remains unused regardless of how `_is_protected_branch()` is fixed.

## Rollback considerations

- If adding `protected_branches` to `snapshot()` causes unexpected behavior due to edge cases in downstream logic, reverting the 3 call-site changes restores the pre-change state.

## Validation plan

- Integration: `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py tests/mcp_servers/git/test_mcp_git.py -v` — new `/v1/call_tool` tests pass; protected branches denied, non-protected allowed.
- Regression: `uv run pytest tests/mcp_servers/git/ -v` — 184+ tests pass, no new failures.
- Static: `uv run ruff check scripts/mcp_servers/git/`; `uv run mypy scripts/mcp_servers/git/`; `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`; `PYTHONPATH=scripts uv run lint-imports` — all pass with no new findings.

## Completion criteria

- All 3 `RepositoryState.snapshot()` calls in `git_server.py` pass `protected_branches=_cfg.protected_branches`.
- Configured protected branches (`main`, `master`, `release`) are identified and rejected consistently via the live `POST /v1/call_tool` path.
- No new static analysis findings introduced.

## Out of scope

- Adding `protected_branches` to `snapshot()` itself (covered by `repository_state.py` implementation procedure).
- Fixing `_is_protected_branch()` (covered by `repository_state.py` implementation procedure).
- Adding Stage 3 call to `WriteProtectionPipeline.run()` (covered by `repository_state.py` implementation procedure).
- Adding tests (covered by separate test-file implementation procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-09-04T20:30:00Z | 2026-09-04T20:35:00Z | Added `protected_branches=_cfg.protected_branches` to 3 `snapshot()` call sites in `git_server.py` |
| 2 | Add or update tests per Validation plan | Skipped | — | — | Out of scope per section; covered by separate test-file implementation procedures |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-09-04T20:35:00Z | 2026-09-04T20:36:00Z | `ruff check` passed; `mypy` passed; `pytest tests/mcp_servers/git/` 184 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | No docs/00_index.md task-scope mapping matched for changed files |

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
- **Generated at**: 20260904-203023
- **Related target files**: scripts/mcp_servers/git/git_server.py
