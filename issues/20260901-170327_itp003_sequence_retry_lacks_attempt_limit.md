# Zero-padded-sequence collision retry has no attempt-limit guard

## Priority
Medium

## Summary
`skills/issue-to-plan/workflow.md` Steps 5 and 6 retry a colliding output path
(`plans/{timestamp}_plan.md`, `issues/{timestamp}_unknowns.md` /
`_risks.md`) by incrementing a zero-padded sequence, but neither Step states
whether `AGENTS.md`'s "Attempt Limit: Maximum 3 attempts for the same error" rule
applies to this retry loop, or what a runaway sequence (e.g. concurrent agents
colliding repeatedly) should do instead of retrying indefinitely.

## Background
`workflow.md` Step 5: "If that path already exists, use the lowest available
zero-padded sequence (`plans/{timestamp}_01_plan.md`, `plans/{timestamp}_02_plan.md`,
...)." Step 6 applies "the same lowest-available zero-padded sequence rule as Step
5" for `issues/{timestamp}_unknowns.md` / `_risks.md`.

`tools/generate_workitem.py`'s own docstring documents this as reject-only (no
auto-increment) — the *caller* (this workflow) is the one responsible for
retrying with the next sequence number, per this session's recent tool-integration
work (`skills/issue-to-plan/workflow.md` Step 5/6's "Optionally scaffold..." notes).

`AGENTS.md` Loop Prevention > Attempt Limit: "Maximum 3 attempts for the same
error. After 3 failures, stop executing and report a summary... — do not continue
blindly."

## Problem
Neither Step 5 nor Step 6 states:
1. Whether a sequence collision counts as "the same error" under the Attempt Limit
   rule (if so, the retry loop should stop and report after 3 collisions, not keep
   incrementing).
2. What the workflow should do if it *does* stop after some bound — is a
   3-collision streak actually the wrong bound for what is presumably a rare
   filesystem race, or is it the right bound and simply undocumented?

Without an explicit answer, an agent following the letter of "use the lowest
available zero-padded sequence" could increment indefinitely (`_01`, `_02`, `_03`,
... `_99`) in a pathological case (e.g. many concurrent agents processing
overlapping Issues in the same second), which both wastes time and produces a
confusing pile of near-duplicate filenames before any stop condition is reached.

## Reason for Change
A concurrent multi-agent Issue-processing scenario is exactly what Step 1.5's
duplicate-Plan check exists to guard against — the same class of race applies to
filename collisions in Step 5/6. Leaving the retry bound unstated is inconsistent
with the rest of the workflow's careful handling of concurrency-driven duplication.

## Implementation Intent
State an explicit retry bound for the Step 5/6 sequence-collision retry loop (e.g.
"retry up to 3 times before stopping and reporting `Blocked: repeated filename
collision — {path}`"), and clarify whether this bound is the same 3-attempt limit
`AGENTS.md` defines for "the same error" or a workflow-specific bound justified on
its own terms.

## Target Files or Areas
- `skills/issue-to-plan/workflow.md` (Step 5, Step 6)

## Required Changes
- Add an explicit maximum retry count to the zero-padded-sequence collision-retry
  procedure in Step 5 and Step 6.
- State the stop-and-report behavior once that maximum is reached (message format,
  consistent with the workflow's existing `Blocked` reporting convention).
- Cross-reference `AGENTS.md` Attempt Limit explicitly, stating whether this retry
  loop is an instance of it or a separate, workflow-specific bound.

## Constraints
The added bound must not conflict with the existing collision-handling text for
`tools/generate_workitem.py` (Step 5/6's "treat that refusal as the trigger for the
zero-padded sequence rule ... not as a workflow failure") — the retry-count limit
applies to how many times the sequence is incremented, not to whether a single
collision is itself treated as failure.

## Acceptance Criteria
- Step 5 and Step 6 each state a concrete maximum number of sequence-retry attempts.
- Each Step states the reporting behavior once that maximum is reached.

## Testing Expectations
Manual review: confirm the added bound is internally consistent with `AGENTS.md`
Attempt Limit and does not contradict the existing tool-refusal-handling text.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this mechanism.

## Out of Scope
- Changing `tools/generate_workitem.py`'s own reject-only collision behavior.
- Adding retry-limit logic to other skills' analogous collision-handling steps not
  covered by this issue (e.g. `plan-to-implementation-procedure`'s own sequence
  rules, if any) — file separately if the same gap is confirmed there.

## Dependencies
N/A: none.

## Unresolved Questions
- Whether 3 (matching `AGENTS.md`'s general Attempt Limit) or a different number is
  the right bound for this specific case — left to implementation planning, but the
  chosen number must be stated explicitly either way.

## AI Implementation Instruction
Read `AGENTS.md` Loop Prevention > Attempt Limit and `workflow.md` Step 5/Step 6 in
full before proposing the exact bound and its wording. Do not silently reuse "3"
without stating whether it is the same rule or a coincidentally identical
workflow-specific choice — the issue's Problem section explicitly asks this
question and it must not be left unanswered.
