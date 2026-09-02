# H-01: Git MCP write-protection status is stale/contradictory across NC-019, MCP-003, and ADR-012 despite the underlying guards being implemented and tested

## Priority
High

## Summary
Three tracking documents disagree about whether Git MCP's write-protection gaps are open or
resolved: `NC-019` (governance Needs-Confirmation inventory) and `MCP-003` (MCP Known Issues)
both still show `Status: open`, while `00_security_02_high-risk-tool-common-policy.md` states the
same guards "are implemented." Code and test inspection confirms the common-policy doc is
correct and the two `open` statuses are stale — the underlying fixes already shipped. This issue
asks for the three documents to be corrected to a single, consistent, current state.

## Background
- `NC-019` (`docs/00_governance_03_issue-and-uncertainty-management.md`) originally asked whether
  Git MCP's missing command-specific guards were intentional. It was already investigated and
  resolved once: issue `issues/done/20260828-155804_nc019_git_mcp_command_specific_guards.md`
  narrowed it to a single concrete gap (protected-branch bypass via empty `branch` on
  `git_push`/`git_pull`) and plan `plans/done/20260829-090751_nc019_plan.md` specified the fix.
  Evidence label: `Verified by test` — commit `800aea33e` ("fix: reject empty branch in
  `_validate_protected` to prevent protected-branch bypass") implements exactly this fix in
  `scripts/mcp_servers/git/git_service.py::_validate_protected()`, and
  `tests/mcp_servers/git/test_git_security_compliance.py::test_git_push_with_empty_branch_returns_denied`
  / `test_git_pull_with_empty_branch_returns_denied` cover it. Despite this, the `NC-019` entry in
  the governance doc was never updated or removed — it still carries its original `Status: open`,
  `Last Reviewed: 2026-08-21`, and Evidence text ("confirmed exploitable gap (forced
  checkout/push)") predating both the investigation and the fix.
- `MCP-003` (`docs/04_mcp_90_inconsistencies_and_known_issues.md`) is `Status: open`, but its own
  `Resolution Notes` field already states the remaining scope was narrowed to `GIT-001`
  (Dirty-Worktree/Detached-HEAD) and `GIT-002` (postcondition verification) — both listed in the
  same document with `Status: resolved`, each citing passing tests. The parent `MCP-003` entry was
  never flipped to `resolved` to match. This is a self-contradiction within one document, not just
  across documents.
- `00_security_02_high-risk-tool-common-policy.md`'s "Tool-specific exceptions" section states:
  "Dirty-Worktree/Detached-HEAD guards and postcondition verification are implemented (see
  `04_mcp_90_inconsistencies_and_known_issues.md`)" — this claim is accurate (`Verified by test`,
  per `GIT-001`/`GIT-002`'s own Resolution Notes) but points a reader at a source document whose
  parent entry (`MCP-003`) still displays `open`, making the policy doc look wrong on a surface
  read.
- `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` Known Deviations also still lists
  "`MCP-003` — no protected-branch/Force-Push guard; confirmed option-injection exploit via
  `branch`/`remote`" as an open Known Issue, which is stale for the same reason: protected-branch
  enforcement and `branch`/`remote` option-injection rejection are implemented and covered by
  `test_check_protected_branch` and `test_is_safe_ref` (`Verified by test`).
- Separately, three unexecuted plans were found proposing to flip `MCP-003` to `resolved`
  (`plans/20260901-081741_plan.md`, `plans/20260901-214523_plan.md`, `plans/20260901-223706_plan.md`
  — all three generated from the same source issue,
  `issues/done/20260831-185650_adr012_02_mcp_known_issues_stale_status.md`, none moved to
  `plans/done/`, none show completed Execution Status). Decided: `plans/20260901-223706_plan.md`
  is carried forward — it is the most complete of the three (explicitly excludes `CI-002`, and
  treats MCP-004 items (2)/(3) re-verification as a blocking precondition rather than an
  informational note). The other two have been deleted (`git rm`) as redundant duplicates. See
  Dependencies.

## Problem
Documentation states two different things about the same technical fact (Git MCP write-protection
guard completeness) depending on which file is read, and one of the two known-issue trackers is
internally self-contradicting. A reader following `00_security_02_high-risk-tool-common-policy.md`
will conclude guards are implemented; a reader following `NC-019` or `MCP-003`'s `Status` field
alone will conclude a confirmed exploitable gap remains open. Both cannot be simultaneously
presented as current without a note explaining which is stale.

