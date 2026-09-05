## Goal
Add `POST /v1/call_tool` tests for the 7 newly-reachable tools (`git_status`,
`git_log`, `git_diff`, `git_branch`, `git_show`, `git_add`, `git_commit`) confirming
they now execute instead of returning `"Unknown tool"` (`REQ-002`, `AC-1`), that the 5
newly-reachable write tools among them (`git_add`/`git_commit`, since
`git_checkout`/`git_pull`/`git_push` are already covered) go through
`WriteProtectionPipeline` (`REQ-004`, `AC-2`), and that a read-only tool is not
rejected by write-only preconditions in a dirty/detached-HEAD repository (`REQ-003`,
`AC-3`).

## Scope
- In scope: this file only — new `TestClient`-based tests reusing the existing
  module-scoped `client` fixture (line 490-496).
- Out of scope: the contract test comparing advertised/enabled/registered/reachable
  sets — `tests/mcp_servers/git/test_mcp_git.py`'s own procedure document (`REQ-007`);
  `_run_tool()`'s read/write split implementation — `scripts/mcp_servers/git/
  git_service.py`'s own procedure document; `call_tool()`'s dispatch-call replacement
  — `scripts/mcp_servers/git/git_server.py`'s own procedure document (this file's new
  tests depend on that change landing to pass, but do not implement it).

## Assumptions
- This file's stale "zero `TestClient` usage" claim was corrected during this Plan's
  `plan-to-implementation-procedure` Step 3a revalidation — the file already has a
  `client` fixture (lines 490-496) and 5 existing `TestClient`-based tests, all
  scoped to `git_checkout`/`git_pull`/`git_push` only (confirmed via `grep` for
  `call_tool` — no existing test posts `git_status`/`git_log`/`git_diff`/
  `git_branch`/`git_show`/`git_add`/`git_commit`).
- A real (or `tmp_path`-created) git repository fixture is needed for these tests,
  since read/write tools need actual repository state to operate on — check whether
  this file or a shared `conftest.py` already provides one (this file's existing
  checkout/pull/push `TestClient` tests must already construct or reference such a
  fixture; reuse the same pattern).

## Design decisions
- Add tests grouped by concern, mirroring this Plan's Acceptance Criteria rather than one giant test: a "newly reachable" group (AC-1: each of the 7 returns something other than `"Unknown tool"`), a "write tools still protected" group (AC-2: `git_add`/`git_commit` denied under dirty-worktree/detached-HEAD, matching the existing `test_git_checkout_dirty_worktree_denied`-style pattern already in this file for the 3 existing write tools), and a "read tool bypasses write-only checks" group (AC-3: one read-only tool, e.g. `git_status`, succeeds via `/v1/call_tool` against a dirty/detached-HEAD repo where a write tool would be denied).
- Reuse the existing module-scoped `client` fixture rather than adding a second one — this file already has exactly one `TestClient` construction pattern (line 490-496); a second, differently-configured client should only be added if the existing fixture's `GitConfig` (`read_only`/`allowed_repo_paths`) cannot support the new tests' needs.

## Alternatives considered
- Put the 7 new HTTP tests in `test_mcp_git.py` instead: rejected — the Plan's own Implementation Target Files table assigns this file as "the designated home for live-path HTTP tests across the `gitauth`/`gitpipeline`/`gitdryrun`/`gitdispatch` Plan set", consistent with this file's existing `TestClient`-based tests for checkout/pull/push.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_security_compliance.py`

### Procedure
1. Add a new test class (e.g. `TestNewlyReachableToolsViaHTTP`) with one test per
   `git_status`/`git_log`/`git_diff`/`git_branch`/`git_show`/`git_add`/`git_commit`,
   each posting to `/v1/call_tool` via the existing `client` fixture with a valid
   `repo_path` (matching whatever repo fixture this file's existing checkout/pull/push
   `TestClient` tests use) and asserting the response is not
   `"Unknown tool: {name}"` (AC-1).
2. Add a test confirming `git_add`/`git_commit` (the 2 write tools among the 7 newly
   reachable) are denied under a dirty-worktree or detached-HEAD condition via
   `/v1/call_tool`, mirroring the existing `test_git_checkout_dirty_worktree_denied`/
   `test_git_checkout_detached_head_denied`-style pattern (lines 147-228) already in
   this file for `git_checkout`/`git_pull` (AC-2).
