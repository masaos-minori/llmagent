# Step 2's revalidation-correction "before continuing" does not state the re-entry point

## Priority
Medium

## Summary
`skills/plan-to-implementation-procedure/workflow.md` Step 2 says a discrepancy
found during frozen-inventory revalidation should be corrected "before
continuing," but does not state what "continuing" resumes from — the rest of Step
2, or all of Step 2 from its start, or directly into Step 3.

## Background
`workflow.md` Step 2: "Revalidate the frozen inventory per
`rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)
— Revalidation, before proceeding to Step 3. If revalidation finds a discrepancy,
correct the Plan per that section's rules before continuing."

`rules/workflow-lifecycle.md`'s Revalidation section (referenced here) states: "If
a row that was `Verified` no longer passes: Correct the Plan document... and
re-run this validation for the corrected row(s) before proceeding. Do not silently
proceed on a row that fails revalidation." This does clarify the re-entry point for
the *validation itself* (re-run validation for the corrected row(s)), but
`workflow.md` Step 2's own "before continuing" is a second, looser instruction
layered on top, and does not repeat or cross-reference that specific re-entry
detail — a reader following only `workflow.md` Step 2 (without also cross-checking
`rules/workflow-lifecycle.md`'s exact wording) could read "continuing" as simply
"proceed to Step 3" without having actually re-run the corrected row's validation.

## Problem
The instruction works correctly only if the reader also independently applies
`rules/workflow-lifecycle.md`'s more precise "re-run this validation for the
corrected row(s)" wording — `workflow.md` Step 2 itself does not restate or
cross-reference that detail tightly enough to guarantee it is not skipped.

## Reason for Change
Tightening the cross-reference removes the risk that "correct... before
continuing" is read as "correct, then move on" rather than "correct, then re-run
validation for exactly the corrected row(s), then move on."

## Implementation Intent
Reword Step 2's discrepancy-handling sentence to explicitly restate the re-entry
point: correct the Plan, re-run the Plan Freeze validation for the corrected
row(s) specifically (not the whole table, not skipped), and only then proceed to
Step 3.

## Target Files or Areas
- `skills/plan-to-implementation-procedure/workflow.md` (Step 2)

## Required Changes
- Reword Step 2's "correct the Plan per that section's rules before continuing" to
  explicitly name the re-entry point (re-run validation for the corrected row(s),
  then proceed to Step 3).

## Constraints
Do not restate `rules/workflow-lifecycle.md`'s full Revalidation procedure inline
— add only enough to make the re-entry point unambiguous from `workflow.md` Step 2
alone.

## Acceptance Criteria
- Step 2 explicitly states that correction is followed by re-running validation
  for the corrected row(s), not merely "continuing."

## Testing Expectations
Manual review: confirm the reworded sentence is consistent with
`rules/workflow-lifecycle.md`'s Revalidation section and does not introduce a
contradiction.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing `rules/workflow-lifecycle.md`'s Revalidation procedure itself.

## Dependencies
Related to `itp005` (issue-to-plan's analogous re-entry-point gap after Step 8) —
resolve independently since the two target different `workflow.md` files.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `workflow.md` Step 2 and `rules/workflow-lifecycle.md`'s Revalidation section
in full before rewording. Keep the fix to a tightened cross-reference, not a full
restatement.
