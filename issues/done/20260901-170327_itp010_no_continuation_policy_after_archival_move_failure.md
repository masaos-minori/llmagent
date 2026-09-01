# No defined continuation policy after an Archival Move failure (Blocked)

## Priority
Medium

## Summary
`rules/workflow-lifecycle.md` Archival Move states that a failed `git mv` (or,
per the newer tool-integration text, a failed `tools/manage_workitem_stage.py
close-issue` call) should be reported as `Blocked`, but neither it nor
`skills/issue-to-plan/workflow.md` states what happens next for a Multi-file-
processing batch: does the whole batch stop, or does processing continue with the
next target file while this one remains un-archived?

## Background
`rules/workflow-lifecycle.md` Archival Move: "If you cannot move the file, stop
and report the error. Do not proceed without completing this step." — "stop" here
most naturally reads as "stop this file's cycle," but the sentence does not
distinguish that from "stop the entire multi-file run."

`rules/ai-execution.md` Sequential Target Processing (Base): "Complete its full
workflow cycle and required gates before loading the next target." This implies a
per-file gate, but does not say whether a `Blocked` gate failure permits skipping
to the next file (leaving the blocked one as-is, Plan generated but not archived)
or halts the entire batch.

`skills/issue-to-plan/workflow.md` Multi-file processing: "each cycle covers Steps
1-10... before starting Step 1 for the next file" — again consistent with either
reading.

## Problem
If a `git mv` (or tool-based equivalent) fails for Issue #3 of a 10-Issue batch
(e.g. due to a filesystem permission issue, a concurrent modification, or the
newer tool's "uncommitted changes" refusal), the workflow does not state whether
Issues #4-10 should still be attempted. This matters in practice — the batch
processing observed in this session's actual runs continued past individual
per-file outcomes report ("Blocking" vs. informational) but never actually
encountered an Archival Move failure to test against, so the intended behavior has
never been exercised or confirmed.

Additionally, "no continuation policy" also means there is no stated retry
behavior — should the same file be retried once more before moving on, or is a
single failure immediately terminal for that file?

## Reason for Change
Without a stated policy, an agent hitting this failure mid-batch must improvise,
risking either an unnecessary full-batch halt (when the failure was file-specific
and recoverable by skipping) or silently continuing past a failure that should
have stopped the batch for investigation (if the failure signals a systemic
problem, e.g. a full disk, that will recur for every remaining file).

## Implementation Intent
Add an explicit continuation policy to `rules/workflow-lifecycle.md` Archival Move
(shared by `issue-to-plan` and `plan-to-impl-procedure`): on move failure, report
`Blocked` for that specific file (leaving its output document generated but
unarchived), and continue to the next target file in the batch rather than halting
the entire run — since the workflow's own Completion Criteria already tracks
per-file completeness, a batch is naturally "partially complete" rather than
all-or-nothing. State this explicitly rather than leaving it implicit.

## Target Files or Areas
- `rules/workflow-lifecycle.md` (Archival Move, Completion Criteria)

## Required Changes
- State explicitly whether a per-file Archival Move failure halts the entire
  Multi-file-processing batch or only that file's cycle.
- If only that file's cycle halts, state that the batch continues to the next
  target file, and that the failed file's final report must clearly mark it as
  `Blocked` with its generated-but-unarchived output path.
- State whether a single move failure is immediately terminal for that file or
  whether one retry is attempted first (and if so, cross-reference `itp003`'s
  Attempt Limit question for consistency).

## Constraints
The policy must not contradict `rules/ai-execution.md` Global Safety Restrictions
(Base)'s "Do not process target-file cycles in parallel" — continuing to the next
file after a `Blocked` result is still strictly sequential, not parallel recovery.

## Acceptance Criteria
- `rules/workflow-lifecycle.md` Archival Move states the batch-continuation policy
  explicitly for a move failure.
- The policy is consistent with Completion Criteria's per-file framing.

## Testing Expectations
Manual review: confirm the added policy is internally consistent and does not
contradict Sequential Target Processing (Base) or Global Safety Restrictions
(Base).

## Documentation Impact
N/A: internal shared-rule fix; no `docs/*.md` file describes this mechanism.

## Out of Scope
- Building actual retry-on-failure logic — this issue only requires the policy to
  be stated, not a new mechanism implemented.

## Dependencies
Related to `itp003` (Attempt Limit) for the retry-before-Blocked question — resolve
consistently if both are implemented.

## Unresolved Questions
N/A: none — the missing policy is directly observable (Archival Move's "stop" is
ambiguous between per-file and whole-batch scope).

## AI Implementation Instruction
Read `rules/workflow-lifecycle.md` Archival Move and Completion Criteria, and
`rules/ai-execution.md` Sequential Target Processing (Base) and Global Safety
Restrictions (Base), in full before wording the policy. State the policy once, in
`rules/workflow-lifecycle.md` (shared by both workflows that reference it), rather
than duplicating it separately in `issue-to-plan`'s and `plan-to-implementation-
procedure`'s own `workflow.md` files.
