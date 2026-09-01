# Archival Move failure continuation policy is undefined and not covered by the shared rule

## Priority
Medium

## Summary
`skills/code-implementation/workflow.md` Step 1's all-steps-completed move and
Step 7's final move each state `Blocked: move failed — {reason}` on failure, but
neither states whether Multi-file processing should continue to the next target
file or halt entirely — and unlike `issue-to-plan`/`plan-to-implementation-
procedure`, this workflow explicitly does not use `rules/workflow-lifecycle.md`
("is scoped to `issue-to-plan`/`plan-to-impl-procedure` only and does not apply to
this workflow at all"), so a shared-rule fix to that continuation policy (as
proposed in `itp010`) will not automatically cover this workflow.

## Background
`workflow.md` Step 7: "If the move fails, stop and report `Blocked: move failed —
{reason}`. Do not fall back to another method beyond the two above." "Stop" here
is ambiguous between "stop this file's cycle" and "stop the entire multi-file
run," exactly as `itp010` identifies for the shared rule.

`workflow.md` explicitly states: "`rules/workflow-lifecycle.md` is scoped to
`issue-to-plan`/`plan-to-impl-procedure` only and does not apply to this workflow
at all" (Step 7's own text). This means `itp010`'s proposed fix to
`rules/workflow-lifecycle.md` Archival Move — even once implemented — has no
effect here; `code-implementation` needs its own, independently stated
continuation policy.

## Problem
Without this workflow's own policy, an agent hitting an Archival Move failure
mid-batch (e.g. Step 7 for the 3rd of 10 implementation procedure files) must
improvise whether to continue to file 4 or halt the whole run — the same
ambiguity `itp010` flags, but here with the added wrinkle that fixing the shared
rule will not close this instance of the gap.

## Reason for Change
Because this workflow deliberately opts out of the shared `rules/workflow-
lifecycle.md`, its continuation policy must be stated locally in `workflow.md`
itself, or it will remain unresolved even after `itp010` is implemented.

## Implementation Intent
Add an explicit continuation policy to `workflow.md` Step 7 (and cross-reference
it from Step 1's all-steps-completed move, which shares the same move mechanism):
on move failure, report `Blocked` for that specific file (leaving its code/test/
doc changes already applied and validated, output document generated but
unarchived) and continue to the next target file in the batch, consistent with
how `itp010` proposes resolving the same question for the shared rule — but
stated here independently since the shared rule does not apply.

## Target Files or Areas
- `skills/code-implementation/workflow.md` (Step 1, Step 7)

## Required Changes
- Add an explicit statement to Step 7 of whether a move failure halts the entire
  Multi-file-processing batch or only that file's cycle, and (if only that file's
  cycle) that the batch continues to the next target file.
- Cross-reference this policy from Step 1's all-steps-completed move, since it
  performs the same kind of move and would face the same ambiguity.

## Constraints
Must remain consistent with `rules/ai-execution.md` Global Safety Restrictions
(Base)'s "Do not process target-file cycles in parallel" — continuing to the next
file after a `Blocked` result is strictly sequential, not parallel recovery.

## Acceptance Criteria
- Step 7 states the batch-continuation policy explicitly for a move failure.
- Step 1's all-steps-completed move cross-references the same policy.

## Testing Expectations
Manual review: confirm the added policy is internally consistent with `rules/ai-
execution.md` Sequential Target Processing (Base) and Global Safety Restrictions
(Base).

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Modifying `rules/workflow-lifecycle.md` (this workflow explicitly does not use
  it) — `itp010` covers that file for the workflows that do use it.

## Dependencies
Same underlying question as `itp010`, but this workflow needs an independently
stated answer since it opts out of the shared rule `itp010` would fix. Implement
independently; keep the two answers consistent if practical.

## Unresolved Questions
N/A: none — the missing policy is directly observable, and this workflow's
explicit opt-out from the shared rule is stated in its own text.

## AI Implementation Instruction
Read `workflow.md` Step 1, Step 7, and the note explicitly excluding `rules/
workflow-lifecycle.md` from this workflow, before wording the policy. Do not
propose simply removing the opt-out and applying the shared rule instead — that
opt-out may be intentional (this phase's approval/validation gates differ from
the two document-only phases'); if implementation planning decides otherwise,
that is a separate, larger decision than this issue's scope.
