## Goal
Satisfy `REQ-001`/`REQ-002` (ptip003): add an explicit cross-row consistency check to
`skills/plan-to-implementation-procedure/workflow.md` Step 3, triggered when a Plan correction
made while processing row K might invalidate an already-generated document for an earlier row.

## Scope
Modify exactly the paragraph at current lines 143-151 of
`skills/plan-to-implementation-procedure/workflow.md` (the Plan-correction-handling paragraph
ending "...Record what was found and corrected in the progress report; do not report a row
`Completed` while a Plan-level inconsistency it surfaced remains unresolved."). No other line
in this file is touched.

## Assumptions
- Re-verified 2026-09-02: lines 143-151 still read exactly as the Plan's evidence describes —
  no drift since Plan creation (the grep pattern used to originally locate it missed a
  line-wrap boundary; direct Read confirmed the exact match).

## Design decisions
**Resolves UNK-01**: default to amending the earlier row's document in the same cycle when the
fix is a bounded, well-understood correction (mirroring the case-by-case judgment already used
for this Step's Blocking/Non-blocking evidence-gap classification); fall back to flagging it in
the progress report and the Plan's Execution Status as needing re-verification before Step 4's
move only when amending would require redoing significant investigation for that earlier row.
Scope the check narrowly to the corrected claim only (Plan `Tests`), not a full re-verification
of every prior row, per the sibling `itp011` finding this Plan mirrors.

## Alternatives considered
Always flagging (never amending inline) — rejected: for a simple, bounded correction (e.g. a
single stale line-number reference), requiring a separate re-verification cycle before Step 4
would be disproportionate overhead compared to fixing it immediately, which this Step's
existing Plan-correction mechanism already does for the current row.
Always amending inline (never flagging) — rejected: a correction affecting an earlier row's
document may require re-investigating that row's own dependencies/tests, which is exactly the
kind of work this Step's own per-row investigation budget (ptip002) is meant to bound; forcing
it inline could blow that budget.

## Implementation
### Target file
skills/plan-to-implementation-procedure/workflow.md

### Procedure
Append a cross-row consistency check and resolution rule to the Plan-correction-handling
paragraph.

### Method
1. Locate lines 143-151 (current):
   ```
   If adversarial verification finds an unconfirmed item or an inconsistency (a stale
   claim, a missing Requirement, a newly discovered dead-code reference, a duplicate or
   superseded Plan, etc.), correct the Plan document itself (`plans/{filename}_plan.md`,
   via Edit) in the same cycle — update whichever sections apply (Background,
   Requirements, Acceptance criteria, Assumptions, Risks, Requirement Traceability,
   Execution Status) rather than silently working around the discrepancy — and reflect
   the corrected understanding in the generated document(s). Record what was found and
   corrected in the progress report; do not report a row `Completed` while a
   Plan-level inconsistency it surfaced remains unresolved.
   ```
2. Append immediately after:
   ```
   If this correction is made while processing row K (K > 1), check whether any
   already-generated document for rows 1..K-1 relied on the now-corrected claim. If one
   does: amend that earlier document in the same cycle when the fix is bounded and does
   not require re-investigating that row's dependencies or tests; otherwise, flag it in
   the progress report and the Plan's Execution Status as needing re-verification before
   Step 4's move — do not silently leave a stale earlier document unflagged. Scope this
   check to the corrected claim only, not a full re-verification of every prior row.
   ```

### Details
This check triggers only on a Plan correction actually made mid-pass (row K > 1) — it does not
apply retroactively to prior Plan cycles, and it does not require new tooling (Plan Scope
Out-of-Scope): the agent performing Step 3 checks by re-reading the earlier document(s)
directly.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure consistency-check clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added check is scoped narrowly (the corrected claim only) and does not require full re-verification of every prior row (Plan `Tests`).

## Completion criteria
Step 3 states an explicit cross-row consistency check triggered by a mid-pass Plan correction,
and the required action (amend now, or flag and block Step 4) when an earlier row's document is
found to rely on the corrected claim.

## Out of scope
Building automated cross-document consistency tooling (Plan Scope Out-of-Scope) — this issue
only adds the workflow instruction.

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add cross-row consistency check per Method | Pending | — | — | |
| 2 | N/A: no test to add (doc-only change) | Pending | — | — | N/A |
| 3 | Manual review validation | Pending | — | — | |
| 4 | Documentation update | Pending | — | — | N/A: this file is the documentation being updated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002 (cross-row consistency check + required resolution action)
- **Source issue**: `issues/20260901-171500_ptip003_plan_correction_mid_pass_may_invalidate_earlier_rows.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-213052_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-152921
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
