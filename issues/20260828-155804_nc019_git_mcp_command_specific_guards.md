# NC-019: Git MCP protected-branch bypass via empty `branch` argument on `git_push`/`git_pull` — owner decision needed

## Priority
High

## Summary
`NC-019` originally asked whether Git MCP's lack of command-specific guards
(Dirty-Worktree/Detached-HEAD/ref-remote validation/postcondition verification) for
`git_checkout`/`git_pull`/`git_push` was intentional or a missing security feature. Code
inspection found that most of that original scope is already implemented (Dirty-Worktree/
Detached-HEAD checks, postcondition verification, ref/remote option-injection rejection are all
present). Adversarial verification — including a live reproduction in a scratch repository —
confirms the residual, genuinely exploitable gap is: an empty `branch` argument skips the
protected-branch check on **both `git_push` and `git_pull`** (not `git_push` alone), because each
resolves an empty `branch` to the currently checked-out branch downstream, while the protection
check runs against the empty string. `git_checkout` was independently confirmed **not** affected
— GitPython itself rejects an empty branch/ref before any checkout can occur, for both its
create and non-create code paths. This issue asks the Tool Owner to decide whether the confirmed
`git_push`/`git_pull` bypass is acceptable or must be closed.

## Background
`NC-019` is tracked in `docs/00_governance_03_issue-and-uncertainty-management.md` (Active
Items), originally sourced from `docs/04_mcp_04_05_git.md` Implementation Notes.
`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` (Status: Proposed) records the
broader target design this NC references. `docs/04_mcp_90_inconsistencies_and_known_issues.md`
tracks `MCP-003` (narrowed per its own Resolution Notes to this residual gap), `GIT-001`, and
`GIT-002` — the latter two are confirmed stale (`Status: open` despite being implemented; see
`DOC-005`). `NC-020` (Git MCP audit `target` field) is tracked in parallel and does not block
this issue.

Separately from this issue's scope: `docs/04_mcp_04_05_git.md` itself — the primary per-server
spec doc, and the document `NC-019`/`MCP-003` name as their `Source File`/`Target` — is
independently confirmed to be significantly stale in the same direction as `GIT-001`/`GIT-002`
(e.g., it still states "no Dirty-Worktree check... no Detached-HEAD control" for `git_checkout`,
and a "Postcondition verification: not implemented" section header, both false as of current
code; one such line was edited as recently as 2026-08-27, a day after the guards it describes as
absent were added in code on 2026-08-26, and still re-affirmed "still true"). This is a larger
staleness problem than `GIT-001`/`GIT-002` alone and is not fixed by this issue or by `DOC-005`
(which only corrects the known-issues doc) — it is flagged here as a candidate for a follow-up
documentation-correction issue, not implemented as part of `NC-019`.

## Problem
Confirmed by reading current code, and by live reproduction in a scratch git repository:

- **`_validate_protected()` (`scripts/mcp_servers/git/git_service.py` lines 120-124) returns
  `(True, "")` immediately whenever `branch` is falsy**, skipping `_check_protected_branch()`
  entirely.
- **`git_push` bypass — confirmed.** `format_output.py::format_push()` (line 165) resolves an
  empty `branch` to `repo.active_branch.name` — whatever branch is currently checked out. A
  caller can push to a protected branch by invoking `git_push` with no `branch` argument while
  that branch is checked out, since the protection check runs against the empty string, not the
  branch actually pushed.
- **`git_pull` bypass — confirmed by live reproduction, not merely by parallel code structure.**
  `format_output.py::format_pull()` (lines 152-155) only appends `branch` to the pull command
  `if req.branch:`; when empty, it runs plain `repo.git.pull(remote)`, which merges into whatever
  branch is currently checked out. Reproduced directly: with a bare remote and two clones, pushing
  an update to `master` from one clone and then running `git_pull` with no `branch` argument in
  the other clone (on `master`, clean worktree) fast-forward-merged into `master` without
  complaint — `config/git_mcp_server.toml`'s `protected_branches` list includes `master`, and this
  repository's own working branch is `master`. `GitPullRequest`'s own schema documents `branch`'s
  default as `""` meaning "current tracking branch," which is precisely the value that defeats
  the protection check.
