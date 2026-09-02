## Goal
Satisfy `REQ-001` (ptip002): add an explicit, checkable per-row stopping condition to
`skills/plan-to-implementation-procedure/workflow.md` Step 3's adversarial verification.

## Scope
Modify exactly the sentence at current lines 138-141 of
`skills/plan-to-implementation-procedure/workflow.md` (ending "...expand beyond this order
only when evidence remains insufficient."). No other line in this file is touched.

## Assumptions
- Re-verified 2026-09-02: lines 134-141 still read exactly as the Plan's evidence describes —
  no drift since Plan creation.

## Design decisions
State the stop condition per row (target file, direct dependencies, related tests each checked
once against the Plan's claim) and a disconfirmation rule (a disconfirming finding ends
investigation for that finding — correct the Plan, don't research further), mirroring the
sibling `itp002` (issue-to-plan) finding applied to this file's per-row loop structure (Plan
`Design`).

## Alternatives considered
Leaving "expand beyond this order only when evidence remains insufficient" as the sole guard —
rejected per the Plan's Problem: this describes the trigger for going further, not a stopping
criterion, and since this Step runs once per row, an unbounded per-row depth compounds across a
multi-row Plan.

## Implementation
### Target file
skills/plan-to-implementation-procedure/workflow.md

### Procedure
Append a stopping condition and disconfirmation rule to the adversarial-verification
investigation-order sentence.

### Method
1. Locate lines 138-141 (current):
   ```
   Verify via `rg`/Read that the target file, symbol, call
   path, and test currently exist and behave as described. Investigate in this order:
   the target file itself, its direct dependencies (immediate imports/importers), then
   related tests — expand beyond this order only when evidence remains insufficient.
   ```
2. Append immediately after:
   ```
   Stop once the target file, its direct dependencies, and its related tests have each
   been checked once against the Plan's claim about them. A disconfirming finding at any
   stage ends investigation for that finding — correct the Plan (see below), rather than
   researching further to double-confirm it.
   ```

### Details
This does not change what evidence Step 3 requires finding (Plan Scope Out-of-Scope) — only
when to stop looking for it. It does not weaken or alter the existing "additional target file
discovery" escalation path or the Blocking/Non-blocking evidence-gap classification later in
this same Step.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure termination-condition clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added condition does not contradict the existing Blocking/Non-blocking classification or the "additional target file discovery" escalation path (Plan `Tests`).

## Completion criteria
Step 3 states a concrete, checkable condition under which per-row adversarial verification is
considered complete.

## Out of scope
Changing what evidence Step 3 requires finding (Plan Scope Out-of-Scope) — only when to stop
looking for it.

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add per-row stopping condition per Method | Pending | — | — | |
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
- **Requirement ID**: REQ-001 (explicit per-row stopping condition for adversarial verification)
- **Source issue**: `issues/20260901-171500_ptip002_step3_verification_lacks_termination_condition.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-212927_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-152819
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
