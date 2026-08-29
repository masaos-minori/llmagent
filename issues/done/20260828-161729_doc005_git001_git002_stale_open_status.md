# DOC-005: GIT-001/GIT-002 are already implemented but still tracked as `open` Known Issues

## Priority
Medium

## Summary
`docs/04_mcp_90_inconsistencies_and_known_issues.md`'s `GIT-001` (Dirty-Worktree/Detached-HEAD
guards) and `GIT-002` (postcondition verification) are both marked `Status: open`, but direct
code inspection confirms both are already implemented in
`scripts/mcp_servers/git/git_service.py` and `format_output.py`. Update both entries' `Status`
and `Resolution Notes`, and check `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`'s
Known Deviations section for the same staleness.

## Background
This was found while drafting a Tool-Owner-decision issue (`NC-019`) that initially assumed
`GIT-001`/`GIT-002` were still open, based on their documented status. Reading the actual
implementation surfaced the mismatch. `ADR-012`'s Known Deviations section also lists `GIT-001`
and `GIT-002` (and, separately, the fuller original scope of `MCP-003`) as open gaps, so it likely
needs the same correction.

Likely root cause: `issues/done/20260823_git_dirty_worktree_detached_head_issue.md` and
`issues/done/20260823_git_postcondition_verification_issue.md` (both already archived to
`issues/done/`, dated 2026-08-23) appear to be the implementation work that closed `GIT-001` and
`GIT-002` respectively — their filenames match the gap each Known Issue describes. The
implementation and archival evidently did not include updating
`docs/04_mcp_90_inconsistencies_and_known_issues.md`'s `Status` field, which is how this
documentation fell out of sync with the code it describes. This suggests the project's
issue-closure procedure should include a docs-sync step for `Status`/`Resolution Notes` when an
implementation issue closes a tracked Known Issue — worth raising separately if this pattern
recurs.

## Problem
- `GIT-001`'s `Observed Implementation` states: "`git_checkout` calls `git reset --hard`
  unconditionally; `git_pull` calls `git pull` without checking for uncommitted changes first."
  Current code: `scripts/mcp_servers/git/git_service.py::git_checkout()` (lines 246-253) and
  `git_pull()` (lines 278-285) both call `self._check_dirty_worktree(repo)` and
  `self._check_detached_head(repo)` before proceeding (unless `dry_run` is set), returning the
  guard's error if either check fails.
- `GIT-002`'s `Observed Implementation` states: "`git_checkout` returns success ... without
  verifying the branch actually changed; `git_pull` returns success ... without verifying the
  remote refs updated." Current code: `scripts/mcp_servers/git/format_output.py::format_checkout()`
  (lines 135-141) verifies the resulting branch/detached-HEAD state and raises `GitServiceError`
  on mismatch; `format_pull()` (lines 156-159) checks for unresolved merge conflicts and raises on
  detection; `format_push()` (lines 169-173) scans for push-rejection markers and raises if found.
- Both entries' `Status: open` and `Observed Implementation` text predate whatever change
  actually implemented these checks, and were not updated when that change landed.

