## Goal
- State the command for the `Work Items Created` update in `plan-to-implementation-procedure` Step 4, replacing "There is no tool for this table" (`REQ-006`: Step 4 names the command).

## Scope
- In scope: the "Record the generated documents in the Plan" paragraph of Step 4, and nothing else.
- Out of scope: Step 2, Step 3c, unit and gated-marker text (edited by sibling Plans).

## Assumptions
- Plan A5, A6, A9 apply. Step 3a verified (2026-11-02): the paragraph says each generated procedure gets one `Work Items Created` row (Item ID = repository-relative path, Related Step, Type `Procedure`, Status `Pending`, Owner and Due Date `—`) and that "There is no tool for this table; edit it directly", followed by the `close-batch` owning-Plan lookup sentence. The new command updates existing rows when procedures are archived; it does not add rows, so row creation at generation time stays a direct edit.
- Overlap (Step 2, Plan A6 and A9): this file is also targeted by flowimp002, flowimp003, flowimp007, flowimp009, and flowimp011. Judged compatible: they edit Step 2, Step 3c, the unit and gated-marker text, and the Step 4 checklist; the `Work Items Created` paragraph sits next to flowimp003's gated-marker text, so whichever lands later rebases.
- The command exists when this row executes (row 01 procedure).

## Design decisions
- Reword the "no tool" sentence into two statements: rows are added at generation time by direct edit, and they are completed later by `tools/close_procedures_batch.py` when `code-implementation` archives the procedures.
- Keep the `close-batch` owning-Plan sentence unchanged.

## Alternatives considered
- N/A: one-paragraph docs change.

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`

### Procedure
- In Step 4 "Record the generated documents in the Plan", replace the sentence "There is no tool for this table; edit it directly." with: adding the rows is a direct edit; updating their Status after execution is done by `uv run python tools/close_procedures_batch.py` (see `skills/code-implementation/workflow.md` Step 7).

### Method
- Add `tools/close_procedures_batch.py` to the Toolchain list of this workflow only if the sentence alone leaves the tool unmentioned there; otherwise keep the Toolchain list unchanged.

### Details
- Do not change the row format (Item ID, Related Step, Type, Status, Owner, Due Date).

## Compatibility considerations
- N/A: skill text.

## Security considerations
- N/A: skill text.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` report no findings.

## Completion criteria
- Step 4 states that the `Work Items Created` rows are updated by `tools/close_procedures_batch.py` after execution and no longer says the table has no tool; both checkers pass.

## Out of Scope
- Any other section of this file; changing how rows are created.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the `Work Items Created` sentence in Step 4 per Implementation > Procedure | Pending | — | — | |
| 2 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` (`routing.md` Tools "When to run which tool") | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (Step 4 states the command for the `Work Items Created` update)
- **Source issue**: issues/20261030-191530_flowimp008_workitem-bulk-close.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080631_flowimp008_workitem-bulk-close.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085613
- **Related target files**: skills/plan-to-implementation-procedure/workflow.md
