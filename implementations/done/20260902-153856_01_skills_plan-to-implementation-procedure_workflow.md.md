## Goal
Satisfy `REQ-001` (ptip010): reword `skills/plan-to-implementation-procedure/workflow.md`'s
"Progress recording during Step 3" so the Execution Status table write is its own,
unconditional per-row requirement, decoupled from the chat-report frequency gate.

## Scope
Modify exactly the "### Progress recording during Step 3" section (current lines 246-255) of
`skills/plan-to-implementation-procedure/workflow.md`. No other line in this file is touched.

## Assumptions
- Re-verified 2026-09-02: lines 246-255 still read exactly as the Plan's evidence describes —
  no drift since Plan creation.

## Design decisions
Keep the existing chat-report frequency gate ("Report an interim update only when...")
unchanged, and state the Execution Status write as a separate, unconditional
per-row-status-transition requirement (Plan `Design`, corrected 2026-09-02 after this session
found the Plan's original Design section was copy-pasted from an unrelated sibling plan,
itp007) — mirroring `itp007`'s resolution of the analogous ambiguity in `issue-to-plan`.

## Alternatives considered
Leaving the Execution Status write bundled inside the chat-report-frequency-gated bullet list —
rejected per the Plan's Problem: the persisted record's purpose (surviving an interruption) is
undermined if its write frequency is coupled to how often the agent chooses to narrate progress
in chat, rather than to the row's actual status transitions.

## Implementation
### Target file
skills/plan-to-implementation-procedure/workflow.md

### Procedure
Split the "Progress recording during Step 3" bullet list into a chat-report-frequency
paragraph and a separate, unconditional Execution-Status-write requirement.

### Method
1. Locate lines 246-255 (current):
   ```
   ### Progress recording during Step 3

   Report an interim update only when a row's outcome is Blocked, Partially implemented,
   fails verification, produces a Plan Gap, or is an additional target file discovery —
   do not report for a row that completes as Already implemented or Not
   implemented→newly created without incident:
   - Note which target file you are working on
   - Record the current status (In Progress / Blocked / Completed) for each row
   - If blocked, describe the blocker and whether it requires user intervention
   - Update the Execution Status table in the output document
   ```
2. Replace with two separated requirements:
   ```
   ### Progress recording during Step 3

   **Chat-facing reporting** (frequency-gated): report an interim update only when a
   row's outcome is Blocked, Partially implemented, fails verification, produces a Plan
   Gap, or is an additional target file discovery — do not report for a row that
   completes as Already implemented or Not implemented→newly created without incident.
   When reporting, note which target file you are working on, record the current status
   (In Progress / Blocked / Completed), and if blocked, describe the blocker and whether
   it requires user intervention.

   **Execution Status table write** (unconditional, per row): update the Execution
   Status table in the output document every time a row's status changes, regardless of
   whether an interim chat report is also made for that row. This persisted record is
   the recovery mechanism if the session is interrupted mid-pass — it must not be
   skipped merely because the chat-report frequency gate above did not trigger for that
   row.
   ```

### Details
This does not change the Execution Status table's own structure or content requirements (Plan
Scope Out-of-Scope) — only when the write happens relative to the chat-report frequency gate.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the reworded section keeps the existing chat-report frequency gate unchanged and only decouples the file-write requirement from it (Plan `Tests`).

## Completion criteria
The Execution Status write requirement is stated as unconditional per row-status-transition,
independent of the chat-report frequency gate, which remains unchanged.

## Out of scope
Changing the Execution Status table's own structure or content requirements (Plan Scope
Out-of-Scope).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Split Progress recording section per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 297-306 matched exactly (51-line shift due to prior edits, within tolerance) |
| 2 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 3 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed chat-report frequency gate preserved verbatim; only decoupling made explicit |
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
- **Requirement ID**: REQ-001 (unconditional per-row Execution Status write, decoupled from chat-report frequency)
- **Source issue**: `issues/20260901-171500_ptip010_progress_recording_couples_reporting_to_file_writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-214325_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-153856
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
