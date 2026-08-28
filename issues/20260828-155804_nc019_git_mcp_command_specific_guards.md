# NC-019: Git MCP protected-branch bypass via empty `branch` argument — owner decision needed

## Priority
High

## Summary
`NC-019` originally asked whether Git MCP's lack of command-specific guards
(Dirty-Worktree/Detached-HEAD/ref-remote validation/postcondition verification) for
`git_checkout`/`git_pull`/`git_push` was intentional or a missing security feature. Direct code
inspection during this issue's drafting found that most of that original scope is **already
implemented**: Dirty-Worktree/Detached-HEAD checks (`GIT-001`), postcondition verification
(`GIT-002`), and ref/remote option-injection rejection are all present in
`scripts/mcp_servers/git/`. The `04_mcp_90_inconsistencies_and_known_issues.md` entries for
`GIT-001`/`GIT-002` are stale and marked `open` despite this. The one gap confirmed to still be
live is narrower and more concrete than the original framing: `git_push`'s protected-branch check
is skipped whenever the `branch` argument is empty, and an empty `branch` resolves downstream to
the currently checked-out branch — so a caller can push to a protected branch by simply omitting
`branch` while that branch is checked out. This issue asks the Tool Owner to decide whether that
specific behavior is acceptable or must be closed.

## Background
`NC-019` is tracked in `docs/00_governance_03_issue-and-uncertainty-management.md` (Active
Items), originally sourced from `docs/04_mcp_04_05_git.md` Implementation Notes.
`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` (Status: Proposed) records the
broader target design this NC references. `docs/04_mcp_90_inconsistencies_and_known_issues.md`
tracks `MCP-003` (narrowed per its own Resolution Notes to the residual empty-`branch` gap),
`GIT-001`, and `GIT-002` — the latter two are confirmed stale as of this issue (see Problem).
`NC-020` (Git MCP audit `target` field) is tracked in parallel and does not block this issue.

## Problem
Confirmed by reading current code:

- **`GIT-001` is already resolved, contrary to its `open` status.**
  `scripts/mcp_servers/git/git_service.py::git_checkout()` (lines 246-253) and `git_pull()`
  (lines 278-285) both call `self._check_dirty_worktree(repo)` and
  `self._check_detached_head(repo)` before proceeding, whenever `dry_run` is not set, and return
  the guard's error immediately if either check fails.
- **`GIT-002` is already resolved, contrary to its `open` status.**
  `scripts/mcp_servers/git/format_output.py::format_checkout()` (lines 135-141) verifies the
  resulting active branch (and detached-HEAD state) matches what was requested and raises
  `GitServiceError` on mismatch; `format_pull()` (lines 156-159) checks for unresolved merge
  conflicts (`repo.index.unmerged_blobs()`) and raises on detection; `format_push()` (lines
  169-173) scans the push output for rejection markers (`"[rejected]"`,
  `"non-fast-forward"`, `"failed to push"`) and raises if found.
- **The `MCP-003` residual gap is confirmed still live and is more concretely exploitable than
  originally described.** `git_service.py::_validate_protected()` (lines 120-124) returns
  `(True, "")` immediately whenever `branch` is falsy, skipping
  `_check_protected_branch()` entirely. For `git_push`, `format_output.py::format_push()` then
  resolves an empty `branch` to `repo.active_branch.name` (line 165) — i.e., whatever branch is
  currently checked out. A caller can therefore push to a protected branch by invoking `git_push`
  with no `branch` argument while that branch happens to be checked out, since the protection
  check runs against the empty string, not the branch actually pushed.

## Reason for Change
This is a confirmed, concretely exploitable protected-branch bypass on a High-Severity write
surface (`git_push`), not merely a theoretical gap — the empty-`branch` short-circuit and the
active-branch fallback combine to let a write proceed against exactly the branch the protection
was meant to guard, without triggering the check. Whether the fix should be "resolve the
effective branch before checking protection" (closing the gap) or whether the current behavior is
an accepted trade-off for the single-operator/local-git trust boundary ADR-012 documents is a
decision only the Tool Owner can make — hence tracking it as `NC-019` rather than assigning it
directly for implementation.

## Implementation Intent
Two phases, per `NC-019`'s `Resolution Target`:

