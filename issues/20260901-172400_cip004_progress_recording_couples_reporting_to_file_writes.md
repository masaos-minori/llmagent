# "Progress recording during Steps 3-6" couples chat reporting to a required file write

## Priority
Low

## Summary
`skills/code-implementation/workflow.md`'s "Progress recording during Steps 3-6"
instructs updating "the implementation procedure file's own `## Execution
Status` section (via Edit)" as part of the same procedure that governs when to
report to chat — the same coupling `ptip010` identifies for `plan-to-
implementation-procedure`, present here too and arguably more consequential since
this section's persisted record ("the persisted record if the session is
interrupted before Step 7's move") is this phase's only recovery mechanism across
Steps 3-6, a wider span than `plan-to-implementation-procedure`'s single Step 3.

## Background
`workflow.md` "Progress recording during Steps 3-6": "Record status when a
sub-task's outcome differs from expected, or when moving between artifact types
(code → test → doc): - Note the current artifact... - Record status... - If
blocked, describe the blocker... - Update the implementation procedure file's own
`## Execution Status` section (via Edit) with the current step's
Status/Started/Completed — the persisted record if the session is interrupted
before Step 7's move. Also update the final report's Execution Status table."

As with `ptip010`, the persisted Execution Status write is presented as a step of
the same procedure whose trigger condition ("when a sub-task's outcome differs
from expected, or when moving between artifact types") is really about *when to
tell the user something*, not about *when the persisted record needs updating to
stay accurate*.

## Problem
Same risk as `ptip010`: if the persisted Execution Status write only happens when
the *chat-reporting* trigger condition fires, a session interrupted between two
Steps whose transition did not meet that trigger (e.g. Step 4's tests passed
uneventfully, moving into Step 5) could leave the persisted record one Step
behind actual progress — exactly the gap this record exists to prevent, since its
whole purpose (per the same sentence) is recovering after an interruption.

## Reason for Change
This phase spans four Steps (3-6) under one combined progress-recording
instruction, more than `plan-to-implementation-procedure`'s single Step 3 —
making the persisted-record staleness risk proportionally larger here if the
coupling to chat-report frequency is not fixed.

## Implementation Intent
Same fix as `ptip010`: split "Progress recording during Steps 3-6" into two
explicitly separate requirements — (1) when to report to chat (kept as currently
gated), and (2) when to write the Execution Status table (every Step
transition/completion, unconditional, regardless of whether a chat report is also
made).

## Target Files or Areas
- `skills/code-implementation/workflow.md` (Progress recording during Steps 3-6)

## Required Changes
- Split the combined instruction into a chat-report frequency rule and an
  unconditional per-Step-transition Execution Status write rule.

## Constraints
Preserve the existing chat-report frequency gate unchanged — only decouple the
file-write requirement from it.

## Acceptance Criteria
- The Execution Status write requirement is stated as unconditional per Step
  transition/completion (Steps 3 through 6), independent of the chat-report
  frequency gate.

## Testing Expectations
Manual review: confirm the reworded section keeps the existing chat-report
frequency gate unchanged and only decouples the file-write requirement.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing the Execution Status table's structure (see `templates/execution-
  status.md`, unaffected by this issue).

## Dependencies
Same underlying gap as `ptip010` — this is the `code-implementation`-specific
instance, spanning Steps 3-6 rather than a single Step. Implement independently;
consider wording the fix consistently with `ptip010`'s resolution.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `workflow.md`'s full "Progress recording during Steps 3-6" section before
rewording. Reuse `ptip010`'s resolution pattern (separate chat-report frequency
from file-write requirement) rather than inventing a different structure.
