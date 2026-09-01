# Step 3's adversarial verification lacks an explicit termination condition

## Priority
High

## Summary
`skills/code-implementation/workflow.md` Step 3 instructs adversarial
verification of the implementation procedure's claims ("check via `rg`/Read
whether the target file, symbol, line numbers, and call path it describes still
match current source...") with no stated point at which this verification is
considered sufficient — the same class of gap `itp002`/`ptip002` identify for the
two upstream phases.

## Background
`workflow.md` Step 3: "Before implementing, perform **adversarial verification**
of the procedure's claims about current source: do not assume its
Procedure/Method/Details are still accurate — check via `rg`/Read whether the
target file, symbol, line numbers, and call path it describes still match current
source, and whether any stated assumption or scope boundary is stale or
inconsistent with a sibling procedure document or the source Plan."

Unlike `plan-to-implementation-procedure/workflow.md` Step 3 (which at least
states an investigation *order* — target file, then dependencies, then tests,
addressed separately in `ptip002`), this Step states neither an order nor a
stopping point.

## Problem
Because this verification happens before every single implementation procedure
document's code changes, an unbounded verification depth compounds across a
Multi-file-processing batch exactly as `ptip002` describes for its own workflow —
here with the added consequence that this phase's verification gates actual code
changes, so excessive time spent here delays real implementation work without a
corresponding, stated increase in required rigor.

## Reason for Change
Same reasoning as `itp002`/`ptip002`, instantiated for the one phase where the
verified claims gate real code modification rather than a document's content.

## Implementation Intent
Add an explicit termination condition to Step 3's adversarial verification: e.g.
"stop once the target file, the specific symbol/line/call-path claims the
procedure makes, and its stated dependencies have each been checked once against
current source; a disconfirming finding ends investigation for that finding (the
procedure document must be corrected, not further researched) rather than
triggering deeper search."

## Target Files or Areas
- `skills/code-implementation/workflow.md` (Step 3)

## Required Changes
- Add a concrete, checkable stopping condition for Step 3's adversarial
  verification.

## Constraints
The stopping condition must not weaken the requirement to correct the
implementation procedure document when a stale claim is found — it bounds how
much *searching* happens before correcting, not whether correction happens.

## Acceptance Criteria
- Step 3 states a concrete condition under which adversarial verification is
  considered complete for the current implementation procedure document.

## Testing Expectations
Manual review: confirm the added condition is consistent with Step 3's existing
correction instruction ("correct the implementation procedure document itself...
to reflect the corrected understanding before proceeding").

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing what claims Step 3 must verify — only when to stop verifying them.

## Dependencies
Same underlying gap as `itp002` (issue-to-plan) and `ptip002`
(plan-to-implementation-procedure) — resolve consistently if practical; each is
independently implementable since all three target different `workflow.md`
files.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `workflow.md` Step 3 in full before wording the stopping condition. For
consistency, consider reusing `ptip002`'s phrasing pattern (order + stop
condition) adapted to this Step's specific claims (target file, symbol, line
numbers, call path, assumption/scope boundary).