- **`git_checkout` — confirmed NOT affected, closing what was previously an open question.**
  `GitCheckoutRequest.branch` is a mandatory field with no default (unlike `git_pull`/`git_push`'s
  optional, empty-defaulting field), so an empty value cannot reach this path via normal request
  construction; and even if it did, GitPython rejects it before any checkout occurs — verified
  directly: the non-create path (`repo.git.checkout("--", "")`) raises
  `GitCommandError: fatal: empty string is not a valid pathspec`, and the `create=True` path
  (`repo.create_head("")`) raises `ValueError: references cannot end with a forward slash (/)`.
  Both are caught by `_wrap_git_op()`'s `_GIT_ERRORS` handling and returned as failures before any
  branch change happens; `format_checkout()`'s postcondition check would also reject an
  empty-branch "success" since no branch is ever actually named `""`.

## Reason for Change
This is a confirmed, concretely exploitable protected-branch bypass on two of Git MCP's
High-Severity write tools (`git_push` and `git_pull`), reproduced directly rather than inferred
from code reading alone — not a theoretical gap. The empty-`branch` short-circuit and each tool's
active-branch/current-branch fallback combine to let a write proceed against exactly the branch
the protection was meant to guard, without triggering the check. Whether the fix should be
"resolve the effective branch before checking protection" (closing the gap for both tools) or
whether the current behavior is an accepted trade-off for the single-operator/local-git trust
boundary ADR-012 documents is a decision only the Tool Owner can make — hence tracking it as
`NC-019` rather than assigning it directly for implementation. `git_checkout` is excluded from
this decision entirely, since it is confirmed not exploitable by construction.

## Implementation Intent
Two phases, per `NC-019`'s `Resolution Target`:

1. **Decision phase (this issue's primary deliverable).** Tool Owner reviews the confirmed
   empty-`branch` protected-branch bypass on `git_push` and `git_pull` and decides whether to
   close it or explicitly accept it as a documented trade-off. `git_checkout` requires no
   decision — it is not affected.
2. **Implementation phase (only if approved).** In `_validate_protected()` or its call sites in
   `git_push()`/`git_pull()`, resolve the *effective* branch (the same fallback each tool's
   `format_*` function already applies — `repo.active_branch.name` for `git_push`, the current
   branch for `git_pull`) before checking it against the protected-branch list, rather than
   checking the raw, possibly-empty argument. Do not apply any change to `git_checkout` — it is
   confirmed unaffected and needs no fix.

## Target Files or Areas
- `scripts/mcp_servers/git/git_service.py` (`_validate_protected()`, call sites in
  `git_push()`/`git_pull()` — not `git_checkout()`)
- `scripts/mcp_servers/git/git_security.py` (`_check_protected_branch()`)
- `scripts/mcp_servers/git/format_output.py` (`format_push()`'s active-branch fallback,
  `format_pull()`'s empty-`branch` handling — for reference, confirms the effective value that
  should be checked)
- `docs/00_governance_03_issue-and-uncertainty-management.md` (`NC-019`)
- `docs/04_mcp_90_inconsistencies_and_known_issues.md` (`MCP-003`; see separate issue for the
  `GIT-001`/`GIT-002` status correction, out of scope here)
- Not in scope: `docs/04_mcp_04_05_git.md` — independently confirmed stale in a broader way (see
  Background); flagged as a candidate follow-up issue, not implemented here.

## Required Changes
- Record an explicit Tool Owner decision on whether to close the empty-`branch`
  protected-branch bypass on `git_push` and `git_pull`.
- If approved: change protected-branch validation to check the effective (post-default-resolution)
  branch name rather than the raw argument, for `git_push` and `git_pull` only.
- Update `MCP-003`'s Status/Resolution Notes once resolved, or record the "intentionally
  accepted" decision and rationale if the owner does not approve a change.
- Explicitly record that `git_checkout` was investigated and confirmed not affected, so a future
  reader does not re-open the question.

## Constraints
- ADR-012's documented single-operator/local-git trust-boundary assumption bounds the acceptable
  risk profile for this decision.
- Do not touch the already-implemented Dirty-Worktree/Detached-HEAD checks or postcondition
  verification logic — they are confirmed working and out of scope for this issue.
- Do not change `git_checkout`'s branch handling — confirmed not exploitable; no fix needed.

## Acceptance Criteria
- A Tool Owner decision on the empty-`branch` protected-branch bypass is recorded (close it, or
  explicitly accept it with documented rationale).
- If approved: `git_push` and `git_pull` reject a push/pull that would affect a protected branch
  even when `branch` is omitted, verified by a regression test that reproduces the exact scenario
  confirmed during this issue's verification (bare remote + two clones; push from one, then
  `git_pull`/`git_push` with no `branch` argument from the other while a protected branch is
  checked out).
