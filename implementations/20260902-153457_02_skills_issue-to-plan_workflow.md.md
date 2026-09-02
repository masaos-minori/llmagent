## Goal
Satisfy `REQ-001` (itp007): cross-reference `rules/ai-execution.md`'s new "report from the
record" rule (seq 01, generated alongside this document) from `skills/issue-to-plan/workflow.md`
Step 9, without duplicating its text.

## Scope
Add exactly one short paragraph to `skills/issue-to-plan/workflow.md` Step 9, after its report
field list (current lines 369-375) and before the "No human approval is required..." paragraph
(current lines 377-379). No other line in this file is touched.

## Assumptions
- This document depends on seq 01 (`rules/ai-execution.md`'s new Progress Reporting (Base)
  bullet) landing in the same cycle, so the cross-reference points to real, existing content.
- Re-verified 2026-09-02: Step 9's report field list is at current lines 369-375, matching the
  Plan's Background quote exactly.

## Design decisions
Point to the shared rule rather than restating it (Plan `Design`, corrected 2026-09-02 after
this session found the Plan's original Design section was boilerplate copied from an unrelated
sibling plan, not describing this Plan's own content) — avoids the two files drifting apart if
the shared rule is later refined.

## Alternatives considered
Restating the full "report from the record" rule here as well — rejected: duplicating the
substantive text in two files risks them drifting out of sync; this file already
cross-references other shared rules the same way (e.g. its existing references to
`rules/workflow-lifecycle.md` for Archival Move and Implementation Target Files Validation).

## Implementation
### Target file
skills/issue-to-plan/workflow.md

### Procedure
Insert a short cross-reference paragraph into Step 9, naming Path A/B classification as the
concrete example this Plan's Problem section identifies.

### Method
1. Locate the report field list ending at current line 375:
   ```
   Report: generated Plan path; generated Unknown/Risk files (or `None`); number of
   Requirements; number of `Implementation Target Files` rows; Path A/B classification
   (one word; rationale is in the Plan's Design section, do not restate);
   information-completeness result; traceability result; `Implementation Target Files`
   freeze status (`Frozen` / not `Frozen` with reason); unresolved items count; and the
   Issue pending move. Do not restate the Requirement Traceability evidence-classification
   breakdown — it is already in the Plan's Requirement Traceability table.
   ```
2. Insert immediately after it, before the "No human approval is required..." paragraph:
   ```
   Per `rules/ai-execution.md` Progress Reporting (Base), every value above is read back from
   where it was already recorded (e.g. the Path A/B classification from Step 3's record, the
   freeze status from Step 8's validation) — not re-derived for this report — unless the
   source is known to have changed since it was recorded.
   ```

### Details
This is a pure cross-reference addition — it does not change Step 9's report field list (Plan
Scope Out-of-Scope).

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a cross-reference addition.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file — should be reverted
together with seq 01 if that rule is rolled back, to avoid a dangling reference.

## Validation plan
- Manual review: confirm the cross-reference resolves to real content in `rules/ai-execution.md` (seq 01) and does not introduce a contradiction (Plan `Tests`).

## Completion criteria
Step 9 cross-references `rules/ai-execution.md`'s report-from-record rule, citing the Path A/B
classification as the concrete example, without restating the rule's text.

## Out of scope
`rules/ai-execution.md`'s substantive rule itself — covered by seq 01, generated alongside this
document for the same Plan. Changing what Step 9 reports (Plan Scope Out-of-Scope).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert cross-reference paragraph per Method | Pending | — | — | Depends on seq 01 landing first (or in the same cycle) |
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
- **Requirement ID**: REQ-001 (cross-reference to shared report-from-record rule)
- **Source issue**: `issues/20260901-170327_itp007_progress_reporting_reverification_ambiguity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-215724_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-153457
- **Related target files**: `skills/issue-to-plan/workflow.md`
