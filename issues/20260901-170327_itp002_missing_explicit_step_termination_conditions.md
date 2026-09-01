# Investigation Steps lack explicit termination conditions

## Priority
High

## Summary
`skills/issue-to-plan/workflow.md` Step 2's adversarial verification and Step 3's
Path B analysis instruct the agent to investigate but never state when
investigation is complete — only the overall workflow's completion criteria are
defined (`rules/workflow-lifecycle.md` Completion Criteria), not each Step's.

## Background
`workflow.md` Step 2: "actively look for evidence that would refute or narrow
them: whether the described problem has already been fixed elsewhere, whether the
named files/symbols/line numbers still exist as stated, whether a claimed
dependency or side effect is missing or overstated, and whether two claims...
contradict each other." This is an open-ended search instruction with no stated
stopping point.

`workflow.md` Step 3 (Path B): "perform the full inspection — source files, tests,
configuration, documentation, callers and callees, dependencies, data ownership,
side effects, error handling, compatibility constraints, and security constraints."
Again, no depth or count bound is stated for any of these dimensions.

`rules/ai-execution.md` Reasoning and Planning offers only qualitative guidance
("Investigate further only when genuinely uncertain", "Judge at the granularity
needed to finish the task") — no quantitative or structural termination rule (e.g.
a fixed evidence-item count, a fixed search-breadth limit, or a explicit "stop when
X").

## Problem
Without a stated termination condition, two failure modes are both consistent with
the current wording:
1. Under-investigation: an agent stops early, having satisfied only the qualitative
   "genuinely uncertain" bar, and misses evidence a stricter reading would require.
2. Over-investigation: an agent keeps searching indefinitely (or re-searching the
   same ground) because no concrete stopping signal is defined, burning time/tokens
   without a corresponding increase in Plan quality.

`rules/workflow-lifecycle.md` Completion Criteria defines when the *whole cycle* is
done (output generated + source moved + no blocking items), but that is a
higher-level gate reached only after Steps 2/3 already finished — it does not help
decide, inside Step 2 or Step 3, when to stop investigating.

## Reason for Change
An explicit termination condition per Step is what makes the workflow's duration
and thoroughness predictable and auditable — without one, two runs of the same
workflow against the same Issue could investigate to very different depths with no
way to say which one was "correct" per the document.

## Implementation Intent
Add a concrete stopping rule to Step 2 and Step 3 (Path B) in `workflow.md`, e.g.:
- Step 2: stop adversarial verification once every field extracted per
  `templates/issue.md` has been checked against at least one concrete source (file,
  test, or existing Plan/Implementation document), and no new disconfirming
  evidence was found in the last full pass over that field list.
- Step 3 (Path B): stop each of the four analysis dimensions once its own
  toolchain command(s) (per `workflow-path-b.md`) have been run once and their
  output reviewed — do not re-run the same command against the same target without
  a changed input, per `rules/ai-execution.md` Tool Usage.

The exact rule is an implementation-planning decision; this issue only requires
that *some* concrete, checkable stopping condition exists per Step, replacing the
current open-ended instruction.

## Target Files or Areas
- `skills/issue-to-plan/workflow.md` (Step 2, Step 3)
- `skills/issue-to-plan/workflow-path-b.md` (if the per-dimension stopping rule
  belongs there instead)

## Required Changes
- Add an explicit, checkable termination condition to Step 2's adversarial
  verification procedure.
- Add an explicit, checkable termination condition to Step 3's Path B full
  inspection (per analysis dimension, or for the inspection as a whole).
- State the relationship between these per-Step conditions and the workflow-level
  `Completion Criteria` (`rules/workflow-lifecycle.md`) so it is clear the two are
  complementary, not duplicative.

## Constraints
The termination condition must be checkable without requiring the agent to
re-derive the current qualitative guidance from scratch — it should be a concrete
addition, not a replacement of the existing "genuinely uncertain" framing.

## Acceptance Criteria
- Step 2 and Step 3 (Path B) each state a concrete condition under which
  investigation for that Step is considered complete.
- The added conditions do not contradict `rules/ai-execution.md` Reasoning and
  Planning's existing qualitative guidance.

## Testing Expectations
Manual review: confirm the added termination conditions are checkable (an agent
following them can determine "done" without further judgment calls) and do not
introduce a contradiction with existing Step 2/3 text.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this mechanism.

## Out of Scope
- Changing what evidence Step 2/3 require finding — only when to stop looking for
  it.
- Adding termination conditions to other skills' Steps not covered by this issue.

## Dependencies
N/A: none.

## Unresolved Questions
- Whether the termination condition should be a fixed rule (e.g. "one full pass per
  field") or a Path A/B-differentiated one — left to implementation planning.

## AI Implementation Instruction
Read `workflow.md` Step 2 and Step 3, and `workflow-path-b.md`, in full before
proposing termination conditions. Do not invent a numeric threshold (e.g. "check 5
sources") without grounding it in the workflow's existing evidence-classification
vocabulary (`Explicit in issue` / `Confirmed by repository evidence` / `Derived
from confirmed evidence` / `Needs confirmation`) — the stopping rule should key off
that vocabulary where possible, not an arbitrary count.
