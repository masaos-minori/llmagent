## Goal
Satisfy `REQ-001` (cip007): add the same "verify the file exists in `implementations/done/`
after the move" instruction to `skills/code-implementation/workflow.md` Step 1's
all-steps-completed check that Step 7 already has.

## Scope
Modify exactly Step 1's all-steps-completed check (current lines 103-110) in
`skills/code-implementation/workflow.md`. No other line in this file is touched. Does not
change `tools/manage_workitem_stage.py`'s own behavior (Plan Scope Out-of-Scope).

## Assumptions
- Re-verified 2026-09-02: Step 1's all-steps-completed check is at current lines 103-110,
  matching the Plan's cited "line 103-110" exactly (also independently confirmed while
  processing `cip002` earlier in this batch, which cross-references this same check from Step
  7). Step 7's own "Verify the file exists in `implementations/done/` after the move." sentence
  is at current line 238, confirmed present.
- Per Plan Unknowns (UNK-01, non-blocking) and the Plan's own Assumptions/Design, the wording
  is reused identically from Step 7 rather than adapted.

## Design decisions
Reuse Step 7's exact phrasing ("Verify the file exists in `implementations/done/` after the
move.") rather than inventing new wording for the same check (Plan `Design`, `Assumptions`) —
pure consistency fix between two Steps performing the identical operation via the identical
tool.

## Alternatives considered
Adapting the wording slightly to Step 1's short-circuit context — considered per Plan Unknowns
(UNK-01) but not adopted; the Plan's own Assumptions section commits to reusing Step 7's exact
phrasing.

## Implementation
### Target file
skills/code-implementation/workflow.md

### Procedure
Append the post-move verification sentence to Step 1's all-steps-completed check.

### Method
1. Locate current lines 103-110:
   ```
   - **All-steps-completed check**: after reading the file, inspect its `## Execution Status`
     table. If every step row shows `Completed` (no `Pending`, `Blocked`, or other status),
     the procedure is fully executed — do not re-execute it. Move it to
     `implementations/done/` (same rules as Step 7): prefer `uv run python
     tools/manage_workitem_stage.py close-implementation implementations/{filename}.md`;
     fall back to `git mv implementations/{filename}.md implementations/done/{filename}.md`
     only if the tool is unavailable. Report
     `Moved to done: {filename} — all steps Completed, no further action needed`.
   ```
2. Insert the verification sentence before the final "Report..." sentence:
   ```
   - **All-steps-completed check**: after reading the file, inspect its `## Execution Status`
     table. If every step row shows `Completed` (no `Pending`, `Blocked`, or other status),
     the procedure is fully executed — do not re-execute it. Move it to
     `implementations/done/` (same rules as Step 7): prefer `uv run python
     tools/manage_workitem_stage.py close-implementation implementations/{filename}.md`;
     fall back to `git mv implementations/{filename}.md implementations/done/{filename}.md`
     only if the tool is unavailable. Verify the file exists in `implementations/done/`
     after the move. Report
     `Moved to done: {filename} — all steps Completed, no further action needed`.
   ```

### Details
This is a pure text insertion within the existing bullet — no other part of Step 1's
all-steps-completed check is reworded. Note: this document was generated in the same batch as
`cip002`'s document (which also touches Step 1's all-steps-completed check, adding a
continuation-policy cross-reference) — both edits target the same bullet but insert
non-overlapping sentences; apply both, verifying the final combined text reads coherently.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a post-move verification consistency fix.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added instruction is worded identically to Step 7's existing text (Plan `Tests`).

## Completion criteria
Step 1's all-steps-completed check includes the same post-move verification instruction Step 7
already has, worded identically.

## Out of scope
Changing `tools/manage_workitem_stage.py`'s own behavior (Plan Scope Out-of-Scope).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add post-move verification sentence to Step 1 per Method | Pending | — | — | Coordinate with `cip002`'s separate edit to the same bullet |
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
- **Requirement ID**: REQ-001 (post-move verification consistency between Step 1 and Step 7)
- **Source issue**: `issues/20260901-172400_cip007_tool_success_judged_by_exit_code_only.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-212403_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-153414
- **Related target files**: `skills/code-implementation/workflow.md`
