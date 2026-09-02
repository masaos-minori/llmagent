## Goal
Satisfy `REQ-001`/`REQ-002` (itp005): add a cause → re-entry-Step decision table to
`skills/issue-to-plan/workflow.md` Step 8, and cross-reference it from Step 9's `Fail`/
`Partial` branch.

## Scope
Modify exactly two locations in `skills/issue-to-plan/workflow.md`: Step 8, after its
`Report one of: Pass / Fail / Partial / Blocked...` paragraph (current lines 355-357), and
Step 9, after its `Pass`-only handling paragraph (current lines 377-379). No other line in this
file is touched.

## Assumptions
- Re-verified 2026-09-02: Step 8's heading is at current line 334 (matching the Plan's cited
  "line 334" exactly) and its Pass/Fail/Partial/Blocked paragraph is at lines 355-357. Step 9's
  `Pass`-only handling text is at current lines 377-379, not the Plan's originally-cited "line
  151-152" — that citation referred to a different numbering basis, not `workflow.md`'s actual
  line numbers; content matches the Plan's Background quote exactly, confirming no substantive
  drift.

## Design decisions
A three-row cause → re-entry-Step table (Plan `Design`, corrected 2026-09-02 after this session
found the Plan's original Design section was copy-pasted from an unrelated sibling plan,
itp007): unmapped-field failures → Step 4; untraceable-Requirement failures → Step 7;
`Implementation Target Files` Frozen-validation failures → the specific row's correction per
`rules/workflow-lifecycle.md`, then re-run only Step 8's freeze check. Corrections default to
the affected section(s) only, not full Plan regeneration.

## Alternatives considered
Restating the full mapping in both Step 8 and Step 9 — rejected: Step 9 only needs a
cross-reference to Step 8's table (REQ-001's "or Step 9" wording allows placing the substantive
table at either location; placing it once, at Step 8, and cross-referencing from Step 9 avoids
duplication).

## Implementation
### Target file
skills/issue-to-plan/workflow.md

### Procedure
Add the decision table after Step 8's Pass/Fail/Partial/Blocked paragraph; add a one-sentence
cross-reference after Step 9's Pass-only handling paragraph.

### Method
1. Locate Step 8's paragraph at current lines 355-357:
   ```
   Report one of: `Pass` / `Fail` / `Partial` / `Blocked`. If any requirement information
   is unmapped or untraceable, or `Implementation Target Files` is not `Frozen`, do not
   report `Pass` or `Completed`.
   ```
   Insert immediately after it:
   ```
   If Step 8 reports `Fail` or `Partial`, resume from the Step matching the failure's cause,
   not from Step 5 (full Plan regeneration), unless the cause is shown to invalidate multiple
   sections:

   | Failure cause | Re-entry Step |
   |---|---|
   | A Requirement field is unmapped | Step 4 (Issue→Plan field mapping) |
   | A Requirement is untraceable | Step 7 (Requirement Traceability) |
   | An `Implementation Target Files` row fails Plan Freeze validation | Correct that row per `rules/workflow-lifecycle.md`'s Revalidation procedure, then re-run only this Step's freeze check |

   Corrections are scoped to the affected section(s) by default.
   ```
2. Locate Step 9's paragraph at current lines 377-379:
   ```
   No human approval is required for the move to `issues/done/`, per
   `rules/workflow-lifecycle.md` Validation Reporting — proceed to Step 10 once Step 8 is
   `Pass` and all required validations are `Pass`.
   ```
   Insert immediately after it:
   ```
   If Step 8 is `Fail` or `Partial`, do not proceed to Step 10 — resume from the Step named in
   Step 8's cause → re-entry-Step table above, then re-run Step 8 before reconsidering Step 10.
   ```

### Details
This mapping does not change what Step 8 validates (Plan Scope Out-of-Scope) — only which Step
to resume from after a non-`Pass` result.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure re-entry-point clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added mapping covers every failure condition Step 8 itself names, and does not contradict `rules/workflow-lifecycle.md`'s existing Frozen-validation correction procedure (Plan `Tests`).

## Completion criteria
Step 8 states a concrete re-entry Step for each named failure category, and Step 9
cross-references it instead of leaving the `Fail`/`Partial` branch implicit.

## Out of scope
Changing what Step 8 validates (Plan Scope Out-of-Scope). The equivalent question for
`plan-to-implementation-procedure`'s own validation steps (Plan Scope Out-of-Scope — file
separately if the same gap is confirmed there).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add cause → re-entry-Step table to Step 8 per Method | Pending | — | — | |
| 2 | Add cross-reference to Step 9 per Method | Pending | — | — | |
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
- **Requirement ID**: REQ-001, REQ-002 (cause → re-entry-Step mapping for Step 8 Fail/Partial)
- **Source issue**: `issues/20260901-170327_itp005_no_re_entry_point_after_step8_fail.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-215253_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-153137
- **Related target files**: `skills/issue-to-plan/workflow.md`
