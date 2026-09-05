## Goal

Add unit tests for the fixed `_is_protected_branch()`, `ref_valid` validation, and the new Stage 3 call in `WriteProtectionPipeline.run()` — covering the previously untested live-path authorization logic at the unit level.

## Scope

- Add new unit tests to `test_repository_state.py` covering:
  - `_is_protected_branch()` against configured `protected_branches` (REQ-002).
  - `ref_valid` rejecting option-like/malformed refs (REQ-004).
  - `WriteProtectionPipeline.run()` invoking Stage 3 (REQ-001; REQ-002; REQ-004; AC-1, AC-2, AC-5, AC-7).

## Assumptions

- `pytest` fixtures (`bare_repo`, `working_repo`) remain unchanged; new tests will use their own setup where needed.
- `WriteProtectionPipeline` can be instantiated with a mock `RepositoryState` for testing Stage 3 invocation.
- Existing tests in this file (184 total in the git-mcp suite pass currently) exercise `RepositoryState`/pipeline unit-level behavior; the new tests add coverage of the fixed authorization logic.

## Design decisions

- **Separate test classes**: New tests go into dedicated classes (`TestProtectedBranchCheck`, `TestRefValidValidation`, `TestStage3Authorization`) to keep them distinct from existing snapshot/guard/pipeline tests.
- **Parametrization**: Use `@pytest.mark.parametrize` for protected/non-protected branch pairs to minimize duplication.
- **Spy on operation callable**: For Stage 3 tests, spy/mock on the operation callable to prove it was never called when a protected-branch state causes `run()` to reject.

## Alternatives considered

- **Adding tests alongside existing `TestGuardDelegation`**: Would mix new authorization tests with existing guard delegation tests, making it harder to distinguish which tests cover the fixed logic vs. existing behavior.
- **Using a conftest fixture for server setup**: Would centralize but adds complexity for a small number of new tests; inline setup keeps the tests self-contained.

## Implementation
### Target file

`tests/mcp_servers/git/test_repository_state.py`

### Procedure

1. Import `MagicMock` from `unittest.mock` at the top of the file.
2. Create a `TestProtectedBranchCheck` class with tests for the fixed `_is_protected_branch()`.
3. Create a `TestRefValidValidation` class with tests for the fixed `ref_valid` validation.
4. Create a `TestStage3Authorization` class with tests for the new Stage 3 call in `WriteProtectionPipeline.run()`.

### Method

Add new test methods and new test classes; do not modify existing tests.

### Details

- **Import addition**: Add `from unittest.mock import MagicMock, patch` at the top of the file (if not already present).
- **New test class**: `class TestProtectedBranchCheck:`
  - `test_is_protected_branch_main`: Assert `_is_protected_branch()` returns `True` for `main` when `main` is in `protected_branches`.
  - `test_is_protected_branch_master`: Assert `_is_protected_branch()` returns `True` for `master` when `master` is in `protected_branches`.
  - `test_is_protected_branch_release`: Assert `_is_protected_branch()` returns `True` for `release` when `release` is in `protected_branches`.
  - `test_is_protected_branch_develop`: Assert `_is_protected_branch()` returns `False` for `develop` when only `main`/`master`/`release` are protected.
  - `test_is_protected_branch_normalized_refs`: Parametrized test asserting both `main` and `refs/heads/main` deny checkout when `main` is protected.
- **New test class**: `class TestRefValidValidation:`
  - `test_ref_valid_option_like_rejected`: Assert `ref_valid` rejects refs starting with `-`.
  - `test_ref_valid_malformed_rejected`: Assert `ref_valid` rejects malformed refs.
  - `test_ref_valid_empty_rejected`: Assert `ref_valid` rejects empty refs where not semantically valid.
  - `test_ref_valid_safe_accepted`: Assert `ref_valid` accepts safe refs like `HEAD`, `develop`, `feature/abc`.
- **New test class**: `class TestStage3Authorization:`
  - `test_pipeline_run_invokes_stage_3_for_protected_branch`: Spy on `verify_authorization()` to prove it is called before Stage 6 executes when a protected-branch state causes rejection.
  - `test_pipeline_run_does_not_call_operation_on_protection_failure`: Assert the operation callable is never invoked when protection fails.
  - `test_pipeline_run_proceeds_to_stage_5_when_auth_passes`: Assert Stage 5 precondition checks run after successful Stage 3 authorization.

## Compatibility considerations

- Default parameter value (`[]`) for `protected_branches` preserves every existing direct-`snapshot()` call that does not pass it.
- Existing test fixtures that construct `RepositoryState` without caring about protection continue to work unchanged.
- `verify_authorization()`'s return type (`tuple[bool, str]`) matches the existing pipeline stage contract.

## Security considerations

- Fail-closed: when an effective operation target cannot be uniquely determined, deny rather than proceed.
- Reject option-like, malformed, ambiguous, or indeterminate refs before any GitPython call executes.
- Empty/whitespace-only values where not semantically valid for the tool must be rejected or resolved to the current branch before authorization runs.

## Rollback considerations

- If adding Stage 3 authorization rejects currently-succeeding operations on non-protected branches due to an edge case in `verify_authorization()`, comprehensive HTTP-level tests covering non-protected branches must pass unchanged before considering the fix complete.
- Threading `protected_branches` through `RepositoryState.snapshot()` changes a shape used across 3 call sites and test fixtures — default parameter value (`[]`) preserves every existing direct-`snapshot()` call that does not pass it.

## Validation plan

- Unit: `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` — Stage 3 call verified via spy on the operation callable; `_is_protected_branch()` against configured `protected_branches`; `ref_valid` rejecting option-like/malformed refs.
- Integration: `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py tests/mcp_servers/git/test_mcp_git.py -v` — new `/v1/call_tool` tests pass; protected branches denied, non-protected allowed.
- Regression: `uv run pytest tests/mcp_servers/git/ -v` — 184+ tests pass, no new failures.
- Static: `uv run ruff check scripts/mcp_servers/git/`; `uv run mypy scripts/mcp_servers/git/`; `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`; `PYTHONPATH=scripts uv run lint-imports` — all pass with no new findings.

## Completion criteria

- Unit tests for `_is_protected_branch()` against configured `protected_branches` pass.
- Unit tests for `ref_valid` rejecting option-like/malformed refs pass.
- Unit tests for `WriteProtectionPipeline.run()` invoking Stage 3 pass.
- Each new/modified test fails against the pre-change code (protected branch currently succeeds via `/v1/call_tool`) and passes after the fix.
- No new static analysis findings introduced.

## Out of scope

- Adding `protected_branches` to `snapshot()` itself (covered by `repository_state.py` implementation procedure).
- Fixing `_is_protected_branch()` (covered by `repository_state.py` implementation procedure).
- Adding Stage 3 call to `WriteProtectionPipeline.run()` (covered by `repository_state.py` implementation procedure).
- Modifying existing `GitService` unit tests (they exercise the dead-code path, which remains unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | |
| 2 | Add or update tests per Validation plan | Completed | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 13 new tests pass; full suite 252 tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: no docs section matches this scope |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004; AC-1, AC-2, AC-5
- **Source issue**: issues/20260902-144907_gitauth_complete_protected_branch_and_ref_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-162951_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-203023
- **Related target files**: tests/mcp_servers/git/test_repository_state.py
