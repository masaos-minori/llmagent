## Goal
Replace the tests in `tests/mcp_servers/github/test_github_mcp_service.py` that assert the skip-when-empty behavior of `_resolve_and_check_branch` (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- Measured: removing `if not self._cfg.protected_branches: return` in `github_service_security.py` (row 16) fails exactly one test in the github test directory, `TestResolveAndCheckBranch.test_empty_protected_branches_skips_check_with_empty_branch`; with an empty list and `branch=""` the code now resolves the default branch through `_run_github`.
- The empty list is unreachable in production after `GitHubConfig.load()` rejects it (row 15); `from_dict` still accepts it, and `_make_service(cfg)` builds through `from_dict`, so these tests can still construct an empty-list service.
- Rows 14-16 keep the rejection in `load()` (Plan Step 3a amendment), which is why dozens of `from_dict`-based fixtures in this file need no change.

## Design decisions
- Replace the two skip tests with one test of the new behavior instead of keeping a test for a removed branch.
- Keep the explicit-branch case: with an empty list `main` matches nothing, so no API call happens (that part of the behavior is unchanged).

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/mcp_servers/github/test_github_mcp_service.py`

### Procedure
- `test_empty_protected_branches_skips_check_with_empty_branch` (line ~320): replace with `test_empty_protected_branches_with_empty_branch_resolves_default_branch` (new): `svc = _make_service()`; patch `_run_github` with an `AsyncMock(return_value="main")`; await `svc._resolve_and_check_branch("org", "repo", "")`; assert the mock was called once (the default branch is now always resolved).
- `test_empty_protected_branches_skips_check_with_explicit_branch` (line 309): rename to `test_empty_protected_branches_allows_explicit_branch_without_api_call` (new); keep its body (still `assert_not_called`).

### Method
- Match the surrounding `@pytest.mark.asyncio` and `patch.object(svc, "_run_github", new=AsyncMock(...))` style (lines 305-335).
- Fixtures with `"protected_branches": []` at lines 219, 241, 263, 283 exercise path/size guards only and stay.

### Details
- If row 16's code differs (for example it still short-circuits when the default branch is unprotected), follow row 16's document and adjust the assertion.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_mcp_service.py -v`

## Completion criteria
- No test asserts that an empty `protected_branches` skips the default-branch lookup.
- The file passes (275 tests in the directory passed before the experiment, one failed).

## Out of Scope
- Rejection-at-load tests (rows 52 and 54).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/mcp_servers/github/test_github_mcp_service.py` per Procedure/Method/Details | Pending | — | — | |
| 2 | Run `uv run pytest tests/mcp_servers/github/test_github_mcp_service.py -v` and fix remaining fixtures in this file only | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (empty `protected_branches` rejected at load; skip-when-empty branch removed)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/mcp_servers/github/test_github_mcp_service.py`
