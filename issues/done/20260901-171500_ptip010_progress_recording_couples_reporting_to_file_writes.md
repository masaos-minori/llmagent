# "Progress recording during Step 3" couples reporting to an Execution Status write

## Priority
Low

## Summary
`skills/plan-to-implementation-procedure/workflow.md`'s "Progress recording during
Step 3" instructs updating "the Execution Status table in the output document" as
part of progress recording, which means the act of reporting progress is defined
to include a file write — this is a stronger coupling between "report" and
"mutate a document" than the general `rules/ai-execution.md` Progress Reporting
(Base) rule implies, and is not called out as a deliberate deviation.

## Background
`rules/ai-execution.md` Progress Reporting (Base): "Report progress once per step,
in one line, after the step completes... Keep start/end progress reports to one or
two lines; do not restate full document content." This describes reporting as a
chat-facing communication act.

`workflow.md`'s "Progress recording during Step 3": "Report an interim update only
when a row's outcome is Blocked, Partially implemented, fails verification,
produces a Plan Gap, or is an additional target file discovery... - Note which
target file you are working on - Record the current status... - If blocked,
describe the blocker... - Update the Execution Status table in the output
document." The fourth bullet is a file-mutation instruction embedded inside what
is titled a "progress recording" procedure — the reporting act and the persisted
Execution Status write are presented as one combined step, not two separately
triggerable ones.

## Problem
This is exactly the shape of risk `itp007` raises in the abstract (does reporting
re-derive/re-trigger work) — here it is concretely realized as "reporting an
interim update requires writing to the output document," which means an agent
that reports progress more often than strictly necessary (e.g. out of caution)
would also be writing to the Execution Status table more often than necessary,
and an agent that skips the Execution Status write because it judged the report
itself unnecessary would also silently skip the persisted record — a record whose
purpose (per `rules/ai-execution.md` "Progress recording... Update the
implementation procedure file's own `## Execution Status` section (via Edit)...
the persisted record if the session is interrupted") is specifically to survive an
interruption. Coupling it to the *chat-facing report frequency* rather than to the
row's actual status transition risks the persisted record under- or
over-representing what happened, independent of how often progress was announced
in chat.

## Reason for Change
Decoupling "when to tell the user something happened" from "when to persist the
Execution Status" makes the persisted record reliable regardless of how verbosely
the agent chooses to narrate progress in chat, which matters specifically because
this record is the recovery mechanism for exactly the kind of interruption this
session experienced mid-batch.

## Implementation Intent
Reword "Progress recording during Step 3" to state the Execution Status write as
its own, unconditional per-row requirement (write it every time a row's status
changes, regardless of whether an interim chat report is also made), separate from
the chat-report frequency rule ("report an interim update only when...").

## Target Files or Areas
- `skills/plan-to-implementation-procedure/workflow.md` (Progress recording during
  Step 3)

## Required Changes
- Split "Progress recording during Step 3" into two explicitly separate
  requirements: (1) when to report to chat (frequency-gated, as currently
  written), and (2) when to write the Execution Status table (every row-status
  transition, unconditional).

## Constraints
Do not reduce the frequency-gating for chat reports — that part of the existing
text is correct and should be preserved; only the coupling to the file write
changes.

## Acceptance Criteria
- The Execution Status write requirement is stated as unconditional per
  row-status-transition, independent of the chat-report frequency gate.

## Testing Expectations
Manual review: confirm the reworded section keeps the existing chat-report
frequency gate unchanged and only decouples the file-write requirement from it.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing the Execution Status table's own structure or content requirements.

## Dependencies
Related to `itp007` (issue-to-plan's analogous Progress Reporting ambiguity) —
this issue is the concrete `plan-to-implementation-procedure`-specific instance;
resolve independently.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `rules/ai-execution.md` Progress Reporting (Base) and `workflow.md`'s full
"Progress recording during Step 3" section before rewording. Preserve the
existing chat-report frequency gate verbatim where possible — the fix is to
separate it from the file-write requirement, not to rewrite both from scratch.
