# Existing idempotency mechanisms are not documented under Multi-file processing

## Priority
Low

## Summary
`skills/plan-to-implementation-procedure/workflow.md` already has two real
idempotency mechanisms — Step 3's `Already implemented` classification and
`tools/generate_workitem.py`'s Plan-file timestamp-marker (added to make repeated
invocations against the same Plan share one timestamp, surviving a resumed
session) — but neither is referenced from the `Multi-file processing` section,
which is where a reader would look to understand how re-processing/resumption is
handled.

## Background
`workflow.md` `Multi-file processing`: "Apply `rules/ai-execution.md` Sequential
Target Processing (Base): each cycle covers Steps 1-4, ending with the move to
`plans/done/` in Step 4, before starting Step 1 for the next file." This states
only per-file ordering — it says nothing about what happens if a cycle is resumed
after interruption, or what already guards against reprocessing.

The actual idempotency guarantees exist elsewhere: Step 3's `Already implemented`
classification (skips a row already covered by an existing document) and the
`tools/generate_workitem.py` Plan-file marker (this session's own tool-integration
work, documented in `Allowed file operations` and Step 3's timestamp-sharing note)
together allow a resumed pass to produce correct, non-duplicated output. But a
reader relying on `Multi-file processing` alone (the section whose name most
directly suggests this topic) would not learn this.

## Problem
This is a documentation-locality gap, not a behavioral one — the mechanisms exist
and (per this session's own real recovery from an interruption) work in practice,
but `itp` (this workflow's counterpart)'s reviewer, or any future reader auditing
"is this workflow safe to resume," would need to already know to look in Step 3
and `Allowed file operations` rather than the section titled `Multi-file
processing`.

## Reason for Change
Consolidating a pointer to the existing mechanisms under `Multi-file processing`
makes the workflow's resumption/idempotency story auditable from the one section
whose name a reviewer would check first, without duplicating the mechanisms'
actual definitions.

## Implementation Intent
Add a short cross-reference note to `Multi-file processing` pointing to Step 3's
`Already implemented` classification and the Plan-file timestamp-marker mechanism
in `Allowed file operations`/Step 3, stating that these together make a resumed
pass idempotent for rows already completed.

## Target Files or Areas
- `skills/plan-to-implementation-procedure/workflow.md` (Multi-file processing)

## Required Changes
- Add a short note to `Multi-file processing` cross-referencing Step 3's `Already
  implemented` classification and the timestamp-marker mechanism, without
  restating their full definitions (per `skills/DESIGN.md` Avoid
  implementation-reference duplication).

## Constraints
The added note must be a pointer, not a restatement — do not duplicate Step 3's or
Allowed file operations' existing text.

## Acceptance Criteria
- `Multi-file processing` contains a short note pointing to where a reader can
  find this workflow's idempotency/resumption guarantees.

## Testing Expectations
Manual review: confirm the added note is a cross-reference only, with no
duplicated definition text.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing the underlying mechanisms themselves.

## Dependencies
Related to `ptip004` (short-circuit for all-rows-already-implemented Plans) — if
both are implemented, this note should also point to `ptip004`'s addition once it
exists.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `workflow.md` `Multi-file processing`, `Allowed file operations`, and Step 3
in full before wording the note. Keep it to 1-2 sentences with direct pointers
(section names), consistent with `skills/DESIGN.md` Avoid implementation-reference
duplication.
