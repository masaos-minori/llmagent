# No explicit short-circuit when every row is already implemented

## Priority
Medium

## Summary
`skills/plan-to-implementation-procedure/workflow.md` has no equivalent of
`code-implementation/workflow.md` Step 1's "All-steps-completed check" — a
Plan whose every `Implementation Target Files` row is already `Already
implemented` must still be read in full and stepped through Step 3's per-row loop
before reaching Step 4, with no stated fast path to move straight to Step 4 once
that condition is detected early.

## Background
`skills/code-implementation/workflow.md` Step 1 explicitly handles the fully-done
case: "if every step row shows `Completed`... the procedure is fully executed —
do not re-execute it. Move it to `implementations/done/`... Report `Moved to
done:`..." This is a direct precedent within the same three-phase pipeline for
short-circuiting a target file that needs no further work.

`plan-to-implementation-procedure/workflow.md` Step 1 (Target Plan File
Identification) has no analogous check — it only validates that the target Plan
file exists, not whether all its rows are already implemented. Step 3 does
classify each row (`Already implemented` / `Partially implemented` / `Not
implemented`), but only after the full per-row loop has processed every row
individually.

## Problem
For a Plan resumed after an interruption (e.g. the session-limit interruption that
occurred mid-batch in this session's own `tool002`-`tool006` processing), or for a
Plan intentionally re-run to confirm it is finished, every row may already be
`Already implemented`. The current text still requires stepping through Step 2's
full read/revalidate and Step 3's full per-row loop (even though each iteration
resolves quickly to "skip this row") before Step 4's move — there is no stated
early-exit once the "all rows already covered" condition is known, unlike
`code-implementation`'s Step 1 precedent for the equivalent situation.

## Reason for Change
An explicit short-circuit, symmetric with `code-implementation`'s Step 1, makes
resumed/idempotent re-runs of this workflow cheaper and gives the workflow a
directly comparable safety net to the one its sibling phase already has.

## Implementation Intent
Add a lightweight pre-check to Step 1 or the start of Step 2: if every
`Implementation Target Files` row's `target_file_slug` already matches a
document under `implementations/` or `implementations/done/` whose `Source plan`
and `Related target files` confirm full coverage (the same criteria Step 3 already
uses per-row), skip the rest of Step 2/Step 3 and proceed directly to Step 4's
move, reporting the short-circuit explicitly (e.g. `All rows already implemented —
proceeding to Step 4`).

## Target Files or Areas
- `skills/plan-to-implementation-procedure/workflow.md` (Step 1 or Step 2)

## Required Changes
- Add an explicit early-exit check, using the same `Already implemented` criteria
  Step 3 already defines, run once against all rows before the full per-row loop.
- State the required report format for this short-circuit path, mirroring
  `code-implementation` Step 1's precedent.

## Constraints
The check must use the exact same `Already implemented` criteria Step 3 already
defines (matching `target_file_slug`, confirmed `Source plan` + `Related target
files`, and confirmed scope coverage against current source) — do not introduce a
looser or different criterion for the short-circuit path than for the per-row
classification.

## Acceptance Criteria
- A Plan whose every row is already implemented can be recognized as such before
  the full Step 2/Step 3 procedure runs, with an explicit short-circuit report.
- The short-circuit criteria are identical to Step 3's existing `Already
  implemented` classification, not a separate, looser check.

## Testing Expectations
Manual review: confirm the added short-circuit reuses Step 3's classification
criteria verbatim rather than restating them with drift.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Changing Step 3's own per-row classification logic — only adding an earlier,
  equivalent check for the all-rows case.

## Dependencies
Related to `ptip005` (idempotency-mechanism documentation gap) — implement
independently, but keep consistent.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `code-implementation/workflow.md` Step 1 and
`plan-to-implementation-procedure/workflow.md` Step 1-3 in full before wording the
addition. Reuse Step 3's existing `Already implemented` criteria verbatim for the
short-circuit check — do not invent a new, looser criterion.
