# "Needs confirmation" row outcome has no stated retry/re-attempt bound

## Priority
Low

## Summary
`skills/plan-to-implementation-procedure/workflow.md` Step 3 can report a row as
`Needs confirmation` for more than one distinct reason (traceability ambiguity, a
non-blocking evidence gap, or a resumed-cycle path collision), but never states
whether or how many times this same row may be re-attempted within the same
session before the workflow should escalate differently, unlike the file-level
`Blocked` outcomes which at least name a specific stopping action.

## Background
`workflow.md` Step 3 names three distinct triggers for `Needs confirmation`:
1. "If traceability is missing or ambiguous, do not skip the row. Report `Needs
   confirmation`."
2. "Non-blocking: a procedure can still be written with a noted caveat. Report
   `Needs confirmation` and proceed — do not skip the row."
3. "[Resumed-cycle path collision]... Stop and report `Needs confirmation` for
   this row instead."

Cases 1 and 2 both "proceed" (a document is still written, with a caveat). Case 3
explicitly "stops" for that row. Nothing states whether a `Needs confirmation`
row from case 3 (a stopped row) is meant to be retried in the same session, and if
so, how many times, before it should instead be escalated as `Blocked` to a human.

## Problem
Without a stated bound, case 3's "stop" could be read as terminal (report once,
move on to Step 4 with this row unresolved) or as retriable (try again, possibly
repeatedly, hoping the "interrupted cycle" state resolves itself) — these have very
different implications for whether Step 4's "every row... accounted for" check
(which explicitly allows a row to be accounted for as `Needs confirmation`) is
satisfied by a single stopped attempt or requires exhausting some retry budget
first.

## Reason for Change
This is the `plan-to-implementation-procedure`-specific instance of `itp003`'s
general "Stepwise retry limit" finding — worth its own issue because the specific
trigger (a resumed-cycle path collision) and the file it needs fixing in differ
from `itp003`'s Plan/Unknowns/Risks filename-collision case.

## Implementation Intent
State explicitly whether case 3's `Needs confirmation` stop is terminal for the
current cycle (report once, let Step 4's "accounted for" check treat it as
resolved-as-`Needs confirmation`, and let a human resolve the underlying
interrupted-cycle state before any future run) or bounded-retriable (retry up to N
times with a stated N).

## Target Files or Areas
- `skills/plan-to-implementation-procedure/workflow.md` (Step 3)

## Required Changes
- Add an explicit statement of whether case 3's stop is terminal-for-this-cycle or
  retriable, and if retriable, the exact retry bound.

## Constraints
Must remain consistent with Step 4's existing acceptance of `Needs confirmation`
as one of the valid "accounted for" outcomes — do not require exhausting a retry
budget as a precondition for Step 4 to proceed, unless that is the explicitly
chosen design.

## Acceptance Criteria
- Step 3 states explicitly whether the resumed-cycle-collision `Needs
  confirmation` case is terminal-for-this-cycle or has a stated retry bound.

## Testing Expectations
Manual review: confirm the added statement is consistent with Step 4's existing
"accounted for" language.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing the three `Needs confirmation` trigger conditions themselves.

## Dependencies
Related to `itp003` (issue-to-plan's analogous retry-limit gap) — resolve
independently since the two target different `workflow.md` files and different
trigger conditions.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `workflow.md` Step 3 and Step 4 in full before wording the addition.
Distinguish case 3 (stopped row, resumed-cycle collision) from cases 1-2
(proceeded row, caveated) explicitly — do not conflate them under one retry
statement if their intended behavior actually differs.
