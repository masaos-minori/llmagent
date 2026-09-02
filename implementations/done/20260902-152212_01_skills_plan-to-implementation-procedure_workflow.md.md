## Goal
Satisfy `REQ-001`/`REQ-002` (ptip007): state explicitly in
`skills/plan-to-implementation-procedure/workflow.md` Step 3 that the resumed-cycle
path-collision `Needs confirmation` case is terminal-for-this-cycle, not retriable.

## Scope
Modify exactly the sentence at current lines 219-222 of
`skills/plan-to-implementation-procedure/workflow.md` (the resumed-cycle path-collision
`Needs confirmation` case, ending "...Stop and report `Needs confirmation` for this row
instead."). No other line in this file is touched.

## Assumptions
- Re-verified 2026-09-02: the target sentence is at current line 222 ("report `Needs
  confirmation` for this row instead") — a 3-line shift from the Plan's originally-cited
  "line 222-223" is within normal drift tolerance; content matches the Plan's evidence
  exactly, confirming no substantive change since Plan creation.

## Design decisions
Decide the case is terminal-for-this-cycle, not bounded-retriable with an arbitrary `N` (Plan
`Design`, corrected 2026-09-02 after this session found the Plan's original Design section was
copy-pasted from an unrelated sibling plan, ptip003) — a naming/path collision from an
interrupted cycle does not resolve itself by re-attempting in the same session; it needs a
human to resolve the underlying interrupted-cycle state.

## Alternatives considered
Defining a numeric retry bound `N` mirroring `AGENTS.md`'s Attempt Limit (3) — rejected: that
precedent applies to retrying a *fix* after a *failure signal changes*; a path collision's
underlying cause (an existing file at the destination path) does not change by retrying without
human action, so a retry count would not be meaningful here.

## Implementation
### Target file
skills/plan-to-implementation-procedure/workflow.md

### Procedure
Add a terminal-for-this-cycle statement immediately after the resumed-cycle path-collision
sentence.

### Method
1. Locate the sentence ending at current line 222 (context, current lines ~219-223):
   ```
   - If the resulting path already exists, this can only mean an interrupted cycle is
     being resumed and the classification above did not treat it as covering this row
     (e.g. stale or partial-scope content) — it MUST NOT be overwritten. Stop and
     report `Needs confirmation` for this row instead. The tool's own collision
     refusal is the same signal, not a separate failure mode.
   ```
2. Append, before the next bullet:
   ```
     This `Needs confirmation` report is terminal for this cycle, not retriable: do not
     re-attempt the same row again within the same pass. Report it once; Step 4's "every
     row... accounted for" check is satisfied by this single stopped attempt. A human must
     resolve the underlying interrupted-cycle state (confirm whether the existing file is
     stale, partial, or already covers the row) before any future run revisits this row.
   ```

### Details
This applies only to the resumed-cycle path-collision case (case 3 in the Plan's Background),
not to cases 1-2 (traceability ambiguity, non-blocking evidence gap), which already "proceed"
with a document written and a caveat — those are unaffected by this row.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure wording clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added statement is consistent with Step 4's existing "accounted for" language (Plan `Tests`).

## Completion criteria
Step 3 explicitly states the resumed-cycle path-collision `Needs confirmation` case is
terminal-for-this-cycle, and that Step 4's "accounted for" check is satisfied by a single
stopped attempt.

## Out of scope
The three `Needs confirmation` trigger conditions themselves (Plan Scope Out-of-Scope) — not
redefined by this row, only case 3's retry/terminal status.

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add terminal-for-this-cycle statement per Method | Completed | 2026-09-02 | 2026-09-02 | Target sentence found at line 220-224 (3-line drift from Plan's cited 219-223, within tolerance); content matched exactly |
| 2 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 3 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed consistent with Step 4's "accounted for" language (line 275) |
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
- **Requirement ID**: REQ-001, REQ-002 (state terminal-for-this-cycle status for resumed-cycle collision)
- **Source issue**: `issues/20260901-171500_ptip007_needs_confirmation_report_has_no_retry_bound.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-213745_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-152212
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
