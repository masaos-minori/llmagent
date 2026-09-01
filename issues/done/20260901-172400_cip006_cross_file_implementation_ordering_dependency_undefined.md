# No defined handling when one file's implementation invalidates a sibling's already-applied change

## Priority
High

## Summary
`skills/code-implementation/workflow.md` processes implementation procedure
documents one at a time via Multi-file processing, but never addresses what
happens if implementing file N's procedure (e.g. changing a shared helper's
signature) invalidates code already applied and validated for an earlier file in
the same batch — unlike `ptip003`'s document-only equivalent, this risk here is
about real source code, so a missed cross-file dependency can leave the
repository in a broken, partially-inconsistent state that Step 4's "run the full
test suite exactly once" per file may not catch if that earlier file's own tests
don't happen to exercise the interaction.

## Background
`workflow.md` Multi-file processing: "each cycle covers Steps 1-7... before
starting Step 1 for the next file." Each implementation procedure document is
scoped to "exactly this row's `File Path` — no other file" (per the upstream
`plan-to-implementation-procedure` phase's own one-document-per-file design,
carried through here).

Step 3's adversarial verification checks the *current* implementation procedure
document's claims against current source, including "whether any stated
assumption or scope boundary is stale or inconsistent with a sibling procedure
document" — this catches a *staleness* discovered while reading, but does not
address the *forward* case: file N's implementation, applied during *this*
cycle, changing something an *already-processed* file (N-1, N-2, ...) in the same
batch depended on.

Step 4 runs "the repository-defined full test suite exactly once" per file's
cycle — this would catch a regression if the full suite exercises the
broken interaction, but "the only full-suite run for this cycle" (Step 4's own
wording) means this is checked once per file, immediately after that file's own
change, not re-checked after every later file's change in the same batch. A
regression introduced by file N in something file N-1 already validated would
only surface in file N's own full-suite run *if* file N-1's affected code path is
exercised by tests that also run as part of file N's change — not guaranteed.

## Problem
A Plan whose rows are processed in `seq` order specifically because later rows may
build on earlier ones (per `plan-to-implementation-procedure/workflow.md`'s own
"sorting filenames reproduces the implementation order") implies the reverse
dependency (an earlier file being affected by a later one) is presumed not to
happen — but nothing in `code-implementation/workflow.md` states this as an
explicit assumption, checks for it, or defines what to do if it turns out to be
false (e.g. Step 3's adversarial verification for file N discovers that its
required change conflicts with what file N-1 already implemented).

## Reason for Change
This is the code-modifying counterpart to `ptip003`'s document-consistency
finding, with materially higher stakes: a missed cross-file conflict here means
committed source code, not just a stale Markdown claim.

## Implementation Intent
Add an explicit instruction to Step 3: when adversarial verification (or the
implementation itself) reveals that the current file's required change conflicts
with, or invalidates an assumption of, an already-processed file's change in the
same batch, stop and report `Blocked: cross-file conflict with {earlier file} —
{description}` rather than proceeding — do not implement around the conflict
silently. Also state whether re-running the full test suite (Step 4) for the
earlier, now-possibly-affected file is required before continuing the batch.

## Target Files or Areas
- `skills/code-implementation/workflow.md` (Step 3, Step 4, Multi-file
  processing)

## Required Changes
- Add an explicit cross-file-conflict detection-and-stop instruction to Step 3.
- State the required re-validation action for an earlier, potentially-affected
  file's change (re-run its full test suite, or a narrower targeted re-check) when
  such a conflict is found.

## Constraints
This is not a request to re-run the full test suite after every file
unconditionally (that would violate the existing "exactly once... the only
full-suite run for this cycle" rule) — the added re-validation trigger must be
conditional on an actually-detected conflict, not routine.

## Acceptance Criteria
- Step 3 states an explicit stop-and-report action for a detected cross-file
  conflict with an already-processed file in the same batch.
- The required re-validation action for the affected earlier file is stated.

## Testing Expectations
Manual review: confirm the added instruction does not conflict with Step 4's
existing "exactly once" full-suite-run rule outside the conflict-detected case.

## Documentation Impact
N/A: internal workflow-procedure fix; no `docs/*.md` file describes this
mechanism.

## Out of Scope
- Building automated cross-file dependency-detection tooling — this issue only
  requires the workflow instruction for the case where such a conflict is
  discovered during normal Step 3/Step 4 work, not a new detection mechanism.

## Dependencies
Related to `ptip003` (the document-only equivalent for
`plan-to-implementation-procedure`) — this issue is the higher-stakes,
code-modifying counterpart. Implement independently.

## Unresolved Questions
- Whether the re-validation action should always be a full test-suite re-run for
  the earlier file, or a narrower targeted re-check — left to implementation
  planning, but the choice must be stated explicitly.

## AI Implementation Instruction
Read `workflow.md` Step 3, Step 4, and Multi-file processing in full before
wording the addition. Ground the added instruction in the existing "sibling
procedure document" staleness-check language in Step 3 — this issue extends that
concept from "stale claim discovered while reading" to "conflict discovered while
implementing," rather than introducing an unrelated mechanism.
