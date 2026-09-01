# Missing Approval Record (Approved By / Date) across 10 of 12 Accepted ADRs conflicts with governance Merge Conditions

## Priority
Medium

## Summary
`docs/00_governance_01_documentation-policy.md`'s Merge Conditions list "RACI approval not obtained
from accountable party" as a Blocking Condition that prevents merge. Ten of this repository's
twelve current ADR files — including several already marked `Accepted` — have an Approval Record
with `Approved By: pending` / `Approval Date: pending`, meaning no actual approval has been
recorded for them.

## Background
Surfaced while updating ADR-001 to Accepted status (2026-08-31). ADR-001's own Approval Record
was deliberately left as `pending` per explicit instruction not to fabricate an approver or date,
with a note added that setting Status to Accepted is not itself a substitute for approval
evidence. Checking the rest of the ADR set found the same gap is pervasive, not specific to
ADR-001.

## Problem
(Evidence: Explicit in code/docs) `grep -rl "Approved By.*: pending" docs/adr/*.md` currently
matches: `ADR-001`, `ADR-002`, `ADR-004`, `ADR-005`, `ADR-006`, `ADR-007`, `ADR-008`, `ADR-009`,
`ADR-010`, `ADR-012` — all `Accepted` except ADR-012 which was itself just moved to `Accepted`.
Only `ADR-003` currently has a real Approval Record (`Approved By: architecture-reviewer`,
`Approval Date: 2026-08-20`).

## Reason for Change
An `Accepted` ADR with no recorded approver or approval date does not satisfy this repository's
own governance Merge Conditions (RACI approval), and using "pending" as if it were evidence of
approval was explicitly called out as prohibited during the ADR-001 update. Leaving this
unresolved across ten ADRs means any of them could be challenged as not actually meeting the
Accepted bar this repository's own policy defines.

## Implementation Intent
This issue does not resolve the approvals itself — that requires an actual accountable-party
decision per ADR, which only the architecture owner/RACI process can provide. The issue exists to
make the gap visible and trackable: either (a) obtain and record real Approved By/Date/Reference
values for each of the ten ADRs from the appropriate reviewer, or (b) if this repository's
practical convention is that Status=Accepted by itself constitutes sufficient sign-off (bypassing
a formal Approval Record), make that explicit as a governance policy amendment rather than leaving
contradictory "Accepted + pending approval" text scattered across ten files.

## Target Files or Areas
- `docs/adr/ADR-001-workflow-engine-mandatory.md`
- `docs/adr/ADR-002-config-isolation.md`
- `docs/adr/ADR-004-production-failure-handling-policy.md`
- `docs/adr/ADR-005-rag-source-derived-index-relationships.md`
- `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`
- `docs/adr/ADR-008-sqlite-4db-separation.md`
- `docs/adr/ADR-009-rag-ft5-text-separation.md`
- `docs/adr/ADR-010-rag-fallback.md`
- `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`
- `docs/00_governance_01_documentation-policy.md` — Merge Conditions (read-only reference, unless option (b) above is chosen)

## Required Changes
- Obtain an explicit decision from the architecture owner on which path applies: (a) collect real
  approval records per ADR, or (b) amend governance policy to define what satisfies "Accepted"
  status without a per-ADR named approver.
- If (a): fill in `Approved By`/`Approval Date`/`Approval Reference` for each of the ten ADRs with
  real values, one at a time, as each is actually reviewed and approved.
- If (b): update `00_governance_01_documentation-policy.md`'s ADR Status Definitions and/or Merge
  Conditions to state the actual current practice, and remove or reword the Approval Record
  template's implication that a named approver/date is required.

## Constraints
- Do not fabricate an approver name, date, or reference for any ADR to close this issue faster.
- Do not silently change any of the ten ADRs' Status back to `Proposed` as a workaround — the
  underlying architectural decisions have already been separately confirmed as approved in this
  repository's task history; this issue is about the Approval Record's evidentiary gap, not about
  re-litigating whether the decisions themselves are adopted.

## Acceptance Criteria
- Every currently `Accepted` ADR either has a real, non-"pending" Approval Record, or governance
  policy has been amended to define an alternative acceptance-evidence standard that these ADRs
  already satisfy.
- No ADR is left with contradictory "Accepted" status and an explicitly-flagged missing-approval
  note without a resolution path recorded.

## Testing Expectations
Not applicable — documentation/governance-process change only.

## Documentation Impact
Governance policy (`00_governance_01_documentation-policy.md`) may need updating depending on
which resolution path is chosen; each affected ADR's Approval section is the direct target.

## Out of Scope
- Re-evaluating whether any of the ten ADRs' underlying architectural decisions are correct —
  only the approval-recording gap is in scope.
- ADR-003 (already has a real Approval Record) and ADR-011/ADR-013 (deleted, merged into ADR-008/ADR-003).

## Dependencies
Discovered during the 2026-08-31 ADR-001 update. Related to the same pending-approval note left
in ADR-001's own Approval section during that update.

## Unresolved Questions
Whether this repository's actual practice is that a task-level "approved decision" instruction
(as given for ADR-001/ADR-004/ADR-012 in recent work) constitutes sufficient authority to set
Status=Accepted without a separate, named Approval Record — needs an explicit governance-owner
decision; this issue does not assume an answer.

## AI Implementation Instruction
Do not fill in any ADR's Approved By/Approval Date/Approval Reference with an invented value.
If asked to implement this issue, first obtain the owner's choice between options (a) and (b) in
Implementation Intent, and proceed only within whichever path is chosen.
