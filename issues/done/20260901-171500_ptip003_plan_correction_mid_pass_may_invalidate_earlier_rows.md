# Plan correction discovered mid-pass has no defined effect on already-generated rows

## Priority
High

## Summary
`skills/plan-to-implementation-procedure/workflow.md` Step 3 processes a Plan's
`Implementation Target Files` rows in table order, and allows a later row's
adversarial verification to correct the Plan document — but never states what to
do if that correction invalidates an assumption an *earlier* row's
already-generated implementation procedure document relied on.

## Background
`workflow.md` Step 3: "For each row in `Implementation Target Files`, in the order
they appear in that table... If adversarial verification finds an unconfirmed item
or an inconsistency..., correct the Plan document itself... and reflect the
corrected understanding in the generated document(s)." "the generated document(s)"
is plural but unqualified — it does not state whether this means only the document
currently being written, or also any document(s) already written for earlier rows
in the same pass.

Example: row 1 ("scripts/agent/foo.py") is processed first and its generated
document references a shared helper function's current signature. Row 3
("scripts/agent/bar.py")'s adversarial verification later discovers that helper's
signature actually changed (the Plan's Background was stale about it), corrects the
Plan's Background accordingly — but row 1's document, already written under the
old (wrong) assumption, is not revisited.

## Problem
Nothing in Step 3 requires checking whether a Plan correction made while
processing row K invalidates content already written for rows 1..K-1. Since rows
are processed once each ("one target file = one implementation procedure
document"), and the workflow does not loop back, a stale row-1 document can persist
silently through Step 4's move to `plans/done/` and the eventual `code-
implementation` phase that consumes it — exactly the kind of drift `itp001`
(issue-to-plan's equivalent check-detection gap, a different issue) exists to catch
downstream, except this is the drift's point of origin, not its later detection.

## Reason for Change
Detecting this at its origin (mid-Step-3) is cheaper and more reliable than relying
on `code-implementation`'s own later adversarial verification (which operates per
implementation-procedure document, not across the whole Plan) to catch it after the
fact.

## Implementation Intent
Add an explicit instruction to Step 3: whenever a Plan correction is made while
processing row K, check whether any already-generated document for rows 1..K-1
relied on the now-corrected claim; if so, either amend that earlier document in the
same cycle or flag it in the progress report and the Plan's Execution Status as
needing re-verification before Step 4's move.

## Target Files or Areas
- `skills/plan-to-implementation-procedure/workflow.md` (Step 3)

## Required Changes
- Add an explicit cross-row consistency check to Step 3's Plan-correction handling:
  after correcting the Plan, check whether earlier rows' already-generated
  documents relied on the corrected claim.
- State the required action when a stale earlier document is found (amend it now,
  or flag it and block Step 4 until resolved) — do not leave this to agent
  judgment.

## Constraints
This check only applies to the specific claim that was corrected — it is not a
request to re-verify every earlier document from scratch on every correction (that
would reintroduce the unbounded-cost problem `itp002`/`ptip002` already raise).

## Acceptance Criteria
- Step 3 states an explicit cross-row consistency check triggered by a Plan
  correction, scoped to the corrected claim only.
- Step 3 states the required action when an earlier row's document is found to
  rely on the corrected (now-stale) claim.

## Testing Expectations
Manual review: confirm the added check is scoped narrowly (the corrected claim
only) and does not require full re-verification of every prior row.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Building automated cross-document consistency tooling — this issue only
  requires the workflow instruction, not new tooling.

## Dependencies
Related to `itp011` (chained corrections lacking a convergence condition) — that
issue is about repeated correct-and-recheck cycles for a single item; this one is
about a correction's *lateral* effect on sibling rows already processed in the
same pass. Resolve independently.

## Unresolved Questions
- Whether "amend now" or "flag and block Step 4" should be the default action —
  left to implementation planning, but the choice must be stated explicitly.

## AI Implementation Instruction
Read `workflow.md` Step 3 in full, including "Progress recording during Step 3",
before wording the fix. Scope the added check narrowly to the specific corrected
claim, and state the required action explicitly rather than leaving it to agent
judgment — that judgment gap is exactly what this issue exists to close.