- `MCP-003`'s Status/Resolution Notes and `NC-019` are updated to reflect the outcome.

## Testing Expectations
If approved: a regression test exercising `git_push` and `git_pull` with an empty `branch`
argument while a protected branch is checked out, asserting the operation is rejected — modeled
on the reproduction used during this issue's verification (bare remote, two clones, one pushes,
the other calls the tool with no `branch` argument). Extend
`tests/mcp_servers/git/test_git_service_dispatch.py` / `test_git_security_compliance.py`. No new
test is needed for `git_checkout` — its existing protected-branch tests already pass an explicit
branch name and its empty-branch case is structurally rejected before reaching that logic.

## Documentation Impact
Yes. `docs/00_governance_03_issue-and-uncertainty-management.md` (`NC-019`) and
`docs/04_mcp_90_inconsistencies_and_known_issues.md` (`MCP-003`) must record the decision and,
if implemented, the resulting design intent and failure behavior, scoped to `git_push`/`git_pull`
only. This issue does not cover correcting `GIT-001`/`GIT-002`'s stale `open` status (tracked
separately as `DOC-005`) or `docs/04_mcp_04_05_git.md`'s broader staleness (flagged in
Background as a candidate follow-up, not in this issue's scope).

## Out of Scope
- Correcting `GIT-001`/`GIT-002`'s stale `open` status in
  `docs/04_mcp_90_inconsistencies_and_known_issues.md` — tracked separately (`DOC-005`).
- Correcting `docs/04_mcp_04_05_git.md`'s broader staleness (its Dirty-Worktree/Detached-HEAD/
  postcondition sections still describe already-implemented guards as absent) — flagged in
  Background as worth a separate documentation-correction issue; not implemented here.
- Implementing a Force-Push administrative capability (explicitly out of scope per ADR-012).
- GitHub MCP's protected-branch/force-push handling (already implemented separately).
- Fixing the Git MCP audit `target` field (`MCP-005`/`NC-020`) — tracked separately.
- Any change to `git_checkout`'s branch handling, or to the already-implemented
  Dirty-Worktree/Detached-HEAD or postcondition verification logic.

## Dependencies
- Related: `MCP-003` (this issue resolves its residual scope), `NC-020` (parallel, non-blocking),
  `DOC-005` (parallel Known-Issues staleness correction for `GIT-001`/`GIT-002`).
- A separate, not-yet-filed issue would be warranted for `docs/04_mcp_04_05_git.md`'s broader
  staleness (see Background) — out of scope here, noted for follow-up.

## Unresolved Questions
N/A: none — the original question (does `git_checkout` share this exposure?) was investigated
and answered during this issue's verification: confirmed not affected (see Problem).

## AI Implementation Instruction
Do not implement a fix before an explicit Tool Owner decision is recorded — this issue's primary
deliverable is the decision itself. Before drafting the decision material, re-confirm the current
state of `_validate_protected()` and `format_push()`/`format_pull()`'s effective-branch fallback
by reading `scripts/mcp_servers/git/git_service.py` and `format_output.py` in full — this issue's
evidence may go stale if either changes before review. If implementation is authorized, apply the
fix to `git_push` and `git_pull` only — do not touch `git_checkout`, which is confirmed
unaffected — and update `MCP-003`/`NC-019` as part of the same change. Reproduce the bare-remote/
two-clone scenario described in Testing Expectations to verify the fix closes the gap rather than
relying on a unit-level assertion alone.