## Reason for Change
This is a security-relevant documentation/code mismatch: an operator or reviewer deciding whether
Git MCP's write tools are safe to rely on gets a different answer depending on which document they
consult. `NC-019` and `MCP-003`'s stale `open` status also creates governance risk — future
audits or `tools/check_needs_confirmation_inventory.py`-style checks would treat these as live,
unresolved High-severity gaps requiring action, when the underlying work is already done and
tested. Leaving three duplicate, unexecuted plans in `plans/` targeting only part of this problem
adds further risk of divergent or redundant fixes being applied independently.

## Implementation Intent
Reconcile all four documents to reflect the same, currently-true state, using the evidence already
available (commits, tests) rather than re-investigating the underlying code:
- Update `NC-019` in `docs/00_governance_03_issue-and-uncertainty-management.md` per the Part 1/2
  lifecycle rule ("removed from this active inventory once it is resolved") — remove the `NC-019`
  entry from Active Items entirely (decided: follow the governance doc's literal removal
  convention, not `MCP-003`'s keep-with-resolved-status convention). Record commit `800aea33e` and
  the two regression tests as the closing evidence in the edit/commit message, since the entry
  itself will no longer exist in the doc to carry that note.
- Update `MCP-003` in `docs/04_mcp_90_inconsistencies_and_known_issues.md`: change `Status` from
  `open` to `resolved`, with `Resolution Notes` pointing to `GIT-001`/`GIT-002` (already
  `resolved`) plus the empty-`branch` fix (commit `800aea33e`) that closed the last residual gap
  `NC-019` had identified.
- Update `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` Known Deviations: remove or
  correct the stale `MCP-003` bullet to match its corrected status; the existing "Resolved: MCP-005"
  bullet in the same list is the precedent format to follow.
- Do not alter `00_security_02_high-risk-tool-common-policy.md`'s Git MCP claim — it is already
  accurate; only its cross-reference target document needs correcting.
- `plans/20260901-223706_plan.md` (kept; the other two duplicates were deleted) already covers the
  `MCP-003`/`MCP-004`/`MCP-005` correction in `docs/04_mcp_90_inconsistencies_and_known_issues.md`.
  It explicitly excludes `NC-019` and `ADR-012` changes, so it must be extended (or a
  follow-on plan added) to also cover this issue's `NC-019` removal and `ADR-012` Known
  Deviations correction — do not treat `plans/20260901-223706_plan.md` alone as satisfying this
  issue's full scope.

## Target Files or Areas
- `docs/00_governance_03_issue-and-uncertainty-management.md` (`NC-019` entry, Active Items)
- `docs/04_mcp_90_inconsistencies_and_known_issues.md` (`MCP-003` entry)
- `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` (Known Deviations section)
- Not a target: `00_security_02_high-risk-tool-common-policy.md` — its claim is already correct
  (`Verified by test`); no change needed there.

## Required Changes
- Remove or resolve the `NC-019` entry in the governance Needs-Confirmation inventory, citing
  commit `800aea33e` and the two empty-branch regression tests as closing evidence.
- Change `MCP-003`'s `Status` field from `open` to `resolved` in the MCP Known Issues doc, updating
  `Resolution Notes` to state the full original scope (protected-branch/Force-Push guard,
  option-injection rejection, Dirty-Worktree/Detached-HEAD, postcondition verification, and the
  empty-`branch` bypass) is now closed, with pointers to `GIT-001`, `GIT-002`, and the
  `800aea33e` commit/tests.
- Correct or remove the stale `MCP-003` bullet in `ADR-012`'s Known Deviations list.
- Resolve the duplicate-plan situation: pick one of `plans/20260901-081741_plan.md`,
  `plans/20260901-214523_plan.md`, `plans/20260901-223706_plan.md` to carry forward (or supersede
  all three with a new plan generated from this issue) and note the disposition of the other two
  so they are not executed redundantly later.

## Constraints
- Do not re-open or re-investigate the underlying code for `GIT-001`/`GIT-002`/`NC-019`'s
  empty-`branch` fix — all three already have `Verified by test` evidence; this issue is a
  documentation-consistency correction, not a re-verification task.
- Follow this repository's Needs-Confirmation lifecycle rule exactly (`00_governance_03...md` Part
  2: "removed from the Active Items list ... once it is resolved," not left with a closed-out
  status) — do not invent a new status value for `NC-019`.
- Preserve `04_mcp_90_inconsistencies_and_known_issues.md`'s existing template fields and format
  used by `GIT-001`/`GIT-002`/`MCP-005` (the precedent for how a "narrowed-then-resolved" parent
  entry should read).

