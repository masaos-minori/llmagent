## Goal
Add unit tests asserting `GitService._run_tool()`'s new read/write split (implemented
in `scripts/mcp_servers/git/git_service.py`'s own procedure document): `GIT_READ_TOOLS`
calls skip `WriteProtectionPipeline` (`REQ-003`, `AC-3`), `GIT_WRITE_TOOLS` calls
continue through it unchanged (`REQ-004`, `AC-2`).

## Scope
- In scope: this file only — new test classes/methods exercising `_run_tool()`'s
  branch behavior via existing `git_*` handler methods (`GitService` already has a
  `_svc()` test helper this file's existing tests use).
- Out of scope: `_run_tool()`'s implementation itself (`scripts/mcp_servers/git/
  git_service.py`'s own procedure document); `WriteProtectionPipeline` internals
  (`gitauth`/`gitpipeline`/`gitdryrun`'s scope); the HTTP-level contract test
  (`tests/mcp_servers/git/test_mcp_git.py`'s own procedure document, `REQ-007`).

## Assumptions
- This file's existing `_svc()` helper (lines 24-33) and mocking pattern (patching
  `RepositoryState.snapshot`, as seen in `test_git_service_dispatch.py`'s sibling
  `test_git_security_compliance.py` tests) are reusable for asserting whether
  `WriteProtectionPipeline` was constructed/invoked.
- The clearest signal that a read-only call skipped the pipeline is a dirty-worktree
  or detached-HEAD `RepositoryState` mock that would be rejected by Stage 5 if routed
  through `WriteProtectionPipeline`, but succeeds when the read-only bypass is used —
  this is a behavioral assertion, not an implementation-detail mock-call-count
  assertion, and is more robust to the exact bypass mechanism chosen.

## Design decisions
- Assert behaviorally (dirty/detached-HEAD read succeeds; dirty/detached-HEAD write is denied) rather than asserting `WriteProtectionPipeline` was or wasn't constructed — a call-count/mock-patch assertion would couple the test to `_run_tool()`'s exact internal structure, which this Plan's Design explicitly treats as an implementation-time decision (branch location within `_run_tool()`).
- Cover all 5 `GIT_READ_TOOLS` and at least 2 representative `GIT_WRITE_TOOLS` (one already covered by existing tests, e.g. `git_checkout`'s dirty-worktree denial) to keep this file's addition proportional — the full write-tool matrix is already exercised by this file's and `test_git_security_compliance.py`'s existing tests.

## Alternatives considered
- Assert `WriteProtectionPipeline.__init__` is not called for read tools (via `patch.object(WriteProtectionPipeline, "__init__")`): rejected — ties the test to the exact class construction point rather than observable behavior, and this Plan's Design defers the exact branch mechanism to implementation time.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_service_dispatch.py`

### Procedure
1. Add a new test class (e.g. `TestReadOnlyBypassesWriteProtection`) with one test per
   `GIT_READ_TOOLS` member (`git_status`, `git_log`, `git_diff`, `git_branch`,
   `git_show`) that mocks `RepositoryState.snapshot` to report `is_dirty=True` and
   `is_detached_head=True` (conditions that would be rejected by
   `WriteProtectionPipeline`'s Stage 5 precondition for a write tool) and asserts the
   read-only call still succeeds (no `[DENIED]` in the result).
2. Add one test confirming a representative write tool (e.g. `git_checkout`, already
   covered for the dirty-worktree case by this file's/`test_git_security_compliance.py`'s
   existing tests) is still denied under the same dirty/detached-HEAD mock — a
   regression guard confirming the read-only bypass did not accidentally also bypass
   write-tool protection.
3. Import `GIT_READ_TOOLS`/`GIT_WRITE_TOOLS` from `scripts/shared/tool_constants.py`
   only if parametrizing tests over the full read-tool set (e.g.
   `@pytest.mark.parametrize("tool_name", sorted(GIT_READ_TOOLS))`) — otherwise write
   the 5 tests individually to match this file's existing per-tool class style (see
   `TestGitLog`, `TestGitDiff`, etc.).

### Method
Reuse this file's existing `_svc()` helper and `RepositoryState.snapshot` patching
pattern (already used by sibling read-only tests like `TestGitLog.test_denied_when_allowed_empty`, which construct a `GitService` and call its handler method directly)
to construct a service, mock a dirty/detached-HEAD repository state, call each
read-only handler method, and assert success — then do the same for one write tool
and assert denial, proving the split is real and correctly scoped.

### Details
- Follow the existing per-tool class naming convention (`TestGit<ToolName>`) or group
  the new read-only-bypass tests under one dedicated class — either is acceptable;
  prefer whichever keeps this file's existing organization (one class per git
  operation) most consistent, since this file already has classes per read-only tool
  (`TestGitLog`, `TestGitDiff`, `TestGitBranch`, `TestGitShow`, `TestGitPull`,
  `TestGitStatus`) that these new tests could extend rather than duplicate.
- `git_status`'s existing dedicated class in this file only has `test_denied_when_allowed_empty`/`test_audit_record_server_key_present` (per earlier grep of this
  file) — check whether `TestGitStatus`, `TestGitLog`, etc. already have a natural
  home for a new "dirty/detached-HEAD read succeeds" test case before adding a
  brand-new class.

## Compatibility considerations
- Purely additive test file changes; no existing test's behavior or fixtures change.

## Security considerations
- N/A: this is a test file; it verifies but does not itself enforce security behavior.

## Rollback considerations
- Purely additive; revertible via `git revert` alone with no impact beyond removing
  the new test coverage.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py -v` — new tests
  pass only after `scripts/mcp_servers/git/git_service.py`'s read/write split lands;
  confirm each new read-only test fails against pre-change code (pipeline still
  wraps read tools, so a dirty/detached-HEAD mock would cause denial) and passes
  after.
- `uv run pytest tests/mcp_servers/git/ -v` (full suite) — no new failures.

## Completion criteria
- Each of the 5 `GIT_READ_TOOLS` has a test proving it is not rejected by
  dirty-worktree/detached-HEAD conditions that would reject a write tool (AC-3).
- At least one `GIT_WRITE_TOOLS` regression test confirms write-tool denial under the
  same conditions is unchanged (AC-2).

## Out of scope
- The HTTP-level contract test comparing advertised/enabled/dispatch-table/callable
  tool sets — `tests/mcp_servers/git/test_mcp_git.py`'s own procedure document
  (`REQ-007`).
- New tests for the 7 newly-HTTP-reachable tools via `/v1/call_tool` —
  `tests/mcp_servers/git/test_git_security_compliance.py`'s own procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add read-only-bypass tests for all 5 `GIT_READ_TOOLS` (Procedure step 1) | Pending | — | — | |
| 2 | Add write-tool regression test under the same dirty/detached-HEAD mock (Procedure step 2) | Pending | — | — | |
| 3 | Run validation plan (confirm fail-before/pass-after, full suite) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (assert read-only bypass), `REQ-004` (assert write-tool pipeline unchanged)
- **Source issue**: issues/20260902-144910_gitdispatch_unify_git_mcp_tool_dispatch_and_write_protection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-191458_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-203805
- **Related target files**: tests/mcp_servers/git/test_git_service_dispatch.py
