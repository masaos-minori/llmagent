# All-steps-completed check is not cross-referenced from Multi-file processing

## Priority
Low

## Summary
`skills/code-implementation/workflow.md`'s `Multi-file processing` section states
only per-file Step ordering and gives no pointer to Step 1's "All-steps-completed
check" — the mechanism that actually makes a resumed batch run idempotent — the
same documentation-locality gap `ptip005` identifies for `plan-to-implementation-
procedure`.

## Background
`workflow.md` `Multi-file processing`: "Apply `rules/ai-execution.md` Sequential
Target Processing (Base): each cycle covers Steps 1-7, ending with the move to
`implementations/done/` in Step 7... before starting Step 1 for the next file."
No mention of resumption or idempotency.

The actual mechanism lives in Step 1: "**All-steps-completed check**: after
reading the file, inspect its `## Execution Status` table. If every step row
shows `Completed`... the procedure is fully executed — do not re-execute it. Move
it to `implementations/done/`..." This is a stronger, more directly stated
idempotency mechanism than either upstream phase has (see `ptip004`'s finding
that `plan-to-implementation-procedure` lacks an equivalent short-circuit
entirely) — but it is not referenced from the section whose name most directly
suggests this topic.

## Problem
Same as `ptip005`: a reader checking "is this workflow safe to resume" via
`Multi-file processing` would not learn that Step 1 already handles it, unless
they separately read Step 1 in full.

## Reason for Change
Making this workflow's idempotency mechanism (already the most complete of the
three phases) discoverable from `Multi-file processing` costs one sentence and
removes the same documentation-locality risk `ptip005` flags for the sibling
workflow.

## Implementation Intent
Add a short cross-reference from `Multi-file processing` to Step 1's
All-steps-completed check.

## Target Files or Areas
- `skills/code-implementation/workflow.md` (Multi-file processing)

## Required Changes
- Add a one-sentence pointer from `Multi-file processing` to Step 1's
  All-steps-completed check.

## Constraints
The added note must be a pointer, not a restatement, per `skills/DESIGN.md` Avoid
implementation-reference duplication.

## Acceptance Criteria
- `Multi-file processing` contains a short cross-reference to Step 1's
  All-steps-completed check.

## Testing Expectations
Manual review: confirm the added note is a pointer only, with no duplicated
definition text.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing the All-steps-completed check itself.

## Dependencies
Same underlying documentation-locality gap as `ptip005` — implement
independently.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `workflow.md` `Multi-file processing` and Step 1 in full before wording the
cross-reference. Keep it to one sentence.
