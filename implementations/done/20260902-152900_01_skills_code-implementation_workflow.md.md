## Goal
Satisfy `REQ-001` (cip003): add an explicit termination condition to
`skills/code-implementation/workflow.md` Step 3's adversarial verification, stating when
verification is sufficient and how to handle a disconfirming finding.

## Scope
Modify exactly Step 3's adversarial-verification paragraph (current lines 124-130) in
`skills/code-implementation/workflow.md`. No other line in this file is touched. Does not
change what claims Step 3 must verify (Plan Scope Out-of-Scope) — only when to stop verifying
them.

## Assumptions
- Re-verified 2026-09-02: Step 3's adversarial-verification paragraph is at current lines
  124-130, matching the Plan's cited "line 125-130" (off by one due to the `## Step 3` heading
  itself at line 123). Content matches exactly, no drift.
- Per Plan Unknowns (UNK-01, non-blocking), this document includes an investigation order
  (target file → symbol/line → call path → assumption/scope boundary), mirroring `ptip002`'s
  pattern for the sibling `plan-to-implementation-procedure` workflow, since the Plan's own
  Design section already elects to mirror that pattern.

## Design decisions
Mirror `ptip002`'s termination-condition pattern (investigation order + a stop condition: check
each item once, a disconfirming finding ends investigation for that finding rather than
triggering deeper search) adapted to this Step's specific claims (target file, symbol/line,
call path, stated dependencies) — consistent with `itp002`/`ptip002`'s resolution for the two
upstream phases, instantiated here for the one phase where verified claims gate actual code
changes (Plan `Design`, `Reason for change`).

## Alternatives considered
Omitting the investigation order and stating only a stop condition — considered but not
adopted, since the Plan's Design section explicitly elects to mirror `ptip002`'s full pattern
(order + stop condition) for consistency across the three workflows.

## Implementation
### Target file
skills/code-implementation/workflow.md

### Procedure
Append a termination-condition paragraph to Step 3's adversarial-verification instruction.

### Method
1. Locate Step 3's current lines 124-130:
   ```
   ## Step 3: Implement the Feature

   Before implementing, perform **adversarial verification** of the procedure's claims
   about current source: do not assume its Procedure/Method/Details are still
   accurate — check via `rg`/Read whether the target file, symbol, line numbers, and
   call path it describes still match current source, and whether any stated assumption
   or scope boundary is stale or inconsistent with a sibling procedure document or the
   source Plan.
   ```
2. Append, before the following "If verification finds an unconfirmed item..." paragraph:
   ```
   Stop once the target file, the specific symbol/line/call-path claims the procedure
   makes, and its stated dependencies have each been checked once against current
   source, in that order — a disconfirming finding ends investigation for that specific
   finding (the procedure document must be corrected, per the paragraph below, not
   further researched) rather than triggering deeper search.
   ```

### Details
The existing following paragraph ("If verification finds an unconfirmed item or an
inconsistency, correct the implementation procedure document itself...") is left unchanged —
the new sentence explicitly defers to it ("must be corrected... not further researched"),
preserving the requirement to correct a stale description rather than weakening it (Plan Risks
mitigation).

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure termination-condition clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added condition is consistent with Step 3's existing correction instruction and does not weaken it (Plan `Tests`).

## Completion criteria
Step 3 states a concrete, checkable condition (an investigation order plus a stop rule) under
which adversarial verification is considered complete for the current implementation procedure
document.

## Out of scope
Changing what claims Step 3 must verify (Plan Scope Out-of-Scope) — only when to stop verifying
them.

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add termination condition to Step 3 per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 127-132 matched exactly |
| 2 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 3 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed new sentence explicitly defers to the following correction paragraph, does not weaken it |
| 4 | Documentation update | Completed | 2026-09-02 | 2026-09-02 | N/A: this file is the documentation being updated; no `docs/00_index.md` task-scope mapping applies |

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
- **Requirement ID**: REQ-001 (explicit termination condition for Step 3 adversarial verification)
- **Source issue**: `issues/20260901-172400_cip003_step3_verification_lacks_termination_condition.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-211753_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-152900
- **Related target files**: `skills/code-implementation/workflow.md`