## Reason for Change
Known Issues that are actually already resolved but still marked `open` mislead anyone (human or
AI) using this document to scope future Git MCP work — as happened while drafting `NC-019` in
this same session, where the stale status caused an issue to be drafted against work that was
already done. Correcting this prevents duplicate effort and keeps the Known Issues doc usable as
a source of truth for what is actually still open (per this doc's own purpose).

## Implementation Intent
Documentation-only change. Update `GIT-001` and `GIT-002`'s `Status` to `resolved` and rewrite
their `Observed Implementation`/`Resolution Notes` fields to describe the current, confirmed
behavior with a reference to the responsible functions. As of this issue's drafting, the
following tests exist and pass (confirmed by running
`pytest tests/mcp_servers/git/test_git_security_compliance.py tests/mcp_servers/git/test_format_output.py`,
56 passed) and can be cited directly in `Resolution Notes` instead of a vague "covered by tests"
claim: `test_git_checkout_dirty_worktree_denied`, `test_git_pull_dirty_worktree_denied`,
`test_git_checkout_detached_head_denied`, `test_git_pull_detached_head_denied` (all in
`test_git_security_compliance.py`, GIT-001) and `test_checkout_postcondition_failure_wrong_branch`,
`test_checkout_postcondition_failure_detached_head`,
`test_pull_postcondition_failure_unresolved_conflicts`,
`test_push_postcondition_failure_rejection_marker_in_output` (all in `test_format_output.py`,
GIT-002). Re-confirm these still exist and pass at implementation time rather than trusting this
list indefinitely — the repo has other sessions actively modifying it concurrently. Check `ADR-012`'s Known Deviations section
and Verification/Completion-Criteria language for the same staleness and correct it if found —
`ADR-012`'s Status may also need reassessment (still `Proposed`) now that a meaningful portion of
its scope (`GIT-001`, `GIT-002`, and per `MCP-003`'s own Resolution Notes, protected-branch and
ref/remote validation) is confirmed implemented, though the residual `MCP-003` gap tracked in
`NC-019` remains open and should not be closed by this correction alone.

## Target Files or Areas
- `docs/04_mcp_90_inconsistencies_and_known_issues.md` (`GIT-001`, `GIT-002`)
- `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` (Known Deviations; Status — verify
  only, do not change Status without owner input per Constraints)
- Reference for correct current behavior: `scripts/mcp_servers/git/git_service.py`,
  `scripts/mcp_servers/git/format_output.py`

## Required Changes
- Update `GIT-001`'s `Status` to `resolved`, with `Resolution Notes` describing
  `_check_dirty_worktree()`/`_check_detached_head()`'s enforcement in `git_checkout()`/`git_pull()`.
- Update `GIT-002`'s `Status` to `resolved`, with `Resolution Notes` describing
  `format_checkout()`/`format_pull()`/`format_push()`'s postcondition checks.
- Update `ADR-012`'s Known Deviations entries for `GIT-001`/`GIT-002` to reflect the resolved
  state, and re-check its Verification section's test-existence claims against the actual test
  suite (`tests/mcp_servers/git/`) rather than assuming they are still pending.
- Do not change `ADR-012`'s `Status` field (Proposed → Accepted) as part of this issue — that is
  an owner decision tied to `NC-019`'s residual scope, not a mechanical documentation fix.

## Constraints
Documentation-only: do not modify `scripts/mcp_servers/git/git_service.py`,
`format_output.py`, `git_security.py`, or any other implementation file as part of this issue.

## Acceptance Criteria
- `GIT-001` and `GIT-002` in `docs/04_mcp_90_inconsistencies_and_known_issues.md` are marked
  `resolved` with `Resolution Notes` citing the actual implementing functions.
- `ADR-012`'s Known Deviations section no longer lists `GIT-001`/`GIT-002` as unqualified open
  gaps.
- `MCP-003`'s entry and `NC-019` (the residual empty-`branch` protected-branch bypass) are left
  untouched by this issue — they remain open and are tracked separately.

## Testing Expectations
Not required — documentation-only change. Manual verification: re-read
`scripts/mcp_servers/git/git_service.py::git_checkout()`/`git_pull()` and
`format_output.py::format_checkout()`/`format_pull()`/`format_push()`, and check for existing
tests covering these behaviors in `tests/mcp_servers/git/` to cite accurately in the updated
`Resolution Notes` (do not claim a specific test name without confirming it exists).

## Documentation Impact
Yes — this issue is entirely a documentation correction. See Required Changes.

## Out of Scope
- The residual `MCP-003` gap (empty-`branch` protected-branch bypass) and its `NC-019`
  owner-decision — tracked separately and must remain open.
- `ADR-012`'s `Status` transition (Proposed → Accepted/Rejected) — an owner decision, not a
  mechanical correction.
- The Git MCP audit `target` field (`MCP-005`/`NC-020`) — unrelated, tracked separately.

## Dependencies
- Related: `NC-019` (residual `MCP-003` scope must stay open after this correction), `ADR-012`.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Before editing, re-confirm the current implementation by reading
`scripts/mcp_servers/git/git_service.py::git_checkout()`/`git_pull()` and
`format_output.py::format_checkout()`/`format_pull()`/`format_push()` in full, and check
`tests/mcp_servers/git/` for tests actually covering these checks so `Resolution Notes` can cite
real test names rather than guessing. Do not close or modify `MCP-003` or `NC-019` — the
empty-`branch` protected-branch bypass they track is confirmed still open and must remain so.
Do not change `ADR-012`'s `Status` field.
