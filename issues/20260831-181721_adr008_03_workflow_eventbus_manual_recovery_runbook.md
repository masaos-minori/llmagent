# Write the manual operator recovery runbook for workflow.sqlite / eventbus.sqlite

## Priority
Medium

## Summary
ADR-008 (post-merge, 2026-08-31) Decision Details #20 / INV-18 establishes that
`workflow.sqlite` and `eventbus.sqlite` corruption recovery is a manual operator action —
automatic restoration is prohibited. No document currently describes what that manual recovery
procedure actually consists of.

## Background
Confirmed while merging ADR-011 into ADR-008:
`recover_corruption(target="workflow"|"eventbus")` returns `action="no_recovery_allowed"` with
`detail="Automatic recovery is prohibited for {target}. Manual intervention required."`, but no
Operations/Runbook document was found describing the steps an operator should actually take.

## Problem
(Evidence: Explicit in code and confirmed by documentation search) The only Operations-facing
statement about workflow/eventbus recovery today is the error detail string returned by the
API; there is no step-by-step procedure (e.g., what backup exists, if any; how to validate a
candidate; how to manually apply it; what to do if no backup exists).

## Reason for Change
A documented policy without an accompanying runbook leaves operators unable to act when the
documented scenario (workflow/eventbus corruption) actually occurs, defeating the purpose of
documenting the policy at all.

## Implementation Intent
Write an Operations runbook section describing the manual recovery procedure for
`workflow.sqlite` and `eventbus.sqlite`, covering: what backups (if any) currently exist for
these two databases (`rotate_all_dbs()` currently excludes both — confirm current backup
coverage first), the manual steps an operator should take to validate and apply a backup if one
exists, and what to do if no backup exists (data-loss acknowledgment / escalation path).

## Target Files or Areas
- `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` or a new Operations
  document (exact placement needs confirmation)
- `scripts/db/maintenance.py` (`rotate_all_dbs()`, to confirm current backup coverage before
  writing the runbook)

## Required Changes
- Confirm current backup coverage for `workflow.sqlite`/`eventbus.sqlite` (`rotate_all_dbs()`
  scope) before drafting the runbook, since the runbook cannot recommend restoring from a
  backup that is not actually being taken.
- Draft the manual recovery procedure as an Operations document section, cross-referenced from
  ADR-008's Related Documents.
- If no backup exists for these domains today, state that explicitly as a precondition gap
  rather than describing a procedure that assumes one.

## Constraints
- Do not implement any new automatic backup or recovery code — this issue is documentation-only.
- Do not contradict ADR-008's decision that automatic restoration is prohibited for these two
  domains.

## Acceptance Criteria
- An Operations document describes the manual recovery procedure (or the explicit absence of
  one, if no backup exists) for `workflow.sqlite` and `eventbus.sqlite`.
- ADR-008's Related Documents references the new/updated runbook section.
- `uv run python tools/check_docs_quality.py` shows no new issues for the affected document.

## Testing Expectations
Not required — documentation-only change.

## Documentation Impact
This issue is itself the documentation gap it closes.

## Out of Scope
- Implementing backup coverage for workflow/eventbus if none currently exists (that would be a
  separate, code-level decision and issue).
- Changing ADR-008's recovery policy itself.

## Dependencies
Follows the 2026-08-31 ADR-011 → ADR-008 consolidation (Decision Details #20, INV-18).

## Unresolved Questions
Whether `workflow.sqlite`/`eventbus.sqlite` currently have any backup coverage at all to recover
from manually — needs confirmation before the runbook can describe a concrete procedure.

## AI Implementation Instruction
Confirm actual current backup coverage for `workflow.sqlite`/`eventbus.sqlite` in code
(`rotate_all_dbs()`) before writing the runbook. Do not describe a manual restore procedure that
assumes a backup exists if none is actually taken today — state the gap explicitly instead.
