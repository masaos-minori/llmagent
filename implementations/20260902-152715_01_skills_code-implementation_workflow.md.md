## Goal
Satisfy `REQ-001`/`REQ-002` (cip002): add an explicit batch-continuation policy to
`skills/code-implementation/workflow.md` Step 7 for an Archival Move failure, and
cross-reference it from Step 1's all-steps-completed move.

## Scope
Modify exactly two locations in `skills/code-implementation/workflow.md`: Step 7's move-failure
sentence (current lines 239-240) and Step 1's all-steps-completed move description (current
lines 103-110). No other line in this file is touched. This workflow's deliberate opt-out from
`rules/workflow-lifecycle.md` is preserved — the policy is stated locally, not by removing that
opt-out (Plan Assumptions).

## Assumptions
- Re-verified 2026-09-02: Step 7's move-failure sentence is at current lines 239-240 (Plan's
  cited "line 239" is accurate to the sentence's start); Step 1's all-steps-completed move is at
  current lines 103-110. Both match the Plan's evidence with no drift.

## Design decisions
Mirror `itp010`'s proposed resolution for the shared rule (continue to the next target file
after reporting `Blocked` for the failing one) but state it independently in this file, since
`workflow.md` explicitly opts out of `rules/workflow-lifecycle.md` and a shared-rule fix would
not otherwise cover this workflow (Plan `Design`).

## Alternatives considered
Removing the opt-out clause and pointing to the shared rule instead — explicitly deferred by
the Plan's own Unknowns (UNK-01) as a separate design decision outside this issue's scope; not
done here.

## Implementation
### Target file
skills/code-implementation/workflow.md

### Procedure
Add a continuation-policy sentence to Step 7's move-failure bullet, and a short
cross-reference to it from Step 1's all-steps-completed move description.

### Method
1. Locate Step 7's current lines 239-240:
   ```
   - **If the move fails, stop and report `Blocked: move failed — {reason}`. Do not
     fall back to another method beyond the two above.**
   ```
   Append a continuation-policy sentence:
   ```
     Report `Blocked` for this specific file only — its code/test/doc changes remain
     applied and validated, and its implementation procedure document remains generated
     but unarchived — then continue Multi-file processing with the next target file in
     the batch. Do not halt the entire batch because one file's Archival Move failed.
   ```
2. Locate Step 1's all-steps-completed move description (current lines 103-110), specifically
   the sentence ending "...same rules as Step 7)". Append a cross-reference:
   ```
     If this move fails, the same continuation policy applies: report `Blocked` for this
     file only and continue to the next target file in the batch (see Step 7).
   ```

### Details
Both edits are additive sentences appended to existing bullets — no existing sentence is
removed or reworded.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure continuation-policy clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added policy is internally consistent with `rules/ai-execution.md` Sequential Target Processing (Base) and Global Safety Restrictions (Base) (Plan `Tests`).

## Completion criteria
Step 7 explicitly states the batch-continuation policy for a move failure, and Step 1's
all-steps-completed move cross-references the same policy.

## Out of scope
`rules/workflow-lifecycle.md` (covered by a separate plan, itp010, per this Plan's own
Out-of-Scope). Removing the opt-out clause that excludes `rules/workflow-lifecycle.md` from
this workflow (Plan Scope Out-of-Scope; UNK-01 left unresolved as a separate decision).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add continuation policy to Step 7 per Method | Pending | — | — | |
| 2 | Add cross-reference to Step 1 per Method | Pending | — | — | |
| 3 | N/A: no test to add (doc-only change) | Pending | — | — | N/A |
| 4 | Manual review validation | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002 (explicit batch-continuation policy for Archival Move failure)
- **Source issue**: `issues/20260901-172400_cip002_archival_move_failure_continuation_undefined.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-211611_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-152715
- **Related target files**: `skills/code-implementation/workflow.md`
