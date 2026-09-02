## Goal
Satisfy `REQ-001`/`REQ-002` (ptip006): reword Step 2's discrepancy-handling sentence in
`skills/plan-to-implementation-procedure/workflow.md` to explicitly restate the re-entry
point after a Plan correction.

## Scope
Modify exactly the sentence at current lines 106-109 of
`skills/plan-to-implementation-procedure/workflow.md` ("If revalidation finds a discrepancy,
correct the Plan per that section's rules before continuing."). No other line in this file is
touched.

## Assumptions
- Re-verified 2026-09-02: lines 106-109 still read exactly as the Plan's evidence describes —
  no drift since Plan creation.

## Design decisions
Restate the re-entry point explicitly (re-run Plan Freeze validation for the corrected row(s)
only, then proceed to Step 3) rather than relying on the reader to separately cross-check
`rules/workflow-lifecycle.md`'s more precise wording (Plan `Design`, corrected 2026-09-02 after
this session found the Plan's original Design section was copy-pasted from an unrelated
sibling plan, ptip005).

## Alternatives considered
Leaving the cross-reference implicit and only fixing `rules/workflow-lifecycle.md`'s own
wording — rejected: this Plan's Problem is specifically that `workflow.md` Step 2 itself does
not repeat the re-entry detail, so a reader following only this file could miss it.

## Implementation
### Target file
skills/plan-to-implementation-procedure/workflow.md

### Procedure
Reword the discrepancy-handling sentence in Step 2 to name the re-entry point explicitly.

### Method
1. Locate lines 106-109 (current):
   ```
   - Revalidate the frozen inventory per `rules/workflow-lifecycle.md` Implementation
     Target Files Validation (Plan Freeze) — Revalidation, before proceeding to Step 3.
     If revalidation finds a discrepancy, correct the Plan per that section's rules
     before continuing.
   ```
2. Replace the last sentence with:
   ```
   - Revalidate the frozen inventory per `rules/workflow-lifecycle.md` Implementation
     Target Files Validation (Plan Freeze) — Revalidation, before proceeding to Step 3.
     If revalidation finds a discrepancy, correct the Plan per that section's rules, then
     re-run the Plan Freeze validation for the corrected row(s) specifically (not the whole
     table, and not skipped) before proceeding to Step 3.
   ```

### Details
This wording matches `rules/workflow-lifecycle.md`'s own Revalidation section ("re-run this
validation for the corrected row(s) before proceeding"), closing the gap where `workflow.md`
Step 2 previously only said "before continuing" without repeating that detail.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure wording clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the reworded sentence is consistent with `rules/workflow-lifecycle.md`'s Revalidation section and does not introduce a contradiction (Plan `Tests`).

## Completion criteria
Step 2's discrepancy-handling sentence explicitly states that correction is followed by
re-running validation for the corrected row(s), not merely "continuing."

## Out of scope
`rules/workflow-lifecycle.md`'s Revalidation procedure itself (Plan Scope Out-of-Scope) — not
modified by this row.

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword Step 2's discrepancy-handling sentence per Method | Pending | — | — | |
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
- **Requirement ID**: REQ-001, REQ-002 (explicit re-entry point after Plan correction)
- **Source issue**: `issues/20260901-171500_ptip006_step2_revalidation_correction_reentry_unclear.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-213623_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-152136
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
