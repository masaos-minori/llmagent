# Chained adversarial-verification corrections lack a convergence/stop condition

## Priority
Medium

## Summary
`skills/issue-to-plan/workflow.md` allows adversarial verification (Step 2) to
trigger a Plan correction, and Step 8's completeness validation can surface a
further correction need on the same or a different section — but no Step states
how many correction cycles are tolerated before the workflow must stop and escalate
instead of continuing to patch.

## Background
`workflow.md` Step 2: "If adversarial verification surfaces an unconfirmed item or
inconsistency between the Issue and current source, do not silently reconcile
it... write the corrected understanding into the Plan (Step 5)."

`workflow.md` Step 8: "...do not report `Pass` or `Completed` [if] any requirement
information is unmapped or untraceable, or `Implementation Target Files` is not
`Frozen`." A `Fail`/`Partial` here (see `itp005`) implies a correction is needed,
which — per `itp005`'s own finding — has no stated re-entry point, and once
corrected, Step 8 (or the relevant sub-check) is presumably re-run.

Nothing in the workflow states an upper bound on how many times this
correct-then-recheck cycle may repeat for a single Issue before the workflow must
stop and report a different outcome (e.g. escalate to the user, or conclude the
Issue itself is unworkable as currently written) instead of continuing to patch
the Plan.

## Problem
A Plan correction made to satisfy one check can introduce or reveal an
inconsistency elsewhere in the same document (e.g. correcting a `Requirement`'s
scope in response to Step 8 may invalidate an `Acceptance criterion` that
referenced the old scope, which the next completeness check would then flag).
Nothing prevents this from repeating indefinitely across many small patches,
distinct from the already-identified retry-count gaps in `itp003` (which covers
filename-collision retries specifically) and `itp004` (which covers Rollback
Directive's applicability) — this issue is about the correction *chain itself*
having no stated maximum length or convergence check, independent of whether any
single correction is rolled back.

## Reason for Change
Without a stated bound, a Plan could accumulate an unbounded sequence of
patch-on-patch corrections in a single cycle with no signal to the agent (or a
human reviewer) that the Issue or Plan structure itself may be the actual problem,
rather than any individual field's content.

## Implementation Intent
Add an explicit bound to the correction-chain concept — e.g. "after N consecutive
correction-and-recheck cycles for the same Plan without reaching a clean `Pass`,
stop and report `Blocked: Plan requires more than N correction cycles — {summary of
remaining issues}` rather than continuing to patch." Cross-reference `AGENTS.md`
Attempt Limit (3) as a candidate value, consistent with `itp003`'s question about
whether that same number applies here too, but state the chosen number explicitly
either way — do not leave it unstated as it currently is.

## Target Files or Areas
- `skills/issue-to-plan/workflow.md` (Step 8, or a new short note near Step 2/Step
  8)

## Required Changes
- Add an explicit maximum correction-cycle count for a single Issue's Plan before
  the workflow must stop and report `Blocked` instead of continuing to patch.
- State what the `Blocked` report should contain in this case (a summary of the
  remaining unresolved issues, not just the last one encountered).

## Constraints
This bound is about the *number of correction cycles*, not about individual
retry mechanics already covered by `itp003` (filename-collision retries) or
`itp004` (Rollback Directive applicability) — implement independently of those,
though the chosen numeric bound should be consistent across all three if
practical.

## Acceptance Criteria
- `workflow.md` states an explicit maximum number of correction-and-recheck cycles
  tolerated per Issue before escalating.
- The escalation report format is specified (a summary, not just the last
  encountered issue).

## Testing Expectations
Manual review: confirm the added bound is internally consistent with `itp003`'s
and `itp005`'s related findings.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this mechanism.

## Out of Scope
- Building actual cycle-counting tooling — this issue only requires the policy to
  be stated in the workflow document.

## Dependencies
Related to `itp003` (Attempt Limit for filename retries) and `itp005` (re-entry
point after Step 8 Fail) — resolve consistently; implement independently.

## Unresolved Questions
- The exact numeric bound (3, matching `AGENTS.md`'s general Attempt Limit, or a
  different number specific to Plan-correction chains) — left to implementation
  planning, but must be stated explicitly.

## AI Implementation Instruction
Read `AGENTS.md` Loop Prevention, and `workflow.md` Step 2 and Step 8, in full
before proposing the bound. Do not conflate this issue's correction-chain bound
with `itp003`'s filename-collision-retry bound when wording the fix — they are
related but distinct mechanisms and should be stated as separate rules even if
they end up sharing the same numeric value.
