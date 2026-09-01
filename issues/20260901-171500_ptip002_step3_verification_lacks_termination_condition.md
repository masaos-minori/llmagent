# Step 3's adversarial verification lacks an explicit per-row termination condition

## Priority
High

## Summary
`skills/plan-to-implementation-procedure/workflow.md` Step 3's adversarial
verification instructs investigation "in this order: the target file itself, its
direct dependencies..., then related tests — expand beyond this order only when
evidence remains insufficient," but "evidence remains insufficient" is not a
checkable stopping condition — nothing states how much evidence is enough per row.

## Background
`workflow.md` Step 3: "Verify via `rg`/Read that the target file, symbol, call
path, and test currently exist and behave as described. Investigate in this
order: the target file itself, its direct dependencies (immediate
imports/importers), then related tests — expand beyond this order only when
evidence remains insufficient."

This differs from `issue-to-plan/workflow.md`'s Step 2/Step 3 (already flagged in
`itp002`) in one respect: it does state an *order* of investigation. But it does
not state a *stopping point* within or after that order — "expand beyond this
order only when evidence remains insufficient" describes the trigger for going
further, not the criterion for stopping.

## Problem
Because this Step runs once per row in a Plan's `Implementation Target Files`
table (potentially many rows per Plan), an unbounded per-row investigation depth
compounds across the whole pass — a Plan with 10 rows, each investigated to an
unbounded depth, risks disproportionate time/token cost relative to Plans this
skill is meant to process quickly (its own `SKILL.md` calls for "small,
independently reviewable" documents, implying each row's investigation should also
be bounded).

## Reason for Change
Same underlying gap as `itp002`, but concretely instantiated in a per-row loop
here — worth its own issue because the fix belongs in a different file
(`skills/plan-to-implementation-procedure/workflow.md`) and the "loop over rows"
structure gives this issue an additional compounding-cost angle `itp002` does not
have.

## Implementation Intent
Add an explicit stopping condition to Step 3's adversarial verification, scoped
per row: e.g. "stop once the target file, its direct dependencies, and its related
tests have each been checked once against the Plan's claim about them; a
disconfirming finding at any stage ends investigation for that finding (the Plan
must be corrected, not further researched) rather than triggering deeper search."

## Target Files or Areas
- `skills/plan-to-implementation-procedure/workflow.md` (Step 3)

## Required Changes
- Add a concrete, checkable stopping condition for per-row adversarial
  verification, distinct from (but consistent with) the existing investigation
  order.

## Constraints
The stopping condition must not weaken the existing "Blocking vs. Non-blocking"
evidence-gap classification later in Step 3 — a genuinely insufficient finding
still routes to `Blocked`/`Needs confirmation`, it simply should not trigger
unbounded further searching first.

## Acceptance Criteria
- Step 3 states a concrete condition under which per-row adversarial verification
  is considered complete.

## Testing Expectations
Manual review: confirm the added condition does not contradict the existing
Blocking/Non-blocking classification or the "additional target file discovery"
escalation path.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing what evidence Step 3 requires finding — only when to stop looking for
  it.

## Dependencies
Same underlying gap as `itp002` (issue-to-plan's Step 2/Step 3) — resolve
consistently if practical, but each is independently implementable since they
target different `workflow.md` files.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `workflow.md` Step 3 in full before wording the stopping condition. Ground it
in the existing investigation order (target file → dependencies → tests) rather
than inventing an unrelated criterion.