3. Add a test confirming a read-only tool (e.g. `git_status`) called via
   `/v1/call_tool` against a dirty-worktree or detached-HEAD repository is *not*
   denied (contrast directly with step 2's write-tool denial, same fixture repo
   state) (AC-3).

### Method
Reuse the existing `client` fixture and this file's established
`client.post("/v1/call_tool", json={...})` pattern (already used by
`TestHTTPSiblingPathRejection`, `TestPostConditionBypassPrevention`,
`TestCompletePipelineCoverage`) for all new tests — no new fixture machinery beyond
what checkout/pull/push tests in this same file already use.

### Details
- For AC-1's 7 tests, `git_status`/`git_log`/`git_diff`/`git_branch`/`git_show`
  require only `repo_path` (and for `git_log`/`git_show`, an optional `branch`/`ref`
  defaulting to current-branch/`HEAD`); `git_add` requires `paths`; `git_commit`
  requires `message` — construct minimal valid args for each per their respective
  `Request` models in `scripts/mcp_servers/git/git_models.py` (Reference File; no
  change needed there).
- AC-2's dirty-worktree/detached-HEAD write-tool denial test can reuse whatever
  repo-state-mocking or real-repo-manipulation approach `test_git_checkout_dirty_worktree_denied` (lines 147-166) already uses — confirm during implementation
  whether that existing test mocks `RepositoryState.snapshot` or manipulates a real
  `tmp_path` repo, and follow the same approach for consistency within this file.
- AC-3's read-tool test must use the *same* dirty/detached-HEAD condition as AC-2's
  write-tool test (same fixture/mock), so the contrast directly demonstrates the
  read/write split rather than relying on two differently-configured setups.

## Compatibility considerations
- Purely additive; no existing test in this file changes. These new tests will fail
  until `scripts/mcp_servers/git/git_server.py`'s dispatch-unification change and
  `scripts/mcp_servers/git/git_service.py`'s read/write split both land — expected and
  intentional (implementation-procedure execution order: implement those two files'
  procedures before this file's tests can pass).

## Security considerations
- N/A: this is a test file; it verifies but does not itself enforce security
  behavior. Uses the same allowlisted test-repo path convention as this file's
  existing tests — no new repo-path or credential handling introduced.

## Rollback considerations
- Purely additive; revertible via `git revert` alone.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` — new
  tests pass only once `git_server.py`/`git_service.py`'s procedures land; confirm
  each fails against pre-change code (7 "Unknown tool" responses) and passes after.
- `uv run pytest tests/mcp_servers/git/ -v` (full suite) — no new failures.

## Completion criteria
- All 7 newly-reachable tools have a passing `/v1/call_tool` test confirming they no
  longer return `"Unknown tool"` (AC-1).
- `git_add`/`git_commit` are confirmed denied under the same write-only preconditions
  as the existing 3 write tools (AC-2).
- At least one read-only tool is confirmed *not* denied under the same
  dirty/detached-HEAD condition (AC-3).

## Out of scope
- The four-set advertised/enabled/registered/reachable contract test —
  `tests/mcp_servers/git/test_mcp_git.py`'s own procedure document (`REQ-007`).
- Unit-level (non-HTTP) read/write-split tests —
  `tests/mcp_servers/git/test_git_service_dispatch.py`'s own procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add 7 "newly reachable" `/v1/call_tool` tests (Procedure step 1, AC-1) | Pending | — | — | |
| 2 | Add write-tool dirty/detached-HEAD denial test for `git_add`/`git_commit` (Procedure step 2, AC-2) | Pending | — | — | |
| 3 | Add read-tool dirty/detached-HEAD bypass test (Procedure step 3, AC-3) | Pending | — | — | |
| 4 | Run validation plan (this file + full suite) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (7 tools reachable), `REQ-003` (read-only bypass), `REQ-004` (write tools still protected)
- **Source issue**: issues/20260902-144910_gitdispatch_unify_git_mcp_tool_dispatch_and_write_protection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-191458_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-203805
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py
