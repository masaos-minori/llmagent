## Goal
Satisfy `REQ-001` (cip008): add explicit correction-scope and re-validation-scope
clarification to `skills/code-implementation/workflow.md` Step 6's "fix it before proceeding
to Step 7" instruction.

## Scope
Modify exactly Step 6's final sentence (current line 210) in
`skills/code-implementation/workflow.md`. No other line in this file is touched. Does not
change what Step 6 validates (Plan Scope Out-of-Scope) — only the correction/re-validation
scope after a failure.

## Assumptions
- Re-verified 2026-09-02: the target sentence "If validation surfaces an issue, fix it before
  proceeding to Step 7." is at current line 210, matching the Plan's cited "line 210" exactly.
- Per Plan Unknowns (UNK-01, non-blocking) and the Plan's own Design section, the distinction
  between structural failures (local fix) and domain-consistency failures (may require
  revisiting Step 5's changes) is codified using the two concrete example failure types cited
  in the Plan's Problem section (`check_docs_structure.py` vs.
  `check_docs_consistency.py --domain`).

## Design decisions
State two rules together (Plan `Design`): (1) correction scope — a fix is scoped to the
specific section/claim the failing check identified, unless the fix itself touched a different
Task-scope row's content, in which case Step 5's matching procedure applies to that row too;
(2) re-validation scope — re-run only the specific checker(s) that failed, not the full Step 6
checklist, to confirm the fix.

## Alternatives considered
Leaving the structural-vs-domain-consistency distinction as general guidance rather than
codifying it with the two example failure types — considered per Plan Unknowns (UNK-01) but not
adopted; the Plan's own Design section elects to ground the distinction in the two concrete
examples already present in the Plan's Problem section.

## Implementation
### Target file
skills/code-implementation/workflow.md

### Procedure
Replace Step 6's final sentence with an expanded correction-scope and re-validation-scope
clarification.

### Method
1. Locate current line 210:
   ```
   If validation surfaces an issue, fix it before proceeding to Step 7.
   ```
2. Replace with:
   ```
   If validation surfaces an issue, the fix is scoped to the specific section/claim the
   failing check identified (e.g. a `check_docs_structure.py` broken-link finding is a
   local fix to that link) — unless the fix itself requires touching a different Task
   scope row's content (e.g. a `check_docs_consistency.py --domain` drift finding that
   traces back to what Step 5 actually changed), in which case Step 5's matching
   procedure applies to that row as well. After fixing, re-run only the specific
   checker(s) that failed to confirm the fix — not the full Step 6 checklist — then
   proceed to Step 7.
   ```

### Details
This sentence replacement does not alter Step 6's preceding checker-selection or manual-check
list (current lines 187-209) — only its final "what happens on failure" sentence.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure correction-scope clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added clarification is consistent with Step 5's existing task-scope-row matching procedure (Plan `Tests`).

## Completion criteria
Step 6 states explicitly what scope a correction should take (section-local vs. Step-5-wide)
and what re-validation is required (specific failing checker(s) only) before proceeding to
Step 7.

## Out of scope
Changing what Step 6 validates (Plan Scope Out-of-Scope) — only the correction/re-validation
scope after a failure.

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace Step 6's final sentence per Method | Pending | — | — | |
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
- **Requirement ID**: REQ-001 (correction scope and re-validation scope after Step 6 failure)
- **Source issue**: `issues/20260901-172400_cip008_step6_validation_failure_reentry_point_unclear.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-212520_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-153520
- **Related target files**: `skills/code-implementation/workflow.md`
