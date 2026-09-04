## Goal

Add `POST /v1/call_tool`-level regression tests via `TestClient` for `git_checkout`, `git_pull`, and `git_push` against protected and non-protected branches — closing the coverage gap where all existing tests exercise only the dead-code `GitService` path.

## Scope

- Add new `TestClient`-based tests to `test_git_security_compliance.py` covering the live `POST /v1/call_tool` path for checkout/pull/push against protected and non-protected branches, including implicit (empty branch) targets.

## Assumptions

- `TestClient` from `httpx` or `fastapi.testclient.TestClient` is available in the project's dev dependencies (confirmed by existing usage patterns in other MCP server tests).
- The git-mcp server can be started in-process for testing via its `app` object.
- Existing fixtures (`svc`, `svc_allow_detached`) remain unchanged; new tests will use their own setup.

## Design decisions

- **Separate test class**: New `TestClient` tests go into a dedicated class (`TestLiveCallToolAuthorization`) to keep them distinct from the existing `GitService` unit tests.
- **Parametrization**: Use `@pytest.mark.parametrize` for protected/non-protected branch pairs to minimize duplication.
- **Implicit target tests**: Separate explicit tests for empty-branch scenarios on pull/push to ensure REQ-007 compliance.

## Alternatives considered

- **Adding `TestClient` tests alongside existing `GitService` tests**: Would mix two different authorization paths in one class, making it harder to distinguish which path each test exercises.
- **Using a conftest fixture for server setup**: Would centralize but adds complexity for a small number of new tests; inline setup keeps the tests self-contained.

## Implementation
### Target file

`tests/mcp_servers/git/test_git_security_compliance.py`

### Procedure

1. Import `TestClient` from `fastapi.testclient` at the top of the file.
2. Create a `TestLiveCallToolAuthorization` class with tests for the live `POST /v1/call_tool` path.
3. Add parametrized tests for protected/non-protected branches for checkout/pull/push.
4. Add explicit tests for implicit (empty branch) targets.
5. Add parametrized test asserting `main` and `refs/heads/main` both deny when `main` is protected.

### Method

Add new test methods and a new test class; do not modify existing tests.

### Details

- **Import addition**: Add `from fastapi.testclient import TestClient` at the top of the file.
- **New test class**: `class TestLiveCallToolAuthorization:`
- **Tests to add**:
  - `test_checkout_protected_branch_denied`: POST `/v1/call_tool` with `git_checkout` + `branch=main` → expect denial.
  - `test_checkout_non_protected_branch_allowed`: POST `/v1/call_tool` with `git_checkout` + `branch=develop` → expect success.
  - `test_pull_protected_branch_denied`: POST `/v1/call_tool` with `git_pull` + `branch=master` → expect denial.
  - `test_pull_non_protected_branch_allowed`: POST `/v1/call_tool` with `git_pull` + `branch=develop` → expect success.
  - `test_push_protected_branch_denied`: POST `/v1/call_tool` with `git_push` + `branch=release` → expect denial.
  - `test_push_non_protected_branch_allowed`: POST `/v1/call_tool` with `git_push` + `branch=develop` → expect success.
  - `test_checkout_implicit_target_denied`: POST `/v1/call_tool` with `git_checkout` + `branch=""` (empty) → expect denial/resolution.
  - `test_pull_implicit_target_denied`: POST `/v1/call_tool` with `git_pull` + `branch=""` (empty) → expect denial/resolution.
  - `test_push_implicit_target_denied`: POST `/v1/call_tool` with `git_push` + `branch=""` (empty) → expect denial/resolution.
  - `test_parametrized_main_vs_refs_heads_main`: Parametrized test asserting both `main` and `refs/heads/main` deny checkout when `main` is protected.

## Compatibility considerations

- New tests are additive only; no existing tests are modified.
- Default parameter value (`[]`) for `protected_branches` preserves every existing direct-`snapshot()` call that does not pass it.

## Security considerations

- Fail-closed: when an effective operation target cannot be uniquely determined, deny rather than proceed.
- Reject option-like, malformed, ambiguous, or indeterminate refs before any GitPython call executes.
- Empty/whitespace-only values where not semantically valid for the tool must be rejected or resolved to the current branch before authorization runs.

## Rollback considerations

- If adding Stage 3 authorization rejects currently-succeeding operations on non-protected branches due to an edge case in `verify_authorization()`, comprehensive HTTP-level tests covering non-protected branches must pass unchanged before considering the fix complete.
- Threading `protected_branches` through `RepositoryState.snapshot()` changes a shape used across 3 call sites and test fixtures — default parameter value (`[]`) preserves every existing direct-`snapshot()` call that does not pass it.

## Validation plan

- Integration: `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py tests/mcp_servers/git/test_mcp_git.py -v` — new `/v1/call_tool` tests pass; protected branches denied, non-protected allowed.
- Regression: `uv run pytest tests/mcp_servers/git/ -v` — 184+ tests pass, no new failures.
- Static: `uv run ruff check scripts/mcp_servers/git/`; `uv run mypy scripts/mcp_servers/git/`; `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`; `PYTHONPATH=scripts uv run lint-imports` — all pass with no new findings.

## Completion criteria

- HTTP-level authorization tests cover explicit and implicit targets for checkout, pull, and push via `POST /v1/call_tool`.
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
- **Requirement ID**: REQ-010; AC-1, AC-2, AC-3, AC-6
- **Source issue**: issues/20260902-144907_gitauth_complete_protected_branch_and_ref_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-162951_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-203023
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py
