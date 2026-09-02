## Goal
Satisfy `REQ-001` (cip004): split `skills/code-implementation/workflow.md`'s "Progress
recording during Steps 3-6" into a chat-report frequency rule (kept as currently gated) and an
unconditional per-Step-transition Execution Status write rule.

## Scope
Modify exactly the "### Progress recording during Steps 3-6" section (current lines 57-67) in
`skills/code-implementation/workflow.md`. No other line in this file is touched. Does not
change the Execution Status table's structure (`templates/execution-status.md`, Plan Scope
Out-of-Scope).

## Assumptions
- Re-verified 2026-09-02: the section is at current lines 57-67, matching the Plan's cited
  "line 57-67" exactly, no drift.
- Per Plan Unknowns (UNK-01, non-blocking), the Execution Status write is unconditional per
  Step *transition* (not only at Step completion boundaries), matching the Plan's own Design
  section wording ("every Step transition/completion").

## Design decisions
Mirror `ptip010`'s resolution pattern for the sibling `plan-to-implementation-procedure`
workflow: keep the chat-report frequency gate exactly as currently worded ("when a sub-task's
outcome differs from expected, or when moving between artifact types"), and state the
Execution Status file write as unconditional and independent of that gate — proportionally more
important here since this phase spans four Steps (3-6) rather than `ptip010`'s single Step 3
(Plan `Reason for change`).

## Alternatives considered
Leaving the two requirements combined and only clarifying wording — rejected: the Plan's
Problem is structural (the file write's trigger is coupled to the chat-report trigger), not
merely a wording ambiguity; a structural split is required to close the staleness gap.

## Implementation
### Target file
skills/code-implementation/workflow.md

### Procedure
Split the section into two explicitly separate parts: an unchanged chat-report frequency
gate, and a new, unconditional Execution Status write requirement.

### Method
1. Locate current lines 57-67:
   ```
   ### Progress recording during Steps 3-6

   Record status when a sub-task's outcome differs from expected, or when moving between
   artifact types (code → test → doc):
   - Note the current artifact (code, test, or documentation)
   - Record status (In Progress / Blocked / Completed) per sub-task
   - If blocked, describe the blocker and whether it requires user intervention
   - Update the implementation procedure file's own `## Execution Status` section (via
     Edit) with the current step's Status/Started/Completed — the persisted record if
     the session is interrupted before Step 7's move. Also update the final report's
     Execution Status table.
   ```
2. Replace with two explicitly separate parts under the same heading:
   ```
   ### Progress recording during Steps 3-6

   **Chat-report frequency** (when to tell the user something): report status when a
   sub-task's outcome differs from expected, or when moving between artifact types
   (code → test → doc):
   - Note the current artifact (code, test, or documentation)
   - Record status (In Progress / Blocked / Completed) per sub-task
   - If blocked, describe the blocker and whether it requires user intervention

   **Execution Status file write** (unconditional, independent of the chat-report
   frequency gate above): update the implementation procedure file's own
   `## Execution Status` section (via Edit) with the current step's Status/Started/
   Completed at every Step transition or completion within Steps 3-6, regardless of
   whether a chat report is also made for that transition — this is the persisted
   record if the session is interrupted before Step 7's move. Also update the final
   report's Execution Status table.
   ```

### Details
The chat-report bullet list (artifact/status/blocker-description) is preserved verbatim under
the "Chat-report frequency" heading — only its trigger condition's independence from the file
write is made explicit; no existing chat-reporting content is removed (Plan Risks mitigation:
"Align wording... noting the independent statement requirement").

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure structural clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the reworded section keeps the existing chat-report frequency gate unchanged and only decouples the file-write requirement (Plan `Tests`).

## Completion criteria
The Execution Status write requirement is stated as unconditional per Step transition/
completion (Steps 3 through 6), independent of the chat-report frequency gate, and the
chat-report frequency gate itself is unchanged.

## Out of scope
Changing the Execution Status table's structure (`templates/execution-status.md`, Plan Scope
Out-of-Scope, unaffected by this issue).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Split section into chat-report gate and unconditional file-write requirement per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 57-67 matched exactly |
| 2 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 3 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed chat-report bullet list preserved verbatim; only trigger independence made explicit |
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
- **Requirement ID**: REQ-001 (decouple Execution Status write from chat-report frequency gate)
- **Source issue**: `issues/20260901-172400_cip004_progress_recording_couples_reporting_to_file_writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-212023_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-153001
- **Related target files**: `skills/code-implementation/workflow.md`
