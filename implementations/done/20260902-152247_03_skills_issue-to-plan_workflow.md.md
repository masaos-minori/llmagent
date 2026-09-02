## Goal
Satisfy `REQ-001`/`REQ-002` (itp004): add a short cross-reference near Step 8 in
`skills/issue-to-plan/workflow.md` pointing to `rules/workflow-lifecycle.md`'s new shared
Rollback-Directive-applicability clarification (seq 02, generated alongside this document),
without duplicating its text.

## Scope
Add exactly one short paragraph to `skills/issue-to-plan/workflow.md` Step 8, after the
"Report one of: `Pass` / `Fail` / `Partial` / `Blocked`..." paragraph (current lines 355-357)
and before the "Before delivering, cross-check" paragraph (current line 359). No other line in
this file is touched.

## Assumptions
- This document depends on seq 02 (`rules/workflow-lifecycle.md`'s new `## Plan-Document
  Correction Handling` section) landing in the same cycle, so the cross-reference points to
  real, existing content rather than a section that does not yet exist.
- Re-verified 2026-09-02: Step 8 currently has no statement about Rollback Directive
  applicability — confirmed by reading the full section (lines 334-363).

## Design decisions
Point to the shared rule rather than restating it (Plan `Design`, corrected 2026-09-02 after
this session found the Plan's original Design section was copy-pasted from an unrelated sibling
plan, ptip007) — avoids the two files drifting apart if the shared rule is later refined.

## Alternatives considered
Restating the full Rollback-Directive-non-applicability statement here as well as in
`rules/workflow-lifecycle.md` — rejected: duplicating the substantive text in two files risks
them drifting out of sync; a cross-reference is sufficient since this file already
cross-references other shared rules the same way (e.g. its existing references to
`rules/workflow-lifecycle.md` Implementation Target Files Validation).

## Implementation
### Target file
skills/issue-to-plan/workflow.md

### Procedure
Insert a short cross-reference paragraph into Step 8.

### Method
1. Locate the paragraph at current lines 355-357:
   ```
   Report one of: `Pass` / `Fail` / `Partial` / `Blocked`. If any requirement information
   is unmapped or untraceable, or `Implementation Target Files` is not `Frozen`, do not
   report `Pass` or `Completed`.
   ```
2. Insert immediately after it, before the "Before delivering, cross-check" paragraph:
   ```
   If Step 8 (or an earlier Step's revalidation) requires correcting the Plan document via
   Edit, see `rules/workflow-lifecycle.md` Plan-Document Correction Handling for whether
   `AGENTS.md` Rollback Directive applies (it does not) and how a repeated-correction risk is
   bounded instead.
   ```

### Details
This is a pure cross-reference addition — it does not change Step 8's Pass/Fail/Partial/
Blocked reporting logic or its cross-check list (Plan Scope Out-of-Scope).

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a cross-reference addition.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file — should be reverted
together with seq 02 if that section is rolled back, to avoid a dangling reference.

## Validation plan
- Manual review: confirm the cross-reference resolves to real content in `rules/workflow-lifecycle.md` (seq 02) and does not introduce a contradiction with `AGENTS.md` Instruction Precedence (Plan `Tests`).

## Completion criteria
Step 8 cross-references `rules/workflow-lifecycle.md`'s Plan-Document Correction Handling
section for Rollback Directive applicability, without restating its content.

## Out of scope
`rules/workflow-lifecycle.md`'s substantive clarification itself — covered by seq 02, generated
alongside this document for the same Plan. `AGENTS.md`'s Rollback Directive text (Plan Scope
Out-of-Scope).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert cross-reference paragraph per Method | Completed | 2026-09-02 | 2026-09-02 | seq 02 (`rules/workflow-lifecycle.md` Plan-Document Correction Handling) landed first in this same cycle |
| 2 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 3 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed cross-reference resolves to real heading at rules/workflow-lifecycle.md:37 |
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
- **Requirement ID**: REQ-001, REQ-002 (cross-reference to shared Rollback-Directive clarification)
- **Source issue**: `issues/20260901-170327_itp004_rollback_directive_undefined_for_plan_documents.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-215116_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-152247
- **Related target files**: `skills/issue-to-plan/workflow.md`