1. **Decision phase (this issue's primary deliverable).** Tool Owner reviews the confirmed
   empty-`branch` protected-branch bypass on `git_push` (and the equivalent short-circuit that
   applies to `git_checkout`/`git_pull`, though their default-branch semantics differ) and decides
   whether to close it or explicitly accept it as a documented trade-off.
2. **Implementation phase (only if approved).** In `_validate_protected()` or its call sites,
   resolve the *effective* branch (falling back to `repo.active_branch.name` the same way
   `format_push()` does) before checking it against the protected-branch list, rather than
   checking the raw, possibly-empty argument. Apply the same treatment consistently across
   `git_checkout`/`git_pull`/`git_push` given each resolves an empty `branch` differently.

## Target Files or Areas
- `scripts/mcp_servers/git/git_service.py` (`_validate_protected()`, call sites in
  `git_checkout()`/`git_pull()`/`git_push()`)
- `scripts/mcp_servers/git/git_security.py` (`_check_protected_branch()`)
- `scripts/mcp_servers/git/format_output.py` (`format_push()`'s active-branch fallback, for
  reference — confirms the value that should be checked)
- `docs/00_governance_03_issue-and-uncertainty-management.md` (`NC-019`)
- `docs/04_mcp_90_inconsistencies_and_known_issues.md` (`MCP-003`; see separate issue for the
  `GIT-001`/`GIT-002` status correction, out of scope here)

## Required Changes
- Record an explicit Tool Owner decision on whether to close the empty-`branch`
  protected-branch bypass on `git_push` (and, if applicable, the equivalent case for
  `git_checkout`/`git_pull`).
- If approved: change protected-branch validation to check the effective (post-default-resolution)
  branch name rather than the raw argument, consistently across all three tools.
- Update `MCP-003`'s Status/Resolution Notes once resolved, or record the "intentionally
  accepted" decision and rationale if the owner does not approve a change.

## Constraints
- ADR-012's documented single-operator/local-git trust-boundary assumption bounds the acceptable
  risk profile for this decision.
- Do not touch the already-implemented Dirty-Worktree/Detached-HEAD checks or postcondition
  verification logic — they are confirmed working and out of scope for this issue.

## Acceptance Criteria
- A Tool Owner decision on the empty-`branch` protected-branch bypass is recorded (close it, or
  explicitly accept it with documented rationale).
- If approved: `git_push` (and `git_checkout`/`git_pull` if applicable to their semantics) reject
  a push/checkout/pull that would affect a protected branch even when `branch` is omitted, verified
  by a test that checks out a protected branch locally and calls the tool with no `branch`
  argument.
- `MCP-003`'s Status/Resolution Notes and `NC-019` are updated to reflect the outcome.

## Testing Expectations
If approved: a regression test exercising `git_push` (and `git_checkout`/`git_pull` as
applicable) with an empty `branch` argument while a protected branch is checked out, asserting
the operation is rejected. Extend `tests/mcp_servers/git/test_mcp_git.py` /
`test_git_service_dispatch.py` / `test_git_security_compliance.py`.

## Documentation Impact
Yes. `docs/00_governance_03_issue-and-uncertainty-management.md` (`NC-019`) and
`docs/04_mcp_90_inconsistencies_and_known_issues.md` (`MCP-003`) must record the decision and,
if implemented, the resulting design intent and failure behavior. This issue does not cover
correcting `GIT-001`/`GIT-002`'s stale `open` status or `ADR-012`'s Known Deviations section —
tracked separately (see Dependencies).

## Out of Scope
- Correcting `GIT-001`/`GIT-002`'s stale `open` status in
  `docs/04_mcp_90_inconsistencies_and_known_issues.md` and any related `ADR-012` Known-Deviations
  cleanup — tracked as a separate documentation-correction issue.
- Implementing a Force-Push administrative capability (explicitly out of scope per ADR-012).
- GitHub MCP's protected-branch/force-push handling (already implemented separately).
- Fixing the Git MCP audit `target` field (`MCP-005`/`NC-020`) — tracked separately.
- Any change to the already-implemented Dirty-Worktree/Detached-HEAD or postcondition
  verification logic.

## Dependencies
- Related: `MCP-003` (this issue resolves its residual scope), `NC-020` (parallel, non-blocking).
- A separate issue tracks correcting `GIT-001`/`GIT-002`'s stale Known-Issues status; that
  correction can proceed independently of this issue's owner decision.

## Unresolved Questions
- Whether `git_checkout`/`git_pull`'s empty-`branch` semantics ("current tracking branch") pose
  the same protected-branch bypass risk as `git_push`'s active-branch fallback, or whether their
  different resolution paths make the bypass inapplicable to them — needs confirmation by reading
  each tool's full resolution path before deciding the fix's exact scope.

## AI Implementation Instruction
Do not implement a fix before an explicit Tool Owner decision is recorded — this issue's primary
deliverable is the decision itself. Before drafting the decision material, re-confirm the current
state of `_validate_protected()`, `format_push()`'s active-branch fallback, and the equivalent
paths in `git_checkout()`/`git_pull()` by reading `scripts/mcp_servers/git/git_service.py` and
`format_output.py` in full — this issue's evidence may go stale if either changes before review.
If implementation is authorized, apply the fix consistently across all three tools and update
`MCP-003`/`NC-019` as part of the same change.