## Acceptance Criteria
- `NC-019` no longer appears at all in `docs/00_governance_03_issue-and-uncertainty-management.md`'s
  Active Items list (removed per the lifecycle rule, not left with any status marker).
- `MCP-003`'s `Status` field in `docs/04_mcp_90_inconsistencies_and_known_issues.md` reads
  `resolved`, with `Resolution Notes` citing `GIT-001`, `GIT-002`, and commit `800aea33e`/its
  tests.
- `ADR-012`'s Known Deviations no longer lists `MCP-003` as an open protected-branch/option-injection
  gap.
- `00_security_02_high-risk-tool-common-policy.md`'s Git MCP claim and the corrected `MCP-003`
  entry are mutually consistent when read together (no reader can conclude both "implemented" and
  "open, confirmed exploitable gap" about the same guards).
- `plans/20260901-223706_plan.md` is extended (or a follow-on plan is added) to also cover the
  `NC-019` removal and `ADR-012` Known Deviations correction, so this issue's full scope is
  covered by a single, non-duplicated plan.
- `tools/check_needs_confirmation_inventory.py` passes after `NC-019` is removed/updated.

## Testing Expectations
Documentation-only change; no code behavior changes. Run
`uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`,
`uv run python tools/check_docs_consistency.py --domain mcp`, and
`uv run python tools/check_needs_confirmation_inventory.py` per `routing.md` "When to run which
tool" for any edit under `docs/`.

## Documentation Impact
Yes — this issue is entirely a documentation-consistency correction across the governance
Needs-Confirmation inventory, the MCP Known Issues doc, and ADR-012's Known Deviations section, per
the Documentation Impact fields above.

## Out of Scope
- Any change to `scripts/mcp_servers/git/` code — the underlying fixes are already implemented and
  tested; this issue only corrects tracking documents.
- `docs/04_mcp_04_05_git.md`'s own staleness (it independently describes some of these guards as
  absent) — already flagged as a candidate follow-up in
  `issues/done/20260828-155804_nc019_git_mcp_command_specific_guards.md` Background, not yet filed
  as its own issue, and not part of this issue's scope.
- `MCP-004` (approval risk-tier mapping) and its own remaining sub-items — tracked separately, not
  part of this contradiction.
- Any change to `00_security_02_high-risk-tool-common-policy.md` — its content is already correct.

## Dependencies
- Builds on: `plans/20260901-223706_plan.md` (kept after maintainer decision; covers
  `MCP-003`/`MCP-004`/`MCP-005` correction in `docs/04_mcp_90_inconsistencies_and_known_issues.md`)
  — needs extending to also cover this issue's `NC-019` and `ADR-012` scope, since that plan's
  own Scope explicitly excludes both. `plans/20260901-081741_plan.md` and
  `plans/20260901-214523_plan.md` were duplicates of the same source issue and have been deleted.
- Related, already resolved: `GIT-001`, `GIT-002`, `MCP-005`, `NC-020` (audit `target` field fix,
  commit `6708ff710`).
- Prior issue/plan: `issues/done/20260828-155804_nc019_git_mcp_command_specific_guards.md`,
  `plans/done/20260829-090751_nc019_plan.md` (implemented the code fix; scoped documentation
  updates for `NC-019`/`MCP-003` out, deferring them to a follow-up — this issue is that
  follow-up).

## Unresolved Questions
- Whether the ~65 other unexecuted files currently in `plans/` (observed during this
  investigation, unrelated in content to `MCP-003`) reflect an unrelated, larger process issue
  worth its own investigation — noted here only as an observation, explicitly out of scope for
  this issue, and not something this issue's acceptance criteria depend on.

## AI Implementation Instruction
Do not modify any file under `scripts/` or `tests/` — this issue is documentation-only. When
editing `docs/00_governance_03_issue-and-uncertainty-management.md`, remove the entire `NC-019`
entry from Active Items (decided: full removal, not a `resolved` status marker — that status value
does not exist in this document's Status Values list). Before editing, re-read the current state of
`NC-019`, `MCP-003`, `GIT-001`, `GIT-002`, and the `ADR-012` Known Deviations bullet in full, since
further edits may have landed since this issue was filed. `plans/20260901-223706_plan.md` covers
only `MCP-003`/`MCP-004`/`MCP-005` — extend it (or add a follow-on plan) for `NC-019` and
`ADR-012`; do not treat it as already covering this issue's full scope.
