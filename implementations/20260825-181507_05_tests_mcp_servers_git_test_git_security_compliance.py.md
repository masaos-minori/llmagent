## Goal

`REQ-005`: add the four regression patterns proving ADR-012 Decision #5's
dirty-worktree/detached-HEAD gate on `git_checkout()`/`git_pull()`: (a) dirty worktree
denied, (b) detached HEAD denied by default, (c) detached HEAD allowed when
`allow_detached_head=True`, (d) `dry_run=True` bypasses both checks (regression-safe
preview behavior).

## Scope

- **In-Scope**: add test methods to
  `tests/mcp_servers/git/test_git_security_compliance.py`'s `TestGitSecurityCompliance`
  class covering the four patterns for both `git_checkout()` and `git_pull()`.
- **Out-of-Scope**: any other test file; any change to the existing tests in this
  class.

## Assumptions

- Confirmed via Read (`tests/mcp_servers/git/test_git_security_compliance.py:1-102`)
  that the existing `svc` fixture constructs `GitService(allowed_repo_paths=["/tmp/repo"],
  read_only=False, max_log_entries=50, protected_branches=["main"])` and that every
  existing async handler test mocks `svc._open_repo = MagicMock(return_value=
  MagicMock())` to inject a mock `git.Repo` without touching the filesystem — the new
  tests follow this exact mocking pattern, configuring the mock repo's `is_dirty`/
  `head.is_detached` attributes as needed per case.
- Confirmed via Read (`tests/mcp_servers/git/test_git_security_compliance.py:36-49`)
  that `test_git_checkout_protected_branch` uses `branch="main"` (the fixture's
  protected branch) to trigger a denial — the new dirty/detached tests must use a
  *non*-protected branch (e.g. `"develop"`, matching `test_git_pull_unsafe_remote`'s
  convention) so the protected-branch check does not short-circuit before the new
  dirty/detached checks run.
- This document depends on REQ-001/REQ-002 (`git_security.py`), REQ-003
  (`git_models.py`), and REQ-004 (`git_service.py`) all landing first — these tests
  exercise the wired-together behavior across all three.

## Design decisions

- Add a second fixture, `svc_allow_detached`, identical to `svc` but constructed with
  `allow_detached_head=True`, for pattern (c) — rather than parametrizing the existing
  `svc` fixture, to keep each fixture's intent explicit and avoid changing the default
  `svc` fixture used by all existing tests in this class.
- For dirty-worktree tests: `mock_repo = MagicMock(); mock_repo.is_dirty.return_value =
  True; mock_repo.head.is_detached = False; svc._open_repo = MagicMock(return_value=
  mock_repo)`.
- For detached-HEAD tests: `mock_repo = MagicMock(); mock_repo.is_dirty.return_value =
  False; mock_repo.head.is_detached = True`.
- For the `dry_run=True` regression test: configure the mock repo as *both* dirty and
  detached, set `args["dry_run"] = True`, and assert the result does NOT contain
  `"[DENIED]"` — proving both checks are skipped together, not just one.
- Use `branch="develop"` (non-protected) for all new `git_checkout` test args, and
  `remote="origin", branch="develop"` for all new `git_pull` test args, per Assumptions.

## Alternatives considered

- Testing only `git_checkout` or only `git_pull` for brevity: rejected — the source
  Plan's AC-01/AC-02/AC-04 explicitly require both handlers to be covered, and the two
  handlers' checks are wired independently (per the companion `git_service.py`
  document, each handler gets its own rewritten `op` callable) so a bug in one would not
  necessarily be caught by testing only the other.

## Implementation

### Target file
`tests/mcp_servers/git/test_git_security_compliance.py`

### Procedure
1. Add the `svc_allow_detached` fixture per Design decisions.
2. Add `test_git_checkout_dirty_worktree_denied` and `test_git_pull_dirty_worktree_denied`
   (pattern a).
3. Add `test_git_checkout_detached_head_denied` and `test_git_pull_detached_head_denied`
   using the default `svc` fixture (pattern b).
4. Add `test_git_checkout_detached_head_allowed` and `test_git_pull_detached_head_allowed`
   using the `svc_allow_detached` fixture (pattern c).
5. Add `test_git_checkout_dry_run_skips_dirty_and_detached_checks` and
   `test_git_pull_dry_run_skips_dirty_and_detached_checks` (pattern d).

### Method
Eight new test methods (4 patterns × 2 handlers) plus one new fixture, all following
the existing `svc._open_repo = MagicMock(return_value=<configured mock>)` pattern
already used by every async test in this class.

### Details
- Assert on `"[DENIED]"` presence/absence plus a distinguishing substring
  (`"dirty"`/`"uncommitted"` for the worktree check, `"detached"` for the HEAD check),
  matching the existing tests' style of asserting both the `[DENIED]` marker and a
  content-specific substring (e.g. `"protected branch"`, `"CLI option"`).

## Compatibility considerations

N/A: test-only addition, no production code or existing test change.

## Security considerations

N/A: no security-relevant logic in this file itself; these tests verify the security
behavior implemented in the companion documents.

## Rollback considerations

- Remove the eight new test methods and the new fixture.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/git/test_git_security_compliance.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` | All 8 new tests pass; all pre-existing tests in the class remain green |
| Repository-wide | Full suite | `PYTHONPATH=scripts uv run pytest` | No new failures |

## Completion criteria

- All four patterns (dirty-denied, detached-denied, detached-allowed-via-config,
  dry-run-bypasses-both) are covered for both `git_checkout` and `git_pull`.
- All 8 new tests pass; no pre-existing test in this file regresses.

## Out of scope

- `scripts/mcp_servers/git/git_security.py`, `git_models.py`, `git_service.py` — see
  their own companion implementation procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `svc_allow_detached` fixture | Pending | — | — | |
| 2 | Add dirty-worktree-denied tests (`git_checkout`, `git_pull`) | Pending | — | — | |
| 3 | Add detached-HEAD-denied tests (`git_checkout`, `git_pull`) | Pending | — | — | |
| 4 | Add detached-HEAD-allowed tests (`git_checkout`, `git_pull`) | Pending | — | — | |
| 5 | Add dry-run-bypass tests (`git_checkout`, `git_pull`) | Pending | — | — | |
| 6 | Run the validation sequence (`rules/toolchain.md`) scoped to this file | Pending | — | — | Apply only after REQ-001/002/003/004 companion documents land |
| 7 | Documentation update | N/A | — | — | Not in scope for this file |

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
- **Requirement ID**: `REQ-005` — add 4-pattern regression coverage for dirty-worktree/detached-HEAD checks
- **Source issue**: `issues/20260823_git_dirty_worktree_detached_head_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-133945_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-181507
- **Related target files**: `tests/mcp_servers/git/test_git_security_compliance.py`
