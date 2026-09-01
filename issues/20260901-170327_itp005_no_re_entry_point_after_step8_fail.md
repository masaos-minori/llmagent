# No defined re-entry point when Step 8 reports Fail or Partial

## Priority
Medium

## Summary
`skills/issue-to-plan/workflow.md` Step 8 reports one of `Pass` / `Fail` / `Partial`
/ `Blocked`, but the workflow never states which earlier Step to resume from when
the result is `Fail` or `Partial` — leaving the correction-and-retry path
unspecified.

## Background
`workflow.md` Step 8: "Report one of: `Pass` / `Fail` / `Partial` / `Blocked`. If
any requirement information is unmapped or untraceable, or `Implementation Target
Files` is not `Frozen`, do not report `Pass` or `Completed`."

Step 9 only handles the `Pass` case explicitly: "No human approval is required for
the move to `issues/done/`... proceed to Step 10 once Step 8 is `Pass` and all
required validations are `Pass`." Nothing states what happens next for `Fail` or
`Partial` — whether to go back to Step 4 (the Issue→Plan mapping), Step 5 (Plan
generation), or edit only the specific missing/unmapped field directly and
re-run Step 8 alone.

## Problem
Depending on what caused the `Fail`/`Partial` (a genuinely unmapped field vs. a
field that was mapped but not traceable vs. an `Implementation Target Files` row
that failed the Plan Freeze validation in `rules/workflow-lifecycle.md`), the
correct re-entry point differs:
- An unmapped field → likely needs Step 4's mapping table revisited.
- A Frozen-validation failure on one row → likely needs only that row corrected
  and Step 8's freeze check re-run, not the whole Plan regenerated.
- An untraceable Requirement → likely needs Step 7 (Traceability) revisited.

Without a stated decision rule, an agent could over-correct (regenerate the entire
Plan from Step 5 for a single-row issue) or under-correct (patch only the
symptom Step 8 reported without checking whether the same root cause affects other
rows), and two different agents could resolve the same `Fail` differently.

## Reason for Change
An explicit re-entry mapping makes Step 8 failures resolvable in a bounded,
predictable way, and is a prerequisite for `itp003`'s and `itp011`'s
retry/chaining-limit questions to be answerable at all — without knowing where a
correction cycle restarts, "how many cycles are tolerated" cannot be evaluated.

## Implementation Intent
Add a short decision table or rule set to Step 8 (or immediately after it)
mapping each category of `Fail`/`Partial` cause to the Step it should resume from:
unmapped-field failures → Step 4; traceability failures → Step 7; Implementation
Target Files Frozen-validation failures → the specific row's correction per
`rules/workflow-lifecycle.md`, then re-run Step 8's freeze check only (not the
whole Step 5). State that corrections are scoped to the affected section(s), not a
full Plan regeneration, unless the cause is broad enough to invalidate multiple
sections.

## Target Files or Areas
- `skills/issue-to-plan/workflow.md` (Step 8, Step 9)

## Required Changes
- Add a cause → re-entry-Step mapping (or equivalent decision rule) to Step 8.
- State explicitly that a `Fail`/`Partial` correction is scoped to the affected
  section(s) by default, not a full Plan regeneration, unless the cause is shown to
  be broader.
- Cross-reference this mapping from Step 9 so the `Fail`/`Partial` branch is not
  left implicit.

## Constraints
The mapping must stay consistent with `rules/workflow-lifecycle.md` Implementation
Target Files Validation (Plan Freeze)'s existing re-verification procedure — do not
duplicate or contradict that section's own correction rules for Frozen-validation
failures.

## Acceptance Criteria
- Step 8 (or Step 9) states a concrete re-entry Step for each named failure
  category (unmapped field, untraceable Requirement, Frozen-validation failure).
- The mapping does not require a full Plan regeneration for a single-row or
  single-field failure.

## Testing Expectations
Manual review: confirm the added mapping covers every failure condition Step 8
itself names, and does not contradict `rules/workflow-lifecycle.md`'s existing
Frozen-validation correction procedure.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this mechanism.

## Out of Scope
- Changing what Step 8 validates — only what happens after a non-`Pass` result.
- The equivalent question for `plan-to-implementation-procedure`'s own validation
  steps, if any — file separately if the same gap is confirmed there.

## Dependencies
Related to `itp003` and `itp011` (both need a defined re-entry/retry concept to
bound their own retry-limit questions) — implement independently, but keep the
resulting rules mutually consistent.

## Unresolved Questions
N/A: none — the missing mapping is directly observable from the current text
(Step 9 only branches on `Pass`).

## AI Implementation Instruction
Read `workflow.md` Step 4 through Step 9 in full, and `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze), before proposing the
cause-to-Step mapping. Ground each mapping entry in a specific failure condition
Step 8 already names — do not invent a new failure category not present in the
current text.
